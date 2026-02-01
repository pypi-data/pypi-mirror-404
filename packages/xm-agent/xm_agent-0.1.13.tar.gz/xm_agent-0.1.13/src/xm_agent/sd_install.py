"""Install stable-diffusion.cpp from source."""

import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

# Default paths
DEFAULT_REPO_URL = "https://github.com/leejet/stable-diffusion.cpp.git"
DEFAULT_INSTALL_PREFIX = Path.home() / ".local"
DEFAULT_BUILD_DIR = Path.home() / ".cache" / "sd-cpp-build"

BACKENDS = {
    "cuda": "SD_CUDA",
    "rocm": "SD_HIPBLAS",
    "metal": "SD_METAL",
    "vulkan": "SD_VULKAN",
}


class InstallError(Exception):
    """Error during installation."""

    pass


def detect_backend() -> str | None:
    """
    Auto-detect available GPU backend.

    Returns None if no supported GPU found.
    """
    # CUDA (NVIDIA)
    if shutil.which("nvcc"):
        return "cuda"
    if Path("/usr/local/cuda/bin/nvcc").exists():
        return "cuda"

    # ROCm (AMD)
    if Path("/opt/rocm").exists():
        return "rocm"
    if shutil.which("hipcc"):
        return "rocm"

    # Metal (macOS)
    if sys.platform == "darwin":
        return "metal"

    # Vulkan (fallback for other GPUs)
    if shutil.which("vulkaninfo"):
        return "vulkan"

    return None


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    log: Callable[[str], None] | None = None,
) -> None:
    """Run a command with live output streaming."""
    cmd_str = " ".join(cmd)
    if log:
        log(f"$ {cmd_str}")

    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in iter(process.stdout.readline, ""):
        line = line.rstrip()
        if log:
            log(f"  {line}")
        else:
            print(line)

    process.wait()
    if process.returncode != 0:
        raise InstallError(f"Command failed (exit {process.returncode}): {cmd_str}")


