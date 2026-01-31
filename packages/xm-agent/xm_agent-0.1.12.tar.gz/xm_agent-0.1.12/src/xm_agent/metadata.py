"""CivitAI metadata lookup."""

from typing import Any
from functools import lru_cache
import time

import httpx

from xm_agent.config import get_settings

CIVITAI_API_BASE = "https://civitai.com/api/v1"

# Simple in-memory cache with TTL
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 300  # 5 minutes


def _get_cached(key: str) -> Any | None:
    """Get value from cache if not expired."""
    if key in _cache:
        timestamp, value = _cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return value
        del _cache[key]
    return None


def _set_cached(key: str, value: Any) -> None:
    """Set value in cache."""
    _cache[key] = (time.time(), value)


async def get_model_by_hash(sha256: str) -> dict | None:
    """
    Look up model information on CivitAI by SHA256 hash.

    Args:
        sha256: SHA256 hash of the model file (uppercase or lowercase)

    Returns:
        CivitAI model version data, or None if not found
    """
    # Normalize hash
    sha256 = sha256.upper()

    # Check cache
    cached = _get_cached(sha256)
    if cached is not None:
        return cached

    settings = get_settings()

    # Build request
    url = f"{CIVITAI_API_BASE}/model-versions/by-hash/{sha256}"
    headers = {}
    if settings.civitai_api_key:
        headers["Authorization"] = f"Bearer {settings.civitai_api_key}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 404:
                # Cache negative result
                _set_cached(sha256, None)
                return None

            response.raise_for_status()
            data = response.json()

            # Cache result
            _set_cached(sha256, data)
            return data

    except httpx.HTTPStatusError:
        return None
    except Exception:
        return None


def parse_civitai_response(data: dict) -> dict:
    """
    Parse CivitAI API response into a simplified format.

    Args:
        data: Raw CivitAI API response

    Returns:
        Simplified metadata dict
    """
    model = data.get("model", {})
    files = data.get("files", [])
    primary_file = next((f for f in files if f.get("primary")), files[0] if files else {})

    return {
        "model_id": data.get("modelId"),
        "version_id": data.get("id"),
        "name": model.get("name"),
        "version_name": data.get("name"),
        "type": model.get("type"),
        "base_model": data.get("baseModel"),
        "nsfw": model.get("nsfw", False),
        "trained_words": data.get("trainedWords", []),
        "download_url": data.get("downloadUrl"),
        "images": [
            {"url": img.get("url"), "nsfw": img.get("nsfw")}
            for img in data.get("images", [])[:5]  # Limit to 5 images
        ],
        "stats": {
            "downloads": data.get("stats", {}).get("downloadCount", 0),
            "rating": data.get("stats", {}).get("rating", 0),
            "thumbs_up": data.get("stats", {}).get("thumbsUpCount", 0),
        },
        "file": {
            "name": primary_file.get("name"),
            "size_kb": primary_file.get("sizeKB"),
            "hash": primary_file.get("hashes", {}).get("SHA256"),
        },
    }
