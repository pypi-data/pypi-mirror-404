# Version-by-version power analysis.
# Measure power consumption across multiple software versions/tags.

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from greenmining.utils import colored_print


@dataclass
class VersionPowerProfile:
    # Power profile for a single version.

    version: str
    commit_sha: str
    energy_joules: float = 0.0
    power_watts_avg: float = 0.0
    duration_seconds: float = 0.0
    iterations: int = 0
    energy_std: float = 0.0  # Standard deviation across iterations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "commit_sha": self.commit_sha,
            "energy_joules": round(self.energy_joules, 4),
            "power_watts_avg": round(self.power_watts_avg, 4),
            "duration_seconds": round(self.duration_seconds, 4),
            "iterations": self.iterations,
            "energy_std": round(self.energy_std, 4),
        }


@dataclass
class VersionPowerReport:
    # Complete power analysis report across versions.

    versions: List[VersionPowerProfile] = field(default_factory=list)
    trend: str = "stable"  # increasing, decreasing, stable
    total_change_percent: float = 0.0
    most_efficient: str = ""
    least_efficient: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "versions": [v.to_dict() for v in self.versions],
            "trend": self.trend,
            "total_change_percent": round(self.total_change_percent, 2),
            "most_efficient": self.most_efficient,
            "least_efficient": self.least_efficient,
        }

    def summary(self) -> str:
        # Generate human-readable summary.
        lines = [
            "Version Power Analysis Report",
            "-" * 40,
            f"Versions analyzed: {len(self.versions)}",
            f"Trend: {self.trend}",
            f"Total change: {self.total_change_percent:+.2f}%",
            f"Most efficient: {self.most_efficient}",
            f"Least efficient: {self.least_efficient}",
            "",
            "Per-version breakdown:",
        ]
        for v in self.versions:
            lines.append(
                f"  {v.version}: {v.energy_joules:.4f}J "
                f"({v.power_watts_avg:.2f}W avg, {v.duration_seconds:.2f}s)"
            )
        return "\n".join(lines)


class VersionPowerAnalyzer:
    # Measure and compare power consumption across software versions.

    def __init__(
        self,
        test_command: str = "pytest tests/",
        energy_backend: str = "rapl",
        iterations: int = 10,
        warmup_iterations: int = 2,
    ):
        # Initialize version power analyzer.
        # Args:
        #   test_command: Shell command to run for measurement
        #   energy_backend: Energy measurement backend
        #   iterations: Number of measurement iterations per version
        #   warmup_iterations: Warmup runs before measuring
        self.test_command = test_command
        self.energy_backend = energy_backend
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self._meter = None

    def _get_energy_meter(self):
        # Get energy meter instance.
        if self._meter is None:
            from greenmining.energy.base import get_energy_meter

            self._meter = get_energy_meter(self.energy_backend)
        return self._meter

    def _measure_version(self, repo_path: str, version: str) -> VersionPowerProfile:
        # Measure power consumption for a specific version.
        meter = self._get_energy_meter()

        # Checkout version
        sha = self._checkout_version(repo_path, version)
        colored_print(f"  Measuring {version} ({sha[:8]})...", "cyan")

        # Warmup
        for i in range(self.warmup_iterations):
            subprocess.run(
                self.test_command,
                shell=True,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=600,
            )

        # Measure iterations
        measurements = []
        for i in range(self.iterations):
            meter.start()
            subprocess.run(
                self.test_command,
                shell=True,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=600,
            )
            metrics = meter.stop()
            measurements.append(metrics)

        # Aggregate
        import numpy as np

        energies = [m.joules for m in measurements]
        avg_energy = float(np.mean(energies))
        std_energy = float(np.std(energies))
        avg_power = float(np.mean([m.watts_avg for m in measurements]))
        avg_duration = float(np.mean([m.duration_seconds for m in measurements]))

        profile = VersionPowerProfile(
            version=version,
            commit_sha=sha,
            energy_joules=avg_energy,
            power_watts_avg=avg_power,
            duration_seconds=avg_duration,
            iterations=self.iterations,
            energy_std=std_energy,
        )

        colored_print(
            f"  {version}: {avg_energy:.4f}J +/-{std_energy:.4f} "
            f"({avg_power:.2f}W, {avg_duration:.2f}s)",
            "green",
        )
        return profile

    def analyze_versions(
        self,
        repo_path: str,
        versions: List[str],
    ) -> VersionPowerReport:
        # Analyze power consumption across multiple versions.
        # Args:
        #   repo_path: Path to local git repository
        #   versions: List of version tags or commit references
        colored_print(f"\nAnalyzing {len(versions)} versions for power consumption", "cyan")
        colored_print(f"  Test: {self.test_command}", "cyan")
        colored_print(f"  Iterations: {self.iterations} (+{self.warmup_iterations} warmup)", "cyan")

        profiles = []
        for version in versions:
            try:
                profile = self._measure_version(repo_path, version)
                profiles.append(profile)
            except Exception as e:
                colored_print(f"  Error measuring {version}: {e}", "red")

        if not profiles:
            return VersionPowerReport()

        # Determine trend
        first_energy = profiles[0].energy_joules
        last_energy = profiles[-1].energy_joules

        if first_energy > 0:
            total_change = ((last_energy - first_energy) / first_energy) * 100
        else:
            total_change = 0.0

        if total_change > 5:
            trend = "increasing"
        elif total_change < -5:
            trend = "decreasing"
        else:
            trend = "stable"

        # Find most/least efficient
        most_efficient = min(profiles, key=lambda p: p.energy_joules)
        least_efficient = max(profiles, key=lambda p: p.energy_joules)

        report = VersionPowerReport(
            versions=profiles,
            trend=trend,
            total_change_percent=total_change,
            most_efficient=most_efficient.version,
            least_efficient=least_efficient.version,
        )

        colored_print(f"\nTrend: {trend} ({total_change:+.2f}%)", "cyan")
        colored_print(f"Most efficient: {most_efficient.version}", "green")
        colored_print(f"Least efficient: {least_efficient.version}", "red")

        # Restore to latest version
        try:
            self._checkout_version(repo_path, versions[-1])
        except Exception:
            pass

        return report

    @staticmethod
    def _checkout_version(repo_path: str, version: str) -> str:
        # Checkout a version and return its SHA.
        subprocess.run(
            ["git", "checkout", version, "--quiet"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
