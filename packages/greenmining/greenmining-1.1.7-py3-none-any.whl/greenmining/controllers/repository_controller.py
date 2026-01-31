# Repository Controller - Handles repository fetching operations.

from tqdm import tqdm

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

    def fetch_repositories(
        self,
        max_repos: int = None,
        min_stars: int = None,
        languages: list[str] = None,
        keywords: str = None,
        created_after: str = None,
        created_before: str = None,
        pushed_after: str = None,
        pushed_before: str = None,
    ) -> list[Repository]:
        # Fetch repositories from GitHub using GraphQL API.
        max_repos = max_repos or self.config.MAX_REPOS
        min_stars = min_stars or self.config.MIN_STARS
        languages = languages or self.config.SUPPORTED_LANGUAGES
        keywords = keywords or "microservices"

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
