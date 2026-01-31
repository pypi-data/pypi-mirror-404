# CodeCarbon integration for carbon-aware energy measurement.

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from .base import EnergyMeter, EnergyMetrics, EnergyBackend


class CodeCarbonMeter(EnergyMeter):
    # Energy measurement using CodeCarbon library.

    def __init__(
        self,
        project_name: str = "greenmining",
        output_dir: Optional[str] = None,
        save_to_file: bool = False,
    ):
        # Initialize CodeCarbon energy meter.
        super().__init__(EnergyBackend.CODECARBON)
        self.project_name = project_name
        self.output_dir = output_dir
        self.save_to_file = save_to_file
        self._tracker = None
        self._start_time: Optional[float] = None
        self._codecarbon_available = self._check_codecarbon()

    def _check_codecarbon(self) -> bool:
        # Check if CodeCarbon is installed.
        try:
            from codecarbon import EmissionsTracker

            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        # Check if CodeCarbon is available.
        return self._codecarbon_available

    def start(self) -> None:
        # Start energy measurement.
        if not self._codecarbon_available:
            raise RuntimeError("CodeCarbon is not installed. Run: pip install codecarbon")

        if self._is_measuring:
            raise RuntimeError("Already measuring energy")

        from codecarbon import EmissionsTracker

        self._is_measuring = True
        self._start_time = time.time()

        # Create emissions tracker
        tracker_kwargs = {
            "project_name": self.project_name,
            "measure_power_secs": 1,
            "save_to_file": self.save_to_file,
            "log_level": "error",  # Suppress verbose output
        }

        if self.output_dir:
            tracker_kwargs["output_dir"] = self.output_dir

        self._tracker = EmissionsTracker(**tracker_kwargs)
        self._tracker.start()

    def stop(self) -> EnergyMetrics:
        # Stop energy measurement and return results.
        if not self._is_measuring:
            raise RuntimeError("Not currently measuring energy")

        end_time = time.time()
        self._is_measuring = False

        # Stop tracker and get emissions
        emissions_kg = self._tracker.stop()

        # Get detailed data from tracker
        duration = end_time - self._start_time

        # CodeCarbon stores data in tracker._total_energy (kWh)
        # In v3.x it may return an Energy object, extract the value
        energy_raw = getattr(self._tracker, "_total_energy", 0) or 0
        if hasattr(energy_raw, "kWh"):
            energy_kwh = float(energy_raw.kWh)
        else:
            energy_kwh = float(energy_raw) if energy_raw else 0.0

        # Convert kWh to joules (1 kWh = 3,600,000 J)
        energy_joules = energy_kwh * 3_600_000

        # Calculate average power
        watts_avg = (energy_joules / duration) if duration > 0 else 0

        # Get carbon intensity if available
        carbon_intensity = None
        try:
            carbon_intensity = getattr(self._tracker, "_carbon_intensity", None)
            if hasattr(carbon_intensity, "value"):
                carbon_intensity = float(carbon_intensity.value)
        except Exception:
            pass

        # Convert emissions from kg to grams (handle Energy objects)
        if hasattr(emissions_kg, "value"):
            emissions_kg = float(emissions_kg.value)
        carbon_grams = float(emissions_kg or 0) * 1000

        return EnergyMetrics(
            joules=energy_joules,
            watts_avg=watts_avg,
            watts_peak=watts_avg,  # CodeCarbon doesn't provide peak
            duration_seconds=duration,
            cpu_energy_joules=energy_joules,  # CodeCarbon aggregates all sources
            dram_energy_joules=0,
            gpu_energy_joules=None,
            carbon_grams=carbon_grams,
            carbon_intensity=carbon_intensity,
            backend="codecarbon",
            start_time=datetime.fromtimestamp(self._start_time),
            end_time=datetime.fromtimestamp(end_time),
        )

    def get_carbon_intensity(self) -> Optional[float]:
        # Get current carbon intensity for the configured region.
        if not self._codecarbon_available:
            return None

        try:
            from codecarbon import EmissionsTracker

            # Create temporary tracker to get carbon intensity
            tracker = EmissionsTracker(
                project_name="carbon_check",
                country_iso_code=self.country_iso_code,
                save_to_file=False,
                log_level="error",
            )
            tracker.start()
            tracker.stop()

            return getattr(tracker, "_carbon_intensity", None)
        except Exception:
            return None
