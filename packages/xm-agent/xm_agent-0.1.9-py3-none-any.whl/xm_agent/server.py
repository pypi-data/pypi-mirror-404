"""FastAPI server for XM Agent."""

from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from xm_agent.config import get_settings
from xm_agent.models import list_models, get_model_path, delete_model
from xm_agent.hash import compute_sha256
from xm_agent.download import download_file, is_url_allowed, DownloadError
from xm_agent.tasks import task_manager, TaskStatus
from xm_agent.metadata import get_model_by_hash, parse_civitai_response

VERSION = version("xm-agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = get_settings()

    # Print startup info
    print(f"XM Agent v{VERSION} starting...")
    print(f"Listening on {settings.host}:{settings.port}")
    print(f"Models path: {settings.models_path}")

    if settings.is_runpod:
        print(f"RunPod detected: {settings.runpod_pod_id}")
        print(f"Proxy URL: {settings.runpod_proxy_url}")

    yield


app = FastAPI(
    title="XM Agent",
    description="HTTP API for remote model management",
    version=VERSION,
    lifespan=lifespan,
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": VERSION,
        "runpod_url": settings.runpod_proxy_url,
    }


@app.get("/models")
async def get_all_models():
    """List all models across all types."""
    settings = get_settings()
    result = {}
    for model_type in settings.model_types:
        models = list_models(model_type)
        result[model_type] = [m.to_dict() for m in models]
    return result


@app.get("/models/{model_type}")
async def get_models_by_type(model_type: str):
    """List models of a specific type."""
    settings = get_settings()
    if model_type not in settings.model_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type. Must be one of: {settings.model_types}",
        )
    models = list_models(model_type)
    return {"models": [m.to_dict() for m in models]}


@app.get("/models/{model_type}/{filename:path}/hash")
async def get_model_hash(model_type: str, filename: str, models_path: str):
    """Compute SHA256 hash of a model file."""
    from pathlib import Path

    path = Path(models_path) / model_type / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Model not found")

    hash_value = compute_sha256(path)
    return {"hash": hash_value, "filename": filename}


@app.delete("/models/{model_type}/{filename:path}")
async def delete_model_file(model_type: str, filename: str, models_path: str):
    """Delete a model file."""
    from pathlib import Path

    path = Path(models_path) / model_type / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Model not found")

    path.unlink()
    return {"deleted": True, "filename": filename}


# Download endpoints


class DownloadRequest(BaseModel):
    """Request body for download endpoint."""

    url: str
    type: str  # model type subfolder (loras, checkpoints, etc.)
    filename: str
    models_path: str  # base path for models (e.g., /workspace/ComfyUI/models)
    expected_hash: str | None = None
    api_key: str | None = None  # CivitAI API key (passed from client)


@app.post("/download")
async def start_download(request: DownloadRequest):
    """Start a model download as a background task."""
    from pathlib import Path

    from xm_agent import extract_civitai_id, resolve_civitai_model

    # Validate URL
    if not is_url_allowed(request.url):
        raise HTTPException(
            status_code=400,
            detail="URL domain not allowed. Only CivitAI and HuggingFace are permitted.",
        )

    # Use provided values - XM app already resolved the version
    download_url = request.url
    filename = request.filename
    model_type = request.type
    expected_hash = request.expected_hash

    # Create task
    task = task_manager.create_task()

    # Build destination path from client-provided models_path
    dest = Path(request.models_path) / model_type / filename

    async def do_download():
        def on_progress(progress):
            task.progress.progress = progress.progress_percent or 0
            task.progress.speed = progress.speed_str

        await download_file(
            url=download_url,
            dest=dest,
            on_progress=on_progress,
            expected_hash=expected_hash,
            api_key=request.api_key,
        )
        return {"filename": filename, "path": str(dest)}

    task_manager.start_task(task, do_download())

    return {"task_id": task.task_id}


@app.get("/download/{task_id}")
async def get_download_progress(task_id: str):
    """Get the progress of a download task."""
    progress = task_manager.get_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    return progress.to_dict()


@app.delete("/download/{task_id}")
async def cancel_download(task_id: str):
    """Cancel a download task."""
    cancelled = task_manager.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    return {"cancelled": True, "task_id": task_id}


# Metadata endpoints


@app.get("/metadata/{hash}")
async def get_metadata(hash: str):
    """Look up model metadata on CivitAI by SHA256 hash."""
    data = await get_model_by_hash(hash)
    if data is None:
        raise HTTPException(status_code=404, detail="Model not found on CivitAI")
    return parse_civitai_response(data)


@app.post("/metadata/sync")
async def sync_metadata():
    """
    Sync metadata for all models.

    Computes SHA256 hashes for all models and fetches metadata from CivitAI.
    Returns a background task ID.
    """
    settings = get_settings()
    task = task_manager.create_task()

    async def do_sync():
        results = {"found": 0, "not_found": 0, "errors": 0, "models": []}

        # Collect all models
        all_models = []
        for model_type in settings.model_types:
            for model in list_models(model_type):
                path = get_model_path(model_type, model.filename)
                if path:
                    all_models.append((model_type, model.filename, path))

        total = len(all_models)

        for i, (model_type, filename, path) in enumerate(all_models):
            # Update progress
            task.progress.progress = int((i / total) * 100) if total > 0 else 0

            try:
                # Compute hash
                hash_value = compute_sha256(path)

                # Look up on CivitAI
                data = await get_model_by_hash(hash_value)

                if data:
                    results["found"] += 1
                    results["models"].append({
                        "filename": filename,
                        "type": model_type,
                        "hash": hash_value,
                        "civitai": parse_civitai_response(data),
                    })
                else:
                    results["not_found"] += 1

            except Exception as e:
                results["errors"] += 1

        return results

    task_manager.start_task(task, do_sync())

    return {"task_id": task.task_id}


def run_server():
    """Run the uvicorn server."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "xm_agent.server:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
