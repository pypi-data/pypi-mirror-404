"""Fallback backend when no GPU is detected."""

from typing import Optional
from gpulegion.backends.base import GPUBackend


class FallbackBackend(GPUBackend):
    """Fallback backend that returns None for all queries."""

    name = "fallback"

    def available(self) -> bool:
        """Always returns False - no GPU available."""
        return False

    def usage(self) -> Optional[float]:
        """No GPU available."""
        return None

    def power(self) -> Optional[float]:
        """No GPU available."""
        return None

    def memory(self) -> Optional[dict]:
        """No GPU available."""
        return None

    def device(self) -> Optional[dict]:
        """No GPU available."""
        return None
