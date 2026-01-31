"""Image generation using sd-cli subprocess."""

import asyncio
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from xm_agent.sd_install import get_sd_cli_path


class WeightType(str, Enum):
    """Supported weight quantization types."""

    F32 = "f32"
    F16 = "f16"
    Q8_0 = "q8_0"
    Q5_0 = "q5_0"
    Q5_1 = "q5_1"
    Q4_0 = "q4_0"
    Q4_1 = "q4_1"
    Q2_K = "q2_K"
    Q3_K = "q3_K"
    Q4_K = "q4_K"


class SamplingMethod(str, Enum):
    """Supported sampling methods."""

    EULER = "euler"
    EULER_A = "euler_a"
    HEUN = "heun"
    DPM2 = "dpm2"
    DPM_PP_2S_A = "dpm++2s_a"
    DPM_PP_2M = "dpm++2m"
    DPM_PP_2MV2 = "dpm++2mv2"
    IPNDM = "ipndm"
    IPNDM_V = "ipndm_v"
    LCM = "lcm"
    DDIM_TRAILING = "ddim_trailing"
    TCD = "tcd"


class Scheduler(str, Enum):
    """Supported schedulers."""

    DISCRETE = "discrete"
    KARRAS = "karras"
    EXPONENTIAL = "exponential"
    AYS = "ays"
    GITS = "gits"
    SMOOTHSTEP = "smoothstep"
    SGM_UNIFORM = "sgm_uniform"
    SIMPLE = "simple"
    KL_OPTIMAL = "kl_optimal"
    LCM = "lcm"


class GenerateError(Exception):
    """Error during image generation."""

    pass


@dataclass
class GenerateRequest:
    """Parameters for image generation."""

    # Required
    prompt: str
    model: str  # Path to model file

    # Output
    output: str | None = None  # Output path (auto-generated if None)

    # Image dimensions
    width: int = 512
    height: int = 512

    # Generation parameters
    steps: int = 20
    cfg_scale: float = 7.0
    seed: int = -1  # -1 for random
    batch_count: int = 1

    # Optional parameters
    negative_prompt: str | None = None
    sampling_method: SamplingMethod | None = None
    scheduler: Scheduler | None = None
    clip_skip: int | None = None
    guidance: float | None = None  # For Flux models

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
    diffusion_fa: bool = False  # Flash attention
    weight_type: WeightType | None = None  # Quantization (q8_0, q4_0, etc.)
    offload_to_cpu: bool = False  # Offload weights to RAM


@dataclass
class GenerateProgress:
    """Progress information during generation."""

    step: int = 0
    total_steps: int = 0
    progress_percent: int = 0
    status: str = "pending"
    logs: list[str] = field(default_factory=list)


def build_sd_cli_args(request: GenerateRequest, output_path: Path) -> list[str]:
    """Build sd-cli command line arguments from request."""
    args = [
        "-m", request.model,
        "-p", request.prompt,
        "-o", str(output_path),
        "-W", str(request.width),
        "-H", str(request.height),
        "--steps", str(request.steps),
        "--cfg-scale", str(request.cfg_scale),
        "-s", str(request.seed),
        "-b", str(request.batch_count),
        "--color",  # Colored output for parsing
    ]

    if request.negative_prompt:
        args.extend(["-n", request.negative_prompt])

    if request.sampling_method:
        args.extend(["--sampling-method", request.sampling_method.value])

    if request.scheduler:
        args.extend(["--scheduler", request.scheduler.value])

    if request.clip_skip is not None:
        args.extend(["--clip-skip", str(request.clip_skip)])

    if request.guidance is not None:
        args.extend(["--guidance", str(request.guidance)])

    if request.vae:
        args.extend(["--vae", request.vae])

    if request.lora_model_dir:
        args.extend(["--lora-model-dir", request.lora_model_dir])

    if request.controlnet:
        args.extend(["--control-net", request.controlnet])

    if request.control_image:
        args.extend(["--control-image", request.control_image])

    if request.control_strength is not None:
        args.extend(["--control-strength", str(request.control_strength)])

    if request.init_image:
        args.extend(["-i", request.init_image])

    if request.strength is not None:
        args.extend(["--strength", str(request.strength)])

    if request.threads is not None:
        args.extend(["-t", str(request.threads)])

    if request.vae_tiling:
        args.append("--vae-tiling")

    if request.diffusion_fa:
        args.append("--diffusion-fa")

    if request.weight_type:
        args.extend(["--type", request.weight_type.value])

    if request.offload_to_cpu:
        args.append("--offload-to-cpu")

    return args


