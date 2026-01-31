"""Core API for gpulegion."""

from typing import Optional
from gpulegion.backends.detector import detect_backend

_BACKEND = None  # pylint: disable=invalid-name


def _get_backend():
    """Lazy-load the appropriate backend."""
    global _BACKEND  # pylint: disable=global-statement
    if _BACKEND is None:
        _BACKEND = detect_backend()
    return _BACKEND


def backends() -> list[str]:
    """Return list of available backend names."""
    backend = _get_backend()
    return [backend.name] if backend.available() else []


def is_available() -> bool:
    """Check if GPU monitoring is available on this system."""
    backend = _get_backend()
    return backend.available()


def usage() -> Optional[float]:
    """
    Get current GPU usage percentage.

    Returns:
        Float between 0-100, or None if unavailable.
    """
    backend = _get_backend()
    if not backend.available():
        return None
    return backend.usage()


def power() -> Optional[float]:
    """
    Get current GPU power consumption in watts.

    Returns:
        Float in watts, or None if unavailable.
    """
    backend = _get_backend()
    if not backend.available():
        return None
    return backend.power()


def memory() -> Optional[dict]:
    """
    Get GPU memory information.

    Returns:
        Dict with 'used_mb' and 'total_mb', or None if unavailable.
    """
    backend = _get_backend()
    if not backend.available():
        return None
    return backend.memory()


def device() -> Optional[dict]:
    """
    Get GPU device information.

    Returns:
        Dict with 'vendor', 'model', and other device info,
        or None if unavailable.
    """
    backend = _get_backend()
    if not backend.available():
        return None
    return backend.device()
