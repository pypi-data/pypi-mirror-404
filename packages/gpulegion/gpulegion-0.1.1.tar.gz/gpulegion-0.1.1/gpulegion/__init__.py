"""gpulegion - Unified GPU telemetry for Apple Silicon, NVIDIA, and beyond."""

from gpulegion.core import (
    backends,
    is_available,
    usage,
    power,
    memory,
    device,
)

__version__ = "0.1.1"
__all__ = [
    "backends",
    "is_available",
    "usage",
    "power",
    "memory",
    "device",
]
