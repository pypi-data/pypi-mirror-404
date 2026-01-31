import numpy as np
import wandb
import logging
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback

logger = logging.getLogger(__name__)

class WandbMetricsCallback(BaseCallback):
    """
    Callback that directly logs SB3 metrics to W&B.
    This callback computes rollout/* metrics directly from ep_info_buffer and reads train/* metrics from the logger.
    """

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
        self._last_log_step = 0

    def _on_step(self) -> bool:
        return True

    def _on_rollout_end(self) -> None:
        metrics = {}

        # 1. Compute rollout metrics from ep_info_buffer
        if hasattr(self.model, 'ep_info_buffer') and len(self.model.ep_info_buffer) > 0:
            ep_rewards = [ep_info["r"] for ep_info in self.model.ep_info_buffer]
            ep_lengths = [ep_info["l"] for ep_info in self.model.ep_info_buffer]

            if len(ep_rewards) > 0:
                metrics["rollout/ep_rew_mean"] = float(np.mean(ep_rewards))
                metrics["rollout/ep_len_mean"] = float(np.mean(ep_lengths))

        # 2. Read train/* metrics from logger
        if hasattr(self.logger, 'name_to_value'):
            for key, value in self.logger.name_to_value.items():
                if not key.startswith('time/') and not key.startswith('rollout/'):
                    try:
                        metrics[key] = float(value)
                    except (TypeError, ValueError):
                        pass

        # 3. Log to W&B
        if metrics and wandb.run is not None:
            wandb.log(metrics, step=self.num_timesteps)
            self._last_log_step = self.num_timesteps

class WandbEpisodeCallback(BaseCallback):
    """
    Logs environment-specific episode-level metrics to WandB.
    Specifically logs stars collected, level status, etc.
    """

    def __init__(
        self,
        project: str = "nexus-gym",
        entity: str = "rl4aa",
        run_name: str = None,
        verbose: int = 0,
    ):
        super().__init__(verbose)
        self.project = project
        self.entity = entity
        self.run_name = run_name
        self._initialized = False

    def _on_training_start(self) -> None:
        if wandb.run is not None:
            self._initialized = True
            return

        logger.warning("WandbEpisodeCallback: wandb.run is None. Metrics will not be logged.")
        self._initialized = True

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [{}])

        for info in infos:
            if "episode" not in info:
                continue

            # Standard metrics
            metrics = {
                "custom/episode_reward": info["episode"]["r"],
                "custom/episode_length": info["episode"]["l"],
            }

            # Custom Nexus Gym components
            if "reward_components" in info:
                for key, value in info["reward_components"].items():
                    metrics[f"custom/reward_{key}"] = value
            
            # Additional game stats
            for key in ["stars_collected", "total_stars", "level_complete", "is_dead"]:
                if key in info:
                    metrics[f"game/{key}"] = info[key]

            if wandb.run is not None:
                wandb.log(metrics, step=self.num_timesteps)

        return True

    def _on_training_end(self) -> None:
        # We don't always want to finish the run here if other callbacks use it
        pass

class WandbEvalCallback(EvalCallback):
    """
    Evaluation callback that logs evaluation metrics to W&B.
    """
    def _on_step(self) -> bool:
        result = super()._on_step()

        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            if self.last_mean_reward is not None:
                if wandb.run is not None:
                    wandb.log({
                        "eval/mean_reward": self.last_mean_reward,
                        "eval/mean_ep_length": (
                            float(np.mean(self.evaluations_length[-1]))
                            if self.evaluations_length else 0
                        ),
                    }, step=self.num_timesteps)

        return result
