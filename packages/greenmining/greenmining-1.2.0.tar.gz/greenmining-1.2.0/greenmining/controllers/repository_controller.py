# Repository Controller - Handles repository fetching + cloning operations.

import re
import shutil
from pathlib import Path

from greenmining.models.repository import Repository
from greenmining.services.github_graphql_fetcher import GitHubGraphQLFetcher
from greenmining.utils import colored_print, load_json_file, save_json_file


class RepositoryController:
    # Controller for GitHub repository operations using GraphQL API.

    def __init__(self, github_token: str, output_dir: str = "./data"):
        # Initialize controller with GitHub token and output directory.
        self.graphql_fetcher = GitHubGraphQLFetcher(github_token)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repos_file = self.output_dir / "repositories.json"
        self.repos_dir = Path.cwd() / "greenmining_repos"

    def fetch_repositories(
        self,
        max_repos: int = 100,
        min_stars: int = 100,
        languages: list[str] = None,
        keywords: str = None,
        created_after: str = None,
        created_before: str = None,
        pushed_after: str = None,
        pushed_before: str = None,
    ) -> list[Repository]:
        # Fetch repositories from GitHub using GraphQL API.
        colored_print(f"Fetching up to {max_repos} repositories...", "cyan")
        colored_print(f"   Keywords: {keywords}", "cyan")
        colored_print(f"   Filters: min_stars={min_stars}", "cyan")

        if created_after or created_before:
            colored_print(
                f"   Created: {created_after or 'any'} to {created_before or 'any'}", "cyan"
            )
        if pushed_after or pushed_before:
            colored_print(
                f"   Pushed: {pushed_after or 'any'} to {pushed_before or 'any'}", "cyan"
            )

        try:
            repositories = self.graphql_fetcher.search_repositories(
                keywords=keywords,
                max_repos=max_repos,
                min_stars=min_stars,
                languages=languages,
                created_after=created_after,
                created_before=created_before,
                pushed_after=pushed_after,
                pushed_before=pushed_before,
            )

            repo_dicts = [r.to_dict() for r in repositories]
            save_json_file(repo_dicts, self.repos_file)

            colored_print(f"Fetched {len(repositories)} repositories", "green")
            colored_print(f"   Saved to: {self.repos_file}", "cyan")

            return repositories

        except Exception as e:
            colored_print(f"Error fetching repositories: {e}", "red")
            raise

    def clone_repositories(
        self,
        repositories: list[Repository],
        cleanup_existing: bool = False,
    ) -> list[Path]:
        # Clone repositories into ./greenmining_repos with sanitized directory names.
        self.repos_dir.mkdir(parents=True, exist_ok=True)

        if cleanup_existing and self.repos_dir.exists():
            shutil.rmtree(self.repos_dir)
            self.repos_dir.mkdir(parents=True, exist_ok=True)

        cloned_paths = []
        colored_print(f"\nCloning {len(repositories)} repositories into {self.repos_dir}", "cyan")

        for repo in repositories:
            safe_name = self._sanitize_repo_name(repo)
            local_path = self.repos_dir / safe_name

            if local_path.exists():
                colored_print(f"   Already exists: {safe_name}", "yellow")
                cloned_paths.append(local_path)
                continue

            try:
                url = repo.url if hasattr(repo, "url") else f"https://github.com/{repo.full_name}"
                colored_print(f"   Cloning {repo.full_name} -> {safe_name}", "cyan")

                import subprocess

                subprocess.run(
                    ["git", "clone", "--depth", "1", url, str(local_path)],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=120,
                )
                cloned_paths.append(local_path)
                colored_print(f"   Cloned: {safe_name}", "green")

            except Exception as e:
                colored_print(f"   Failed to clone {repo.full_name}: {e}", "yellow")

        colored_print(f"Cloned {len(cloned_paths)}/{len(repositories)} repositories", "green")
        return cloned_paths

    def _sanitize_repo_name(self, repo: Repository) -> str:
        # Safe unique directory name: owner_repo. Handles case collisions.
        base = re.sub(r"[^a-z0-9-]", "_", repo.full_name.replace("/", "_").lower())
        path = self.repos_dir / base
        if not path.exists():
            return base
        counter = 1
        while (self.repos_dir / f"{base}_{counter}").exists():
            counter += 1
        return f"{base}_{counter}"

    def load_repositories(self) -> list[Repository]:
        # Load repositories from file.
        if not self.repos_file.exists():
            raise FileNotFoundError(f"No repositories file found at {self.repos_file}")

        repo_dicts = load_json_file(self.repos_file)
        return [Repository.from_dict(r) for r in repo_dicts]

    def get_repository_stats(self, repositories: list[Repository]) -> dict:
        # Get statistics about fetched repositories.
        if not repositories:
            return {}

        return {
            "total": len(repositories),
            "by_language": self._count_by_language(repositories),
            "total_stars": sum(r.stars for r in repositories),
            "avg_stars": sum(r.stars for r in repositories) / len(repositories),
            "top_repo": max(repositories, key=lambda r: r.stars).full_name,
        }

    def _count_by_language(self, repositories: list[Repository]) -> dict:
        # Count repositories by language.
        counts = {}
        for repo in repositories:
            lang = repo.language or "Unknown"
            counts[lang] = counts.get(lang, 0) + 1
        return counts
