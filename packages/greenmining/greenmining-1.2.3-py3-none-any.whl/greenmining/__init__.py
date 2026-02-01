# GreenMining - MSR library for Green IT research.

from greenmining.controllers.repository_controller import RepositoryController
from greenmining.gsf_patterns import (
    GREEN_KEYWORDS,
    GSF_PATTERNS,
    get_pattern_by_keywords,
    is_green_aware,
)

__version__ = "1.2.3"


def fetch_repositories(
    github_token: str,
    max_repos: int = 100,
    min_stars: int = 100,
    languages: list = None,
    keywords: str = None,
    created_after: str = None,
    created_before: str = None,
    pushed_after: str = None,
    pushed_before: str = None,
    output_dir: str = "./data",
):
    # Fetch repositories from GitHub via GraphQL search.
    controller = RepositoryController(github_token, output_dir=output_dir)

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


def clone_repositories(
    repositories: list,
    github_token: str = None,
    output_dir: str = "./data",
    cleanup_existing: bool = False,
):
    # Clone repositories into ./greenmining_repos with sanitized directory names.
    # Args:
    #   repositories: List of Repository objects (from fetch_repositories)
    #   github_token: GitHub token (required for controller init)
    #   output_dir: Output directory for metadata files
    #   cleanup_existing: Remove existing greenmining_repos/ before cloning
    token = github_token or "unused"
    controller = RepositoryController(token, output_dir=output_dir)

    return controller.clone_repositories(
        repositories=repositories,
        cleanup_existing=cleanup_existing,
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
    cleanup_after: bool = True,
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
        cleanup_after=cleanup_after,
        **kwargs,
    )

    return analyzer.analyze_repositories(
        urls=urls,
        parallel_workers=parallel_workers,
        output_format=output_format,
    )


__all__ = [
    "GSF_PATTERNS",
    "GREEN_KEYWORDS",
    "is_green_aware",
    "get_pattern_by_keywords",
    "fetch_repositories",
    "clone_repositories",
    "analyze_repositories",
    "__version__",
]
