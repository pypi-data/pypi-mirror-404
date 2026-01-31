#!/usr/bin/env python3
"""
Nexus Platformer RL Training Script

This script demonstrates how to train a PPO agent on the Nexus Platformer
game using Stable-Baselines3.

"""
import argparse
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()
import hydra
from omegaconf import DictConfig, OmegaConf

import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment(cfg: DictConfig):
    """Create and configure the environment."""
    import nexus_env
    
    env = nexus_env.make(
        render_mode=cfg.env.render_mode,
        ws_port=8765, # Fixed for local training usually
        http_port=8080, # Fixed for local training usually
        auto_launch=cfg.env.auto_launch,
        max_steps=cfg.env.max_episode_steps,
        step_penalty=cfg.env.step_penalty,
        theme=cfg.env.theme,
    )
    
    return env


def create_model(env, cfg: DictConfig):
    """Create or load the PPO model."""
    from stable_baselines3 import PPO
    
    logger.info(f"Creating model: {cfg.algo.name}")
    
    # Model hyperparameters
    policy_kwargs = OmegaConf.to_container(cfg.algo.policy_kwargs, resolve=True)
    
    if cfg.algo.resume_path and os.path.exists(cfg.algo.resume_path):
        logger.info(f"Resuming from checkpoint: {cfg.algo.resume_path}")
        model = PPO.load(cfg.algo.resume_path, env=env)
    else:
        logger.info("Creating new PPO model")
        model = PPO(
            "MlpPolicy",
            env,
            verbose=cfg.algo.verbose,
            learning_rate=cfg.algo.learning_rate,
            n_steps=cfg.algo.n_steps,
            batch_size=cfg.algo.batch_size,
            n_epochs=cfg.algo.n_epochs,
            gamma=cfg.algo.gamma,
            gae_lambda=cfg.algo.gae_lambda,
            clip_range=cfg.algo.clip_range,
            ent_coef=cfg.algo.ent_coef,
            vf_coef=cfg.algo.vf_coef,
            max_grad_norm=cfg.algo.max_grad_norm,
            policy_kwargs=policy_kwargs,
            tensorboard_log=cfg.algo.tensorboard_log,
        )
    
    return model


def setup_callbacks(cfg: DictConfig, env):
    """Setup training callbacks."""
    from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback
    from nexus_env.callbacks.wandb_callback import WandbMetricsCallback, WandbEpisodeCallback
    from nexus_env.callbacks.save_model_callback import SaveModelCallback
    import wandb
    
    callbacks_list = []
    
    # Standard Checkpoint
    checkpoint_callback = CheckpointCallback(
        save_freq=cfg.callbacks.checkpoint.save_freq,
        save_path=cfg.callbacks.checkpoint.save_path,
        name_prefix=cfg.callbacks.checkpoint.name_prefix
    )
    callbacks_list.append(checkpoint_callback)

    # WandB
    if cfg.callbacks.wandb.enabled and os.environ.get("WANDB_API_KEY"):
        wandb.init(
            project=cfg.callbacks.wandb.project,
            entity=cfg.callbacks.wandb.entity,
            name=f"nexus-ppo-{cfg.env.theme}-{int(time.time())}",
            config=OmegaConf.to_container(cfg, resolve=True),
            sync_tensorboard=False,
            monitor_gym=True
        )
        callbacks_list.append(WandbMetricsCallback(verbose=1))
        callbacks_list.append(WandbEpisodeCallback(
            project=cfg.callbacks.wandb.project,
            entity=cfg.callbacks.wandb.entity,
            run_name=f"nexus-ppo-{cfg.env.theme}",
            verbose=1
        ))

    # Save Model
    callbacks_list.append(SaveModelCallback(
        save_path=cfg.callbacks.save_model.save_path,
        verbose=cfg.callbacks.save_model.verbose
    ))
    
    return CallbackList(callbacks_list)


