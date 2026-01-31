"""Backend detection logic."""

from gpulegion.backends.base import GPUBackend
from gpulegion.backends.apple import AppleBackend
from gpulegion.backends.nvidia import NvidiaBackend
from gpulegion.backends.fallback import FallbackBackend


def detect_backend() -> GPUBackend:
    """
    Detect and return the appropriate GPU backend for this system.

    Priority order:
    1. Apple Silicon (if on macOS ARM)
    2. NVIDIA (if nvidia-smi available)
    3. Fallback (no GPU support)
    """
    # Try Apple Silicon first
    apple = AppleBackend()
    if apple.available():
        return apple

    # Try NVIDIA
    nvidia = NvidiaBackend()
    if nvidia.available():
        return nvidia

    # Fallback
    return FallbackBackend()
