"""
Nexus Gym - A Gymnasium environment for the Nexus Platformer game.

This package provides a Gymnasium-compatible environment for training 
reinforcement learning agents on the Nexus platformer game using 
WebSocket communication between Python and the browser-based game.

Example usage:
    import nexus_gym
    from stable_baselines3 import PPO
    
    # Create environment (auto-launches browser in human mode)
    env = nexus_gym.make(render_mode="human")
    
    # Train with PPO
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=100000)
    
    # Or use the environment directly
    obs, info = env.reset()
    for _ in range(1000):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            obs, info = env.reset()
    
    env.close()
"""

# Avoid top-level import of env to prevent circular dependency with Gymnasium
# from nexus_env.env import NexusPlatformerEnv, make_nexus_env, GameState, WebSocketServer

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("nexus-gym")
except PackageNotFoundError:
    __version__ = "unknown"
__all__ = ["NexusPlatformerEnv", "make_nexus_env", "GameState", "WebSocketServer", "make"]


def make(render_mode=None, **kwargs):
    """
    Create a Nexus Platformer environment.
    
    Args:
        render_mode: "human" to launch browser automatically, None for headless
        **kwargs: Additional arguments passed to NexusPlatformerEnv
        
    Returns:
        NexusPlatformerEnv instance
    """
    from nexus_env.env import NexusPlatformerEnv
    return NexusPlatformerEnv(render_mode=render_mode, **kwargs)


# Register with Gymnasium
try:
    import gymnasium as gym
    from gymnasium.envs.registration import registry
    
    if "NexusPlatformer-v0" not in registry:
        gym.register(
            id="NexusPlatformer-v0",
            entry_point="nexus_env.env:NexusPlatformerEnv",
            max_episode_steps=5000,
        )
except Exception:
    pass  # Gymnasium not available or registration failed
