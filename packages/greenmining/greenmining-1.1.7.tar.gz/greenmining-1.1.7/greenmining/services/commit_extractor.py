# Commit extractor for green microservices mining.

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from github import Github
from tqdm import tqdm

from greenmining.config import get_config
from greenmining.models.repository import Repository
from greenmining.utils import (
    colored_print,
    format_timestamp,
    load_json_file,
    print_banner,
    retry_on_exception,
    save_json_file,
)


class CommitExtractor:
    # Extracts commit data from repositories using GitHub API.

    def __init__(
        self,
        max_commits: int = 50,
        skip_merges: bool = True,
        days_back: int = 730,
        github_token: str | None = None,
        timeout: int = 60,
    ):
        # Initialize commit extractor.
        self.max_commits = max_commits
        self.skip_merges = skip_merges
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.github = Github(github_token) if github_token else None
        self.timeout = timeout

    def extract_from_repositories(
        self, repositories: list[dict[str, Any] | Repository]
    ) -> list[dict[str, Any]]:
        # Extract commits from list of repositories.
        all_commits = []
        failed_repos = []

        colored_print(f"\nExtracting commits from {len(repositories)} repositories...", "cyan")
        colored_print(
            f"Settings: max_commits={self.max_commits}, skip_merges={self.skip_merges}, days_back={self.days_back}",
            "cyan",
        )

        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Repository extraction timeout")

        with tqdm(total=len(repositories), desc="Processing repositories", unit="repo") as pbar:
            for repo in repositories:
                try:
                    # Set timeout alarm
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(self.timeout)

                    commits = self._extract_repo_commits(repo)
                    all_commits.extend(commits)

                    # Cancel alarm
                    signal.alarm(0)

                    pbar.set_postfix({"commits": len(all_commits), "failed": len(failed_repos)})
                    pbar.update(1)
                except TimeoutError:
                    signal.alarm(0)  # Cancel alarm
                    repo_name = (
                        repo.full_name if isinstance(repo, Repository) else repo["full_name"]
                    )
                    colored_print(f"\nTimeout processing {repo_name} (>{self.timeout}s)", "yellow")
                    failed_repos.append(repo_name)
                    pbar.update(1)
                except Exception as e:
                    signal.alarm(0)  # Cancel alarm
                    repo_name = (
                        repo.full_name if isinstance(repo, Repository) else repo["full_name"]
                    )
                    colored_print(f"\nError processing {repo_name}: {e}", "yellow")
                    failed_repos.append(repo_name)
                    pbar.update(1)

        if failed_repos:
            colored_print(f"\nFailed to process {len(failed_repos)} repositories:", "yellow")
            for repo_name in failed_repos[:5]:
                colored_print(f"  - {repo_name}", "yellow")
            if len(failed_repos) > 5:
                colored_print(f"  ... and {len(failed_repos) - 5} more", "yellow")

        return all_commits

    @retry_on_exception(max_retries=2, delay=5.0, exceptions=(Exception,))
    def _extract_repo_commits(self, repo: dict[str, Any]) -> list[dict[str, Any]]:
        # Extract commits from a single repository using GitHub API.
        commits = []
        # Handle both Repository objects and dicts
        repo_name = repo.full_name if isinstance(repo, Repository) else repo["full_name"]

        try:
            # Get repository from GitHub API
            if not self.github:
                config = get_config()
                self.github = Github(config.GITHUB_TOKEN)

            gh_repo = self.github.get_repo(repo_name)

            # Get recent commits (GitHub API returns in reverse chronological order)
            commit_count = 0

            for commit in gh_repo.get_commits():
                # Skip if reached max commits
                if commit_count >= self.max_commits:
                    break

                # Skip merge commits if requested
                if self.skip_merges and len(commit.parents) > 1:
                    continue

                # Skip trivial commits
                commit_msg = commit.commit.message
                if not commit_msg or len(commit_msg.strip()) < 10:
                    continue

                # Extract commit data
                commit_data = self._extract_commit_metadata_from_github(commit, repo_name)
                commits.append(commit_data)
                commit_count += 1

        except Exception as e:
            colored_print(f"Error extracting commits from {repo_name}: {e}", "yellow")
            raise

        return commits

    def _extract_commit_metadata(self, commit, repo_name: str) -> dict[str, Any]:
        # Extract metadata from commit object.
        # Get modified files
        files_changed = []
        lines_added = 0
        lines_deleted = 0

        try:
            for modified_file in commit.modified_files:
                files_changed.append(modified_file.filename)
                lines_added += modified_file.added_lines
                lines_deleted += modified_file.deleted_lines
        except Exception:
            pass

        return {
            "commit_id": commit.hash,
            "repo_name": repo_name,
            "date": commit.committer_date.isoformat(),
            "author": commit.author.name,
            "author_email": commit.author.email,
            "message": commit.msg.strip(),
            "files_changed": files_changed[:20],  # Limit to 20 files
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "insertions": lines_added,
            "deletions": lines_deleted,
            "is_merge": commit.merge,
            "branches": (
                list(commit.branches) if hasattr(commit, "branches") and commit.branches else []
            ),
            "in_main_branch": commit.in_main_branch if hasattr(commit, "in_main_branch") else True,
        }

    def _extract_commit_metadata_from_github(self, commit, repo_name: str) -> dict[str, Any]:
        # Extract metadata from GitHub API commit object.
        # Get modified files and stats
        files_changed = []
        lines_added = 0
        lines_deleted = 0

        try:
            for file in commit.files:
                files_changed.append(file.filename)
                lines_added += file.additions
                lines_deleted += file.deletions
        except Exception:
            pass

        return {
            "commit_id": commit.sha,
            "repo_name": repo_name,
            "date": commit.commit.committer.date.isoformat(),
            "author": commit.commit.author.name,
            "author_email": commit.commit.author.email,
            "message": commit.commit.message.strip(),
            "files_changed": files_changed[:20],  # Limit to 20 files
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "insertions": lines_added,
            "deletions": lines_deleted,
            "is_merge": len(commit.parents) > 1,
            "branches": [],
            "in_main_branch": True,
        }

    def save_results(self, commits: list[dict[str, Any]], output_file: Path, repos_count: int):
        # Save extracted commits to JSON file.
        data = {
            "metadata": {
                "extracted_at": format_timestamp(),
                "total_commits": len(commits),
                "total_repos": repos_count,
                "max_commits_per_repo": self.max_commits,
                "skip_merges": self.skip_merges,
                "days_back": self.days_back,
                "cutoff_date": self.cutoff_date.isoformat(),
            },
            "commits": commits,
        }

        save_json_file(data, output_file)
        colored_print(f"Saved {len(commits)} commits to {output_file}", "green")
