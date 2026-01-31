import os
import sys
import asyncio
import logging
import time
import threading
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.websockets import WebSocketState
import websockets
import json

from dotenv import load_dotenv
import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import CallbackList
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.vec_env import DummyVecEnv
    from nexus_env.callbacks.hf_upload_callback import HFUploadCallback
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False


# Load .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus-fastapi")

app = FastAPI(title="Nexus Gym")


def get_static_path():
    """Find the best path for index.html using absolute paths."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, "sim", "dist"),
        os.path.join(base_dir, "src", "nexus_env", "static"),
    ]
    for p in paths:
        if os.path.exists(os.path.join(p, "index.html")):
            return p
    return None

@app.get("/")
async def get_index(request: Request, theme: str = "cyber_district", training: str = "true", ws: str = None):
    # theme param above is just for default if not provided in URL
    host = request.headers.get("host", "localhost:7860")
    if ws is None:
        # Determine current protocol
        protocol = "wss" if "hf.space" in host or request.headers.get("x-forwarded-proto") == "https" else "ws"
        new_ws = f"{protocol}://{host}/ws"
        logger.info(f"Redirecting to include default params: theme={theme}, ws={new_ws}")
        return RedirectResponse(url=f"/?training={training}&theme={theme}&ws={new_ws}&rays=true")
    
    static_dir = get_static_path()
    if static_dir:
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return {
        "error": "Game simulation not built. Run 'npm run build' first.",
        "cwd": os.getcwd(),
        "base_dir": base_dir,
        "checked_paths": [
            os.path.join(base_dir, "dist"),
            os.path.join(base_dir, "nexus_package", "nexus_env", "static")
        ],
        "exists_dist": os.path.exists(os.path.join(base_dir, "dist")),
        "exists_static": os.path.exists(os.path.join(base_dir, "nexus_package", "nexus_env", "static"))
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

# WebSocket Proxy Logic
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to FastAPI WebSocket proxy")
    
    target_url = "ws://localhost:8765"
    retries = 3
    target_ws = None

    # Try to connect to the target WebSocket with retries
    for i in range(retries):
        try:
            target_ws = await websockets.connect(target_url, open_timeout=2)
            logger.info(f"Connected to local nexus-gym WebSocket at {target_url} (Attempt {i+1})")
            break
        except Exception as e:
            if i < retries - 1:
                logger.warning(f"WebSocket proxy connection attempt {i+1} failed: {e}. Retrying in 2s...")
                await asyncio.sleep(2)
            else:
                logger.error(f"WebSocket proxy could not connect to {target_url} after {retries} attempts: {e}")
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.close()
                return

    try:
        async def client_to_target():
            try:
                while True:
                    data = await websocket.receive_text()
                    await target_ws.send(data)
            except Exception:
                pass

        async def target_to_client():
            try:
                while True:
                    data = await target_ws.recv()
                    await websocket.send_text(data)
            except Exception:
                pass

        await asyncio.gather(client_to_target(), target_to_client())
            
    except Exception as e:
        logger.error(f"WebSocket proxy session error: {e}")
    finally:
        if target_ws:
            await target_ws.close()
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()

def run_random_agent(theme: str):
    import nexus_env
    env = nexus_env.make(render_mode=None, theme=theme, auto_launch=False)
    
    while True:
        obs, info = env.reset()
        if info.get("stars_collected") is None:
            time.sleep(5)
            continue
            
        done = False
        while not done:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            time.sleep(0.05)
        
        time.sleep(1)

def run_rl_agent(cfg: DictConfig):
    """Start RL agent (Training or Random) in background."""
    import nexus_env
    theme = cfg.env.theme
    
    # Wait a bit for FastAPI to start
    time.sleep(2)
    
    if not SB3_AVAILABLE:
        logger.warning("Stable-Baselines3 not found. Defaulting to random agent.")
        run_random_agent(theme)
        return

    mode = cfg.get("mode", "train")
    if mode == "train":
        try:
            logger.info(f"Starting PPO training with theme: {theme}")

            # Use config settings for local dev convenience
            render_mode = cfg.env.get("render_mode", "human")
            auto_launch = cfg.env.get("auto_launch", True)

            raw_env = nexus_env.make(
                render_mode=render_mode,
                theme=theme,
                auto_launch=auto_launch
            )

            # Explicitly wrap to avoid warnings
            logger.info("Wrapping environment with Monitor and DummyVecEnv...")
            monitored_env = Monitor(raw_env)
            env = DummyVecEnv([lambda: monitored_env])

            # Setup Callbacks
            callbacks = []
            
            # HF Upload Callback
            if cfg.callbacks.hf_upload.enabled:
                save_path = Path("checkpoints/nexus_ppo_final.zip")
                hf_cb = HFUploadCallback(
                    cfg=cfg,
                    model_path=str(save_path),
                    push_strategy=cfg.callbacks.hf_upload.push_strategy,
                    verbose=1
                )
                callbacks.append(hf_cb)
            
            # Initialize Model
            model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./logs")
            
            # Train
            total_timesteps = cfg.trainer.get("total_timesteps", 100000)
            model.learn(total_timesteps=total_timesteps, callback=callbacks)
            
            logger.info("Training finished.")
            
            # Keep environment alive with trained model (optional inference loop)
            # while True: ...
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback to random
            logger.info("Falling back to random agent...")
            run_random_agent(theme)
    else:
        run_random_agent(theme)

@hydra.main(config_path="configs", config_name="config", version_base="1.3")
def main(cfg: DictConfig):
    # Determine theme from config
    theme = cfg.env.theme

    # Mount static files
    static_dir = get_static_path()
    if static_dir:
        app.mount("/", StaticFiles(directory=static_dir), name="static")

    # Start the agent in a background thread
    threading.Thread(target=run_rl_agent, args=(cfg,), daemon=True).start()
    
    port = int(os.environ.get("PORT", 7860))
    logger.info(f"Starting FastAPI on port {port} with theme {theme}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
