"""GPU monitoring backends."""

from gpulegion.backends.base import GPUBackend
from gpulegion.backends.apple import AppleBackend
from gpulegion.backends.nvidia import NvidiaBackend
from gpulegion.backends.fallback import FallbackBackend
from gpulegion.backends.detector import detect_backend

__all__ = [
    "GPUBackend",
    "AppleBackend",
    "NvidiaBackend",
    "FallbackBackend",
    "detect_backend",
]
