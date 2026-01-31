"""Abstract base class for GPU backends."""

from abc import ABC, abstractmethod
from typing import Optional


class GPUBackend(ABC):
    """Abstract interface for GPU monitoring backends."""

    name: str = "base"

    @abstractmethod
    def available(self) -> bool:
        """Check if this backend is available on the current system."""
        raise NotImplementedError

    @abstractmethod
    def usage(self) -> Optional[float]:
        """Get GPU usage percentage (0-100)."""
        raise NotImplementedError

    @abstractmethod
    def power(self) -> Optional[float]:
        """Get GPU power consumption in watts."""
        raise NotImplementedError

    @abstractmethod
    def memory(self) -> Optional[dict]:
        """Get GPU memory info: {'used_mb': float, 'total_mb': float}."""
        raise NotImplementedError

    @abstractmethod
    def device(self) -> Optional[dict]:
        """Get device info: {'vendor': str, 'model': str, ...}."""
        raise NotImplementedError
