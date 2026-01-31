import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


def _load_yaml_config(yaml_path: Path) -> Dict[str, Any]:
    # Load configuration from YAML file if it exists.
    if not yaml_path.exists():
        return {}
    try:
        import yaml

        with open(yaml_path, "r") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return {}
    except Exception:
        return {}


class Config:
    # Configuration class for loading from env vars and YAML.

    def __init__(self, env_file: str = ".env", yaml_file: str = "greenmining.yaml"):
        # Initialize configuration from environment and YAML file.
        # Load environment variables
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()  # Load from system environment

        # Load YAML config (takes precedence for certain options)
        yaml_path = Path(yaml_file)
        self._yaml_config = _load_yaml_config(yaml_path)

        # GitHub API Configuration
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        if not self.GITHUB_TOKEN or self.GITHUB_TOKEN == "your_github_pat_here":
            raise ValueError("GITHUB_TOKEN not set. Please set it in .env file or environment.")

        # Analysis Type
        self.ANALYSIS_TYPE = "keyword_heuristic"

        # Search and Processing Configuration (YAML: sources.search.keywords)
        yaml_search = self._yaml_config.get("sources", {}).get("search", {})
        self.GITHUB_SEARCH_KEYWORDS = yaml_search.get(
            "keywords", ["microservices", "microservice-architecture", "cloud-native"]
        )

        # Supported Languages (YAML: sources.search.languages)
        self.SUPPORTED_LANGUAGES = yaml_search.get(
            "languages",
            [
                "Java",
                "Python",
                "Go",
                "JavaScript",
                "TypeScript",
                "C#",
                "Rust",
            ],
        )

        # Repository and Commit Limits (YAML: extraction.*)
        yaml_extraction = self._yaml_config.get("extraction", {})
        self.MIN_STARS = yaml_search.get("min_stars", int(os.getenv("MIN_STARS", "100")))
        self.MAX_REPOS = int(os.getenv("MAX_REPOS", "100"))
        self.COMMITS_PER_REPO = yaml_extraction.get(
            "max_commits", int(os.getenv("COMMITS_PER_REPO", "50"))
        )
        self.DAYS_BACK = yaml_extraction.get("days_back", int(os.getenv("DAYS_BACK", "730")))
        self.SKIP_MERGES = yaml_extraction.get("skip_merges", True)

        # Analysis Configuration (YAML: analysis.*)
        yaml_analysis = self._yaml_config.get("analysis", {})
        self.ENABLE_NLP_ANALYSIS = os.getenv("ENABLE_NLP_ANALYSIS", "false").lower() == "true"
        self.ENABLE_TEMPORAL_ANALYSIS = (
            os.getenv("ENABLE_TEMPORAL_ANALYSIS", "false").lower() == "true"
        )
        self.TEMPORAL_GRANULARITY = os.getenv("TEMPORAL_GRANULARITY", "quarter")
        self.ENABLE_ML_FEATURES = os.getenv("ENABLE_ML_FEATURES", "false").lower() == "true"
        self.VALIDATION_SAMPLE_SIZE = int(os.getenv("VALIDATION_SAMPLE_SIZE", "30"))

        # PyDriller options (YAML: analysis.process_metrics, etc.)
        self.PROCESS_METRICS_ENABLED = yaml_analysis.get(
            "process_metrics", os.getenv("PROCESS_METRICS_ENABLED", "true").lower() == "true"
        )
        self.STRUCTURAL_METRICS_ENABLED = yaml_analysis.get(
            "structural_metrics", os.getenv("STRUCTURAL_METRICS_ENABLED", "true").lower() == "true"
        )
        self.DMM_ENABLED = yaml_analysis.get(
            "delta_maintainability", os.getenv("DMM_ENABLED", "true").lower() == "true"
        )

        # Temporal Filtering
        self.CREATED_AFTER = os.getenv("CREATED_AFTER")
        self.CREATED_BEFORE = os.getenv("CREATED_BEFORE")
        self.PUSHED_AFTER = os.getenv("PUSHED_AFTER")
        self.PUSHED_BEFORE = os.getenv("PUSHED_BEFORE")
        self.COMMIT_DATE_FROM = os.getenv("COMMIT_DATE_FROM")
        self.COMMIT_DATE_TO = os.getenv("COMMIT_DATE_TO")
        self.MIN_COMMITS = int(os.getenv("MIN_COMMITS", "0"))
        self.ACTIVITY_WINDOW_DAYS = int(os.getenv("ACTIVITY_WINDOW_DAYS", "730"))

        # Analysis Configuration
        self.BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

        # Processing Configuration
        self.TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.RETRY_DELAY = 2
        self.EXPONENTIAL_BACKOFF = True

        # Output Configuration (YAML: output.directory)
        yaml_output = self._yaml_config.get("output", {})
        self.OUTPUT_DIR = Path(yaml_output.get("directory", os.getenv("OUTPUT_DIR", "./data")))
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # File Paths
        self.REPOS_FILE = self.OUTPUT_DIR / "repositories.json"
        self.COMMITS_FILE = self.OUTPUT_DIR / "commits.json"
        self.ANALYSIS_FILE = self.OUTPUT_DIR / "analysis_results.json"
        self.AGGREGATED_FILE = self.OUTPUT_DIR / "aggregated_statistics.json"
        self.CSV_FILE = self.OUTPUT_DIR / "green_analysis_results.csv"
        self.REPORT_FILE = self.OUTPUT_DIR / "green_microservices_analysis.md"
        self.CHECKPOINT_FILE = self.OUTPUT_DIR / "checkpoint.json"

        # Direct Repository URL Support (YAML: sources.urls)
        yaml_urls = self._yaml_config.get("sources", {}).get("urls", [])
        env_urls = self._parse_repository_urls(os.getenv("REPOSITORY_URLS", ""))
        self.REPOSITORY_URLS: List[str] = yaml_urls if yaml_urls else env_urls

        # Clone path (YAML: extraction.clone_path)
        self.CLONE_PATH = Path(
            yaml_extraction.get("clone_path", os.getenv("CLONE_PATH", "/tmp/greenmining_repos"))
        )
        self.CLEANUP_AFTER_ANALYSIS = os.getenv("CLEANUP_AFTER_ANALYSIS", "true").lower() == "true"

        # Energy Measurement (YAML: energy.*)
        yaml_energy = self._yaml_config.get("energy", {})
        self.ENERGY_ENABLED = yaml_energy.get(
            "enabled", os.getenv("ENERGY_ENABLED", "false").lower() == "true"
        )
        self.ENERGY_BACKEND = yaml_energy.get("backend", os.getenv("ENERGY_BACKEND", "rapl"))
        self.CARBON_TRACKING = yaml_energy.get(
            "carbon_tracking", os.getenv("CARBON_TRACKING", "false").lower() == "true"
        )
        self.COUNTRY_ISO = yaml_energy.get("country_iso", os.getenv("COUNTRY_ISO", "USA"))

        # Power profiling (YAML: energy.power_profiling.*)
        yaml_power = yaml_energy.get("power_profiling", {})
        self.POWER_PROFILING_ENABLED = yaml_power.get("enabled", False)
        self.POWER_TEST_COMMAND = yaml_power.get("test_command", None)
        self.POWER_REGRESSION_THRESHOLD = yaml_power.get("regression_threshold", 5.0)

        # Logging
        self.VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"
        self.LOG_FILE = self.OUTPUT_DIR / "mining.log"

    def _parse_repository_urls(self, urls_str: str) -> List[str]:
        # Parse comma-separated repository URLs from environment variable.
        if not urls_str:
            return []
        return [url.strip() for url in urls_str.split(",") if url.strip()]

    def validate(self) -> bool:
        # Validate that all required configuration is present.
        required_attrs = ["GITHUB_TOKEN", "MAX_REPOS", "COMMITS_PER_REPO"]

        for attr in required_attrs:
            if not getattr(self, attr, None):
                raise ValueError(f"Missing required configuration: {attr}")

        return True

    def __repr__(self) -> str:
        # String representation of configuration (hiding sensitive data).
        return (
            f"Config("
            f"MAX_REPOS={self.MAX_REPOS}, "
            f"COMMITS_PER_REPO={self.COMMITS_PER_REPO}, "
            f"BATCH_SIZE={self.BATCH_SIZE}, "
            f"OUTPUT_DIR={self.OUTPUT_DIR}"
            f")"
        )


# Global config instance
_config_instance = None


def get_config(env_file: str = ".env") -> Config:
    # Get or create global configuration instance.
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(env_file)
    return _config_instance
