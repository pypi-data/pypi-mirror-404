"""Model discovery and listing."""

from dataclasses import dataclass
from pathlib import Path

from xm_agent.config import get_settings

# Supported model file extensions
MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".pt", ".pth", ".bin"}


@dataclass
class ModelFile:
    """Information about a model file."""

    filename: str
    size_bytes: int
    mtime: float  # Unix timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2),
            "mtime": self.mtime,
        }


def list_models(model_type: str) -> list[ModelFile]:
    """
    List all model files of the given type.

    Args:
        model_type: One of checkpoints, loras, embeddings, vae, controlnet

    Returns:
        List of ModelFile objects sorted by filename
    """
    settings = get_settings()
    model_path = settings.get_model_path(model_type)

    if not model_path.exists():
        return []

    models = []
    # Scan directory recursively for model files
    for file_path in model_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in MODEL_EXTENSIONS:
            # Use relative path from model directory for nested structures
            relative_path = file_path.relative_to(model_path)
            stat = file_path.stat()
            models.append(
                ModelFile(
                    filename=str(relative_path),
                    size_bytes=stat.st_size,
                    mtime=stat.st_mtime,
                )
            )

    return sorted(models, key=lambda m: m.filename.lower())


def get_model_path(model_type: str, filename: str) -> Path | None:
    """
    Get the full path to a model file.

    Args:
        model_type: One of checkpoints, loras, embeddings, vae, controlnet
        filename: The model filename (can include subdirectory)

    Returns:
        Path to the model file, or None if it doesn't exist
    """
    settings = get_settings()
    base_path = settings.get_model_path(model_type)
    full_path = base_path / filename

    # Security: Ensure the resolved path is still within the model directory
    try:
        full_path = full_path.resolve()
        base_path = base_path.resolve()
        if not str(full_path).startswith(str(base_path)):
            return None
    except (OSError, ValueError):
        return None

    if full_path.exists() and full_path.is_file():
        return full_path

    return None


def delete_model(model_type: str, filename: str) -> bool:
    """
    Delete a model file.

    Args:
        model_type: One of checkpoints, loras, embeddings, vae, controlnet
        filename: The model filename

    Returns:
        True if deleted, False if not found
    """
    path = get_model_path(model_type, filename)
    if path is None:
        return False

    path.unlink()
    return True
