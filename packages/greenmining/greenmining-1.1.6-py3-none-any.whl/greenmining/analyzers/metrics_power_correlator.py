# Metrics-to-power correlation analysis.
# Build models correlating code metrics (complexity, nloc, churn) with power consumption.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats


@dataclass
class CorrelationResult:
    # Result of a metrics-to-power correlation analysis.

    metric_name: str
    pearson_r: float = 0.0
    pearson_p: float = 1.0
    spearman_r: float = 0.0
    spearman_p: float = 1.0
    significant: bool = False
    strength: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "pearson_r": round(self.pearson_r, 4),
            "pearson_p": round(self.pearson_p, 6),
            "spearman_r": round(self.spearman_r, 4),
            "spearman_p": round(self.spearman_p, 6),
            "significant": self.significant,
            "strength": self.strength,
        }


class MetricsPowerCorrelator:
    # Correlate code metrics with power consumption measurements.
    # Computes Pearson and Spearman correlations between software metrics
    # and measured energy/power values.

    def __init__(self, significance_level: float = 0.05):
        # Initialize correlator.
        # Args:
        #   significance_level: P-value threshold for significance
        self.significance_level = significance_level
        self._metrics_data: Dict[str, List[float]] = {}
        self._power_data: List[float] = []
        self._fitted = False
        self._results: Dict[str, CorrelationResult] = {}
        self._feature_importance: Dict[str, float] = {}

    def fit(
        self,
        metrics: List[str],
        metrics_values: Dict[str, List[float]],
        power_measurements: List[float],
    ) -> None:
        # Fit the correlator with metrics and power data.
        # Args:
        #   metrics: List of metric names to correlate
        #   metrics_values: Dict mapping metric name -> list of values
        #   power_measurements: List of power measurement values
        self._metrics_data = {m: metrics_values[m] for m in metrics if m in metrics_values}
        self._power_data = power_measurements

        n = len(power_measurements)
        if n < 3:
            raise ValueError("Need at least 3 data points for correlation analysis")

        # Compute correlations
        for metric_name, values in self._metrics_data.items():
            if len(values) != n:
                continue

            result = self._compute_correlation(metric_name, values, power_measurements)
            self._results[metric_name] = result

        # Compute feature importance (normalized absolute Spearman)
        max_abs = max((abs(r.spearman_r) for r in self._results.values()), default=1.0)
        if max_abs > 0:
            self._feature_importance = {
                name: abs(r.spearman_r) / max_abs for name, r in self._results.items()
            }

        self._fitted = True

    def _compute_correlation(
        self, metric_name: str, metric_values: List[float], power_values: List[float]
    ) -> CorrelationResult:
        # Compute Pearson and Spearman correlations for a single metric.
        x = np.array(metric_values, dtype=float)
        y = np.array(power_values, dtype=float)

        # Handle constant arrays
        if np.std(x) == 0 or np.std(y) == 0:
            return CorrelationResult(metric_name=metric_name)

        # Pearson correlation (linear)
        pearson_r, pearson_p = stats.pearsonr(x, y)

        # Spearman correlation (monotonic)
        spearman_r, spearman_p = stats.spearmanr(x, y)

        # Significance
        significant = pearson_p < self.significance_level or spearman_p < self.significance_level

        # Strength classification
        abs_r = max(abs(pearson_r), abs(spearman_r))
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.4:
            strength = "moderate"
        elif abs_r >= 0.2:
            strength = "weak"
        else:
            strength = "negligible"

        return CorrelationResult(
            metric_name=metric_name,
            pearson_r=float(pearson_r),
            pearson_p=float(pearson_p),
            spearman_r=float(spearman_r),
            spearman_p=float(spearman_p),
            significant=significant,
            strength=strength,
        )

    @property
    def pearson(self) -> Dict[str, float]:
        # Get Pearson correlations for all metrics.
        return {name: r.pearson_r for name, r in self._results.items()}

    @property
    def spearman(self) -> Dict[str, float]:
        # Get Spearman correlations for all metrics.
        return {name: r.spearman_r for name, r in self._results.items()}

    @property
    def feature_importance(self) -> Dict[str, float]:
        # Get normalized feature importance scores.
        return self._feature_importance

    def get_results(self) -> Dict[str, CorrelationResult]:
        # Get all correlation results.
        return self._results

    def get_significant_correlations(self) -> Dict[str, CorrelationResult]:
        # Get only statistically significant correlations.
        return {name: r for name, r in self._results.items() if r.significant}

    def summary(self) -> Dict[str, Any]:
        # Generate summary of correlation analysis.
        return {
            "total_metrics": len(self._results),
            "significant_count": sum(1 for r in self._results.values() if r.significant),
            "correlations": {name: r.to_dict() for name, r in self._results.items()},
            "feature_importance": self._feature_importance,
            "strongest_positive": max(
                self._results.values(), key=lambda r: r.spearman_r, default=None
            ),
            "strongest_negative": min(
                self._results.values(), key=lambda r: r.spearman_r, default=None
            ),
        }
