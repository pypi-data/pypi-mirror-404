"""File download with progress tracking."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import httpx

from xm_agent.config import get_settings
from xm_agent.hash import compute_sha256

# Allowed download domains
ALLOWED_DOMAINS = {
    "civitai.com",
    "huggingface.co",
    "cdn-lfs.huggingface.co",
    "cdn-lfs-us-1.huggingface.co",
}


@dataclass
class DownloadProgress:
    """Progress information for a download."""

    bytes_downloaded: int
    total_bytes: int | None
    speed_bps: float  # bytes per second

    @property
    def progress_percent(self) -> int | None:
        """Get progress as percentage (0-100)."""
        if self.total_bytes and self.total_bytes > 0:
            return min(100, int(self.bytes_downloaded * 100 / self.total_bytes))
        return None

    @property
    def speed_str(self) -> str:
        """Human-readable speed string."""
        if self.speed_bps >= 1024 * 1024:
            return f"{self.speed_bps / (1024 * 1024):.1f} MB/s"
        elif self.speed_bps >= 1024:
            return f"{self.speed_bps / 1024:.1f} KB/s"
        return f"{self.speed_bps:.0f} B/s"


class DownloadError(Exception):
    """Error during download."""

    pass


def is_url_allowed(url: str) -> bool:
    """Check if URL domain is in allowlist."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Check exact match or subdomain match
        for allowed in ALLOWED_DOMAINS:
            if domain == allowed or domain.endswith(f".{allowed}"):
                return True
        return False
    except Exception:
        return False


async def download_file(
    url: str,
    dest: Path,
    on_progress: Callable[[DownloadProgress], None] | None = None,
    expected_hash: str | None = None,
    api_key: str | None = None,
) -> Path:
    """
    Download a file from URL to destination.

    Args:
        url: Source URL (must be from allowed domains)
        dest: Destination file path
        on_progress: Optional progress callback
        expected_hash: Optional SHA256 hash to verify after download
        api_key: Optional API key for CivitAI (passed from client, overrides env)

    Returns:
        Path to downloaded file

    Raises:
        DownloadError: If download fails or hash doesn't match
    """
    if not is_url_allowed(url):
        raise DownloadError(f"URL domain not allowed: {url}")

    settings = get_settings()

    # Build headers - use passed api_key or fall back to env
    headers = {"User-Agent": "curl/7.68.0"}
    effective_api_key = api_key or settings.civitai_api_key
    if effective_api_key and "civitai.com" in url:
        headers["Authorization"] = f"Bearer {effective_api_key}"

    # Ensure parent directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Download with streaming
    import time

    start_time = time.time()
    bytes_downloaded = 0

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()

                total_bytes = response.headers.get("content-length")
                total_bytes = int(total_bytes) if total_bytes else None

                with dest.open("wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

                        if on_progress:
                            elapsed = time.time() - start_time
                            speed = bytes_downloaded / elapsed if elapsed > 0 else 0
                            on_progress(
                                DownloadProgress(
                                    bytes_downloaded=bytes_downloaded,
                                    total_bytes=total_bytes,
                                    speed_bps=speed,
                                )
                            )

    except httpx.HTTPStatusError as e:
        # Clean up partial file
        if dest.exists():
            dest.unlink()
        raise DownloadError(f"HTTP error {e.response.status_code}")
    except Exception as e:
        # Clean up partial file
        if dest.exists():
            dest.unlink()
        raise DownloadError(f"Download failed: {e}")

    # Verify hash if provided
    if expected_hash:
        actual_hash = compute_sha256(dest)
        if actual_hash.upper() != expected_hash.upper():
            dest.unlink()
            raise DownloadError(
                f"Hash mismatch: expected {expected_hash}, got {actual_hash}"
            )

    return dest
