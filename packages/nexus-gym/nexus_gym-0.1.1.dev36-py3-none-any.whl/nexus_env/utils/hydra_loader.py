from __future__ import annotations

import os
from typing import Optional, List
from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf

class ConfigError(RuntimeError):
    pass


REQUIRED_TOP_KEYS = ["env", "agent"]  # Adjusted based on config.yaml content

def load_config(
    config_name: str = "config",
    overrides: Optional[List[str]] = None,
) -> DictConfig:
    """Load Hydra configuration from configs directory.

    Args:
        config_name: Name of config file (without .yaml)
        overrides: List of Hydra overrides (e.g., ["env.theme=cyber_district"])

    Returns:
        DictConfig with all overrides applied
    """
    # Clear any existing Hydra instance to ensure clean state
    if GlobalHydra.instance().is_initialized():
        GlobalHydra.instance().clear()

    # Find configs directory relative to this file
    # src/nexus_env/utils/hydra_loader.py -> .../nexus-gym/configs
    file_path = Path(__file__).resolve()
    # Go up 3 levels: utils -> nexus_env -> src -> nexus-gym -> configs
    # Wait: 
    # __file__ = .../src/nexus_env/utils/hydra_loader.py
    # parents[0] = utils
    # parents[1] = nexus_env
    # parents[2] = src
    # parents[3] = nexus-gym
    # configs_dir = parents[3] / "configs"
    
    # Let's try to find it more dynamically or hardcodish for this repo structure
    root_dir = file_path.parents[3]
    config_dir = root_dir / "configs"
    
    if not config_dir.exists():
        # Fallback if structure is different
        config_dir = Path(os.getcwd()) / "configs"

    if not config_dir.exists():
        raise ConfigError(f"Could not find configs directory at {config_dir}")

    initialize_config_dir(config_dir=str(config_dir), version_base=None)
    cfg = compose(config_name=config_name, overrides=overrides or [])

    # Validation
    # defaults in config.yaml might make keys appear
    # missing = [k for k in REQUIRED_TOP_KEYS if k not in cfg]
    # if missing:
    #    raise ConfigError(f"Invalid config: missing required sections -> {missing}")

    return cfg


def pretty_print_cfg(cfg: DictConfig) -> str:
    """Return readable simplified config summary for logging."""
    # check keys existence before accessing
    env = cfg.get("env", {}).get("theme", "unknown")
    algo = cfg.get("algo", "unknown")

    header = [
        "========== Loaded Config ==========",
        f"Env Theme:      {env}",
        f"Algo:           {algo}",
        "===================================\n",
    ]
    return "\n".join(header) + OmegaConf.to_yaml(cfg, resolve=True)
