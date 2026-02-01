# Base classes and interfaces for energy measurement.

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import time


class EnergyBackend(Enum):
    # Supported energy measurement backends.

    RAPL = "rapl"  # Intel RAPL (Linux)
    CODECARBON = "codecarbon"  # CodeCarbon (cross-platform)
    CPU_METER = "cpu_meter"  # CPU Energy Meter


@dataclass
class EnergyMetrics:
    # Energy measurement results from a profiling session.

    # Core energy metrics
    joules: float = 0.0  # Total energy consumed
    watts_avg: float = 0.0  # Average power draw
    watts_peak: float = 0.0  # Peak power draw
    duration_seconds: float = 0.0  # Measurement duration

    # Component-specific energy (if available)
    cpu_energy_joules: float = 0.0  # CPU-specific energy
    dram_energy_joules: float = 0.0  # Memory energy
    gpu_energy_joules: Optional[float] = None  # GPU energy if available

    # Carbon footprint (if carbon tracking enabled)
    carbon_grams: Optional[float] = None  # CO2 equivalent in grams
    carbon_intensity: Optional[float] = None  # gCO2/kWh of grid

    # Metadata
    backend: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def energy_joules(self) -> float:
        return self.joules

    @property
    def average_power_watts(self) -> float:
        return self.watts_avg

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary.
        return {
            "joules": self.joules,
            "watts_avg": self.watts_avg,
            "watts_peak": self.watts_peak,
            "duration_seconds": self.duration_seconds,
            "cpu_energy_joules": self.cpu_energy_joules,
            "dram_energy_joules": self.dram_energy_joules,
            "gpu_energy_joules": self.gpu_energy_joules,
            "carbon_grams": self.carbon_grams,
            "carbon_intensity": self.carbon_intensity,
            "backend": self.backend,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


@dataclass
class CommitEnergyProfile:
    # Energy profile for a specific commit.

    commit_hash: str
    energy_before: Optional[EnergyMetrics] = None  # Parent commit energy
    energy_after: Optional[EnergyMetrics] = None  # This commit energy
    energy_delta: float = 0.0  # Change in joules
    energy_regression: bool = False  # True if energy increased
    regression_percentage: float = 0.0  # % change

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary.
        return {
            "commit_hash": self.commit_hash,
            "energy_before": self.energy_before.to_dict() if self.energy_before else None,
            "energy_after": self.energy_after.to_dict() if self.energy_after else None,
            "energy_delta": self.energy_delta,
            "energy_regression": self.energy_regression,
            "regression_percentage": self.regression_percentage,
        }


class EnergyMeter(ABC):
    # Abstract base class for energy measurement backends.

    def __init__(self, backend: EnergyBackend):
        # Initialize the energy meter.
        self.backend = backend
        self._is_measuring = False
        self._start_time: Optional[float] = None
        self._measurements: List[float] = []

    @abstractmethod
    def is_available(self) -> bool:
        # Check if this energy measurement backend is available on the system.
        pass

    @abstractmethod
    def start(self) -> None:
        # Start energy measurement.
        pass

    @abstractmethod
    def stop(self) -> EnergyMetrics:
        # Stop energy measurement and return results.
        pass

    def measure(self, func: Callable, *args, **kwargs) -> tuple[Any, EnergyMetrics]:
        # Measure energy consumption of a function call.
        self.start()
        try:
            result = func(*args, **kwargs)
        finally:
            metrics = self.stop()
        return result, metrics

    def measure_command(self, command: str, timeout: Optional[int] = None) -> EnergyMetrics:
        # Measure energy consumption of a shell command.
        import subprocess

        self.start()
        try:
            subprocess.run(
                command,
                shell=True,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        finally:
            metrics = self.stop()
        return metrics

    def __enter__(self):
        # Context manager entry.
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Context manager exit.
        self.stop()
        return False


def get_energy_meter(backend: str = "rapl") -> EnergyMeter:
    # Factory function to get an energy meter instance.
    # Supported backends: rapl, codecarbon, cpu_meter, auto
    from .rapl import RAPLEnergyMeter
    from .codecarbon_meter import CodeCarbonMeter
    from .cpu_meter import CPUEnergyMeter

    backend_lower = backend.lower()

    if backend_lower == "rapl":
        meter = RAPLEnergyMeter()
    elif backend_lower == "codecarbon":
        meter = CodeCarbonMeter()
    elif backend_lower in ("cpu_meter", "cpu"):
        meter = CPUEnergyMeter()
    elif backend_lower == "auto":
        # Try RAPL first (most accurate), fall back to CPU meter
        rapl = RAPLEnergyMeter()
        if rapl.is_available():
            return rapl
        meter = CPUEnergyMeter()
    else:
        raise ValueError(f"Unsupported energy backend: {backend}")

    if not meter.is_available():
        raise ValueError(f"Energy backend '{backend}' is not available on this system")

    return meter
