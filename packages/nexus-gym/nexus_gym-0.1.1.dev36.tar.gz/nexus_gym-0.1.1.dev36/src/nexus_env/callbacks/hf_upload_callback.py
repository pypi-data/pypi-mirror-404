"""
HFUploadCallback: Upload final SB3 model + metadata to Hugging Face Hub.

Adapted for Nexus Gym.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from huggingface_hub import (
    HfApi,
    create_repo,
    upload_folder,
    upload_file,
)

from stable_baselines3.common.callbacks import BaseCallback
from nexus_env.callbacks.model_card import ModelCardBuilder


class HFUploadCallback(BaseCallback):
    """
    HuggingFace Upload Callback.

    Parameters
    ----------
    cfg : DictConfig
        Hydra configuration object containing hf_upload settings.
    model_path : Path or str
        Path where the final model will be saved and should be uploaded from.
    push_strategy : str
        Upload strategy, currently only "final" is supported.
    verbose : int
        Verbosity level.
    """

    def __init__(
        self,
        cfg,
        model_path: str,
        push_strategy: str = "final",
        verbose: int = 1,
    ):
        super().__init__(verbose)
        self.cfg = cfg
        self.output_dir = Path(model_path).parent # Assume output dir is parent of model file
        self.model_path = Path(model_path)
        self.push_strategy = push_strategy
        self.api = HfApi()
        
        # Determine upload settings from config
        self.hf_config = cfg.get("callbacks", {}).get("hf_upload", {})
        
        # Override strategy if in config
        if "push_strategy" in self.hf_config:
            self.push_strategy = self.hf_config["push_strategy"]

    # ------------------------------------------------------------
    # Helper: Get HF token from various sources
    # ------------------------------------------------------------
    def _get_token(self) -> Optional[str]:
        """
        Get HF token from various sources.
        """
        # 1. Check if already set in HfApi
        if self.api.token:
            return self.api.token

        # 2. Check environment variables
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if token:
            return token

        # 3. Try loading from .env file (local dev)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            token = os.environ.get("HF_TOKEN")
            if token:
                return token
        except ImportError:
            pass

        # 4. Check huggingface-cli stored token
        try:
            from huggingface_hub import HfFolder
            token = HfFolder.get_token()
            if token:
                return token
        except Exception:
            pass

        return None

    # ------------------------------------------------------------
    # SB3: Callback step hook
    # ------------------------------------------------------------
    def _on_step(self) -> bool:
        return True

    # ------------------------------------------------------------
    # SB3: Called when training ends
    # ------------------------------------------------------------
    def _on_training_end(self) -> None:
        import logging
        logger = logging.getLogger("NEXUS.HFUploadCallback")

        if not self.hf_config.get("enabled", False):
             logger.info("[HFUploadCallback] Disabled in config. Skipping upload.")
             return

        if self.push_strategy != "final":
            return

        logger.info("[HFUploadCallback] Training complete. Beginning upload...")

        try:
            # ------------------------------------------------------------
            # Validate HF token
            # ------------------------------------------------------------
            token = self._get_token()

            if token is None:
                raise RuntimeError(
                    "No HuggingFace token found. Options:\n"
                    "  1. Run `huggingface-cli login`\n"
                    "  2. Set HF_TOKEN in .env file (requires python-dotenv)\n"
                    "  3. Export HF_TOKEN environment variable"
                )

            repo_id = self.hf_config.get("repo_id")
            if not repo_id:
                raise ValueError("[HFUploadCallback] repo_id not specified in config.")
                
            repo_type = self.hf_config.get("repo_type", "model")
            private = self.hf_config.get("private", True)
            lfs_patterns = self.hf_config.get("lfs_files", [])

            logger.info(f"[HFUploadCallback] Target repo: {repo_id}")

            # ------------------------------------------------------------
            # Ensure model file exists
            # ------------------------------------------------------------
            model_file = self.model_path

            # If the model hasn't been saved yet by another callback, we might need to save it.
            # But the user logic implies it's already saved or we should do it.
            # SB3 'save' on the model object.
            if not model_file.exists():
                logger.info(f"Model file {model_file} does not exist. Saving model now...")
                self.model.save(model_file)

            if not model_file.exists():
                raise FileNotFoundError(
                    f"[HFUploadCallback] Model file not found at {model_file}."
                )

            logger.info(f"[HFUploadCallback] Found model file: {model_file}")

            # ------------------------------------------------------------
            # Ensure repo exists
            # ------------------------------------------------------------
            create_repo(
                repo_id=repo_id,
                exist_ok=True,
                repo_type=repo_type,
                private=private,
                token=token,
            )

            # ------------------------------------------------------------
            # Prepare upload directory
            # ------------------------------------------------------------
            upload_dir = self.output_dir / "hf_upload_tmp"

            if upload_dir.exists():
                shutil.rmtree(upload_dir)
            upload_dir.mkdir(parents=True, exist_ok=True)

            # ------------------------------------------------------------
            # Copy model checkpoint into upload directory
            # ------------------------------------------------------------
            # Copy just the zip file to root of repo or models dir?
            # User example: models_dir = upload_dir / "models"
            # Let's clean it up and put it in root for simplicity unless we want versioning
            # But adapting user code:
            dst = upload_dir / model_file.name
            logger.info(f"[HFUploadCallback] Copying model -> {dst}")
            shutil.copy2(model_file, dst)

            # ------------------------------------------------------------
            # Configure .gitattributes for LFS
            # ------------------------------------------------------------
            if lfs_patterns:
                self._configure_lfs(upload_dir, lfs_patterns)

            # ------------------------------------------------------------
            # Generate README model card
            # ------------------------------------------------------------
            logger.info("[HFUploadCallback] Writing model card...")
            
            card_builder = ModelCardBuilder(self.cfg)
            card_builder.write(
                repo_dir=upload_dir,
                model_filename=model_file.name,
            )

            # ------------------------------------------------------------
            # Upload folder to HF Hub
            # ------------------------------------------------------------
            logger.info("[HFUploadCallback] Uploading to Hugging Face Hub...")

            upload_folder(
                repo_id=repo_id,
                folder_path=str(upload_dir),
                repo_type=repo_type,
                commit_message="Upload trained model",
                token=token,
            )

            logger.info(f"[HFUploadCallback] ✓ Model uploaded to https://huggingface.co/{repo_id}")

            # ------------------------------------------------------------
            # Logs upload (optional)
            # ------------------------------------------------------------
            if self.hf_config.get("upload_logs", False):
                # Assume logs are in output_dir/logs or similar.
                # Or just upload the whole output dir minus model?
                # Let's just skip complex log logic for now or try to guess.
                # If tensorboard log is active.
                pass 

            # ------------------------------------------------------------
            # Cleanup temporary directory
            # ------------------------------------------------------------
            if upload_dir.exists():
                shutil.rmtree(upload_dir)

            logger.info("[HFUploadCallback] Upload completed.")

        except Exception as e:
            logger.error(f"[HFUploadCallback] Upload FAILED: {e}")
            import traceback
            logger.error(traceback.format_exc())

    # ------------------------------------------------------------
    # Helper: Configure Git LFS via .gitattributes
    # ------------------------------------------------------------
    def _configure_lfs(self, repo_dir: Path, patterns: list[str]) -> None:
        """Create .gitattributes file with LFS patterns."""
        gitattributes = repo_dir / ".gitattributes"
        lines = [f"{p} filter=lfs diff=lfs merge=lfs -text" for p in patterns]
        content = "\n".join(lines) + "\n"

        with open(gitattributes, "w") as f:
            f.write(content)
