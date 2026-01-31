"""Apple Silicon GPU backend using powermetrics."""

import subprocess
import re
import platform
from typing import Optional
from gpulegion.backends.base import GPUBackend


class AppleBackend(GPUBackend):
    """Backend for Apple Silicon (M1-M5) GPU monitoring."""

    name = "apple"

    def __init__(self):
        self._cached_device_info = None

    def available(self) -> bool:
        """Check if running on macOS with Apple Silicon."""
        if platform.system() != "Darwin":
            return False

        # Check if it's Apple Silicon (arm64)
        machine = platform.machine().lower()
        return machine in ("arm64", "aarch64")

    def _run_powermetrics(
        self, samplers: str = "gpu_power", duration_ms: int = 100
    ) -> Optional[str]:
        """Run powermetrics command and return output."""
        try:
            cmd = [
                "sudo",
                "-n",  # -n = non-interactive, will fail if password required
                "powermetrics",
                "--samplers",
                samplers,
                "--sample-count",
                "1",
                "--sample-rate",
                str(duration_ms),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return None

    def usage(self) -> Optional[float]:
        """
        Get GPU usage percentage.

        Note: Requires passwordless sudo for powermetrics.
        """
        output = self._run_powermetrics("gpu_power")
        if not output:
            return None

        # Parse GPU HW active residency percentage (M1-M5)
        # Example: "GPU HW active residency:  35.34%"
        match = re.search(r"GPU HW active residency:\s+([\d.]+)%", output)
        if match:
            return float(match.group(1))

        # Fallback: older pattern
        match = re.search(r"GPU active residency:\s+([\d.]+)%", output)
        if match:
            return float(match.group(1))

        # Alternative pattern
        match = re.search(r"GPU\s+active:\s+([\d.]+)%", output)
        if match:
            return float(match.group(1))

        return None

    def power(self) -> Optional[float]:
        """Get GPU power consumption in watts."""
        output = self._run_powermetrics("gpu_power")
        if not output:
            return None

        # Parse GPU power
        # Example: "GPU Power: 1234 mW"
        match = re.search(r"GPU Power:\s+([\d.]+)\s*mW", output)
        if match:
            return float(match.group(1)) / 1000.0  # Convert mW to W

        return None

    def memory(self) -> Optional[dict]:
        """
        Get GPU memory info.

        Note: Apple Silicon uses unified memory, so this returns None.
        Use system memory monitoring instead.
        """
        return None

    def device(self) -> Optional[dict]:
        """Get Apple Silicon device information."""
        if self._cached_device_info:
            return self._cached_device_info

        try:
            # Get chip model
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            chip_name = result.stdout.strip() if result.returncode == 0 else "Unknown"

            # Get GPU core count (if available)
            subprocess.run(
                ["sysctl", "-n", "hw.nperflevels"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )

            self._cached_device_info = {
                "vendor": "Apple",
                "model": chip_name,
                "arch": platform.machine(),
            }

            return self._cached_device_info
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "vendor": "Apple",
                "model": "Unknown",
                "arch": platform.machine(),
            }
