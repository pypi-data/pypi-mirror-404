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
import numpy as np
from dotenv import load_dotenv
import hydra
from omegaconf import DictConfig, OmegaConf

import nexus_env
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, CallbackList
from nexus_env.callbacks.wandb_callback import WandbMetricsCallback, WandbEpisodeCallback
from nexus_env.callbacks.save_model_callback import SaveModelCallback
from nexus_env.callbacks.hf_upload_callback import HFUploadCallback
from pathlib import Path
import wandb
    

# Load .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus-train-hf")

app = FastAPI(title="Nexus Gym Training")


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
    retries = 10
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

# Mount static files
static_dir = get_static_path()
if static_dir:
    app.mount("/", StaticFiles(directory=static_dir), name="static")

def run_ppo_training(cfg: DictConfig):
    """Start PPO training in the background."""    
    # Wait for FastAPI to start
    time.sleep(5)
    
    logger.info("=" * 60)
    logger.info("Nexus Platformer RL Training (Server Mode)")
    logger.info("=" * 60)
    logger.info(f"Config:\n{OmegaConf.to_yaml(cfg)}")

    while True:
        env = None
        try:
            logger.info("Setting up environment...")
            
            # Create environment
            raw_env = nexus_env.make(
                render_mode=cfg.env.render_mode,
                theme=cfg.env.theme,
                auto_launch=cfg.env.auto_launch,
                max_steps=cfg.env.max_episode_steps,
                step_penalty=cfg.env.step_penalty
            )
            
            # Explicitly wrap the environment to avoid SB3 warnings
            logger.info("Wrapping environment with Monitor and DummyVecEnv...")
            monitored_env = Monitor(raw_env)
            env = DummyVecEnv([lambda: monitored_env])

            logger.info(f"Observation space: {env.observation_space}")
            logger.info(f"Action space: {env.action_space}")

            logger.info("Creating model...")
            logger.info("Creating new PPO model")

            # Finish any existing W&B run from a previous loop iteration
            if wandb.run is not None:
                wandb.finish()

            # Initialize W&B if API key is present
            if cfg.callbacks.wandb.enabled and os.environ.get("WANDB_API_KEY"):
                algo_name = cfg.algo.get("name", "ppo")
                theme_name = cfg.env.get("theme", "default")

                wandb.init(
                    project=cfg.callbacks.wandb.project,
                    entity=cfg.callbacks.wandb.entity,
                    name=f"nexus-{algo_name}-{theme_name}-{int(time.time())}",
                    config=OmegaConf.to_container(cfg, resolve=True),
                    sync_tensorboard=False,
                    monitor_gym=True
                )
            else:
                logger.warning("WANDB_API_KEY not found. W&B logging disabled.")

            # Check if tensorboard is available
            tb_log = "./tensorboard_logs"
            try:
                import tensorboard
            except ImportError:
                logger.warning("Tensorboard not found, disabling logging.")
                tb_log = None

            # Model hyperparameters
            model = PPO(
                "MlpPolicy",
                env,
                verbose=cfg.algo.verbose,
                learning_rate=cfg.algo.learning_rate,
                n_steps=cfg.algo.n_steps,
                batch_size=cfg.algo.batch_size,
                n_epochs=cfg.algo.n_epochs,
                gamma=cfg.algo.gamma,
                ent_coef=cfg.algo.ent_coef,
                tensorboard_log=cfg.algo.tensorboard_log,
                policy_kwargs=OmegaConf.to_container(cfg.algo.policy_kwargs, resolve=True)
            )
            
            # Callbacks list
            callbacks_list = [
                CheckpointCallback(
                    save_freq=cfg.callbacks.checkpoint.save_freq,
                    save_path=cfg.callbacks.checkpoint.save_path,
                    name_prefix=cfg.callbacks.checkpoint.name_prefix
                ),
                SaveModelCallback(
                    save_path=cfg.callbacks.save_model.save_path,
                    verbose=cfg.callbacks.save_model.verbose
                )
            ]
            
            if cfg.callbacks.wandb.enabled and os.environ.get("WANDB_API_KEY"):
                algo_name = cfg.algo.get("name", "ppo")
                theme_name = cfg.env.get("theme", "default")

                callbacks_list.append(WandbMetricsCallback(verbose=1))
                callbacks_list.append(WandbEpisodeCallback(
                    project=cfg.callbacks.wandb.project,
                    entity=cfg.callbacks.wandb.entity,
                    run_name=f"nexus-{algo_name}-{theme_name}",
                    verbose=1
                ))

            # --------------------------------------------------------
            # HF Upload Callback
            # --------------------------------------------------------
            if cfg.callbacks.hf_upload.enabled:
                # Use the same path as SaveModelCallback
                model_path = cfg.callbacks.save_model.save_path

                hf_cb = HFUploadCallback(
                    cfg=cfg,
                    model_path=model_path,
                    push_strategy=cfg.callbacks.hf_upload.push_strategy,
                    verbose=1
                )
                callbacks_list.append(hf_cb)

            callbacks = CallbackList(callbacks_list)
            
            logger.info(f"Starting training ({cfg.trainer.total_timesteps} steps)...")
            model.learn(
                total_timesteps=cfg.trainer.total_timesteps,
                callback=callbacks,
                reset_num_timesteps=cfg.trainer.reset_num_timesteps,
                progress_bar=cfg.trainer.progress_bar
            )
            
            logger.info("Training session complete. Restarting...")
            
        except Exception as e:
            logger.error(f"Training agent error: {e}. Retrying in 10s...")
            time.sleep(10)
        finally:
            if env:
                try:
                    logger.info("Cleaning up environment...")
                    env.close()
                except Exception as ce:
                    logger.error(f"Cleanup error: {ce}")

            if wandb.run is not None:
                wandb.finish()

            # Give a small gap for ports to release
            time.sleep(2)

@hydra.main(config_path="configs", config_name="config", version_base="1.3")
def main(cfg: DictConfig):
    # Ensure headless mode on HF Space
    cfg.env.render_mode = None
    cfg.env.auto_launch = False

    # Mount static files
    static_dir = get_static_path()
    if static_dir:
        app.mount("/", StaticFiles(directory=static_dir), name="static")

    # Start the training agent in a background thread
    threading.Thread(target=run_ppo_training, args=(cfg,), daemon=True).start()
    
    port = int(os.environ.get("PORT", 7860))
    # Note: run_ppo_training is already using cfg.env.theme
    logger.info(f"[TRAINING MODE] Starting FastAPI on port {port} with theme {cfg.env.theme}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
