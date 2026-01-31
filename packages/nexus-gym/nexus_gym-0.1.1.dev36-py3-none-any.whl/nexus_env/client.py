import numpy as np
import requests
from typing import List, Dict, Any, Optional
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from nexus_env.types import GameState

class NexusOpenEnvClient(EnvClient[List[int], np.ndarray, GameState]):
    """
    OpenEnv client for the Nexus Platformer game.
    Communicates with the Nexus OpenEnv Server via HTTP.
    """
    def __init__(self, base_url: str = "http://localhost:8000"):
        # We manually initialize without super().__init__ to skip WebSocket setup
        self.base_url = base_url.rstrip("/")
        self._message_timeout = 10.0
        self._connected = True

    def connect(self) -> None:
        """No-op for stateless HTTP client."""
        self._connected = True

    def close(self) -> None:
        """No-op for stateless HTTP client."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Checks if the client is effectively 'connected'."""
        return self._connected

    def _step_payload(self, action: List[int]) -> Dict[str, Any]:
        """Convert action into payload for the server."""
        return {"action": action}

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[np.ndarray]:
        """Convert server response into a StepResult."""
        obs_raw = payload.get("observation", [])
        observation = np.array(obs_raw, dtype=np.float32)
        reward = payload.get("reward", 0.0)
        done = payload.get("done", False)
        
        return StepResult(
            observation=observation,
            reward=float(reward if reward is not None else 0.0),
            done=bool(done)
        )

    def _parse_state(self, payload: Dict[str, Any]) -> GameState:
        """Convert server response into GameState."""
        return GameState(**payload)

    def _send_and_receive(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hijack the internal message routing to use HTTP REST endpoints.
        """
        msg_type = message.get("type")
        data = message.get("data", {})
        
        try:
            if msg_type == "reset":
                response = requests.post(f"{self.base_url}/reset", json=data, timeout=self._message_timeout)
            elif msg_type == "step":
                response = requests.post(f"{self.base_url}/step", json=data, timeout=self._message_timeout)
            elif msg_type == "state":
                response = requests.get(f"{self.base_url}/state", timeout=self._message_timeout)
            else:
                return {}
                
            response.raise_for_status()
            return {"data": response.json()}
        except Exception as e:
            raise RuntimeError(f"Nexus OpenEnv HTTP Error ({msg_type}): {e}")

    def get_state(self) -> GameState:
        """Custom helper to fetch state, used by the Gymnasium adapter."""
        message = {"type": "state"}
        response = self._send_and_receive(message)
        return self._parse_state(response.get("data", {}))
