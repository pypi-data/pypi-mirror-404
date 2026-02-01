import os
from pathlib import Path
from typing import Any, Dict, List

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
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        # Load YAML config
        yaml_path = Path(yaml_file)
        self._yaml_config = _load_yaml_config(yaml_path)

        # GitHub API Configuration
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        if not self.GITHUB_TOKEN or self.GITHUB_TOKEN == "your_github_pat_here":
            raise ValueError("GITHUB_TOKEN not set. Please set it in .env file or environment.")

        # Search Configuration (YAML: sources.search.*)
        yaml_search = self._yaml_config.get("sources", {}).get("search", {})

        self.SUPPORTED_LANGUAGES: List[str] = yaml_search.get(
            "languages",
            [
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "C++",
                "C#",
                "Go",
                "Rust",
                "PHP",
                "Ruby",
                "Swift",
                "Kotlin",
                "Scala",
                "R",
                "MATLAB",
                "Dart",
                "Lua",
                "Perl",
                "Haskell",
                "Elixir",
            ],
        )

        # Repository Limits
        self.MIN_STARS = yaml_search.get("min_stars", int(os.getenv("MIN_STARS", "100")))
        self.MAX_REPOS = int(os.getenv("MAX_REPOS", "100"))

        # Output Configuration (YAML: output.directory)
        yaml_output = self._yaml_config.get("output", {})
        self.OUTPUT_DIR = Path(yaml_output.get("directory", os.getenv("OUTPUT_DIR", "./data")))
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # File Paths
        self.REPOS_FILE = self.OUTPUT_DIR / "repositories.json"

    def __repr__(self) -> str:
        # String representation of configuration (hiding sensitive data).
        return (
            f"Config("
            f"MAX_REPOS={self.MAX_REPOS}, "
            f"OUTPUT_DIR={self.OUTPUT_DIR}"
            f")"
        )
