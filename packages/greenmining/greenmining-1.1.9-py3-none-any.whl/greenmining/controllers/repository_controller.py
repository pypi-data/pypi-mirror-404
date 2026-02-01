# Repository Controller - Handles repository fetching + cloning operations.
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict

from greenmining.config import Config
from greenmining.models.repository import Repository
from greenmining.services.github_graphql_fetcher import GitHubGraphQLFetcher
from greenmining.utils import colored_print, load_json_file, save_json_file


class RepositoryController:
    # Controller for GitHub repository operations using GraphQL API.

    def __init__(self, config: Config):
        # Initialize controller with configuration.
        self.config = config
        self.graphql_fetcher = GitHubGraphQLFetcher(config.GITHUB_TOKEN)
        self.repos_dir = Path.cwd() / "greenmining_repos"

    def _sanitize_repo_name(self, repo: Repository, index: int = 0) -> str:
        """Safe unique dir name: owner_repo[_index]. Handles case collisions."""
        base = re.sub(r'[^a-z0-9-]', '_', repo.full_name.replace('/', '_').lower())
        name = f"{base}_{index}" if index else base
        path = self.repos_dir / name
        counter = 1
        while path.exists():
            name = f"{base}_{counter}"
            path = self.repos_dir / name
            counter += 1
        return name

    def clone_repositories(
        self, 
        repositories: List[Repository], 
        github_token: str = None,
        cleanup: bool = True,
        depth: int = 1  # Shallow clone
    ) -> List[Dict]:
        """Clone repos to ./greenmining_repos/ with unique sanitized names."""
        self.repos_dir.mkdir(exist_ok=True)
        if cleanup:
            shutil.rmtree(self.repos_dir, ignore_errors=True)
            self.repos_dir.mkdir(exist_ok=True)
            colored_print(f"Cleaned {self.repos_dir}", "yellow")

        results = []
        for i, repo in enumerate(repositories, 1):
            safe_name = self._sanitize_repo_name(repo, i)
            clone_path = self.repos_dir / safe_name
            
            colored_print(f"[{i}/{len(repositories)}] Cloning {repo.full_name} → {safe_name}", "cyan")
            
            url = f"https://{github_token}@github.com/{repo.full_name}.git" if github_token else repo.url
            cmd = ["git", "clone", f"--depth={depth}", "-v", url, str(clone_path)]
            
            import subprocess
            try:
                subprocess.check_call(cmd, cwd=self.repos_dir.parent)
                colored_print(f"{safe_name}", "green")
                results.append({
                    "full_name": repo.full_name,
                    "local_path": str(clone_path),
                    "success": True
                })
            except subprocess.CalledProcessError as e:
                colored_print(f"{safe_name}: {e}", "red")
                results.append({
                    "full_name": repo.full_name,
                    "local_path": str(clone_path),
                    "success": False,
                    "error": str(e)
                })

        # Save map for analyze_repositories
        save_json_file(results, self.repos_dir / "clone_results.json")
        success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
        colored_print(f"Cloned: {success_rate:.1f}% ({self.repos_dir}/clone_results.json)", "green")
        return results





    def fetch_repositories(self, max_repos: int = None, min_stars: int = None,
                          languages: list[str] = None, keywords: str = None,
                          created_after: str = None, created_before: str = None,
                          pushed_after: str = None, pushed_before: str = None) -> list[Repository]:
        # Fetch repositories from GitHub using GraphQL API.
        max_repos = max_repos or self.config.MAX_REPOS
        min_stars = min_stars or self.config.MIN_STARS
        languages = languages or self.config.SUPPORTED_LANGUAGES
        keywords = keywords 

        colored_print(f"Fetching up to {max_repos} repositories...", "cyan")
        colored_print(f"   Keywords: {keywords}", "cyan")
        colored_print(f"   Filters: min_stars={min_stars}", "cyan")

        if created_after or created_before:
            colored_print(
                f"   Created: {created_after or 'any'} to {created_before or 'any'}", "cyan"
            )
        if pushed_after or pushed_before:
            colored_print(f"   Pushed: {pushed_after or 'any'} to {pushed_before or 'any'}", "cyan")

        try:
            # Execute GraphQL search
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

            # Save to file
            repo_dicts = [r.to_dict() for r in repositories]
            save_json_file(repo_dicts, self.config.REPOS_FILE)

            colored_print(f"Fetched {len(repositories)} repositories", "green")
            colored_print(f"   Saved to: {self.config.REPOS_FILE}", "cyan")

            return repositories

        except Exception as e:
            colored_print(f"Error fetching repositories: {e}", "red")
            raise

    def load_repositories(self) -> list[Repository]:
        # Load repositories from file.
        if not self.config.REPOS_FILE.exists():
            raise FileNotFoundError(f"No repositories file found at {self.config.REPOS_FILE}")

        repo_dicts = load_json_file(self.config.REPOS_FILE)
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
