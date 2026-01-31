"""
ModelCardBuilder
Creates README.md for the Hugging Face Hub upload with comprehensive metadata
and documentation following HF model card best practices.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf


def indent_block(text: str, indent: int) -> str:
    """Indent a block of text."""
    return "\n".join(" " * indent + line for line in text.splitlines())


class ModelCardBuilder:
    """Builds comprehensive Hugging Face model cards for Nexus Gym trained agents."""

    def __init__(self, cfg) -> None:
        self.cfg = cfg

    # ------------------------------------------------------------
    # Build YAML frontmatter with HF metadata
    # ------------------------------------------------------------
    def _build_yaml_frontmatter(self, model_filename: str) -> tuple[str, str, str, Dict[str, Any]]:
        """Build the YAML frontmatter with all required HF metadata."""
        cfg = self.cfg
        
        # Access hf_upload config safely
        hf_cfg = cfg.get("callbacks", {}).get("hf_upload", {})
        hf_meta = hf_cfg.get("metadata", {})

        # Extract training hyperparameters (if available in cfg)
        # Assuming cfg structure could vary, use safe gets
        algo_cfg = cfg.get("algo", {}) # e.g. might be just 'ppo' string or dict
        # If algo is just a string (from defaults), we might not have detailed params here unless fully composed.
        # But commonly hydra composes everything.
        
        # Let's assume some defaults if missing
        total_timesteps = cfg.get("trainer", {}).get("total_timesteps", "N/A")
        learning_rate = cfg.get("algo", {}).get("learning_rate", "3e-4")
        
        # Build comprehensive metadata
        metadata = {
            "utc_timestamp": datetime.datetime.utcnow().isoformat(),
            "env_name": cfg.get("env", {}).get("theme", "Nexus-Platformer"),
            "model_file": model_filename,
            "total_timesteps": total_timesteps,
            "learning_rate": learning_rate,
            **hf_meta,
        }

        # Convert Hydra config to JSON for embedding
        try:
            hydra_config = OmegaConf.to_container(cfg, resolve=True)
            hydra_json = json.dumps(hydra_config, indent=2)
            hydra_yaml_block = indent_block(hydra_json, 4)
        except Exception:
            hydra_yaml_block = "Config not serializable"

        # Format metadata entries
        metadata_yaml = "\n".join(f"  {k}: {v}" for k, v in metadata.items())

        # Get repo info from hf_cfg with defaults
        repo_id = hf_cfg.get("repo_id", "chrisjcc/nexus-gym-agent")

        frontmatter = f"""---
language: en
license: mit
library_name: stable-baselines3
tags:
  - reinforcement-learning
  - stable-baselines3
  - gymnasium
  - nexus-gym
  - platformer
  - game-ai
datasets:
  - nexus-gym-env
metrics:
  - episode_reward
  - episode_length
model-index:
  - name: Nexus-Gym-Agent
    results:
      - task:
          type: reinforcement-learning
          name: Platformer
        dataset:
          type: custom
          name: Nexus Gym Environment
        metrics:
          - type: episode_reward
            name: Mean Episode Reward
            value: TBD
pipeline_tag: reinforcement-learning
metadata:
{metadata_yaml}
  hydra_config: |
{hydra_yaml_block}
---"""
        return frontmatter, repo_id, model_filename, metadata

    # ------------------------------------------------------------
    # Build Model Details section with training hyperparameters
    # ------------------------------------------------------------
    def _build_model_details_section(self, metadata: dict[str, Any]) -> str:
        """Build the Model Details section with training hyperparameters."""
        return f"""
## Model Details

### Description

This model is a reinforcement learning agent trained on the **Nexus Gym** environment.

### Model Architecture

- **Algorithm**: PPO (Proximal Policy Optimization)
- **Framework**: [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
- **Environment**: Nexus Gym

### Training Hyperparameters

| Parameter | Value |
|-----------|-------|
| Total Timesteps | {metadata.get('total_timesteps', 'N/A')} |
| Learning Rate | {metadata.get('learning_rate', '3e-4')} |
"""

    # ------------------------------------------------------------
    # Build Usage section with code examples
    # ------------------------------------------------------------
    def _build_usage_section(self, repo_id: str, model_filename: str) -> str:
        """Build the Usage section with code examples."""
        return f'''
## Usage

### Quick Start

```python
from huggingface_hub import hf_hub_download
from stable_baselines3 import PPO

# Download the model from Hugging Face Hub
model_path = hf_hub_download(
    repo_id="{repo_id}",
    filename="{model_filename}"
)

# Load the trained model
model = PPO.load(model_path)
```
'''

    # ------------------------------------------------------------
    # Build Environment section describing the env
    # ------------------------------------------------------------
    def _build_environment_section(self) -> str:
        """Build the Environment section describing the env."""
        return """
## Environment

### Nexus Gym

Nexus Gym is a platformer environment where agents learn to navigate obstacles and collect stars.
"""

    # ------------------------------------------------------------
    # Build Training section with methodology details
    # ------------------------------------------------------------
    def _build_training_section(self) -> str:
        """Build the Training section with methodology details."""
        return """
## Training

### Methodology

The model was trained using Stable-Baselines3.
"""

    # ------------------------------------------------------------
    # Build Repository Contents section
    # ------------------------------------------------------------
    def _build_files_section(self, model_filename: str) -> str:
        """Build the Repository Contents section."""
        return f"""
## Repository Contents

| File | Description |
|------|-------------|
| `{model_filename}` | Trained model checkpoint |
| `README.md` | This model card with full documentation |
"""

    # ------------------------------------------------------------
    # Write README.md into HF repo directory
    # ------------------------------------------------------------
    def write(self, repo_dir: Path, model_filename: str) -> None:
        """
        Write comprehensive README.md into HF repo directory.

        Args:
            repo_dir: Path to the repository directory
            model_filename: Name of the model file (e.g., 'model.zip')
        """
        # Build all sections
        frontmatter, repo_id, model_filename, metadata = self._build_yaml_frontmatter(
            model_filename
        )

        readme_content = f"""{frontmatter}

# Nexus Gym Agent

[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Model-yellow)](https://huggingface.co/{repo_id})

> A trained reinforcement learning agent for Nexus Gym.

{self._build_model_details_section(metadata)}
{self._build_usage_section(repo_id, model_filename)}
{self._build_environment_section()}
{self._build_training_section()}
{self._build_files_section(model_filename)}
---

*Generated on {metadata.get('utc_timestamp', datetime.datetime.utcnow().isoformat())} UTC*
"""

        readme = repo_dir / "README.md"
        readme.write_text(readme_content, encoding="utf-8")