# Regex patterns for parsing sd-cli output
# sd-cli outputs progress like: |==>                    | 1/20 - 1.70it/s
PROGRESS_BAR_PATTERN = re.compile(r"\|\s*(\d+)/(\d+)\s*-")
# Fallback patterns for other formats
STEP_PATTERN = re.compile(r"step\s+(\d+)/(\d+)", re.IGNORECASE)
SAMPLING_PATTERN = re.compile(r"sampling.*?(\d+)/(\d+)", re.IGNORECASE)


def parse_progress(line: str, progress: GenerateProgress) -> None:
    """Parse sd-cli output line to update progress."""
    # Try progress bar format first (most common)
    match = PROGRESS_BAR_PATTERN.search(line)
    if not match:
        # Fallback to other formats
        match = STEP_PATTERN.search(line) or SAMPLING_PATTERN.search(line)
    if match:
        progress.step = int(match.group(1))
        progress.total_steps = int(match.group(2))
        if progress.total_steps > 0:
            progress.progress_percent = int((progress.step / progress.total_steps) * 100)


async def generate_image(
    request: GenerateRequest,
    output_dir: Path,
    log: Callable[[str], None] | None = None,
    on_progress: Callable[[GenerateProgress], None] | None = None,
) -> Path:
    """
    Generate an image using sd-cli.

    Args:
        request: Generation parameters
        output_dir: Directory for output images
        log: Callback for log messages
        on_progress: Callback for progress updates

    Returns:
        Path to generated image

    Raises:
        GenerateError: If generation fails
    """
    log = log or (lambda x: None)
    progress = GenerateProgress(status="starting")

    # Get sd-cli path
    sd_cli = get_sd_cli_path()
    if not sd_cli:
        raise GenerateError("sd-cli not installed. Run 'xm-agent install-sd' first.")

    log(f"[generate] Using sd-cli at {sd_cli}")

    # Validate model exists
    model_path = Path(request.model)
    if not model_path.exists():
        raise GenerateError(f"Model not found: {request.model}")
    log(f"[generate] Model: {model_path}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    output_name = request.output or f"{uuid.uuid4().hex[:8]}.png"
    output_path = output_dir / output_name
    log(f"[generate] Output: {output_path}")

    # Build command
    args = build_sd_cli_args(request, output_path)
    cmd = [str(sd_cli)] + args

    log(f"[generate] Command: {' '.join(cmd)}")
    log(f"[generate] Prompt: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
    log(f"[generate] Size: {request.width}x{request.height}, Steps: {request.steps}, CFG: {request.cfg_scale}")

    progress.status = "running"
    if on_progress:
        on_progress(progress)

    # Run sd-cli
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    # Stream output
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        line_str = line.decode().rstrip()
        progress.logs.append(line_str)
        log(f"[sd-cli] {line_str}")

        # Parse progress
        parse_progress(line_str, progress)
        if on_progress:
            on_progress(progress)

    await process.wait()

    if process.returncode != 0:
        progress.status = "failed"
        if on_progress:
            on_progress(progress)
        raise GenerateError(f"sd-cli failed with exit code {process.returncode}")

    # Verify output
    if not output_path.exists():
        progress.status = "failed"
        if on_progress:
            on_progress(progress)
        raise GenerateError(f"Generation completed but output not found: {output_path}")

    progress.status = "completed"
    progress.progress_percent = 100
    if on_progress:
        on_progress(progress)

    log(f"[generate] Done! Image saved to {output_path}")
    return output_path