def train(cfg: DictConfig):
    """Main training loop."""
    logger.info("=" * 60)
    logger.info("Nexus Platformer RL Training")
    logger.info("=" * 60)
    
    # Create directories
    os.makedirs(cfg.callbacks.checkpoint.save_path, exist_ok=True)
    os.makedirs(cfg.algo.tensorboard_log, exist_ok=True)
    
    # Setup environment
    logger.info("Setting up environment...")
    env = setup_environment(cfg)
    
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.vec_env import DummyVecEnv
    
    logger.info("Wrapping environment with Monitor and DummyVecEnv...")
    monitored_env = Monitor(env)
    env = DummyVecEnv([lambda: monitored_env])

    logger.info(f"Observation space: {env.observation_space}")
    logger.info(f"Action space: {env.action_space}")
    
    # Create model
    logger.info("Creating model...")
    model = create_model(env, cfg)
    
    # Setup callbacks
    callbacks = setup_callbacks(cfg, env)
    
    # Train
    logger.info(f"Starting training for {cfg.trainer.total_timesteps} timesteps...")
    start_time = time.time()
    
    try:
        model.learn(
            total_timesteps=cfg.trainer.total_timesteps,
            callback=callbacks,
            progress_bar=cfg.trainer.progress_bar,
            reset_num_timesteps=cfg.trainer.reset_num_timesteps,
        )
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Training completed in {elapsed_time:.2f} seconds")
    
    # Cleanup
    env.close()


def evaluate(cfg: DictConfig):
    """Evaluate a trained model."""
    from stable_baselines3 import PPO
    
    logger.info("=" * 60)
    logger.info("Nexus Platformer Model Evaluation")
    logger.info("=" * 60)
    
    if not cfg.eval.model_path or not os.path.exists(cfg.eval.model_path):
        logger.error(f"Model not found: {cfg.eval.model_path}")
        return
    
    # Setup environment (always render for evaluation)
    # Ensure render_mode is set for evaluation
    cfg.env.render_mode = "human" 
    cfg.env.auto_launch = True # Always auto-launch for evaluation
    env = setup_environment(cfg)
    
    # Load model
    logger.info(f"Loading model from: {cfg.eval.model_path}")
    model = PPO.load(cfg.eval.model_path, env=env)
    
    # Evaluate
    logger.info(f"Running {cfg.eval.episodes} evaluation episodes...")
    
    episode_rewards = []
    episode_lengths = []
    stars_collected = []
    levels_completed = 0
    
    for episode in range(cfg.eval.episodes):
        obs, info = env.reset()
        total_reward = 0
        steps = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=cfg.eval.deterministic)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated
            
            if cfg.eval.render_delay > 0:
                time.sleep(cfg.eval.render_delay)
        
        episode_rewards.append(total_reward)
        episode_lengths.append(steps)
        stars_collected.append(info.get('stars_collected', 0))
        
        if info.get('level_complete', False):
            levels_completed += 1
        
        logger.info(f"Episode {episode + 1}: Reward={total_reward:.2f}, "
                   f"Steps={steps}, Stars={info.get('stars_collected', 0)}, "
                   f"Complete={info.get('level_complete', False)}")
    
    # Summary
    logger.info("=" * 60)
    logger.info("Evaluation Summary")
    logger.info("=" * 60)
    logger.info(f"Episodes: {cfg.eval.episodes}")
    logger.info(f"Mean Reward: {np.mean(episode_rewards):.2f} ± {np.std(episode_rewards):.2f}")
    logger.info(f"Mean Length: {np.mean(episode_lengths):.2f} ± {np.std(episode_lengths):.2f}")
    logger.info(f"Mean Stars: {np.mean(stars_collected):.2f} ± {np.std(stars_collected):.2f}")
    logger.info(f"Success Rate: {levels_completed / cfg.eval.episodes * 100:.1f}%")
    
    env.close()


@hydra.main(config_path="../configs", config_name="config", version_base="1.3")
def main(cfg: DictConfig):
    # Auto-enable wandb if API key is in environment
    if os.environ.get("WANDB_API_KEY") and not cfg.callbacks.wandb.enabled:
        logger.info("WANDB_API_KEY detected in environment, enabling W&B logging.")
        cfg.callbacks.wandb.enabled = True

    # Check dependencies
    try:
        import gymnasium
        import numpy
        import websockets
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install with: pip install gymnasium numpy websockets")
        sys.exit(1)
    
    try:
        import stable_baselines3
        import torch
        if cfg.callbacks.wandb.enabled:
            import wandb
            from dotenv import load_dotenv
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install with: pip install stable-baselines3 torch wandb python-dotenv")
        sys.exit(1)
    
    # Run
    if cfg.mode == "eval":
        evaluate(cfg)
    else:
        train(cfg)


if __name__ == "__main__":
    main()
