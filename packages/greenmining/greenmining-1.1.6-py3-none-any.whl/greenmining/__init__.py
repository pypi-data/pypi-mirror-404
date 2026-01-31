# Green Microservices Mining - GSF Pattern Analysis Tool.

from greenmining.config import Config
from greenmining.controllers.repository_controller import RepositoryController
from greenmining.gsf_patterns import (
    GREEN_KEYWORDS,
    GSF_PATTERNS,
    get_pattern_by_keywords,
    is_green_aware,
)

__version__ = "1.1.6"


def fetch_repositories(
    github_token: str,
    max_repos: int = None,
    min_stars: int = None,
    languages: list = None,
    keywords: str = None,
    created_after: str = None,
    created_before: str = None,
    pushed_after: str = None,
    pushed_before: str = None,
):
    # Fetch repositories from GitHub with custom search keywords.
    config = Config()
    config.GITHUB_TOKEN = github_token
    controller = RepositoryController(config)

    return controller.fetch_repositories(
        max_repos=max_repos,
        min_stars=min_stars,
        languages=languages,
        keywords=keywords,
        created_after=created_after,
        created_before=created_before,
        pushed_after=pushed_after,
        pushed_before=pushed_before,
    )


def analyze_repositories(
    urls: list,
    max_commits: int = 500,
    parallel_workers: int = 1,
    output_format: str = "dict",
    energy_tracking: bool = False,
    energy_backend: str = "rapl",
    method_level_analysis: bool = False,
    include_source_code: bool = False,
    ssh_key_path: str = None,
    github_token: str = None,
    since_date: str = None,
    to_date: str = None,
):
    # Analyze multiple repositories from URLs.
    # Args:
    #   urls: List of GitHub repository URLs
    #   max_commits: Maximum commits to analyze per repository
    #   parallel_workers: Number of parallel analysis workers (1=sequential)
    #   output_format: Output format (dict, json, csv)
    #   energy_tracking: Enable automatic energy measurement during analysis
    #   energy_backend: Energy backend (rapl, codecarbon, cpu_meter, auto)
    #   method_level_analysis: Include per-method metrics via Lizard
    #   include_source_code: Include source code before/after in results
    #   ssh_key_path: SSH key path for private repositories
    #   github_token: GitHub token for private HTTPS repositories
    #   since_date: Analyze commits from this date (YYYY-MM-DD string)
    #   to_date: Analyze commits up to this date (YYYY-MM-DD string)
    from greenmining.services.local_repo_analyzer import LocalRepoAnalyzer

    kwargs = {}
    if since_date:
        from datetime import datetime

        kwargs["since_date"] = datetime.strptime(since_date, "%Y-%m-%d")
    if to_date:
        from datetime import datetime

        kwargs["to_date"] = datetime.strptime(to_date, "%Y-%m-%d")

    analyzer = LocalRepoAnalyzer(
        max_commits=max_commits,
        energy_tracking=energy_tracking,
        energy_backend=energy_backend,
        method_level_analysis=method_level_analysis,
        include_source_code=include_source_code,
        ssh_key_path=ssh_key_path,
        github_token=github_token,
        **kwargs,
    )

    return analyzer.analyze_repositories(
        urls=urls,
        parallel_workers=parallel_workers,
        output_format=output_format,
    )


__all__ = [
    "Config",
    "GSF_PATTERNS",
    "GREEN_KEYWORDS",
    "is_green_aware",
    "get_pattern_by_keywords",
    "fetch_repositories",
    "analyze_repositories",
    "__version__",
]
