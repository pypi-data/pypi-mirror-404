# Carbon footprint reporter for estimating CO2 emissions from energy measurements.
# Converts energy consumption to carbon equivalents using regional grid intensity data.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import EnergyMetrics

# Average carbon intensity by country (gCO2/kWh) - 2024 data
# Source: Electricity Maps, IEA
CARBON_INTENSITY_BY_COUNTRY = {
    "USA": 379,
    "GBR": 207,
    "DEU": 338,
    "FRA": 56,
    "SWE": 25,
    "NOR": 17,
    "CAN": 120,
    "AUS": 548,
    "JPN": 432,
    "CHN": 555,
    "IND": 632,
    "BRA": 75,
    "ITA": 315,
    "ESP": 175,
    "NLD": 328,
    "KOR": 415,
    "POL": 614,
    "ZAF": 709,
    "MEX": 391,
    "TUR": 377,
}

# Carbon intensity by cloud provider region (gCO2/kWh)
CLOUD_REGION_INTENSITY = {
    "aws": {
        "us-east-1": 379,
        "us-east-2": 425,
        "us-west-1": 230,
        "us-west-2": 118,
        "eu-west-1": 316,
        "eu-west-2": 207,
        "eu-west-3": 56,
        "eu-north-1": 25,
        "eu-central-1": 338,
        "ap-northeast-1": 432,
        "ap-southeast-1": 379,
        "ap-south-1": 632,
        "ca-central-1": 120,
        "sa-east-1": 75,
    },
    "gcp": {
        "us-central1": 425,
        "us-east1": 379,
        "us-west1": 118,
        "europe-west1": 175,
        "europe-west4": 328,
        "europe-north1": 25,
        "asia-east1": 509,
        "asia-northeast1": 432,
        "australia-southeast1": 548,
    },
    "azure": {
        "eastus": 379,
        "westus2": 118,
        "westeurope": 328,
        "northeurope": 316,
        "swedencentral": 25,
        "francecentral": 56,
        "japaneast": 432,
        "australiaeast": 548,
    },
}


@dataclass
class CarbonReport:
    # Carbon emissions report from energy measurements.

    total_energy_kwh: float = 0.0
    total_emissions_kg: float = 0.0
    carbon_intensity_gco2_kwh: float = 0.0
    country_iso: str = ""
    cloud_provider: str = ""
    cloud_region: str = ""
    tree_months: float = 0.0  # Equivalent tree-months to offset
    smartphone_charges: float = 0.0  # Equivalent smartphone charges
    km_driven: float = 0.0  # Equivalent km driven in average car
    analysis_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_energy_kwh": round(self.total_energy_kwh, 6),
            "total_emissions_kg": round(self.total_emissions_kg, 6),
            "total_emissions_grams": round(self.total_emissions_kg * 1000, 4),
            "carbon_intensity_gco2_kwh": self.carbon_intensity_gco2_kwh,
            "country_iso": self.country_iso,
            "cloud_provider": self.cloud_provider,
            "cloud_region": self.cloud_region,
            "equivalents": {
                "tree_months": round(self.tree_months, 2),
                "smartphone_charges": round(self.smartphone_charges, 1),
                "km_driven": round(self.km_driven, 3),
            },
            "analysis_results": self.analysis_results,
        }

    def summary(self) -> str:
        # Generate human-readable summary.
        lines = [
            "Carbon Footprint Report",
            "-" * 40,
            f"Total Energy: {self.total_energy_kwh:.6f} kWh",
            f"CO2 Emissions: {self.total_emissions_kg * 1000:.4f} grams",
            f"Carbon Intensity: {self.carbon_intensity_gco2_kwh} gCO2/kWh",
        ]
        if self.country_iso:
            lines.append(f"Region: {self.country_iso}")
        if self.cloud_provider and self.cloud_region:
            lines.append(f"Cloud: {self.cloud_provider} ({self.cloud_region})")
        lines.extend(
            [
                "",
                "Equivalents:",
                f"  {self.tree_months:.2f} tree-months to offset",
                f"  {self.smartphone_charges:.1f} smartphone charges",
                f"  {self.km_driven:.3f} km driven (average car)",
            ]
        )
        return "\n".join(lines)


