# Code diff analyzer for detecting green software patterns in code changes.

import re
from typing import Any, Dict, List

from pydriller import Commit, ModifiedFile


class CodeDiffAnalyzer:
    # Analyze code diffs to detect green software patterns

    # Pattern indicators in code changes
    PATTERN_SIGNATURES = {
        "caching": {
            "imports": [
                r"import.*cache",
                r"from.*cache.*import",
                r"import redis",
                r"import memcached",
            ],
            "annotations": [r"@cache", r"@cached", r"@lru_cache", r"@memoize"],
            "function_calls": [r"\.cache\(", r"\.get_cache\(", r"\.set_cache\("],
            "variable_names": [r"cache", r"cached_", r"_cache"],
        },
        "resource_optimization": {
            "kubernetes": [
                r"resources:\s*limits:",
                r"resources:\s*requests:",
                r"memory:\s*[0-9]+Mi",
                r"cpu:\s*[0-9]+m",
            ],
            "docker": [
                r"FROM.*alpine",
                r"FROM.*scratch",
                r"--no-cache",
                r"apt-get.*--no-install-recommends",
            ],
        },
        "database_optimization": {
            "indexes": [r"CREATE.*INDEX", r"@Index", r"add_index"],
            "query_optimization": [
                r"\.select_related\(",
                r"\.prefetch_related\(",
                r"EXPLAIN",
            ],
            "connection_pooling": [
                r"pool_size",
                r"max_connections",
                r"connection_pool",
            ],
        },
        "async_processing": {
            "keywords": [r"\basync\s+def\b", r"\bawait\b", r"asyncio", r"aiohttp"],
            "patterns": [
                r"ThreadPoolExecutor",
                r"ProcessPoolExecutor",
                r"@celery\.task",
            ],
        },
        "lazy_loading": {
            "keywords": [r"lazy", r"defer", r"\.only\(", r"select_related"],
            "patterns": [r"@lazy", r"LazyLoader", r"dynamic.*import"],
        },
        # NEW: Serverless computing patterns
        "serverless_computing": {
            "providers": [
                r"aws.*lambda",
                r"@app\.route",
                r"functions\.https",
                r"azure.*function",
            ],
            "frameworks": [r"serverless", r"chalice", r"zappa", r"claudia"],
            "keywords": [r"lambda_handler", r"cloud.*function", r"function.*app"],
        },
        # NEW: CDN and edge computing
        "cdn_edge": {
            "providers": [
                r"cloudflare",
                r"cloudfront",
                r"fastly",
                r"akamai",
                r"cdn\.js",
            ],
            "keywords": [
                r"edge.*cache",
                r"cdn",
                r"\.distribute\(",
                r"edge.*function",
            ],
        },
        # NEW: Compression patterns
        "compression": {
            "algorithms": [r"gzip", r"brotli", r"deflate", r"zstd", r"lz4"],
            "keywords": [
                r"compress",
                r"decompress",
                r"\.gz\b",
                r"Content-Encoding",
            ],
            "libraries": [r"import gzip", r"import zlib", r"import brotli"],
        },
        # NEW: ML model optimization
        "model_optimization": {
            "techniques": [
                r"quantize",
                r"quantization",
                r"prune",
                r"pruning",
                r"distill",
            ],
            "formats": [r"onnx", r"tensorrt", r"tflite", r"coreml"],
            "keywords": [
                r"int8",
                r"fp16",
                r"mixed.*precision",
                r"model\.optimize",
            ],
        },
        # NEW: Efficient protocols (HTTP/2, gRPC)
        "efficient_protocols": {
            "http2": [r"http2", r"http/2", r"h2", r"alpn"],
            "grpc": [r"grpc", r"protobuf", r"\.proto\b"],
            "keywords": [
                r"stream",
                r"multiplexing",
                r"server.*push",
                r"binary.*protocol",
            ],
        },
        # NEW: Container optimization
        "container_optimization": {
            "base_images": [
                r"FROM.*alpine",
                r"FROM.*scratch",
                r"FROM.*distroless",
            ],
            "techniques": [
                r"multi-stage",
                r"--no-install-recommends",
                r"&&.*rm.*-rf",
                r"\.dockerignore",
            ],
            "keywords": [r"layer.*cache", r"build.*cache", r"image.*size"],
        },
        # NEW: Green cloud regions
        "green_regions": {
            "regions": [
                r"eu-west",
                r"eu-north",
                r"sweden",
                r"norway",
                r"canada",
            ],
            "keywords": [
                r"renewable",
                r"green.*region",
                r"sustainable.*region",
                r"carbon.*neutral",
            ],
        },
        # NEW: Auto-scaling patterns
        "auto_scaling": {
            "kubernetes": [
                r"HorizontalPodAutoscaler",
                r"autoscaling/v",
                r"hpa",
                r"minReplicas",
                r"maxReplicas",
            ],
            "cloud": [
                r"auto.*scal",
                r"scale.*to.*zero",
                r"ScalingPolicy",
                r"TargetTracking",
            ],
            "keywords": [
                r"scale.*up",
                r"scale.*down",
                r"metrics.*server",
                r"cpu.*utilization",
            ],
        },
        # NEW: Code splitting and lazy loading (web)
        "code_splitting": {
            "webpack": [
                r"dynamic.*import",
                r"lazy.*load",
                r"code.*split",
                r"chunk",
            ],
            "react": [r"React\.lazy", r"Suspense", r"loadable"],
            "keywords": [r"bundle", r"split.*chunk", r"async.*component"],
        },
        # NEW: Green ML training
        "green_ml_training": {
            "keywords": [
                r"early.*stopping",
                r"learning.*rate.*scheduler",
                r"gradient.*checkpointing",
                r"mixed.*precision",
            ],
            "frameworks": [
                r"apex",
                r"torch\.cuda\.amp",
                r"tf\.keras\.mixed_precision",
            ],
        },
    }

    def analyze_commit_diff(self, commit: Commit) -> Dict[str, Any]:
        # Analyze code changes in a commit to detect green patterns.
        patterns_detected = []
        evidence = {}
        metrics = self._calculate_metrics(commit)

        for modified_file in commit.modified_files:
            # Skip non-code files
            if not self._is_code_file(modified_file):
                continue

            # Analyze additions
            if modified_file.diff_parsed and modified_file.diff_parsed.get("added"):
                for line in modified_file.diff_parsed["added"]:
                    detected = self._detect_patterns_in_line(line[1])  # line[1] is content
                    patterns_detected.extend(detected)

                    for pattern in detected:
                        if pattern not in evidence:
                            evidence[pattern] = []
                        evidence[pattern].append(
                            f"{modified_file.filename}:{line[0]} - {line[1][:80]}"
                        )

        # Deduplicate patterns
        patterns_detected = list(set(patterns_detected))

        # Confidence scoring
        confidence = self._calculate_diff_confidence(patterns_detected, evidence, metrics)

        return {
            "patterns_detected": patterns_detected,
            "confidence": confidence,
            "evidence": evidence,
            "metrics": metrics,
        }

    def _detect_patterns_in_line(self, code_line: str) -> List[str]:
        # Detect patterns in a single line of code.
        detected = []

        for pattern_name, signatures in self.PATTERN_SIGNATURES.items():
            for signature_type, patterns in signatures.items():
                for pattern_regex in patterns:
                    if re.search(pattern_regex, code_line, re.IGNORECASE):
                        detected.append(pattern_name)
                        break

        return detected

    def _calculate_metrics(self, commit: Commit) -> Dict[str, int]:
        # Calculate code change metrics.
        lines_added = sum(f.added_lines for f in commit.modified_files)
        lines_removed = sum(f.deleted_lines for f in commit.modified_files)
        files_changed = len(commit.modified_files)

        # Complexity change (requires static analysis - simplified for now)
        complexity_before = sum(f.complexity or 0 for f in commit.modified_files)
        complexity_after = complexity_before  # Simplified

        return {
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "files_changed": files_changed,
            "net_lines": lines_added - lines_removed,
            "complexity_change": complexity_after - complexity_before,
        }

    def _calculate_diff_confidence(
        self, patterns: List[str], evidence: Dict[str, List[str]], metrics: Dict[str, int]
    ) -> str:
        # Calculate confidence level for diff-based detection.
        if not patterns:
            return "none"

        evidence_count = sum(len(v) for v in evidence.values())

        if len(patterns) >= 3 and evidence_count >= 5:
            return "high"
        elif len(patterns) >= 2 and evidence_count >= 3:
            return "medium"
        else:
            return "low"

    def _is_code_file(self, modified_file: ModifiedFile) -> bool:
        # Check if file is a code file (not config, docs, etc.).
        code_extensions = [
            ".py",
            ".java",
            ".go",
            ".js",
            ".ts",
            ".cpp",
            ".c",
            ".cs",
            ".rb",
            ".php",
            ".scala",
            ".kt",
            ".rs",
            ".swift",
        ]

        # Check file extension
        for ext in code_extensions:
            if modified_file.filename.endswith(ext):
                return True

        # Also analyze Dockerfiles and Kubernetes manifests
        if "Dockerfile" in modified_file.filename:
            return True
        if modified_file.filename.endswith((".yaml", ".yml")):
            # Check if it's a Kubernetes manifest
            if modified_file.source_code and any(
                k in modified_file.source_code for k in ["kind:", "apiVersion:", "metadata:"]
            ):
                return True

        return False
