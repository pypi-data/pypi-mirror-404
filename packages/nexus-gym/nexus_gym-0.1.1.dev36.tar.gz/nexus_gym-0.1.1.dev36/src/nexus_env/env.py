"""
Nexus Platformer Gymnasium Environment

A Gymnasium-compatible environment for training RL agents on the Nexus platformer game.
Communicates with a browser-based game simulation via WebSocket.
"""

import gymnasium as gym
from gymnasium import spaces
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
import webbrowser
import http.server
import socketserver
from functools import partial

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Represents the current state of the game."""
    player_x: float = 0.0
    player_y: float = 0.0
    player_vx: float = 0.0
    player_vy: float = 0.0
    player_grounded: bool = False
    stars_collected: int = 0
    total_stars: int = 0
    goal_x: float = 0.0
    goal_y: float = 0.0
    level_width: float = 800.0
    is_dead: bool = False
    level_complete: bool = False
    platforms: list = None
    hazards: list = None
    collectibles: list = None
    raycasts: list = None
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = []
        if self.hazards is None:
            self.hazards = []
        if self.collectibles is None:
            self.collectibles = []
        if self.raycasts is None:
            self.raycasts = []


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
        # SimpleHTTPRequestHandler.log_message is an instance method, 
        # but partial makes it hard to override. We can wrap the handler.
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


class NexusPlatformerEnv(gym.Env):
    """
    Gymnasium environment for the Nexus Platformer game.
    
    Observation Space:
        A Box space containing:
        - Player position (x, y) normalized
        - Player velocity (vx, vy) normalized
        - Player grounded (0 or 1)
        - Distance to goal (x, y) normalized
        - Stars collected ratio
        - Nearest platform info (relative position)
        - Nearest hazard info (relative position)
        - Nearest uncollected star info (relative position)
    
    Action Space:
        Discrete(5):
        - 0: No action
        - 1: Move left
        - 2: Move right
        - 3: Jump
        - 4: Jump + Move left
        - 5: Jump + Move right (actually 6 actions but we use MultiDiscrete or combine)
        
        Or MultiDiscrete([3, 2]):
        - First: 0=none, 1=left, 2=right
        - Second: 0=no jump, 1=jump
    
    Rewards:
        - +1 for collecting each star
        - +100 for completing the level
        - -10 for dying
        - Small negative reward per step to encourage efficiency
    """
    
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}
    
    # Available themes (must match THEMES in platformer_with_training.jsx)
    AVAILABLE_THEMES = [
        'crystal_caves',
        'volcanic_depths',
        'cyber_district',
        'enchanted_forest',
        'frozen_peaks',
        'desert_ruins',
        'cosmic_void',
        'steampunk_factory',
    ]

    def __init__(
        self,
        render_mode: Optional[str] = None,
        ws_host: str = "localhost",
        ws_port: int = 8765,
        http_port: int = 8080,
        auto_launch: bool = True,
        max_steps: int = 5000,
        level_config: Optional[Dict] = None,
        step_penalty: float = -0.01,
        theme: str = "cyber_district",
        max_star_reward: float = 100.0,  # New: Max reward for collecting a star quickly
        min_star_reward: float = 10.0,   # New: Min reward for collecting a star
        star_decay_rate: float = 1.0,    # New: Rate at which star reward decays per step
    ):
        """
        Initialize the Nexus Platformer environment.
        
        Args:
            render_mode: "human" to auto-launch browser, None for headless
            ws_host: WebSocket server host
            ws_port: WebSocket server port
            http_port: HTTP server port for serving game files
            auto_launch: Whether to automatically launch the browser
            max_steps: Maximum steps per episode
            level_config: Optional level configuration dict
            step_penalty: Small negative reward per step
            theme: Visual theme for the game. Options: crystal_caves, volcanic_depths,
                   cyber_district, enchanted_forest, frozen_peaks, desert_ruins,
                   cosmic_void, steampunk_factory. Default: cyber_district
            max_star_reward: Maximum reward for a star, received if collected instantly.
            min_star_reward: Minimum reward for a star, acts as a floor for decay.
            star_decay_rate: How much the star reward decreases per step taken.
        """
        super().__init__()
        
        # Validate theme
        if theme not in self.AVAILABLE_THEMES:
            logger.warning(f"Unknown theme '{theme}'. Available themes: {self.AVAILABLE_THEMES}. Using 'cyber_district'.")
            theme = "cyber_district"

        self.render_mode = render_mode
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.http_port = http_port
        self.auto_launch = auto_launch
        self.max_steps = max_steps
        self.level_config = level_config
        self.step_penalty = step_penalty
        self.theme = theme
        self.max_star_reward = max_star_reward
        self.min_star_reward = min_star_reward
        self.star_decay_rate = star_decay_rate
        
        # Observation space: 22-dimensional continuous
        # Observation space: 40-dimensional continuous
        # [player_vx, player_vy, grounded, goal_dx, goal_dy, stars_ratio,
        #  level_progress, can_reach_goal,
        #  ray1_dist, ray1_type, ..., ray16_dist, ray16_type]
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(40,),
            dtype=np.float32
        )
        
        # Action space: MultiDiscrete for movement and jump
        # [0,1,2] for none/left/right, [0,1] for no jump/jump
        self.action_space = spaces.MultiDiscrete([3, 2])
        
        # Internal state
        self.ws_server: Optional[WebSocketServer] = None
        self.http_server: Optional[HTTPServerThread] = None
        self.current_state: Optional[GameState] = None
        self.prev_stars_collected = 0
        self.steps = 0
        self.last_star_collection_step = 0 # New: Track when the last star was collected
        self.prev_action = [0, 0]
        self.episode_count = 0
        self._initialized = False
        
    def _get_game_dir(self) -> str:
        """Get the directory containing the game files."""
        # First, check for a built Vite app in common locations
        cwd = os.getcwd()
        possible_paths = [
            os.path.join(cwd, "sim", "dist"),  # New structure
            os.path.join(cwd, "dist"),  # Old structure legacy
            os.path.join(cwd, "..", "sim", "dist"),
            os.path.join(os.path.dirname(__file__), "..", "..", "sim", "dist"),
            os.path.join(os.path.dirname(__file__), "static"),  # Fallback to static (batteries included)
        ]
        
        logger.debug(f"Current working directory: {cwd}")
        logger.debug(f"Searching for game files in: {possible_paths}")
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path) and os.path.isdir(abs_path):
                # Check if it has index.html
                if os.path.exists(os.path.join(abs_path, "index.html")):
                    logger.info(f"Using game files from: {abs_path}")
                    return abs_path
        
        # Default fallback
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        logger.info(f"Using fallback static directory: {static_dir}")
        return static_dir
    
    def _get_game_url(self) -> str:
        """Get the URL to open in the browser."""
        game_dir = self._get_game_dir()
        
        # Check if this is a Vite build (has index.html)
        if os.path.exists(os.path.join(game_dir, "index.html")):
            # For Vite build, add training mode query params including theme and ray visualization
            url = f"http://localhost:{self.http_port}/?training=true&ws=ws://{self.ws_host}:{self.ws_port}&theme={self.theme}&rays=true"
            logger.info(f"Detected Vite build, using training mode URL with theme '{self.theme}' and rays=true")
            return url
        else:
            # Fallback to standalone trainer HTML
            return f"http://localhost:{self.http_port}/nexus_trainer.html"
        
    def _start_servers(self):
        """Start WebSocket and HTTP servers."""
        if self._initialized:
            return
            
        # Start WebSocket server
        self.ws_server = WebSocketServer(self.ws_host, self.ws_port)
        self.ws_server.start()
        
        # Start HTTP server for game files
        game_dir = self._get_game_dir()
        if os.path.exists(game_dir):
            self.http_server = HTTPServerThread(self.http_port, game_dir)
            self.http_server.start()
            
        self._initialized = True
        
    def _launch_browser(self):
        """Launch the game in a web browser."""
        url = self._get_game_url()
        logger.info(f"Launching browser at {url}")
        webbrowser.open(url)
        
    def _wait_for_game(self, timeout: float = 60.0) -> bool:
        """Wait for the game client to connect."""
        url = self._get_game_url()
        logger.info("=" * 60)
        logger.info("WAITING FOR GAME CLIENT")
        logger.info(f"Please open your browser at: {url}")
        logger.info("=" * 60)

        if self.ws_server.wait_for_connection(timeout):
            logger.info("Game client connected! Starting training...")
            time.sleep(1.0)  # Give the game time to stabilize
            return True

        logger.error("-" * 60)
        logger.error("CONNECTION TIMEOUT")
        logger.error(f"The game client failed to connect to the RL environment within {timeout}s.")
        logger.error(f"Make sure you have opened: {url}")
        logger.error("-" * 60)
        return False
        
    def _get_observation(self) -> np.ndarray:
        """Convert game state to observation vector."""
        if self.current_state is None:
            return np.zeros(40, dtype=np.float32)
            
        state = self.current_state
        
        # Normalize positions (assuming max level width ~2000, height ~600)
        max_x = max(state.level_width, 800)
        max_y = 450
        
        player_x_norm = state.player_x / max_x
        player_y_norm = state.player_y / max_y
        player_vx_norm = state.player_vx / 10.0  # Max velocity ~10
        player_vy_norm = state.player_vy / 20.0  # Max velocity ~20
        grounded = 1.0 if state.player_grounded else 0.0
        
        # Goal direction
        goal_dx = (state.goal_x - state.player_x) / max_x
        goal_dy = (state.goal_y - state.player_y) / max_y
        
        # Stars ratio
        stars_ratio = state.stars_collected / max(state.total_stars, 1)
        
        # Find nearest platform
        nearest_plat_dx, nearest_plat_dy, nearest_plat_w = 0.0, 0.0, 0.0
        dist_to_left, dist_to_right = 0.0, 0.0

        min_dist = float('inf')
        for plat in state.platforms:
            plat_x = plat.get('x', 0)
            plat_y = plat.get('y', 0)
            plat_w = plat.get('width', 0)

            # Center of platform
            plat_center_x = plat_x + plat_w / 2

            dx = plat_center_x - state.player_x
            dy = plat_y - state.player_y
            dist = abs(dx) + abs(dy)

            if dist < min_dist:
                min_dist = dist
                nearest_plat_dx = dx / max_x
                nearest_plat_dy = dy / max_y
                nearest_plat_w = plat_w / max_x

                # Calculate distance to edges relative to player
                # Positive means edge is to the right, negative means to the left
                # Player at 100, Left Edge at 0 -> -100 (Edge is to left)
                # Player at 100, Right Edge at 200 -> +100 (Edge is to right)
                
                # However, for normalizing and stable learning, absolute distance
                # might be better if we just want "how close am I to falling",
                # but signed distance gives direction. Let's use signed.

                left_edge_x = plat_x
                right_edge_x = plat_x + plat_w

                dist_to_left = (left_edge_x - state.player_x) / max_x
                dist_to_right = (right_edge_x - state.player_x) / max_x

        # Find nearest hazard
        nearest_hazard_dx, nearest_hazard_dy = 1.0, 1.0  # Default far away
        min_dist = float('inf')
        for hazard in state.hazards:
            dx = hazard.get('x', 0) - state.player_x
            dy = hazard.get('y', 0) - state.player_y
            dist = abs(dx) + abs(dy)
            if dist < min_dist:
                min_dist = dist
                nearest_hazard_dx = dx / max_x
                nearest_hazard_dy = dy / max_y
                
        # Find nearest uncollected star
        nearest_star_dx, nearest_star_dy = 1.0, 1.0  # Default far away
        min_dist = float('inf')
        for i, col in enumerate(state.collectibles):
            if col.get('collected', False):
                continue
            dx = col.get('x', 0) - state.player_x
            dy = col.get('y', 0) - state.player_y
            dist = abs(dx) + abs(dy)
            if dist < min_dist:
                min_dist = dist
                nearest_star_dx = dx / max_x
                nearest_star_dy = dy / max_y
                
        # Level progress (how far right we've moved)
        level_progress = state.player_x / max_x
        
        # Can reach goal (all stars collected)
        can_reach_goal = 1.0 if state.stars_collected >= state.total_stars else 0.0
        
        # Raycasts (32 values: 16 rays * [dist, type])
        raycast_obs = np.array(state.raycasts, dtype=np.float32)
        if len(raycast_obs) != 32:
            # Fallback if raycasts missing or wrong size
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
        
    def _compute_reward(self, prev_state: Optional[GameState], new_state: Optional[GameState]) -> Tuple[float, Dict[str, float]]:
        """Compute the reward for the current transition."""
        components = {
            "step": self.step_penalty,
            "stars": 0.0,
            "shaping": 0.0,
            "completion": 0.0,
            "death": 0.0
        }

        if new_state is None:
            return components["step"], components
            
        # Star collection reward with time decay
        if prev_state:
            stars_gained = new_state.stars_collected - prev_state.stars_collected
            if stars_gained > 0:
                steps_taken_for_star = self.steps - self.last_star_collection_step
                decayed_reward = max(
                    self.min_star_reward,
                    self.max_star_reward - (steps_taken_for_star * self.star_decay_rate)
                )
                components["stars"] = decayed_reward * stars_gained # Apply decay per star gained
                self.last_star_collection_step = self.steps # Update last collected step
            else:
                components["stars"] = 0.0 # No star gained, no reward

            # Unified Distance Shaping
            # Guide agent to nearest star (if any) or to goal (if done)
            dist_prev = self._get_dist_to_current_objective(prev_state)
            dist_new = self._get_dist_to_current_objective(new_state)

            if dist_prev < float('inf') and dist_new < float('inf') and not new_state.is_dead:
                # Reward for getting closer to objective
                shaping_delta = (dist_prev - dist_new) * 0.2
                components["shaping"] += np.clip(shaping_delta, -1.0, 1.0)
            
            # Hazard Proximity Penalty
            # "Pain" signal when getting too close to a hazard (within 50 units)
            # This teaches avoidance without needing to die
            dist_to_hazard = self._get_min_dist_to_hazard(new_state)
            HAZARD_THRESHOLD = 50.0
            if dist_to_hazard < HAZARD_THRESHOLD:
                 # Linear penalty from 0 at threshold to -0.05 at contact
                 # Reduced from -1.0 to prevent excessive "fear" accumulation
                 penalty = -0.05 * (1.0 - (dist_to_hazard / HAZARD_THRESHOLD))
                 components["shaping"] += penalty

        # Level completion reward
        if new_state.level_complete:
            components["completion"] = 500.0
            
        # Death penalty
        # Increased to -50.0 to make death significantly worse than surviving
        if new_state.is_dead:
            components["death"] = -50.0
            
        total_reward = sum(components.values())
        return total_reward, components

    def _get_min_dist_to_star(self, state: GameState) -> float:
        """Calculate the Manhattan distance to the nearest uncollected star."""
        min_dist = float('inf')
        if not state.collectibles:
            return min_dist

        for col in state.collectibles:
            if not col.get('collected', False):
                dx = abs(col.get('x', 0) - state.player_x)
                dy = abs(col.get('y', 0) - state.player_y)
                dist = dx + dy
                if dist < min_dist:
                    min_dist = dist
        return min_dist

    def _get_min_dist_to_hazard(self, state: GameState) -> float:
        """Calculate the Manhattan distance to the nearest hazard."""
        min_dist = float('inf')
        if not state.hazards:
            return min_dist

        for hazard in state.hazards:
            dx = abs(hazard.get('x', 0) - state.player_x)
            dy = abs(hazard.get('y', 0) - state.player_y)
            dist = dx + dy
            if dist < min_dist:
                min_dist = dist
        return min_dist
        
    def _get_dist_to_current_objective(self, state: GameState) -> float:
        """
        Calculate distance to the current objective.
        If stars remain: Distance to nearest uncollected star.
        If all stars collected: Manhattan distance to goal.
        """
        # If in a terminating state (dead or won), distance is irrelevant for shaping
        if state.is_dead or state.level_complete:
            return float('inf')

        if state.stars_collected < state.total_stars:
            return self._get_min_dist_to_star(state)

        # All stars collected, objective is the goal
        dx = abs(state.goal_x - state.player_x)
        dy = abs(state.goal_y - state.player_y)
        return dx + dy

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """Reset the environment."""
        super().reset(seed=seed)
        
        # Start servers if needed
        self._start_servers()
        
        # Launch browser if render_mode is "human" and auto_launch is True
        if self.render_mode == "human" and self.auto_launch and not self.ws_server.connected_event.is_set():
            self._launch_browser()
            
        # Wait for game client
        if not self.ws_server.connected_event.is_set():
            if not self._wait_for_game():
                raise RuntimeError("Failed to connect to game client")

        # Wait for user to click "Start Training"
        if not self.ws_server.start_event.is_set():
            logger.info("Waiting for user to click Start Training...")
            # We can optionally send a status update here if we want the UI to know we are waiting
            self.ws_server.start_event.wait()
            logger.info("Start Training signal received!")
        
        # Increment episode counter
        self.episode_count += 1
        
        # Send reset command with episode count
        level_config = options.get("level_config") if options else self.level_config
        self.ws_server.state_received_event.clear()
        self.ws_server.send_reset_sync(level_config, self.episode_count)
        
        # Wait for state update
        if not self.ws_server.state_received_event.wait(timeout=5.0):
            logger.warning("Timeout waiting for state after reset")
            
        self.current_state = self.ws_server.get_state()
        self.prev_stars_collected = 0
        self.steps = 0
        self.last_star_collection_step = 0 # Reset for new episode
        self.prev_action = [0, 0]
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
        
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute one step in the environment."""
        # Convert action to game commands
        move_action = int(action[0])  # 0=none, 1=left, 2=right
        jump_action = int(action[1])  # 0=no jump, 1=jump
        
        action_msg = {
            "type": "action",
            "left": move_action == 1,
            "right": move_action == 2,
            "jump": jump_action == 1,
        }
        
        prev_state = self.current_state
        
        # Send action and wait for state update
        self.ws_server.state_received_event.clear()
        self.ws_server.send_action_sync(action_msg)
        
        # Wait briefly for state update
        self.ws_server.state_received_event.wait(timeout=0.1)
        
        self.current_state = self.ws_server.get_state()
        self.steps += 1
        self.prev_action = [move_action, jump_action]
        
        # Compute reward and components
        reward, reward_components = self._compute_reward(prev_state, self.current_state)
        
        # Check termination conditions
        terminated = False
        truncated = False
        
        if self.current_state:
            if self.current_state.is_dead:
                terminated = True
            elif self.current_state.level_complete:
                terminated = True
                
        if self.steps >= self.max_steps:
            truncated = True
            
        observation = self._get_observation()
        info = self._get_info()
        
        # Add reward components and episode stats to info
        info["reward_components"] = reward_components
        if terminated or truncated:
            # For SB3 WandbEpisodeCallback to pick up components at end of episode
            info["episode_components"] = reward_components

        return observation, reward, terminated, truncated, info
        
    def _get_info(self) -> Dict[str, Any]:
        """Get additional info about the current state."""
        if self.current_state is None:
            return {
                "stars_collected": 0,
                "total_stars": 0,
                "level_complete": False,
                "is_dead": False,
                "player_x": 0,
                "player_y": 0,
                "steps": self.steps,
            }
            
        return {
            "stars_collected": self.current_state.stars_collected,
            "total_stars": self.current_state.total_stars,
            "level_complete": self.current_state.level_complete,
            "is_dead": self.current_state.is_dead,
            "player_x": self.current_state.player_x,
            "player_y": self.current_state.player_y,
            "steps": self.steps,
        }
        
    def render(self):
        """Render the environment."""
        if self.render_mode == "human":
            pass  # Game renders in browser
        elif self.render_mode == "rgb_array":
            # Would need to capture browser screenshot
            logger.warning("rgb_array render mode not fully implemented")
            return np.zeros((500, 800, 3), dtype=np.uint8)
            
    def close(self):
        """Clean up resources."""
        logger.info("Closing environment...")
        
        # Stop HTTP server first
        if self.http_server:
            try:
                self.http_server.stop()
            except Exception as e:
                logger.debug(f"HTTP server stop error: {e}")
            self.http_server = None
            
        # Stop WebSocket server
        if self.ws_server:
            try:
                self.ws_server.stop()
            except Exception as e:
                logger.debug(f"WebSocket server stop error: {e}")
            self.ws_server = None
            
        self._initialized = False
        
        # Suppress any remaining asyncio warnings
        import warnings
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop.*")
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*was destroyed.*")


# Convenience function for creating the environment
def make_nexus_env(**kwargs) -> NexusPlatformerEnv:
    """Create a Nexus Platformer environment with default settings."""
    return NexusPlatformerEnv(**kwargs)
