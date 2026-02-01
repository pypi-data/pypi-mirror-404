"""Configuration management for XM Agent."""

import os
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """XM Agent settings loaded from environment and config file."""

    model_config = SettingsConfigDict(
        env_prefix="XM_AGENT_",
        env_file=".env",
        extra="ignore",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8765, description="Server port")

    # Model paths
    models_path: str = Field(
        default="/workspace/ComfyUI/models",
        description="Base path for model directories",
    )

    # Model subdirectories (relative to models_path)
    checkpoints_dir: str = "checkpoints"
    loras_dir: str = "loras"
    embeddings_dir: str = "embeddings"
    vae_dir: str = "vae"
    controlnet_dir: str = "controlnet"

    # CivitAI settings
    civitai_api_key: str | None = Field(
        default=None,
        description="CivitAI API key for gated models",
        alias="CIVITAI_API_KEY",
    )

    # SD-CLI settings
    sd_cli_path: str | None = Field(
        default=None,
        description="Path to sd-cli binary (auto-detected if not set)",
    )
    sd_output_path: str = Field(
        default="~/.xm/agent/outputs",
        description="Directory for generated images",
    )
    sd_default_steps: int = Field(default=20, description="Default sampling steps")
    sd_default_cfg: float = Field(default=7.0, description="Default CFG scale")

    @property
    def runpod_pod_id(self) -> str | None:
        """Get RunPod pod ID from environment."""
        return os.environ.get("RUNPOD_POD_ID")

    @property
    def is_runpod(self) -> bool:
        """Check if running on RunPod."""
        return self.runpod_pod_id is not None

    @property
    def runpod_proxy_url(self) -> str | None:
        """Get RunPod proxy URL for this agent."""
        if not self.runpod_pod_id:
            return None
        return f"https://{self.runpod_pod_id}-{self.port}.proxy.runpod.net"

    def get_model_path(self, model_type: str) -> Path:
        """Get the full path for a model type directory."""
        base = Path(self.models_path)
        subdir_map = {
            "checkpoints": self.checkpoints_dir,
            "loras": self.loras_dir,
            "embeddings": self.embeddings_dir,
            "vae": self.vae_dir,
            "controlnet": self.controlnet_dir,
        }
        subdir = subdir_map.get(model_type)
        if not subdir:
            raise ValueError(f"Unknown model type: {model_type}")
        return base / subdir

    @property
    def model_types(self) -> list[str]:
        """List of supported model types."""
        return ["checkpoints", "loras", "embeddings", "vae", "controlnet"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
