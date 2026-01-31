"""SHA256 hashing for model files."""

import hashlib
from pathlib import Path
from typing import Callable

# 8MB chunks (matching xm_get.py pattern)
CHUNK_SIZE = 8 * 1024 * 1024


def compute_sha256(
    file_path: Path,
    on_progress: Callable[[int, int], None] | None = None,
) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash
        on_progress: Optional callback (bytes_processed, total_bytes)

    Returns:
        Uppercase hex digest (CivitAI format)
    """
    sha256 = hashlib.sha256()
    file_size = file_path.stat().st_size
    processed = 0

    with file_path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
            processed += len(chunk)
            if on_progress:
                on_progress(processed, file_size)

    return sha256.hexdigest().upper()
