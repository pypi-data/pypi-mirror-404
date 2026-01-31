# Local repository analyzer for direct GitHub URL analysis using PyDriller.

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator

from pydriller import Repository
from pydriller.metrics.process.change_set import ChangeSet
from pydriller.metrics.process.code_churn import CodeChurn
from pydriller.metrics.process.commits_count import CommitsCount
from pydriller.metrics.process.contributors_count import ContributorsCount
from pydriller.metrics.process.contributors_experience import ContributorsExperience
from pydriller.metrics.process.history_complexity import HistoryComplexity
from pydriller.metrics.process.hunks_count import HunksCount
from pydriller.metrics.process.lines_count import LinesCount

from greenmining.gsf_patterns import get_pattern_by_keywords, is_green_aware, GSF_PATTERNS
from greenmining.utils import colored_print


@dataclass
class MethodMetrics:
    # Per-method analysis metrics from Lizard integration.

    name: str
    long_name: str
    filename: str
    nloc: int = 0
    complexity: int = 0
    token_count: int = 0
    parameters: int = 0
    start_line: int = 0
    end_line: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "long_name": self.long_name,
            "filename": self.filename,
            "nloc": self.nloc,
            "complexity": self.complexity,
            "token_count": self.token_count,
            "parameters": self.parameters,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


@dataclass
class SourceCodeChange:
    # Source code before/after a commit for refactoring detection.

    filename: str
    source_code_before: Optional[str] = None
    source_code_after: Optional[str] = None
    diff: Optional[str] = None
    added_lines: int = 0
    deleted_lines: int = 0
    change_type: str = ""  # ADD, DELETE, MODIFY, RENAME

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "source_code_before": self.source_code_before,
            "source_code_after": self.source_code_after,
            "diff": self.diff,
            "added_lines": self.added_lines,
            "deleted_lines": self.deleted_lines,
            "change_type": self.change_type,
        }


@dataclass
class CommitAnalysis:
    # Analysis result for a single commit.

    hash: str
    message: str
    author: str
    author_email: str
    date: datetime
    green_aware: bool
    gsf_patterns_matched: List[str]
    pattern_count: int
    pattern_details: List[Dict[str, Any]]
    confidence: str
    files_modified: List[str]
    insertions: int
    deletions: int

    # PyDriller DMM metrics
    dmm_unit_size: Optional[float] = None
    dmm_unit_complexity: Optional[float] = None
    dmm_unit_interfacing: Optional[float] = None

    # Structural metrics (Lizard)
    total_nloc: int = 0
    total_complexity: int = 0
    max_complexity: int = 0
    methods_count: int = 0

    # Method-level analysis (Phase 3.2)
    methods: List[MethodMetrics] = field(default_factory=list)

    # Source code access (Phase 3.3)
    source_changes: List[SourceCodeChange] = field(default_factory=list)

    # Energy metrics (Phase 2.2 - populated when energy_tracking=True)
    energy_joules: Optional[float] = None
    energy_watts_avg: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary.
        result = {
            "commit_hash": self.hash,
            "message": self.message,
            "author": self.author,
            "author_email": self.author_email,
            "date": self.date.isoformat() if self.date else None,
            "green_aware": self.green_aware,
            "gsf_patterns_matched": self.gsf_patterns_matched,
            "pattern_count": self.pattern_count,
            "pattern_details": self.pattern_details,
            "confidence": self.confidence,
            "files_modified": self.files_modified,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "dmm_unit_size": self.dmm_unit_size,
            "dmm_unit_complexity": self.dmm_unit_complexity,
            "dmm_unit_interfacing": self.dmm_unit_interfacing,
            "total_nloc": self.total_nloc,
            "total_complexity": self.total_complexity,
            "max_complexity": self.max_complexity,
            "methods_count": self.methods_count,
        }

        if self.methods:
            result["methods"] = [m.to_dict() for m in self.methods]

        if self.source_changes:
            result["source_changes"] = [s.to_dict() for s in self.source_changes]

        if self.energy_joules is not None:
            result["energy_joules"] = self.energy_joules
            result["energy_watts_avg"] = self.energy_watts_avg

        return result


