# Power regression detection for identifying commits that increased power consumption.
# Compares energy measurements between baseline and target commits.

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydriller import Repository

from greenmining.utils import colored_print


@dataclass
class PowerRegression:
    # A detected power regression from a commit.

    sha: str
    message: str
    author: str
    date: str
    power_before: float  # watts
    power_after: float  # watts
    power_increase: float  # percentage
    energy_before: float  # joules
    energy_after: float  # joules
    is_regression: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sha": self.sha,
            "message": self.message,
            "author": self.author,
            "date": self.date,
            "power_before": round(self.power_before, 4),
            "power_after": round(self.power_after, 4),
            "power_increase": round(self.power_increase, 2),
            "energy_before": round(self.energy_before, 4),
            "energy_after": round(self.energy_after, 4),
            "is_regression": self.is_regression,
        }


class PowerRegressionDetector:
    # Detect commits that caused power consumption regressions.
    # Runs a test command at each commit and measures energy usage.

    def __init__(
        self,
        test_command: str = "pytest tests/ -x",
        energy_backend: str = "rapl",
        threshold_percent: float = 5.0,
        iterations: int = 5,
        warmup_iterations: int = 1,
    ):
        # Initialize power regression detector.
        # Args:
        #   test_command: Shell command to run for energy measurement
        #   energy_backend: Energy measurement backend (rapl, codecarbon, cpu_meter)
        #   threshold_percent: Minimum percentage increase to flag as regression
        #   iterations: Number of measurement iterations per commit (for accuracy)
        #   warmup_iterations: Number of warmup runs before measurement
        self.test_command = test_command
        self.energy_backend = energy_backend
        self.threshold_percent = threshold_percent
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self._meter = None

    def _get_energy_meter(self):
        # Get energy meter instance.
        if self._meter is None:
            from greenmining.energy.base import get_energy_meter

            self._meter = get_energy_meter(self.energy_backend)
        return self._meter

    def _run_test_command(self, cwd: str) -> float:
        # Run test command and return energy consumed in joules.
        meter = self._get_energy_meter()

        # Warmup
        for _ in range(self.warmup_iterations):
            subprocess.run(
                self.test_command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,
            )

        # Measure
        total_joules = 0.0
        for _ in range(self.iterations):
            meter.start()
            subprocess.run(
                self.test_command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            metrics = meter.stop()
            total_joules += metrics.joules

        return total_joules / self.iterations

    def detect(
        self,
        repo_path: str,
        baseline_commit: str = "HEAD~10",
        target_commit: str = "HEAD",
        max_commits: int = 50,
    ) -> List[PowerRegression]:
        # Detect power regressions between baseline and target commits.
        # Args:
        #   repo_path: Path to local git repository
        #   baseline_commit: Baseline commit SHA or reference
        #   target_commit: Target commit SHA or reference
        #   max_commits: Maximum commits to analyze
        regressions = []

        colored_print(f"Detecting power regressions in {repo_path}", "cyan")
        colored_print(f"  Range: {baseline_commit}..{target_commit}", "cyan")
        colored_print(f"  Test: {self.test_command}", "cyan")
        colored_print(f"  Threshold: {self.threshold_percent}%", "cyan")

        # Get commits in range
        commits = list(
            Repository(
                path_to_repo=repo_path,
                from_commit=baseline_commit,
                to_commit=target_commit,
            ).traverse_commits()
        )

        if not commits:
            colored_print("No commits found in range", "yellow")
            return regressions

        # Measure baseline
        colored_print(f"  Measuring baseline ({commits[0].hash[:8]})...", "cyan")
        self._checkout(repo_path, commits[0].hash)
        baseline_energy = self._run_test_command(repo_path)
        colored_print(f"  Baseline: {baseline_energy:.4f} joules", "green")

        previous_energy = baseline_energy
        commit_count = 0

        for commit in commits[1:]:
            if commit_count >= max_commits:
                break

            try:
                self._checkout(repo_path, commit.hash)
                current_energy = self._run_test_command(repo_path)

                # Calculate change
                if previous_energy > 0:
                    change_percent = ((current_energy - previous_energy) / previous_energy) * 100
                else:
                    change_percent = 0.0

                # Check for regression
                if change_percent > self.threshold_percent:
                    regression = PowerRegression(
                        sha=commit.hash,
                        message=commit.msg[:200],
                        author=commit.author.name,
                        date=commit.author_date.isoformat() if commit.author_date else "",
                        power_before=previous_energy / max(1, self.iterations),
                        power_after=current_energy / max(1, self.iterations),
                        power_increase=change_percent,
                        energy_before=previous_energy,
                        energy_after=current_energy,
                    )
                    regressions.append(regression)
                    colored_print(f"  REGRESSION: {commit.hash[:8]} +{change_percent:.1f}%", "red")
                else:
                    colored_print(f"  OK: {commit.hash[:8]} {change_percent:+.1f}%", "green")

                previous_energy = current_energy
                commit_count += 1

            except Exception as e:
                colored_print(f"  Warning: Failed on {commit.hash[:8]}: {e}", "yellow")
                continue

        # Restore to target
        self._checkout(repo_path, target_commit)

        colored_print(
            f"\nFound {len(regressions)} power regressions "
            f"(>{self.threshold_percent}% increase)",
            "cyan" if not regressions else "red",
        )

        return regressions

    @staticmethod
    def _checkout(repo_path: str, ref: str):
        # Checkout a specific commit.
        subprocess.run(
            ["git", "checkout", ref, "--quiet"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
