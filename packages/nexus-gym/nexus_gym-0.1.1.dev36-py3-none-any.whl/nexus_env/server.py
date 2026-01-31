from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uvicorn
import os
import logging
from nexus_env.types import GameState
from nexus_env.common import WebSocketServer, HTTPServerThread, logger
import numpy as np

app = FastAPI(title="Nexus OpenEnv Server")

# Global state
ws_server: Optional[WebSocketServer] = None
http_server: Optional[HTTPServerThread] = None

class StepRequest(BaseModel):
    action: List[int]  # [move, jump]

class ResetRequest(BaseModel):
    level_config: Optional[Dict] = None

class StepResponse(BaseModel):
    observation: List[float]
    reward: float
    done: bool
    truncated: bool
    info: Dict[str, Any]

class ResetResponse(BaseModel):
    observation: List[float]
    info: Dict[str, Any]

def get_observation(state: GameState) -> List[float]:
    """Convert GameState to observation vector (copied from env.py)."""
    # ... logic from NexusPlatformerEnv._get_observation ...
    # Simplified version for now, or I should move the logic to common.py if it's identical
    # For now, I'll copy the logic or assume it's provided by a helper
    
    # Actually, I'll move this logic to common.py to avoid duplication
    from nexus_env.common import compute_observation
    return compute_observation(state).tolist()

@app.on_event("startup")
async def startup_event():
    global ws_server, http_server
    ws_host = os.getenv("WS_HOST", "localhost")
    ws_port = int(os.getenv("WS_PORT", 8765))
    http_port = int(os.getenv("HTTP_PORT", 8080))
    
    ws_server = WebSocketServer(ws_host, ws_port)
    ws_server.start()
    
    # Find game files
    # Reuse _get_game_dir logic
    game_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sim", "dist"))
    if not os.path.exists(game_dir):
         game_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
    
    http_server = HTTPServerThread(http_port, game_dir)
    http_server.start()
    logger.info(f"OpenEnv Server started. Game files served from {game_dir}")

@app.on_event("shutdown")
async def shutdown_event():
    if ws_server:
        ws_server.stop()
    if http_server:
        http_server.stop()

@app.post("/reset", response_model=ResetResponse)
async def reset(request: Optional[ResetRequest] = None):
    if not ws_server or not ws_server.connected_event.is_set():
        raise HTTPException(status_code=503, detail="No game client connected. Please open the game UI in your browser.")
    
    level_config = request.level_config if request else None
    ws_server.state_received_event.clear()
    ws_server.send_reset_sync(level_config)
    
    if not ws_server.state_received_event.wait(timeout=5.0):
        raise HTTPException(status_code=504, detail="Timeout waiting for game state after reset")
    
    state = ws_server.get_state()
    from nexus_env.common import compute_observation
    obs = compute_observation(state)
    return ResetResponse(observation=obs.tolist(), info={})

@app.post("/step", response_model=StepResponse)
async def step(request: StepRequest):
    move_action = request.action[0]
    jump_action = request.action[1]
    
    action_msg = {
        "type": "action",
        "left": move_action == 1,
        "right": move_action == 2,
        "jump": jump_action == 1,
    }
    
    if not ws_server or not ws_server.connected_event.is_set():
        raise HTTPException(status_code=503, detail="No game client connected. Please open the game UI in your browser.")
    
    prev_state = ws_server.get_state()
    ws_server.state_received_event.clear()
    ws_server.send_action_sync(action_msg)
    
    if not ws_server.state_received_event.wait(timeout=1.0):
         # Fallback to latest state if no update received
         logger.warning("Timeout waiting for state update after step")
    
    new_state = ws_server.get_state()
    from nexus_env.common import compute_observation, compute_reward
    
    obs = compute_observation(new_state)
    reward, components = compute_reward(prev_state, new_state)
    
    done = new_state.is_dead or new_state.level_complete
    truncated = False # Add logic if max steps reached
    
    return StepResponse(
        observation=obs.tolist(),
        reward=reward,
        done=done,
        truncated=truncated,
        info=components
    )

@app.get("/state")
async def get_state():
    state = ws_server.get_state()
    if not state:
        raise HTTPException(status_code=404, detail="No state available")
    return state.__dict__

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
