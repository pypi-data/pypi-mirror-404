"""NVIDIA GPU backend using nvidia-smi."""

import subprocess
from typing import Optional
from gpulegion.backends.base import GPUBackend


class NvidiaBackend(GPUBackend):
    """Backend for NVIDIA GPU monitoring via nvidia-smi."""

    name = "nvidia"

    def available(self) -> bool:
        """Check if nvidia-smi is available."""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                timeout=2,
                check=False,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _query_nvidia_smi(self, query: str) -> Optional[str]:
        """Query nvidia-smi and return result."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    f"--query-gpu={query}",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def usage(self) -> Optional[float]:
        """Get GPU utilization percentage."""
        output = self._query_nvidia_smi("utilization.gpu")
        if output:
            try:
                return float(output.split("\n")[0])
            except (ValueError, IndexError):
                pass
        return None

    def power(self) -> Optional[float]:
        """Get GPU power consumption in watts."""
        output = self._query_nvidia_smi("power.draw")
        if output:
            try:
                return float(output.split("\n")[0])
            except (ValueError, IndexError):
                pass
        return None

    def memory(self) -> Optional[dict]:
        """Get GPU memory information."""
        output = self._query_nvidia_smi("memory.used,memory.total")
        if output:
            try:
                used, total = output.split("\n")[0].split(",")
                return {
                    "used_mb": float(used.strip()),
                    "total_mb": float(total.strip()),
                }
            except (ValueError, IndexError):
                pass
        return None

    def device(self) -> Optional[dict]:
        """Get NVIDIA device information."""
        output = self._query_nvidia_smi("name,driver_version,compute_cap")
        if output:
            try:
                parts = output.split("\n")[0].split(",")
                return {
                    "vendor": "NVIDIA",
                    "model": (parts[0].strip() if len(parts) > 0 else "Unknown"),
                    "driver": (parts[1].strip() if len(parts) > 1 else "Unknown"),
                    "compute_cap": (parts[2].strip() if len(parts) > 2 else "Unknown"),
                }
            except (ValueError, IndexError):
                pass
        return None
