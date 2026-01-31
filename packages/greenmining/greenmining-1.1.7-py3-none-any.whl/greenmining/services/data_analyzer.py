# Data analyzer for green microservices commits using GSF patterns.

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tqdm import tqdm

from greenmining.analyzers import (
    CodeDiffAnalyzer,
)
from greenmining.config import get_config
from greenmining.gsf_patterns import (
    GREEN_KEYWORDS,
    GSF_PATTERNS,
    get_pattern_by_keywords,
    is_green_aware,
)
from greenmining.utils import (
    colored_print,
    create_checkpoint,
    format_timestamp,
    load_checkpoint,
    load_json_file,
    print_banner,
    save_json_file,
)


class DataAnalyzer:
    # Analyzes commits for green software patterns using GSF (Green Software Founda...

    def __init__(
        self,
        batch_size: int = 10,
        enable_diff_analysis: bool = False,
    ):
        # Initialize analyzer with GSF patterns.
        # Use GSF patterns from gsf_patterns.py
        self.gsf_patterns = GSF_PATTERNS
        self.green_keywords = GREEN_KEYWORDS
        self.batch_size = batch_size
        self.enable_diff_analysis = enable_diff_analysis

        # Initialize code diff analyzer if enabled
        if self.enable_diff_analysis:
            self.diff_analyzer = CodeDiffAnalyzer()
            colored_print("Code diff analysis enabled (may increase processing time)", "cyan")
        else:
            self.diff_analyzer = None

    def analyze_commits(
        self, commits: list[dict[str, Any]], resume_from: int = 0
    ) -> list[dict[str, Any]]:
        # Analyze commits for green software practices.
        results = []

        colored_print(f"\nAnalyzing {len(commits)} commits for green practices...", "cyan")

        with tqdm(
            total=len(commits), initial=resume_from, desc="Analyzing commits", unit="commit"
        ) as pbar:
            for _idx, commit in enumerate(commits[resume_from:], start=resume_from):
                try:
                    analysis = self._analyze_commit(commit)
                    results.append(analysis)
                    pbar.update(1)
                except Exception as e:
                    colored_print(
                        f"\nError analyzing commit {commit.get('commit_id', 'unknown')}: {e}",
                        "yellow",
                    )
                    pbar.update(1)

        return results

    def _analyze_commit(self, commit: dict[str, Any]) -> dict[str, Any]:
        # Analyze a single commit using GSF patterns.
        message = commit.get("message", "")

        # Q1: GREEN AWARENESS - Check using GSF keywords
        green_aware = is_green_aware(message)

        # Q2: KNOWN GSF PATTERNS - Match against Green Software Foundation patterns
        matched_patterns = get_pattern_by_keywords(message)

        # Q3: CODE DIFF ANALYSIS (if enabled and diff data available)
        diff_analysis = None
        if self.diff_analyzer and commit.get("diff_data"):
            try:
                # Note: This requires commit object from PyDriller
                # For now, we'll store a placeholder for future integration
                diff_analysis = {
                    "enabled": True,
                    "status": "requires_pydriller_commit_object",
                    "patterns_detected": [],
                    "confidence": "none",
                    "evidence": {},
                    "metrics": {},
                }
            except Exception as e:
                diff_analysis = {
                    "enabled": True,
                    "status": f"error: {str(e)}",
                    "patterns_detected": [],
                    "confidence": "none",
                }

        # Get detailed pattern info
        pattern_details = []
        for _pattern_id, pattern in self.gsf_patterns.items():
            if pattern["name"] in matched_patterns:
                pattern_details.append(
                    {
                        "name": pattern["name"],
                        "category": pattern["category"],
                        "description": pattern["description"],
                        "sci_impact": pattern["sci_impact"],
                    }
                )

        # Calculate confidence based on number of patterns matched
        # Boost confidence if diff analysis also detected patterns
        pattern_count = len(matched_patterns)
        if diff_analysis and diff_analysis.get("patterns_detected"):
            pattern_count += len(diff_analysis["patterns_detected"])

        confidence = "high" if pattern_count >= 2 else "medium" if pattern_count == 1 else "low"

        result = {
            "commit_hash": commit.get("hash", commit.get("commit_id", "unknown")),
            "repository": commit.get("repository", commit.get("repo_name", "unknown")),
            "author": commit.get("author", commit.get("author_name", "unknown")),
            "date": commit.get("date", commit.get("author_date", "unknown")),
            "message": message,
            # Research Question 1: Green awareness
            "green_aware": green_aware,
            # Research Question 2: Known GSF patterns
            "gsf_patterns_matched": matched_patterns,
            "pattern_count": len(matched_patterns),
            "pattern_details": pattern_details,
            "confidence": confidence,
            # Additional metadata
            "files_modified": commit.get("files_changed", commit.get("modified_files", [])),
            "insertions": commit.get("lines_added", commit.get("insertions", 0)),
            "deletions": commit.get("lines_deleted", commit.get("deletions", 0)),
        }

        # Add diff analysis results if available
        if diff_analysis:
            result["diff_analysis"] = diff_analysis

        return result

    def _check_green_awareness(self, message: str, files: list[str]) -> tuple[bool, Optional[str]]:
        # Check if commit explicitly mentions green/energy concerns.
        # Check message for green keywords
        for keyword in self.GREEN_KEYWORDS:
            if keyword in message:
                # Extract context around keyword
                pattern = rf".{{0,30}}{re.escape(keyword)}.{{0,30}}"
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    evidence = match.group(0).strip()
                    return True, f"Keyword '{keyword}': {evidence}"

        # Check file names for patterns
        cache_files = [f for f in files if "cache" in f or "redis" in f]
        if cache_files:
            return True, f"Modified cache-related file: {cache_files[0]}"

        perf_files = [f for f in files if "performance" in f or "optimization" in f]
        if perf_files:
            return True, f"Modified performance file: {perf_files[0]}"

        return False, None

    def _detect_known_pattern(self, message: str, files: list[str]) -> tuple[Optional[str], str]:
        # Detect known green software pattern.
        matches = []

        # Check each pattern
        for pattern_name, keywords in self.GREEN_PATTERNS.items():
            for keyword in keywords:
                if keyword in message:
                    # Calculate confidence based on specificity
                    confidence = "HIGH" if len(keyword) > 10 else "MEDIUM"
                    matches.append((pattern_name, confidence, len(keyword)))

        # Check file names for pattern hints
        all_files = " ".join(files)
        for pattern_name, keywords in self.GREEN_PATTERNS.items():
            for keyword in keywords:
                if keyword in all_files:
                    matches.append((pattern_name, "MEDIUM", len(keyword)))

        if not matches:
            return "NONE DETECTED", "NONE"

        # Return most specific match (longest keyword)
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches[0][0], matches[0][1]

    def save_results(self, results: list[dict[str, Any]], output_file: Path):
        # Save analysis results to JSON file.
        # Calculate summary statistics
        green_aware_count = sum(1 for r in results if r["green_aware"])

        # Count all matched patterns (results have gsf_patterns_matched which is a list)
        all_patterns = []
        for r in results:
            patterns = r.get("gsf_patterns_matched", [])
            if patterns:  # If there are matched patterns
                all_patterns.extend(patterns)

        pattern_counts = Counter(all_patterns)

        data = {
            "metadata": {
                "analyzed_at": format_timestamp(),
                "total_commits_analyzed": len(results),
                "green_aware_commits": green_aware_count,
                "green_aware_percentage": (
                    round(green_aware_count / len(results) * 100, 2) if results else 0
                ),
                "analyzer_type": "keyword_heuristic",
                "note": "This analysis uses keyword and heuristic matching. For AI-powered analysis, use Claude API.",
            },
            "results": results,
        }

        save_json_file(data, output_file)
        colored_print(f"Saved analysis for {len(results)} commits to {output_file}", "green")

        # Display summary
        colored_print("\n Analysis Summary:", "cyan")
        colored_print(
            f"  Green-aware commits: {green_aware_count} ({data['metadata']['green_aware_percentage']}%)",
            "white",
        )
        if pattern_counts:
            colored_print("\n  Top patterns detected:", "cyan")
            for pattern, count in pattern_counts.most_common(5):
                colored_print(f"    - {pattern}: {count}", "white")
