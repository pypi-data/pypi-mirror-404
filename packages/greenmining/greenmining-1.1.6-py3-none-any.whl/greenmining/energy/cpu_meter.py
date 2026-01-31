# Cross-platform CPU energy meter using system resource monitoring.
# Supports Linux, macOS, and Windows by estimating power from CPU utilization.

from __future__ import annotations

import time
import platform
from datetime import datetime
from typing import Dict, List, Optional

from .base import EnergyMeter, EnergyMetrics, EnergyBackend


class CPUEnergyMeter(EnergyMeter):
    # Cross-platform CPU energy estimation using utilization-based modeling.
    # Uses CPU utilization percentage to estimate power draw based on TDP.
    # Falls back to RAPL on Linux when available for direct measurement.

    # Default TDP values by platform (in watts)
    DEFAULT_TDP = {
        "Linux": 65.0,
        "Darwin": 30.0,  # Apple Silicon typical
        "Windows": 65.0,
    }

    def __init__(self, tdp_watts: Optional[float] = None, sample_interval: float = 0.5):
        # Initialize CPU energy meter.
        # Args:
        #   tdp_watts: CPU Thermal Design Power in watts (auto-detected if None)
        #   sample_interval: Sampling interval in seconds
        super().__init__(EnergyBackend.CPU_METER)
        self.tdp_watts = tdp_watts or self._detect_tdp()
        self.sample_interval = sample_interval
        self._start_time: Optional[float] = None
        self._samples: List[float] = []
        self._platform = platform.system()
        self._psutil_available = self._check_psutil()

    def _check_psutil(self) -> bool:
        # Check if psutil is available.
        try:
            import psutil

            return True
        except ImportError:
            return False

    def _detect_tdp(self) -> float:
        # Auto-detect CPU TDP based on platform.
        system = platform.system()

        # Try to read from Linux sysfs
        if system == "Linux":
            try:
                import os

                rapl_path = "/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_max_power_uw"
                if os.path.exists(rapl_path):
                    with open(rapl_path) as f:
                        return int(f.read().strip()) / 1_000_000  # Convert uW to W
            except Exception:
                pass

        return self.DEFAULT_TDP.get(system, 65.0)

    def _get_cpu_percent(self) -> float:
        # Get current CPU utilization percentage.
        if self._psutil_available:
            import psutil

            return psutil.cpu_percent(interval=None)

        # Fallback: read from /proc/stat on Linux
        if self._platform == "Linux":
            try:
                with open("/proc/stat") as f:
                    line = f.readline()
                    parts = line.split()
                    idle = int(parts[4])
                    total = sum(int(p) for p in parts[1:])
                    return (1 - idle / total) * 100 if total > 0 else 0.0
            except Exception:
                pass

        return 50.0  # Default estimate

    def is_available(self) -> bool:
        # CPU energy estimation is available on all platforms.
        return True

    def start(self) -> None:
        # Start energy measurement.
        if self._is_measuring:
            raise RuntimeError("Already measuring energy")
        self._is_measuring = True
        self._start_time = time.time()
        self._samples = []
        # Prime the CPU percent measurement
        if self._psutil_available:
            import psutil

            psutil.cpu_percent(interval=None)

    def stop(self) -> EnergyMetrics:
        # Stop energy measurement and return results.
        if not self._is_measuring:
            raise RuntimeError("Not currently measuring energy")

        end_time = time.time()
        self._is_measuring = False
        duration = end_time - self._start_time

        # Get final CPU utilization sample
        cpu_percent = self._get_cpu_percent()
        self._samples.append(cpu_percent)

        # Estimate energy from CPU utilization and TDP
        # Power model: P = P_idle + (P_max - P_idle) * utilization
        # Typical idle power is ~30% of TDP
        idle_fraction = 0.3
        p_idle = self.tdp_watts * idle_fraction
        avg_utilization = sum(self._samples) / len(self._samples) / 100.0

        estimated_power = p_idle + (self.tdp_watts - p_idle) * avg_utilization
        estimated_joules = estimated_power * duration

        return EnergyMetrics(
            joules=estimated_joules,
            watts_avg=estimated_power,
            watts_peak=(
                self.tdp_watts * max(s / 100.0 for s in self._samples)
                if self._samples
                else estimated_power
            ),
            duration_seconds=duration,
            cpu_energy_joules=estimated_joules,
            dram_energy_joules=0,
            gpu_energy_joules=None,
            carbon_grams=None,
            carbon_intensity=None,
            backend="cpu_meter",
            start_time=datetime.fromtimestamp(self._start_time),
            end_time=datetime.fromtimestamp(end_time),
        )
