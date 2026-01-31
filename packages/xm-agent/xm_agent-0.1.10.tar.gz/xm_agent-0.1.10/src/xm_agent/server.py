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
    from xm_agent.sd_install import get_sd_cli_path, get_sd_cli_version

    settings = get_settings()
    sd_cli_path = get_sd_cli_path()

    return {
        "status": "ok",
        "version": VERSION,
        "runpod_url": settings.runpod_proxy_url,
        "sd_cli_installed": sd_cli_path is not None,
        "sd_cli_version": get_sd_cli_version(sd_cli_path) if sd_cli_path else None,
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


# SD-CLI endpoints


class SDInstallRequest(BaseModel):
    """Request body for sd-cli install endpoint."""

    backend: str | None = None  # cuda, rocm, metal, vulkan (auto-detect if None)
    force: bool = False  # Force rebuild


@app.post("/sd/install")
async def install_sd():
    """
    Build and install stable-diffusion.cpp.

    Auto-detects GPU backend (cuda, rocm, metal, vulkan).
    Returns a background task ID for progress tracking.
    """
    from xm_agent.sd_install import install_sd_cli_async, InstallError

    task = task_manager.create_task()
    logs: list[str] = []

    def log(msg: str):
        logs.append(msg)

    async def do_install():
        try:
            path = await install_sd_cli_async(log=log)
            return {"success": True, "path": str(path), "logs": logs}
        except InstallError as e:
            return {"success": False, "error": str(e), "logs": logs}

    task_manager.start_task(task, do_install())

    return {"task_id": task.task_id}


class SDConvertRequest(BaseModel):
    """Request body for model conversion to GGUF."""

    input: str  # Path to input model (.safetensors, .ckpt)
    output: str | None = None  # Output path (auto-generated if None)
    weight_type: str = "q8_0"  # Quantization type


@app.post("/sd/convert")
async def convert_model(request: SDConvertRequest):
    """
    Convert a model to quantized GGUF format.

    Reduces loading time and VRAM usage.
    Returns a background task ID for progress tracking.
    """
    from pathlib import Path
    from xm_agent.sd_install import get_sd_cli_path
    import asyncio

    sd_cli = get_sd_cli_path()
    if not sd_cli:
        raise HTTPException(status_code=400, detail="sd-cli not installed")

    input_path = Path(request.input)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail=f"Input model not found: {request.input}")

    # Generate output path if not specified
    if request.output:
        output_path = Path(request.output)
    else:
        output_path = input_path.with_suffix(f".{request.weight_type}.gguf")

    task = task_manager.create_task()
    logs: list[str] = []

    def log(msg: str):
        logs.append(msg)
        print(msg)

    async def do_convert():
        cmd = [
            str(sd_cli),
            "-M", "convert",
            "-m", str(input_path),
            "-o", str(output_path),
            "--type", request.weight_type,
            "-v",
        ]

        log(f"[convert] Command: {' '.join(cmd)}")
        log(f"[convert] Input: {input_path}")
        log(f"[convert] Output: {output_path}")
        log(f"[convert] Type: {request.weight_type}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            log(f"[sd-cli] {line.decode().rstrip()}")

        await process.wait()

        if process.returncode != 0:
            return {"success": False, "error": f"Conversion failed (exit {process.returncode})", "logs": logs}

        if not output_path.exists():
            return {"success": False, "error": "Conversion completed but output not found", "logs": logs}

        log(f"[convert] Done! Saved to {output_path}")
        return {"success": True, "path": str(output_path), "logs": logs}

    task_manager.start_task(task, do_convert())

    return {"task_id": task.task_id}


@app.get("/sd/status")
async def sd_status():
    """Check if sd-cli is installed and get version."""
    from xm_agent.sd_install import get_sd_cli_path, get_sd_cli_version, detect_backend

    path = get_sd_cli_path()
    return {
        "installed": path is not None,
        "path": str(path) if path else None,
        "version": get_sd_cli_version(path) if path else None,
        "detected_backend": detect_backend(),
    }


# Generation endpoints


class GenerateRequestBody(BaseModel):
    """Request body for image generation."""

    # Required
    prompt: str
    model: str  # Path to model file

    # Output
    output: str | None = None

    # Image dimensions
    width: int = 512
    height: int = 512

    # Generation parameters
    steps: int = 20
    cfg_scale: float = 7.0
    seed: int = -1
    batch_count: int = 1

    # Optional parameters
    negative_prompt: str | None = None
    sampling_method: str | None = None
    scheduler: str | None = None
    clip_skip: int | None = None
    guidance: float | None = None

    # Additional model paths
    vae: str | None = None
    lora_model_dir: str | None = None
    controlnet: str | None = None
    control_image: str | None = None
    control_strength: float | None = None

    # Img2img
    init_image: str | None = None
    strength: float | None = None

    # Performance
    threads: int | None = None
    vae_tiling: bool = False
    diffusion_fa: bool = False
    weight_type: str | None = None  # f16, q8_0, q4_0, etc.
    offload_to_cpu: bool = False


# Store generation results (task_id -> output_path)
_generation_results: dict[str, str] = {}


@app.post("/generate")
async def start_generation(request: GenerateRequestBody):
    """
    Start image generation as a background task.

    Returns task_id for progress tracking.
    """
    from pathlib import Path
    from xm_agent.generate import GenerateRequest, generate_image, GenerateError, SamplingMethod, Scheduler, WeightType

    settings = get_settings()
    task = task_manager.create_task()
    logs: list[str] = []

    def log(msg: str):
        logs.append(msg)
        print(msg)

    # Convert request body to GenerateRequest
    gen_request = GenerateRequest(
        prompt=request.prompt,
        model=request.model,
        output=request.output,
        width=request.width,
        height=request.height,
        steps=request.steps,
        cfg_scale=request.cfg_scale,
        seed=request.seed,
        batch_count=request.batch_count,
        negative_prompt=request.negative_prompt,
        sampling_method=SamplingMethod(request.sampling_method) if request.sampling_method else None,
        scheduler=Scheduler(request.scheduler) if request.scheduler else None,
        clip_skip=request.clip_skip,
        guidance=request.guidance,
        vae=request.vae,
        lora_model_dir=request.lora_model_dir,
        controlnet=request.controlnet,
        control_image=request.control_image,
        control_strength=request.control_strength,
        init_image=request.init_image,
        strength=request.strength,
        threads=request.threads,
        vae_tiling=request.vae_tiling,
        diffusion_fa=request.diffusion_fa,
        weight_type=WeightType(request.weight_type) if request.weight_type else None,
        offload_to_cpu=request.offload_to_cpu,
    )

    # Output directory (use models_path parent or /tmp)
    output_dir = Path(settings.sd_output_path).expanduser()

    async def do_generate():
        def on_progress(p):
            task.progress.progress = p.progress_percent

        try:
            output_path = await generate_image(
                gen_request,
                output_dir,
                log=log,
                on_progress=on_progress,
            )
            _generation_results[task.task_id] = str(output_path)
            return {"success": True, "path": str(output_path), "logs": logs}
        except GenerateError as e:
            return {"success": False, "error": str(e), "logs": logs}

    task_manager.start_task(task, do_generate())

    return {"task_id": task.task_id}


@app.get("/generate/{task_id}")
async def get_generation_progress(task_id: str):
    """Get the progress of an image generation task."""
    progress = task_manager.get_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    return progress.to_dict()


@app.get("/generate/{task_id}/image")
async def get_generated_image(task_id: str):
    """Download the generated image."""
    from fastapi.responses import FileResponse

    # Check task exists and is complete
    progress = task_manager.get_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")

    if progress.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Task not complete: {progress.status.value}")

    # Get result path
    output_path = _generation_results.get(task_id)
    if not output_path:
        raise HTTPException(status_code=404, detail="Image not found")

    from pathlib import Path
    path = Path(output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(
        path,
        media_type="image/png",
        filename=path.name,
    )


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
