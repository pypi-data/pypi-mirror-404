import numpy as np
import asyncio
import websockets
import json
import threading
import time
import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import subprocess
import sys
import os
from .types import GameState
import webbrowser
import http.server
import socketserver
from functools import partial

logger = logging.getLogger(__name__)

# GameState has been moved to nexus_env.types to prevent circular imports


class WebSocketServer:
    """Manages WebSocket communication with the game client."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.client = None
        self.loop = None
        self.thread = None
        self.running = False
        self.state_queue = asyncio.Queue()
        self.action_queue = asyncio.Queue()
        self.connected_event = threading.Event()
        self.state_received_event = threading.Event()
        self.latest_state: Optional[GameState] = None
        self.last_reset_msg: Optional[Dict] = None
        self._lock = threading.Lock()
        self.start_event = threading.Event()
        
    async def handler(self, websocket):
        """Handle incoming WebSocket connections."""
        logger.info(f"Game client connected from {websocket.remote_address}")
        self.client = websocket
        self.connected_event.set()
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data.get("type") == "state":
                    state = GameState(
                        player_x=data.get("player_x", 0),
                        player_y=data.get("player_y", 0),
                        player_vx=data.get("player_vx", 0),
                        player_vy=data.get("player_vy", 0),
                        player_grounded=data.get("player_grounded", False),
                        stars_collected=data.get("stars_collected", 0),
                        total_stars=data.get("total_stars", 0),
                        goal_x=data.get("goal_x", 0),
                        goal_y=data.get("goal_y", 0),
                        level_width=data.get("level_width", 800),
                        is_dead=data.get("is_dead", False),
                        level_complete=data.get("level_complete", False),
                        platforms=data.get("platforms", []),
                        hazards=data.get("hazards", []),
                        collectibles=data.get("collectibles", []),
                        raycasts=data.get("raycasts", []),
                    )
                    with self._lock:
                        self.latest_state = state
                    self.state_received_event.set()
                    
                elif data.get("type") == "ready":
                    logger.info("Game client ready")
                    with self._lock:
                        if self.last_reset_msg:
                            logger.info("Resending last reset message to new client")
                            # Run in background to not block the handler loop
                            asyncio.create_task(self.send_reset(
                                level_config=self.last_reset_msg.get("level_config"),
                                episode_count=self.last_reset_msg.get("episode_count")
                            ))

                elif data.get("type") == "start":
                    logger.info("Received START command from client")
                    self.start_event.set()
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Game client disconnected")
        finally:
            self.client = None
            self.connected_event.clear()
            self.start_event.clear()  # Reset start status on disconnect
            
    async def send_action(self, action: Dict[str, Any]):
        """Send an action to the game client."""
        if self.client:
            try:
                await self.client.send(json.dumps(action))
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Failed to send action: client disconnected")
                
    async def send_reset(self, level_config: Optional[Dict] = None, episode_count: int = 0):
        """Send reset command to the game client."""
        msg = {"type": "reset", "episode_count": episode_count}
        if level_config:
            msg["level_config"] = level_config
        if self.client:
            try:
                await self.client.send(json.dumps(msg))
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Failed to send reset: client disconnected")
        
        with self._lock:
            self.last_reset_msg = msg
                
    async def run_server(self):
        """Run the WebSocket server."""
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=20,
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        self._stop_event = asyncio.Event()
        await self._stop_event.wait()
        
    async def _shutdown(self):
        """Gracefully shutdown the server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
        
    def start(self):
        """Start the WebSocket server in a background thread."""
        if self.running:
            return
            
        self.running = True
        self.loop = asyncio.new_event_loop()
        
        def run():
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.run_server())
            except Exception as e:
                if self.running:  # Only log if not intentionally stopped
                    logger.error(f"Server error: {e}")
            finally:
                # Clean up pending tasks
                try:
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
                self.loop.close()
            
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the WebSocket server."""
        if not self.running:
            return
        self.running = False
        
        if self.loop and self.loop.is_running():
            # Schedule graceful shutdown
            future = asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop)
            try:
                future.result(timeout=2.0)
            except Exception:
                pass  # Ignore shutdown errors
            
    def wait_for_connection(self, timeout: float = 30.0) -> bool:
        """Wait for a game client to connect."""
        logger.info(f"Waiting for game client to connect on {self.host}:{self.port} (timeout={timeout}s)...")
        res = self.connected_event.wait(timeout=timeout)
        if res:
            logger.info("Connection event detected!")
        else:
            logger.warning("Connection event timed out.")
        return res
    
    def get_state(self) -> Optional[GameState]:
        """Get the latest game state."""
        with self._lock:
            return self.latest_state
        
    def send_action_sync(self, action: Dict[str, Any]):
        """Synchronously send an action to the game."""
        if self.loop and self.client:
            future = asyncio.run_coroutine_threadsafe(
                self.send_action(action),
                self.loop
            )
            try:
                future.result(timeout=1.0)
            except Exception as e:
                logger.warning(f"Error sending action: {e}")
                
    def send_reset_sync(self, level_config: Optional[Dict] = None, episode_count: int = 0):
        """Synchronously send a reset command."""
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(
                self.send_reset(level_config, episode_count),
                self.loop
            )
            try:
                future.result(timeout=5.0)
            except Exception as e:
                logger.warning(f"Error sending reset: {e}")


class HTTPServerThread(threading.Thread):
    """Serves the game HTML file."""
    
    def __init__(self, port: int = 8080, directory: str = "."):
        super().__init__(daemon=True)
        self.port = port
        self.directory = directory
        self.server = None
        self._original_dir = os.getcwd()
        
    def run(self):
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=self.directory)
        class NonLoggingHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args): pass
        
        handler = partial(NonLoggingHandler, directory=self.directory)
        
        try:
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                httpd.allow_reuse_address = True
                self.server = httpd
                logger.info(f"HTTP server started on http://localhost:{self.port} serving {self.directory}")
                httpd.serve_forever()
        except OSError as e:
            logger.warning(f"HTTP server error: {e}")
            
    def stop(self):
        if self.server:
            self.server.shutdown()


def compute_observation(state: Optional[GameState]) -> np.ndarray:
    """Convert game state to observation vector."""
    if state is None:
        return np.zeros(40, dtype=np.float32)
        
    # Normalize positions
    max_x = max(state.level_width, 800)
    max_y = 450
    
    player_x_norm = state.player_x / max_x
    player_y_norm = state.player_y / max_y
    player_vx_norm = state.player_vx / 10.0
    player_vy_norm = state.player_vy / 20.0
    grounded = 1.0 if state.player_grounded else 0.0
    
    goal_dx = (state.goal_x - state.player_x) / max_x
    goal_dy = (state.goal_y - state.player_y) / max_y
    
    stars_ratio = state.stars_collected / max(state.total_stars, 1)
    
    # Platform info (nearest)
    nearest_plat_dx, nearest_plat_dy, nearest_plat_w = 0.0, 0.0, 0.0
    min_dist = float('inf')
    for plat in state.platforms:
        plat_x = plat.get('x', 0)
        plat_y = plat.get('y', 0)
        plat_w = plat.get('width', 0)
        plat_center_x = plat_x + plat_w / 2
        dx = plat_center_x - state.player_x
        dy = plat_y - state.player_y
        dist = abs(dx) + abs(dy)
        if dist < min_dist:
            min_dist = dist
            nearest_plat_dx = dx / max_x
            nearest_plat_dy = dy / max_y
            nearest_plat_w = plat_w / max_x

    # Level progress
    level_progress = state.player_x / max_x
    can_reach_goal = 1.0 if state.stars_collected >= state.total_stars else 0.0
    
    # Raycasts
    raycast_obs = np.array(state.raycasts, dtype=np.float32)
    if len(raycast_obs) != 32:
        raycast_obs = np.zeros(32, dtype=np.float32)

    obs = np.concatenate([
        np.array([
            player_vx_norm, player_vy_norm,
            grounded,
            goal_dx, goal_dy,
            stars_ratio,
            level_progress,
            can_reach_goal
        ], dtype=np.float32),
        raycast_obs
    ])
    
    return obs


def compute_reward(prev_state: Optional[GameState], new_state: Optional[GameState], 
                   step_penalty: float = -0.01, max_star_reward: float = 100.0,
                   min_star_reward: float = 10.0, star_decay_rate: float = 1.0,
                   steps: int = 0, last_star_collection_step: int = 0) -> Tuple[float, Dict[str, float]]:
    """Compute the reward for the current transition."""
    components = {
        "step": step_penalty,
        "stars": 0.0,
        "shaping": 0.0,
        "completion": 0.0,
        "death": 0.0
    }

    if new_state is None:
        return components["step"], components
        
    if prev_state:
        stars_gained = new_state.stars_collected - prev_state.stars_collected
        if stars_gained > 0:
            steps_taken_for_star = steps - last_star_collection_step
            decayed_reward = max(
                min_star_reward,
                max_star_reward - (steps_taken_for_star * star_decay_rate)
            )
            components["stars"] = decayed_reward * stars_gained
        
        # Shaping
        def get_dist_to_obj(s: GameState):
            if s.is_dead or s.level_complete: return float('inf')
            if s.stars_collected < s.total_stars:
                # Nearest star
                min_s_dist = float('inf')
                for col in s.collectibles:
                    if not col.get('collected', False):
                        dist = abs(col.get('x', 0) - s.player_x) + abs(col.get('y', 0) - s.player_y)
                        if dist < min_s_dist: min_s_dist = dist
                return min_s_dist
            else:
                return abs(s.goal_x - s.player_x) + abs(s.goal_y - s.player_y)

        dist_prev = get_dist_to_obj(prev_state)
        dist_new = get_dist_to_obj(new_state)
        if dist_prev < float('inf') and dist_new < float('inf') and not new_state.is_dead:
            shaping_delta = (dist_prev - dist_new) * 0.2
            components["shaping"] += np.clip(shaping_delta, -1.0, 1.0)
            
        # Hazard proximity
        min_h_dist = float('inf')
        for hazard in new_state.hazards:
            dist = abs(hazard.get('x', 0) - new_state.player_x) + abs(hazard.get('y', 0) - new_state.player_y)
            if dist < min_h_dist: min_h_dist = dist
        
        HAZARD_THRESHOLD = 50.0
        if min_h_dist < HAZARD_THRESHOLD:
             penalty = -0.05 * (1.0 - (min_h_dist / HAZARD_THRESHOLD))
             components["shaping"] += penalty

    if new_state.level_complete:
        components["completion"] = 500.0
    if new_state.is_dead:
        components["death"] = -50.0
        
    total_reward = sum(components.values())
    return total_reward, components
