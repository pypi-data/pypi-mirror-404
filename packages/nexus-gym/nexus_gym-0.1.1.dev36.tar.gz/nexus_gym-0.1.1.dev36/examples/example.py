#!/usr/bin/env python3
"""
Simple example of using the Nexus Gym environment.

This script demonstrates:
1. Creating the environment
2. Running random actions
3. Basic training with PPO

Run this after installing the package:
    cd nexus_gym
    pip install -e ".[sb3]"
    python example.py
    python example.py --train
    python example.py --theme volcanic_depths
"""

import time
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Available themes
THEMES = [
    'crystal_caves',
    'volcanic_depths',
    'cyber_district',
    'enchanted_forest',
    'frozen_peaks',
    'desert_ruins',
    'cosmic_void',
    'steampunk_factory',
]


def run_random_agent(theme: str = "cyber_district"):
    """Run a random agent to test the environment."""
    import nexus_env
    
    logger.info(f"Creating environment with theme '{theme}'...")
    env = nexus_env.make(render_mode="human", theme=theme)
    
    logger.info("Waiting for browser connection...")
    logger.info("")
    logger.info("=" * 60)
    logger.info("IMPORTANT: Make sure your React app has training mode enabled!")
    logger.info("1. Replace src/platformer.jsx with platformer_with_training.jsx")
    logger.info("2. Run: npm run build")
    logger.info("3. The browser should open with ?training=true parameter")
    logger.info("=" * 60)
    logger.info("")
    
    obs, info = env.reset()
    logger.info(f"Initial observation shape: {obs.shape}")
    logger.info(f"Action space: {env.action_space}")
    
    total_reward = 0
    steps = 0
    episodes = 0
    
    logger.info("Running random agent for 5 episodes...")
    
    while episodes < 5:
        # Random action: [movement (0-2), jump (0-1)]
        action = env.action_space.sample()
        
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1
        
        if terminated or truncated:
            episodes += 1
            logger.info(f"Episode {episodes} finished: "
                       f"Reward={total_reward:.2f}, Steps={steps}, "
                       f"Stars={info.get('stars_collected', 0)}/{info.get('total_stars', 0)}, "
                       f"Complete={info.get('level_complete', False)}")
            total_reward = 0
            steps = 0
            obs, info = env.reset()
        
        # Small delay for visualization
        time.sleep(0.02)
    
    env.close()
    logger.info("Random agent test complete!")


def train_simple_ppo(theme: str = "cyber_district"):
    """Train a PPO agent for a short time."""
    try:
        from stable_baselines3 import PPO
    except ImportError:
        logger.error("stable-baselines3 not installed. Install with: pip install stable-baselines3")
        return
    
    import nexus_env
    
    logger.info(f"Creating environment with theme '{theme}'...")
    env = nexus_env.make(render_mode="human", theme=theme)
    
    logger.info("Creating PPO model...")
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        ent_coef=0.01,
    )
    
    logger.info("Training for 50,000 timesteps...")
    logger.info("Watch the browser to see the agent learning!")
    
    try:
        model.learn(total_timesteps=50000, progress_bar=True)
    except KeyboardInterrupt:
        logger.info("Training interrupted")
    
    # Save model
    model.save("nexus_ppo_example")
    logger.info("Model saved to nexus_ppo_example.zip")
    
    # Evaluate
    logger.info("Evaluating trained agent for 3 episodes...")
    obs, info = env.reset()
    episodes = 0
    total_reward = 0
    
    while episodes < 3:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        if terminated or truncated:
            episodes += 1
            logger.info(f"Eval Episode {episodes}: Reward={total_reward:.2f}, "
                       f"Stars={info.get('stars_collected', 0)}, "
                       f"Complete={info.get('level_complete', False)}")
            total_reward = 0
            obs, info = env.reset()
        
        time.sleep(0.02)
    
    env.close()
    logger.info("Training complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexus Gym Example")
    parser.add_argument("--train", action="store_true", help="Run PPO training instead of random agent")
    parser.add_argument("--theme", type=str, default="cyber_district",
                        choices=THEMES,
                        help=f"Visual theme for the game. Options: {', '.join(THEMES)}")

    args = parser.parse_args()
    
    if args.train:
        train_simple_ppo(theme=args.theme)
    else:
        logger.info("Running random agent test. Use --train for PPO training.")
        logger.info(f"Available themes: {', '.join(THEMES)}")
        run_random_agent(theme=args.theme)