def install_sd_cli(
    backend: str | None = None,
    prefix: Path | None = None,
    build_dir: Path | None = None,
    repo_url: str = DEFAULT_REPO_URL,
    log: Callable[[str], None] | None = None,
    force: bool = False,
) -> Path:
    """
    Download and build stable-diffusion.cpp.

    Args:
        backend: GPU backend (cuda, rocm, metal, vulkan). Auto-detected if None.
        prefix: Install prefix (default: ~/.local)
        build_dir: Build directory (default: ~/.cache/sd-cpp-build)
        repo_url: Git repository URL
        log: Callback for log messages
        force: Force rebuild even if binary exists

    Returns:
        Path to installed sd-cli binary

    Raises:
        InstallError: If no GPU backend detected or build fails
    """
    log = log or print
    prefix = prefix or DEFAULT_INSTALL_PREFIX
    build_dir = build_dir or DEFAULT_BUILD_DIR
    bin_path = prefix / "bin" / "sd-cli"

    # Detect backend
    log("[install-sd] Detecting GPU backend...")
    if backend:
        log(f"[install-sd] Using specified backend: {backend}")
    else:
        backend = detect_backend()
        if backend:
            log(f"[install-sd] Auto-detected backend: {backend}")
        else:
            log("[install-sd] Checking CUDA: nvcc not found")
            log("[install-sd] Checking CUDA: /usr/local/cuda/bin/nvcc not found")
            log("[install-sd] Checking ROCm: /opt/rocm not found")
            log("[install-sd] Checking ROCm: hipcc not found")
            log(f"[install-sd] Checking Metal: platform is {sys.platform}")
            log("[install-sd] Checking Vulkan: vulkaninfo not found")
            raise InstallError("No supported GPU backend detected (cuda, rocm, metal, vulkan)")

    if backend not in BACKENDS:
        raise InstallError(f"Unknown backend: {backend}. Supported: {list(BACKENDS.keys())}")

    # Check if already installed
    if bin_path.exists() and not force:
        log(f"[install-sd] sd-cli already installed at {bin_path}")
        log("[install-sd] Use --force to rebuild")
        return bin_path

    log(f"[install-sd] Backend: {backend}")
    log(f"[install-sd] Build directory: {build_dir}")
    log(f"[install-sd] Install prefix: {prefix}")
    log(f"[install-sd] Target binary: {bin_path}")

    # Create directories
    log(f"[install-sd] Creating {build_dir}...")
    build_dir.mkdir(parents=True, exist_ok=True)
    log(f"[install-sd] Creating {prefix / 'bin'}...")
    (prefix / "bin").mkdir(parents=True, exist_ok=True)

    repo_dir = build_dir / "stable-diffusion.cpp"

    # Clone or update repo
    if repo_dir.exists():
        log(f"[install-sd] Repository exists at {repo_dir}")
        log("[install-sd] Pulling latest changes...")
        run_command(["git", "pull", "--ff-only"], cwd=repo_dir, log=log)
        log("[install-sd] Updating submodules...")
        run_command(["git", "submodule", "update", "--init", "--recursive"], cwd=repo_dir, log=log)
    else:
        log(f"[install-sd] Cloning {repo_url}...")
        run_command(
            ["git", "clone", "--recursive", repo_url, str(repo_dir)],
            log=log,
        )

    # Get commit info
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            log(f"[install-sd] Current commit: {result.stdout.strip()}")
    except Exception:
        pass

    # Configure cmake
    cmake_build_dir = repo_dir / "build"
    log(f"[install-sd] Creating build directory: {cmake_build_dir}")
    cmake_build_dir.mkdir(exist_ok=True)

    cmake_flag = BACKENDS[backend]
    cmake_args = [
        "cmake",
        "..",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-D{cmake_flag}=ON",
    ]

    # ROCm needs position-independent code
    if backend == "rocm":
        cmake_args.append("-DCMAKE_POSITION_INDEPENDENT_CODE=ON")

    log(f"[install-sd] Configuring cmake with {cmake_flag}=ON...")
    run_command(cmake_args, cwd=cmake_build_dir, log=log)

    # Build
    cpu_count = os.cpu_count() or 4
    log(f"[install-sd] Building with {cpu_count} parallel jobs...")
    run_command(
        ["cmake", "--build", ".", "--config", "Release", "-j", str(cpu_count)],
        cwd=cmake_build_dir,
        log=log,
    )

    # Copy binary
    built_binary = cmake_build_dir / "bin" / "sd-cli"
    log(f"[install-sd] Looking for binary at {built_binary}")
    if not built_binary.exists():
        raise InstallError(f"Build succeeded but binary not found at {built_binary}")

    log(f"[install-sd] Copying {built_binary} -> {bin_path}")
    shutil.copy2(built_binary, bin_path)
    bin_path.chmod(0o755)
    log(f"[install-sd] Set executable permissions on {bin_path}")

    # Verify
    log("[install-sd] Verifying installation...")
    try:
        result = subprocess.run(
            [str(bin_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stderr or result.stdout
        # Extract version line
        for line in output.split("\n"):
            if "version" in line.lower():
                log(f"[install-sd] {line.strip()}")
                break
        log("[install-sd] Verification successful")
    except subprocess.TimeoutExpired:
        raise InstallError("Binary verification timed out")
    except Exception as e:
        raise InstallError(f"Binary verification failed: {e}")

    log(f"[install-sd] Done! sd-cli installed at {bin_path}")
    return bin_path


async def install_sd_cli_async(
    backend: str | None = None,
    prefix: Path | None = None,
    build_dir: Path | None = None,
    log: Callable[[str], None] | None = None,
    force: bool = False,
) -> Path:
    """Async wrapper for install_sd_cli."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: install_sd_cli(
            backend=backend,
            prefix=prefix,
            build_dir=build_dir,
            log=log,
            force=force,
        ),
    )


def get_sd_cli_path() -> Path | None:
    """Get path to sd-cli if installed."""
    # Check config setting first
    try:
        from xm_agent.config import get_settings
        settings = get_settings()
        if settings.sd_cli_path:
            path = Path(settings.sd_cli_path)
            if path.exists():
                return path
    except Exception:
        pass

    # Check default location
    default_path = DEFAULT_INSTALL_PREFIX / "bin" / "sd-cli"
    if default_path.exists():
        return default_path

    # Check PATH
    which_result = shutil.which("sd-cli")
    if which_result:
        return Path(which_result)

    return None


def get_sd_cli_version(binary_path: Path | None = None) -> str | None:
    """Get sd-cli version string."""
    binary_path = binary_path or get_sd_cli_path()
    if not binary_path or not binary_path.exists():
        return None

    try:
        result = subprocess.run(
            [str(binary_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stderr or result.stdout
        for line in output.split("\n"):
            if "version" in line.lower():
                return line.strip()
        return "unknown"
    except Exception:
        return None
