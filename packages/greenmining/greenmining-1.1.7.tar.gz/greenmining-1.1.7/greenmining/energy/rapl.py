# Intel RAPL (Running Average Power Limit) energy measurement for Linux.

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .base import EnergyMeter, EnergyMetrics, EnergyBackend


class RAPLEnergyMeter(EnergyMeter):
    # Energy measurement using Intel RAPL on Linux.

    RAPL_PATH = Path("/sys/class/powercap/intel-rapl")

    def __init__(self):
        # Initialize RAPL energy meter.
        super().__init__(EnergyBackend.RAPL)
        self._domains: Dict[str, Path] = {}
        self._start_energy: Dict[str, int] = {}
        self._start_time: Optional[float] = None
        self._power_samples: List[float] = []
        self._discover_domains()

    def _discover_domains(self) -> None:
        # Discover available RAPL domains.
        if not self.RAPL_PATH.exists():
            return

        # Find all RAPL domains (intel-rapl:0, intel-rapl:0:0, etc.)
        for domain_path in self.RAPL_PATH.glob("intel-rapl:*"):
            if (domain_path / "energy_uj").exists():
                # Get domain name
                name_file = domain_path / "name"
                if name_file.exists():
                    domain_name = name_file.read_text().strip()
                else:
                    domain_name = domain_path.name

                self._domains[domain_name] = domain_path / "energy_uj"

            # Check for sub-domains (core, uncore, dram, etc.)
            for subdomain_path in domain_path.glob("intel-rapl:*:*"):
                if (subdomain_path / "energy_uj").exists():
                    name_file = subdomain_path / "name"
                    if name_file.exists():
                        subdomain_name = name_file.read_text().strip()
                    else:
                        subdomain_name = subdomain_path.name

                    self._domains[subdomain_name] = subdomain_path / "energy_uj"

    def _read_energy(self, path: Path) -> int:
        # Read energy value in microjoules from a RAPL file.
        try:
            return int(path.read_text().strip())
        except (PermissionError, FileNotFoundError, ValueError):
            return 0

    def is_available(self) -> bool:
        # Check if RAPL is available on this system.
        if not self.RAPL_PATH.exists():
            return False

        if not self._domains:
            return False

        # Try to read at least one domain
        for path in self._domains.values():
            try:
                self._read_energy(path)
                return True
            except Exception:
                continue

        return False

    def start(self) -> None:
        # Start energy measurement.
        if self._is_measuring:
            raise RuntimeError("Already measuring energy")

        self._is_measuring = True
        self._start_time = time.time()
        self._power_samples = []

        # Read starting energy values for all domains
        self._start_energy = {name: self._read_energy(path) for name, path in self._domains.items()}

    def stop(self) -> EnergyMetrics:
        # Stop energy measurement and return results.
        if not self._is_measuring:
            raise RuntimeError("Not currently measuring energy")

        end_time = time.time()
        self._is_measuring = False

        # Read ending energy values
        end_energy = {name: self._read_energy(path) for name, path in self._domains.items()}

        # Calculate energy consumption per domain (in joules)
        duration = end_time - self._start_time

        # Handle counter wrap-around (RAPL counters are typically 32-bit)
        MAX_ENERGY_UJ = 2**32

        domain_energy = {}
        for name in self._domains:
            start = self._start_energy.get(name, 0)
            end = end_energy.get(name, 0)

            if end >= start:
                delta_uj = end - start
            else:
                # Counter wrapped around
                delta_uj = (MAX_ENERGY_UJ - start) + end

            domain_energy[name] = delta_uj / 1_000_000  # Convert to joules

        # Aggregate metrics
        total_joules = sum(domain_energy.values())

        # Extract component-specific energy
        cpu_energy = domain_energy.get("core", 0) or domain_energy.get("package-0", total_joules)
        dram_energy = domain_energy.get("dram", 0)
        gpu_energy = domain_energy.get("uncore", None)  # Integrated GPU

        # Calculate power
        watts_avg = total_joules / duration if duration > 0 else 0

        return EnergyMetrics(
            joules=total_joules,
            watts_avg=watts_avg,
            watts_peak=watts_avg,  # RAPL doesn't provide instantaneous peak
            duration_seconds=duration,
            cpu_energy_joules=cpu_energy,
            dram_energy_joules=dram_energy,
            gpu_energy_joules=gpu_energy,
            carbon_grams=None,  # RAPL doesn't track carbon
            carbon_intensity=None,
            backend="rapl",
            start_time=datetime.fromtimestamp(self._start_time),
            end_time=datetime.fromtimestamp(end_time),
        )

    def get_available_domains(self) -> List[str]:
        # Get list of available RAPL domains.
        return list(self._domains.keys())