class CarbonReporter:
    # Generate carbon footprint reports from energy measurements.

    # Constants for equivalence calculations
    TREE_ABSORPTION_KG_PER_MONTH = 1.0  # ~12 kg CO2/year per tree
    SMARTPHONE_CHARGE_KWH = 0.012  # ~12 Wh per charge
    CAR_EMISSIONS_KG_PER_KM = 0.12  # Average ICE car

    def __init__(
        self,
        country_iso: str = "USA",
        cloud_provider: Optional[str] = None,
        region: Optional[str] = None,
    ):
        # Initialize carbon reporter.
        # Args:
        #   country_iso: ISO 3166-1 alpha-3 country code
        #   cloud_provider: Cloud provider (aws, gcp, azure)
        #   region: Cloud region (e.g., us-east-1)
        self.country_iso = country_iso.upper()
        self.cloud_provider = (cloud_provider or "").lower()
        self.region = region or ""
        self.carbon_intensity = self._get_carbon_intensity()

    def _get_carbon_intensity(self) -> float:
        # Determine carbon intensity based on cloud region or country.
        # Cloud region takes priority
        if self.cloud_provider and self.region:
            provider_regions = CLOUD_REGION_INTENSITY.get(self.cloud_provider, {})
            if self.region in provider_regions:
                return provider_regions[self.region]

        # Fall back to country average
        return CARBON_INTENSITY_BY_COUNTRY.get(self.country_iso, 400)

    def generate_report(
        self,
        energy_metrics: Optional[EnergyMetrics] = None,
        analysis_results: Optional[List[Dict[str, Any]]] = None,
        total_joules: Optional[float] = None,
    ) -> CarbonReport:
        # Generate a carbon footprint report.
        # Args:
        #   energy_metrics: EnergyMetrics object from measurement
        #   analysis_results: List of analysis result dicts with energy data
        #   total_joules: Direct energy input in joules

        total_energy_joules = 0.0
        result_summaries = []

        if energy_metrics:
            total_energy_joules += energy_metrics.joules

        if total_joules:
            total_energy_joules += total_joules

        if analysis_results:
            for result in analysis_results:
                energy = result.get("energy_metrics", {})
                if energy:
                    joules = energy.get("joules", 0)
                    total_energy_joules += joules
                    result_summaries.append(
                        {
                            "name": result.get("name", "unknown"),
                            "energy_joules": joules,
                            "duration_seconds": energy.get("duration_seconds", 0),
                        }
                    )

        # Convert joules to kWh
        total_kwh = total_energy_joules / 3_600_000

        # Calculate emissions
        emissions_grams = total_kwh * self.carbon_intensity
        emissions_kg = emissions_grams / 1000

        # Calculate equivalents
        tree_months = emissions_kg / self.TREE_ABSORPTION_KG_PER_MONTH if emissions_kg > 0 else 0
        smartphone_charges = total_kwh / self.SMARTPHONE_CHARGE_KWH if total_kwh > 0 else 0
        km_driven = emissions_kg / self.CAR_EMISSIONS_KG_PER_KM if emissions_kg > 0 else 0

        return CarbonReport(
            total_energy_kwh=total_kwh,
            total_emissions_kg=emissions_kg,
            carbon_intensity_gco2_kwh=self.carbon_intensity,
            country_iso=self.country_iso,
            cloud_provider=self.cloud_provider,
            cloud_region=self.region,
            tree_months=tree_months,
            smartphone_charges=smartphone_charges,
            km_driven=km_driven,
            analysis_results=result_summaries,
        )

    def get_carbon_intensity(self) -> float:
        # Get the configured carbon intensity.
        return self.carbon_intensity

    @staticmethod
    def get_supported_countries() -> List[str]:
        # Get list of supported country ISO codes.
        return list(CARBON_INTENSITY_BY_COUNTRY.keys())

    @staticmethod
    def get_supported_cloud_regions(provider: str) -> List[str]:
        # Get list of supported cloud regions for a provider.
        return list(CLOUD_REGION_INTENSITY.get(provider.lower(), {}).keys())