@dataclass
class RepositoryAnalysis:
    # Complete analysis result for a repository.

    url: str
    name: str
    total_commits: int
    green_commits: int
    green_commit_rate: float
    commits: List[CommitAnalysis] = field(default_factory=list)
    process_metrics: Dict[str, Any] = field(default_factory=dict)
    energy_metrics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary.
        result = {
            "url": self.url,
            "name": self.name,
            "total_commits": self.total_commits,
            "green_commits": self.green_commits,
            "green_commit_rate": self.green_commit_rate,
            "commits": [c.to_dict() for c in self.commits],
            "process_metrics": self.process_metrics,
        }
        if self.energy_metrics:
            result["energy_metrics"] = self.energy_metrics
        return result


class LocalRepoAnalyzer:
    # Analyze repositories directly from GitHub URLs using PyDriller.
    # Supports HTTPS URLs, SSH URLs, and private repositories.

    def __init__(
        self,
        clone_path: Optional[Path] = None,
        max_commits: int = 500,
        days_back: int = 730,
        skip_merges: bool = True,
        compute_process_metrics: bool = True,
        cleanup_after: bool = True,
        ssh_key_path: Optional[str] = None,
        github_token: Optional[str] = None,
        energy_tracking: bool = False,
        energy_backend: str = "rapl",
        method_level_analysis: bool = False,
        include_source_code: bool = False,
        process_metrics: str = "standard",
        since_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ):
        # Initialize the local repository analyzer.
        # Args:
        #   clone_path: Directory to clone repos into
        #   max_commits: Maximum commits to analyze per repo
        #   days_back: How far back to analyze
        #   skip_merges: Skip merge commits
        #   compute_process_metrics: Compute PyDriller process metrics
        #   cleanup_after: Remove cloned repos after analysis
        #   ssh_key_path: Path to SSH private key for private repos
        #   github_token: GitHub token for private HTTPS repos
        #   energy_tracking: Enable automatic energy measurement
        #   energy_backend: Energy measurement backend (rapl, codecarbon)
        #   method_level_analysis: Extract per-method metrics via Lizard
        #   include_source_code: Include source code before/after in results
        #   process_metrics: "standard" or "full" PyDriller process metrics
        self.clone_path = clone_path or Path(tempfile.gettempdir()) / "greenmining_repos"
        self.clone_path.mkdir(parents=True, exist_ok=True)
        self.max_commits = max_commits
        self.days_back = days_back
        self.since_date = since_date
        self.to_date = to_date
        self.skip_merges = skip_merges
        self.compute_process_metrics = compute_process_metrics
        self.cleanup_after = cleanup_after
        self.gsf_patterns = GSF_PATTERNS

        # Phase 1.3: Private repository support
        self.ssh_key_path = ssh_key_path
        self.github_token = github_token

        # Phase 2.2: Integrated energy tracking
        self.energy_tracking = energy_tracking
        self.energy_backend = energy_backend
        self._energy_meter = None
        if energy_tracking:
            self._init_energy_meter()

        # Phase 3.2: Method-level analysis
        self.method_level_analysis = method_level_analysis

        # Phase 3.3: Source code access
        self.include_source_code = include_source_code

        # Phase 3.1: Full process metrics mode
        self.process_metrics_mode = process_metrics

    def _init_energy_meter(self):
        # Initialize the energy measurement backend.
        try:
            from greenmining.energy.base import get_energy_meter

            self._energy_meter = get_energy_meter(self.energy_backend)
        except Exception as e:
            colored_print(f"   Warning: Energy tracking unavailable: {e}", "yellow")
            self.energy_tracking = False

    def _prepare_auth_url(self, url: str) -> str:
        # Prepare authenticated URL for private repositories.
        if self.github_token and url.startswith("https://"):
            # Inject token into HTTPS URL for private repo access
            return url.replace("https://", f"https://x-access-token:{self.github_token}@")
        return url

    def _setup_ssh_env(self) -> Dict[str, str]:
        # Set up SSH environment for private repository cloning.
        env = os.environ.copy()
        if self.ssh_key_path:
            ssh_key = os.path.expanduser(self.ssh_key_path)
            if os.path.exists(ssh_key):
                env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key} -o StrictHostKeyChecking=no"
        return env

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        # Parse repository URL to extract owner and name.
        # Handle HTTPS URLs
        https_pattern = r"github\.com[/:]([^/]+)/([^/\.]+)"
        match = re.search(https_pattern, url)
        if match:
            return match.group(1), match.group(2).replace(".git", "")

        # Handle SSH URLs
        ssh_pattern = r"git@github\.com:([^/]+)/([^/\.]+)"
        match = re.search(ssh_pattern, url)
        if match:
            return match.group(1), match.group(2).replace(".git", "")

        raise ValueError(f"Could not parse GitHub URL: {url}")

    def _get_pattern_details(self, matched_patterns: List[str]) -> List[Dict[str, Any]]:
        # Get detailed pattern information.
        details = []
        for pattern_id, pattern in self.gsf_patterns.items():
            if pattern["name"] in matched_patterns:
                details.append(
                    {
                        "name": pattern["name"],
                        "category": pattern["category"],
                        "description": pattern["description"],
                        "sci_impact": pattern["sci_impact"],
                    }
                )
        return details

    def _extract_method_metrics(self, commit) -> List[MethodMetrics]:
        # Extract per-method metrics from modified files using Lizard (via PyDriller).
        methods = []
        try:
            for mod in commit.modified_files:
                if mod.methods:
                    for method in mod.methods:
                        methods.append(
                            MethodMetrics(
                                name=method.name,
                                long_name=method.long_name,
                                filename=mod.filename,
                                nloc=method.nloc,
                                complexity=method.complexity,
                                token_count=method.token_count,
                                parameters=len(method.parameters),
                                start_line=method.start_line,
                                end_line=method.end_line,
                            )
                        )
        except Exception:
            pass
        return methods

    def _extract_source_changes(self, commit) -> List[SourceCodeChange]:
        # Extract source code before/after for each modified file.
        changes = []
        try:
            for mod in commit.modified_files:
                change = SourceCodeChange(
                    filename=mod.filename,
                    source_code_before=mod.source_code_before if mod.source_code_before else None,
                    source_code_after=mod.source_code if mod.source_code else None,
                    diff=mod.diff if mod.diff else None,
                    added_lines=mod.added_lines,
                    deleted_lines=mod.deleted_lines,
                    change_type=mod.change_type.name if mod.change_type else "",
                )
                changes.append(change)
        except Exception:
            pass
        return changes

    def analyze_commit(self, commit) -> CommitAnalysis:
        # Analyze a single PyDriller commit object.
        message = commit.msg or ""

        # Green awareness check
        green_aware = is_green_aware(message)

        # GSF pattern matching
        matched_patterns = get_pattern_by_keywords(message)
        pattern_details = self._get_pattern_details(matched_patterns)

        # Confidence calculation
        pattern_count = len(matched_patterns)
        confidence = "high" if pattern_count >= 2 else "medium" if pattern_count == 1 else "low"

        # File modifications
        files_modified = [mod.filename for mod in commit.modified_files]
        insertions = sum(mod.added_lines for mod in commit.modified_files)
        deletions = sum(mod.deleted_lines for mod in commit.modified_files)

        # Delta Maintainability Model (if available)
        dmm_unit_size = None
        dmm_unit_complexity = None
        dmm_unit_interfacing = None

        try:
            dmm_unit_size = commit.dmm_unit_size
            dmm_unit_complexity = commit.dmm_unit_complexity
            dmm_unit_interfacing = commit.dmm_unit_interfacing
        except Exception:
            pass  # DMM may not be available for all commits

        # Structural metrics from Lizard (via PyDriller)
        total_nloc = 0
        total_complexity = 0
        max_complexity = 0
        methods_count = 0

        try:
            for mod in commit.modified_files:
                if mod.nloc:
                    total_nloc += mod.nloc
                if mod.complexity:
                    total_complexity += mod.complexity
                    if mod.complexity > max_complexity:
                        max_complexity = mod.complexity
                if mod.methods:
                    methods_count += len(mod.methods)
        except Exception:
            pass  # Structural metrics may fail for some files

        # Phase 3.2: Method-level analysis
        methods = []
        if self.method_level_analysis:
            methods = self._extract_method_metrics(commit)

        # Phase 3.3: Source code access
        source_changes = []
        if self.include_source_code:
            source_changes = self._extract_source_changes(commit)

        return CommitAnalysis(
            hash=commit.hash,
            message=message,
            author=commit.author.name,
            author_email=commit.author.email,
            date=commit.author_date,
            green_aware=green_aware,
            gsf_patterns_matched=matched_patterns,
            pattern_count=pattern_count,
            pattern_details=pattern_details,
            confidence=confidence,
            files_modified=files_modified,
            insertions=insertions,
            deletions=deletions,
            dmm_unit_size=dmm_unit_size,
            dmm_unit_complexity=dmm_unit_complexity,
            dmm_unit_interfacing=dmm_unit_interfacing,
            total_nloc=total_nloc,
            total_complexity=total_complexity,
            max_complexity=max_complexity,
            methods_count=methods_count,
            methods=methods,
            source_changes=source_changes,
        )

    def analyze_repository(self, url: str) -> RepositoryAnalysis:
        # Analyze a repository from its URL.
        owner, repo_name = self._parse_repo_url(url)
        full_name = f"{owner}/{repo_name}"

        colored_print(f"\n Analyzing repository: {full_name}", "cyan")

        # Phase 1.3: Prepare authenticated URL for private repos
        auth_url = self._prepare_auth_url(url)

        # Calculate date range
        since_date = self.since_date or (datetime.now() - timedelta(days=self.days_back))

        # Configure PyDriller Repository
        repo_config = {
            "path_to_repo": auth_url,
            "since": since_date,
            "only_no_merge": self.skip_merges,
        }
        if self.to_date:
            repo_config["to"] = self.to_date

        # Clone to specific path if needed
        local_path = self.clone_path / repo_name
        if local_path.exists():
            shutil.rmtree(local_path)

        repo_config["clone_repo_to"] = str(self.clone_path)

        colored_print(f"   Cloning to: {local_path}", "cyan")

        # Phase 2.2: Start energy measurement if enabled (fresh meter per repo)
        energy_result = None
        energy_meter = None
        if self.energy_tracking:
            try:
                from greenmining.energy.base import get_energy_meter
                energy_meter = get_energy_meter(self.energy_backend)
                energy_meter.start()
            except Exception:
                energy_meter = None

        commits_analyzed = []
        commit_count = 0

        try:
            for commit in Repository(**repo_config).traverse_commits():
                if commit_count >= self.max_commits:
                    break

                try:
                    analysis = self.analyze_commit(commit)
                    commits_analyzed.append(analysis)
                    commit_count += 1

                    if commit_count % 50 == 0:
                        colored_print(f"   Processed {commit_count} commits...", "cyan")

                except Exception as e:
                    colored_print(
                        f"   Warning: Error analyzing commit {commit.hash[:8]}: {e}", "yellow"
                    )
                    continue

            colored_print(f"    Analyzed {len(commits_analyzed)} commits", "green")

            # Phase 2.2: Stop energy measurement
            if energy_meter:
                try:
                    energy_result = energy_meter.stop()
                except Exception:
                    pass

            # Compute process metrics if enabled
            process_metrics = {}
            if self.compute_process_metrics and local_path.exists():
                colored_print("   Computing process metrics...", "cyan")
                process_metrics = self._compute_process_metrics(str(local_path))

            # Calculate summary
            green_commits = sum(1 for c in commits_analyzed if c.green_aware)
            green_rate = green_commits / len(commits_analyzed) if commits_analyzed else 0

            # Build energy metrics dict
            energy_dict = None
            if energy_result:
                energy_dict = energy_result.to_dict()

            result = RepositoryAnalysis(
                url=url,
                name=full_name,
                total_commits=len(commits_analyzed),
                green_commits=green_commits,
                green_commit_rate=green_rate,
                commits=commits_analyzed,
                process_metrics=process_metrics,
                energy_metrics=energy_dict,
            )

            return result

        finally:
            # Cleanup if requested
            if self.cleanup_after and local_path.exists():
                colored_print(f"   Cleaning up: {local_path}", "cyan")
                shutil.rmtree(local_path, ignore_errors=True)

    def _compute_process_metrics(self, repo_path: str) -> Dict[str, Any]:
        # Compute PyDriller process metrics for the repository.
        metrics = {}
        since_date = datetime.now() - timedelta(days=self.days_back)
        to_date = datetime.now()

        try:
            # ChangeSet metrics
            cs = ChangeSet(repo_path, since=since_date, to=to_date)
            metrics["change_set_max"] = cs.max()
            metrics["change_set_avg"] = cs.avg()
        except Exception as e:
            colored_print(f"   Warning: ChangeSet metrics failed: {e}", "yellow")

        try:
            # CodeChurn metrics
            churn = CodeChurn(repo_path, since=since_date, to=to_date)
            metrics["code_churn"] = churn.count()
        except Exception as e:
            colored_print(f"   Warning: CodeChurn metrics failed: {e}", "yellow")

        try:
            # CommitsCount metrics
            cc = CommitsCount(repo_path, since=since_date, to=to_date)
            metrics["commits_per_file"] = cc.count()
        except Exception as e:
            colored_print(f"   Warning: CommitsCount metrics failed: {e}", "yellow")

        try:
            # ContributorsCount metrics
            contrib = ContributorsCount(repo_path, since=since_date, to=to_date)
            metrics["contributors_per_file"] = contrib.count()
        except Exception as e:
            colored_print(f"   Warning: ContributorsCount metrics failed: {e}", "yellow")

        try:
            # ContributorsExperience metrics
            exp = ContributorsExperience(repo_path, since=since_date, to=to_date)
            metrics["contributors_experience"] = exp.count()
        except Exception as e:
            colored_print(f"   Warning: ContributorsExperience metrics failed: {e}", "yellow")

        try:
            # HistoryComplexity metrics
            hc = HistoryComplexity(repo_path, since=since_date, to=to_date)
            metrics["history_complexity"] = hc.count()
        except Exception as e:
            colored_print(f"   Warning: HistoryComplexity metrics failed: {e}", "yellow")

        try:
            # HunksCount metrics
            hunks = HunksCount(repo_path, since=since_date, to=to_date)
            metrics["hunks_count"] = hunks.count()
        except Exception as e:
            colored_print(f"   Warning: HunksCount metrics failed: {e}", "yellow")

        try:
            # LinesCount metrics
            lines = LinesCount(repo_path, since=since_date, to=to_date)
            metrics["lines_count"] = lines.count()
        except Exception as e:
            colored_print(f"   Warning: LinesCount metrics failed: {e}", "yellow")

        return metrics

    def analyze_repositories(
        self,
        urls: List[str],
        parallel_workers: int = 1,
        output_format: str = "dict",
    ) -> List[RepositoryAnalysis]:
        # Analyze multiple repositories from URLs.
        # Args:
        #   urls: List of repository URLs to analyze
        #   parallel_workers: Number of concurrent workers (1 = sequential)
        #   output_format: Output format (dict, json, csv)
        if parallel_workers <= 1:
            return self._analyze_sequential(urls)
        return self._analyze_parallel(urls, parallel_workers)

    def _analyze_sequential(self, urls: List[str]) -> List[RepositoryAnalysis]:
        # Analyze repositories sequentially.
        results = []
        for i, url in enumerate(urls, 1):
            colored_print(f"\n[{i}/{len(urls)}] Processing repository...", "cyan")
            try:
                result = self.analyze_repository(url)
                results.append(result)
            except Exception as e:
                colored_print(f"   Error analyzing {url}: {e}", "red")
                continue
        return results

    def _analyze_parallel(self, urls: List[str], max_workers: int) -> List[RepositoryAnalysis]:
        # Analyze repositories in parallel using thread pool.
        results = []
        colored_print(f"\n Analyzing {len(urls)} repositories with {max_workers} workers", "cyan")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.analyze_repository, url): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    colored_print(f"   Completed: {result.name}", "green")
                except Exception as e:
                    colored_print(f"   Error analyzing {url}: {e}", "red")

        return results
