# greenmining

An empirical Python library for Mining Software Repositories (MSR) in Green IT research.

[![PyPI](https://img.shields.io/pypi/v/greenmining)](https://pypi.org/project/greenmining/)
[![Python](https://img.shields.io/pypi/pyversions/greenmining)](https://pypi.org/project/greenmining/)
[![License](https://img.shields.io/github/license/adam-bouafia/greenmining)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue)](https://greenmining.readthedocs.io/)

## Overview

`greenmining` is a research-grade Python library designed for **empirical Mining Software Repositories (MSR)** studies in **Green IT**. It enables researchers and practitioners to:

- **Mine repositories at scale** - Fetch and analyze GitHub repositories via GraphQL API with configurable filters
- **Batch analysis with parallelism** - Analyze multiple repositories concurrently with configurable worker pools
- **Classify green commits** - Detect 122 sustainability patterns from the Green Software Foundation (GSF) catalog
- **Analyze any repository by URL** - Direct Git-based analysis with support for private repositories
- **Measure energy consumption** - RAPL, CodeCarbon, and CPU Energy Meter backends for power profiling
- **Carbon footprint reporting** - CO2 emissions calculation with 20+ country profiles and cloud region support
- **Power regression detection** - Identify commits that increased energy consumption
- **Method-level analysis** - Per-method complexity and metrics via Lizard integration
- **Version power comparison** - Compare power consumption across software versions
- **Generate research datasets** - Statistical analysis, temporal trends, and publication-ready reports
- **Web dashboard** - Flask-based interactive visualization of analysis results

Whether you're conducting MSR research, analyzing green software adoption, or measuring the energy footprint of codebases, GreenMining provides the empirical toolkit you need.

## Installation

### Via pip

```bash
pip install greenmining
```

### From source

```bash
git clone https://github.com/adam-bouafia/greenmining.git
cd greenmining
pip install -e .
```

### With Docker

```bash
docker pull adambouafia/greenmining:latest
```

## Quick Start

### Python API

#### Basic Pattern Detection

```python
from greenmining import GSF_PATTERNS, is_green_aware, get_pattern_by_keywords

# Check available patterns
print(f"Total patterns: {len(GSF_PATTERNS)}")  # 122 patterns across 15 categories

# Detect green awareness in commit messages
commit_msg = "Optimize Redis caching to reduce energy consumption"
if is_green_aware(commit_msg):
    patterns = get_pattern_by_keywords(commit_msg)
    print(f"Matched patterns: {patterns}")
    # Output: ['Cache Static Data', 'Use Efficient Cache Strategies']
```

#### Fetch Repositories with Custom Keywords

```python
from greenmining import fetch_repositories

# Fetch repositories with custom search keywords
repos = fetch_repositories(
    github_token="your_github_token",  # Required: GitHub personal access token
    max_repos=50,                      # Maximum number of repositories to fetch
    min_stars=500,                     # Minimum star count filter
    keywords="kubernetes cloud-native", # Search keywords (space-separated)
    languages=["Python", "Go"],        # Programming language filters
    created_after="2020-01-01",        # Filter by creation date (YYYY-MM-DD)
    created_before="2024-12-31",       # Filter by creation date (YYYY-MM-DD)
    pushed_after="2023-01-01",         # Filter by last push date (YYYY-MM-DD)
    pushed_before="2024-12-31"         # Filter by last push date (YYYY-MM-DD)
)

print(f"Found {len(repos)} repositories")
for repo in repos[:5]:
    print(f"- {repo.full_name} ({repo.stars} stars)")
```

**Parameters:**
- `github_token` (str, required): GitHub personal access token for API authentication
- `max_repos` (int, default=100): Maximum number of repositories to fetch
- `min_stars` (int, default=100): Minimum GitHub stars filter
- `keywords` (str, default="microservices"): Space-separated search keywords
- `languages` (list[str], optional): Programming language filters (e.g., ["Python", "Go", "Java"])
- `created_after` (str, optional): Filter repos created after date (format: "YYYY-MM-DD")
- `created_before` (str, optional): Filter repos created before date (format: "YYYY-MM-DD")
- `pushed_after` (str, optional): Filter repos pushed after date (format: "YYYY-MM-DD")
- `pushed_before` (str, optional): Filter repos pushed before date (format: "YYYY-MM-DD")

#### Analyze Repository Commits

```python
from greenmining.services.commit_extractor import CommitExtractor
from greenmining.services.data_analyzer import DataAnalyzer
from greenmining import fetch_repositories

# Fetch repositories with custom keywords
repos = fetch_repositories(
    github_token="your_token",
    max_repos=10,
    keywords="serverless edge-computing"
)

# Initialize commit extractor with parameters
extractor = CommitExtractor(
    exclude_merge_commits=True,      # Skip merge commits (default: True)
    exclude_bot_commits=True,        # Skip bot commits (default: True)
    min_message_length=10            # Minimum commit message length (default: 10)
)

# Initialize analyzer with advanced features
analyzer = DataAnalyzer(
    enable_diff_analysis=False,      # Enable code diff analysis (slower but more accurate)
    patterns=None,                   # Custom pattern dict (default: GSF_PATTERNS)
    batch_size=10                    # Batch processing size (default: 10)
)

# Extract commits from first repo
commits = extractor.extract_commits(
    repository=repos[0],             # PyGithub Repository object
    max_commits=50,                  # Maximum commits to extract per repository
    since=None,                      # Start date filter (datetime object, optional)
    until=None                       # End date filter (datetime object, optional)
)

**CommitExtractor Parameters:**
- `exclude_merge_commits` (bool, default=True): Skip merge commits during extraction
- `exclude_bot_commits` (bool, default=True): Skip commits from bot accounts
- `min_message_length` (int, default=10): Minimum length for commit message to be included

**DataAnalyzer Parameters:**
- `enable_diff_analysis` (bool, default=False): Enable code diff analysis (slower)
- `patterns` (dict, optional): Custom pattern dictionary (default: GSF_PATTERNS)
- `batch_size` (int, default=10): Number of commits to process in each batch

# Analyze commits for green patterns
results = []
for commit in commits:
    result = analyzer.analyze_commit(commit)
    if result['green_aware']:
        results.append(result)
        print(f"Green commit found: {commit.message[:50]}...")
        print(f"  Patterns: {result['known_pattern']}")
```

#### Access Sustainability Patterns Data

```python
from greenmining import GSF_PATTERNS

# Get all patterns by category
cloud_patterns = {
    pid: pattern for pid, pattern in GSF_PATTERNS.items()
    if pattern['category'] == 'cloud'
}
print(f"Cloud patterns: {len(cloud_patterns)}")  # 40 patterns

ai_patterns = {
    pid: pattern for pid, pattern in GSF_PATTERNS.items()
    if pattern['category'] == 'ai'
}
print(f"AI/ML patterns: {len(ai_patterns)}")  # 19 patterns

# Get pattern details
cache_pattern = GSF_PATTERNS['gsf_001']
print(f"Pattern: {cache_pattern['name']}")
print(f"Category: {cache_pattern['category']}")
print(f"Keywords: {cache_pattern['keywords']}")
print(f"Impact: {cache_pattern['sci_impact']}")

# List all available categories
categories = set(p['category'] for p in GSF_PATTERNS.values())
print(f"Available categories: {sorted(categories)}")
# Output: ['ai', 'async', 'caching', 'cloud', 'code', 'data', 
#          'database', 'general', 'infrastructure', 'microservices',
#          'monitoring', 'network', 'networking', 'resource', 'web']
```

#### Advanced Analysis: Temporal Trends

```python
from greenmining.services.data_aggregator import DataAggregator
from greenmining.analyzers.temporal_analyzer import TemporalAnalyzer
from greenmining.analyzers.qualitative_analyzer import QualitativeAnalyzer

# Initialize aggregator with all advanced features
aggregator = DataAggregator(
    config=None,                        # Config object (optional)
    enable_stats=True,                  # Enable statistical analysis (correlations, trends)
    enable_temporal=True,               # Enable temporal trend analysis
    temporal_granularity="quarter"      # Time granularity: day/week/month/quarter/year
)

# Optional: Configure temporal analyzer separately
temporal_analyzer = TemporalAnalyzer(
    granularity="quarter"               # Time period granularity for grouping commits
)

# Optional: Configure qualitative analyzer for validation sampling
qualitative_analyzer = QualitativeAnalyzer(
    sample_size=30,                     # Number of samples for manual validation
    stratify_by="pattern"               # Stratification method: pattern/repository/time/random
)

# Aggregate results with temporal insights
aggregated = aggregator.aggregate(
    analysis_results=analysis_results,  # List of analysis result dictionaries
    repositories=repositories           # List of PyGithub repository objects
)

**DataAggregator Parameters:**
- `config` (Config, optional): Configuration object
- `enable_stats` (bool, default=False): Enable pattern correlations and effect size analysis
- `enable_temporal` (bool, default=False): Enable temporal trend analysis over time
- `temporal_granularity` (str, default="quarter"): Time granularity (day/week/month/quarter/year)

**TemporalAnalyzer Parameters:**
- `granularity` (str, default="quarter"): Time period for grouping (day/week/month/quarter/year)

**QualitativeAnalyzer Parameters:**
- `sample_size` (int, default=30): Number of commits to sample for validation
- `stratify_by` (str, default="pattern"): Stratification method (pattern/repository/time/random)

# Access temporal analysis results
temporal = aggregated['temporal_analysis']
print(f"Time periods analyzed: {len(temporal['periods'])}")

# View pattern adoption trends over time
for period_data in temporal['periods']:
    print(f"{period_data['period']}: {period_data['commit_count']} commits, "
          f"{period_data['green_awareness_rate']:.1%} green awareness")

# Access pattern evolution insights
evolution = temporal.get('pattern_evolution', {})
print(f"Emerging patterns: {evolution.get('emerging', [])}")
print(f"Stable patterns: {evolution.get('stable', [])}")
```

#### Generate Custom Reports

```python
from greenmining.services.data_aggregator import DataAggregator
from greenmining.config import Config

config = Config()
aggregator = DataAggregator(config)

# Load analysis results
results = aggregator.load_analysis_results()

# Generate statistics
stats = aggregator.calculate_statistics(results)
print(f"Total commits analyzed: {stats['total_commits']}")
print(f"Green-aware commits: {stats['green_aware_count']}")
print(f"Top patterns: {stats['top_patterns'][:5]}")

# Export to CSV
aggregator.export_to_csv(results, "output.csv")
```

#### URL-Based Repository Analysis

```python
from greenmining.services.local_repo_analyzer import LocalRepoAnalyzer

analyzer = LocalRepoAnalyzer(
    max_commits=200,
    cleanup_after=True,
)

result = analyzer.analyze_repository("https://github.com/pallets/flask")

print(f"Repository: {result.name}")
print(f"Commits analyzed: {result.total_commits}")
print(f"Green-aware: {result.green_commits} ({result.green_commit_rate:.1%})")

for commit in result.commits[:5]:
    if commit.green_aware:
        print(f"  {commit.message[:60]}...")
```

#### Batch Analysis with Parallelism

```python
from greenmining import analyze_repositories

results = analyze_repositories(
    urls=[
        "https://github.com/kubernetes/kubernetes",
        "https://github.com/istio/istio",
        "https://github.com/envoyproxy/envoy",
    ],
    max_commits=100,
    parallel_workers=3,
    energy_tracking=True,
    energy_backend="auto",
)

for result in results:
    print(f"{result.name}: {result.green_commit_rate:.1%} green")
```

#### Private Repository Analysis

```python
from greenmining.services.local_repo_analyzer import LocalRepoAnalyzer

# HTTPS with token
analyzer = LocalRepoAnalyzer(github_token="ghp_xxxx")
result = analyzer.analyze_repository("https://github.com/company/private-repo")

# SSH with key
analyzer = LocalRepoAnalyzer(ssh_key_path="~/.ssh/id_rsa")
result = analyzer.analyze_repository("git@github.com:company/private-repo.git")
```

#### Power Regression Detection

```python
from greenmining.analyzers import PowerRegressionDetector

detector = PowerRegressionDetector(
    test_command="pytest tests/ -x",
    energy_backend="rapl",
    threshold_percent=5.0,
    iterations=5,
)

regressions = detector.detect(
    repo_path="/path/to/repo",
    baseline_commit="v1.0.0",
    target_commit="HEAD",
)

for regression in regressions:
    print(f"Commit {regression.sha[:8]}: +{regression.power_increase:.1f}%")
```

#### Version Power Comparison

```python
from greenmining.analyzers import VersionPowerAnalyzer

analyzer = VersionPowerAnalyzer(
    test_command="pytest tests/",
    energy_backend="rapl",
    iterations=10,
    warmup_iterations=2,
)

report = analyzer.analyze_versions(
    repo_path="/path/to/repo",
    versions=["v1.0", "v1.1", "v1.2", "v2.0"],
)

print(report.summary())
print(f"Trend: {report.trend}")
print(f"Most efficient: {report.most_efficient}")
```

#### Metrics-to-Power Correlation

```python
from greenmining.analyzers import MetricsPowerCorrelator

correlator = MetricsPowerCorrelator()
correlator.fit(
    metrics=["complexity", "nloc", "code_churn"],
    metrics_values={
        "complexity": [10, 20, 30, 40],
        "nloc": [100, 200, 300, 400],
        "code_churn": [50, 100, 150, 200],
    },
    power_measurements=[5.0, 8.0, 12.0, 15.0],
)

print(f"Pearson: {correlator.pearson}")
print(f"Spearman: {correlator.spearman}")
print(f"Feature importance: {correlator.feature_importance}")
```

#### Web Dashboard

```python
from greenmining.dashboard import run_dashboard

# Launch interactive dashboard (requires pip install greenmining[dashboard])
run_dashboard(data_dir="./data", host="127.0.0.1", port=5000)
```

#### Pipeline Batch Analysis

```python
from greenmining.controllers.repository_controller import RepositoryController
from greenmining.config import Config

config = Config()
controller = RepositoryController(config)

# Run full pipeline programmatically
controller.fetch_repositories(max_repos=50)
controller.extract_commits(max_commits=100)
controller.analyze_commits()
controller.aggregate_results()
controller.generate_report()

print("Analysis complete! Check data/ directory for results.")
```

#### Complete Working Example: Full Pipeline

This is a complete, production-ready example that demonstrates the entire analysis pipeline. This example successfully analyzed 100 repositories with 30,543 commits in our testing.

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from greenmining package
from greenmining import fetch_repositories
from greenmining.services.commit_extractor import CommitExtractor
from greenmining.services.data_analyzer import DataAnalyzer
from greenmining.services.data_aggregator import DataAggregator

# Configuration
token = os.getenv("GITHUB_TOKEN")
output_dir = Path("results")
output_dir.mkdir(exist_ok=True)

# STAGE 1: Fetch Repositories
print("Fetching repositories...")
repositories = fetch_repositories(
    github_token=token,
    max_repos=100,
    min_stars=10,
    keywords="software engineering",
)
print(f"Fetched {len(repositories)} repositories")

# STAGE 2: Extract Commits
print("\nExtracting commits...")
extractor = CommitExtractor(
    github_token=token,
    max_commits=1000,
    skip_merges=True,
    days_back=730,
    timeout=120,
)
all_commits = extractor.extract_from_repositories(repositories)
print(f"Extracted {len(all_commits)} commits")

# Save commits
extractor.save_results(
    all_commits,
    output_dir / "commits.json",
    len(repositories)
)

# STAGE 3: Analyze Commits
print("\nAnalyzing commits...")
analyzer = DataAnalyzer(
    enable_diff_analysis=False,  # Set to True for detailed code analysis (slower)
)
analyzed_commits = analyzer.analyze_commits(all_commits)

# Count green-aware commits
green_count = sum(1 for c in analyzed_commits if c.get("green_aware", False))
green_percentage = (green_count / len(analyzed_commits) * 100) if analyzed_commits else 0
print(f"Analyzed {len(analyzed_commits)} commits")
print(f"Green-aware: {green_count} ({green_percentage:.1f}%)")

# Save analysis
analyzer.save_results(analyzed_commits, output_dir / "analyzed.json")

# STAGE 4: Aggregate Results
print("\nAggregating results...")
aggregator = DataAggregator(
    enable_stats=True,
    enable_temporal=True,
    temporal_granularity="quarter",
)
results = aggregator.aggregate(analyzed_commits, repositories)

# STAGE 5: Save Results
print("\nSaving results...")
aggregator.save_results(
    results,
    output_dir / "aggregated.json",
    output_dir / "aggregated.csv",
    analyzed_commits
)

# Print summary
print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
aggregator.print_summary(results)
print(f"\nResults saved in: {output_dir.absolute()}")
```

**What this example does:**

1. **Fetches repositories** from GitHub based on keywords and filters
2. **Extracts commits** from each repository (up to 1000 per repo)
3. **Analyzes commits** for green software patterns
4. **Aggregates results** with temporal analysis and statistics
5. **Saves results** to JSON and CSV files for further analysis

**Expected output files:**
- `commits.json` - All extracted commits with metadata
- `analyzed.json` - Commits analyzed for green patterns
- `aggregated.json` - Summary statistics and pattern distributions
- `aggregated.csv` - Tabular format for spreadsheet analysis
- `metadata.json` - Experiment configuration and timing

**Performance:** This pipeline successfully processed 100 repositories (30,543 commits) in approximately 6.4 hours, identifying 7,600 green-aware commits (24.9%).

### Docker Usage

```bash
# Interactive shell with Python
docker run -it -v $(pwd)/data:/app/data \
           adambouafia/greenmining:latest python

# Run Python script
docker run -v $(pwd)/data:/app/data \
           adambouafia/greenmining:latest python your_script.py
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
GITHUB_TOKEN=your_github_personal_access_token

# Optional - Repository Fetching
MAX_REPOS=100
MIN_STARS=100
SUPPORTED_LANGUAGES=Python,Java,Go,JavaScript,TypeScript
SEARCH_KEYWORDS=microservices

# Optional - Commit Extraction
COMMITS_PER_REPO=50
EXCLUDE_MERGE_COMMITS=true
EXCLUDE_BOT_COMMITS=true

# Optional - Analysis Features
ENABLE_DIFF_ANALYSIS=false
BATCH_SIZE=10

# Optional - Temporal Analysis
ENABLE_TEMPORAL=true
TEMPORAL_GRANULARITY=quarter
ENABLE_STATS=true

# Optional - Output
OUTPUT_DIR=./data
REPORT_FORMAT=markdown
```

### Config Object Parameters

```python
from greenmining.config import Config

config = Config(
    # GitHub API
    github_token="your_token",              # GitHub personal access token (required)
    
    # Repository Fetching
    max_repos=100,                          # Maximum repositories to fetch
    min_stars=100,                          # Minimum star threshold
    supported_languages=["Python", "Go"],   # Language filters
    search_keywords="microservices",        # Default search keywords
    
    # Commit Extraction
    max_commits=50,                         # Commits per repository
    exclude_merge_commits=True,             # Skip merge commits
    exclude_bot_commits=True,               # Skip bot commits
    min_message_length=10,                  # Minimum commit message length
    
    # Analysis Options
    enable_diff_analysis=False,             # Enable code diff analysis
    batch_size=10,                          # Batch processing size
    
    # Temporal Analysis
    enable_temporal=True,                   # Enable temporal trend analysis
    temporal_granularity="quarter",         # day/week/month/quarter/year
    enable_stats=True,                      # Enable statistical analysis
    
    # Output Configuration
    output_dir="./data",                    # Output directory path
    repos_file="repositories.json",         # Repositories filename
    commits_file="commits.json",            # Commits filename
    analysis_file="analysis_results.json",  # Analysis results filename
    stats_file="aggregated_statistics.json", # Statistics filename
    report_file="green_analysis.md"         # Report filename
)
```

## Features

### Core Capabilities

- **Pattern Detection**: 122 sustainability patterns across 15 categories from the GSF catalog
- **Keyword Analysis**: 321 green software detection keywords
- **Repository Fetching**: GraphQL API with date, star, and language filters
- **URL-Based Analysis**: Direct Git-based analysis from GitHub URLs (HTTPS and SSH)
- **Batch Processing**: Parallel analysis of multiple repositories with configurable workers
- **Private Repository Support**: Authentication via SSH keys or GitHub tokens
- **Energy Measurement**: RAPL, CodeCarbon, and CPU Energy Meter backends
- **Carbon Footprint Reporting**: CO2 emissions with 20+ country profiles and cloud region support (AWS, GCP, Azure)
- **Power Regression Detection**: Identify commits that increased energy consumption
- **Metrics-to-Power Correlation**: Pearson and Spearman analysis between code metrics and power
- **Version Power Comparison**: Compare power consumption across software versions with trend detection
- **Method-Level Analysis**: Per-method complexity metrics via Lizard integration
- **Source Code Access**: Before/after source code for refactoring detection
- **Full Process Metrics**: All 8 process metrics (ChangeSet, CodeChurn, CommitsCount, ContributorsCount, ContributorsExperience, HistoryComplexity, HunksCount, LinesCount)
- **Statistical Analysis**: Correlations, effect sizes, and temporal trends
- **Multi-format Output**: Markdown reports, CSV exports, JSON data
- **Web Dashboard**: Flask-based interactive visualization (`pip install greenmining[dashboard]`)
- **Docker Support**: Pre-built images for containerized analysis

### Energy Measurement

greenmining includes built-in energy measurement capabilities for tracking the carbon footprint of your analysis:

#### Backend Options

| Backend | Platform | Metrics | Requirements |
|---------|----------|---------|--------------|
| **RAPL** | Linux (Intel/AMD) | CPU/RAM energy (Joules) | `/sys/class/powercap/` access |
| **CodeCarbon** | Cross-platform | Energy + Carbon emissions (gCO2) | `pip install codecarbon` |
| **CPU Meter** | All platforms | Estimated CPU energy (Joules) | Optional: `pip install psutil` |
| **Auto** | All platforms | Best available backend | Automatic detection |

#### Python API

```python
from greenmining.energy import RAPLEnergyMeter, CPUEnergyMeter, get_energy_meter

# Auto-detect best backend
meter = get_energy_meter("auto")
meter.start()
# ... run analysis ...
result = meter.stop()
print(f"Energy: {result.joules:.2f} J")
print(f"Power: {result.watts_avg:.2f} W")

# Integrated energy tracking during analysis
from greenmining.services.local_repo_analyzer import LocalRepoAnalyzer

analyzer = LocalRepoAnalyzer(energy_tracking=True, energy_backend="auto")
result = analyzer.analyze_repository("https://github.com/pallets/flask")
print(f"Analysis energy: {result.energy_metrics['joules']:.2f} J")
```

#### Carbon Footprint Reporting

```python
from greenmining.energy import CarbonReporter

reporter = CarbonReporter(
    country_iso="USA",
    cloud_provider="aws",
    region="us-east-1",
)
report = reporter.generate_report(total_joules=3600.0)
print(f"CO2: {report.total_emissions_kg * 1000:.4f} grams")
print(f"Equivalent: {report.tree_months:.2f} tree-months to offset")
```

### Pattern Database

**122 green software patterns based on:**
- Green Software Foundation (GSF) Patterns Catalog
- VU Amsterdam 2024 research on ML system sustainability
- ICSE 2024 conference papers on sustainable software

### Detection Performance

- **Coverage**: 67% of patterns actively detect in real-world commits
- **Accuracy**: 100% true positive rate for green-aware commits
- **Categories**: 15 distinct sustainability domains covered
- **Keywords**: 321 detection terms across all patterns

## GSF Pattern Categories

**122 patterns across 15 categories:**

### 1. Cloud (40 patterns)
Auto-scaling, serverless computing, right-sizing instances, region selection for renewable energy, spot instances, idle resource detection, cloud-native architectures

### 2. Web (17 patterns)
CDN usage, caching strategies, lazy loading, asset compression, image optimization, minification, code splitting, tree shaking, prefetching

### 3. AI/ML (19 patterns)
Model optimization, pruning, quantization, edge inference, batch optimization, efficient training, model compression, hardware acceleration, green ML pipelines

### 4. Database (5 patterns)
Indexing strategies, query optimization, connection pooling, prepared statements, database views, denormalization for efficiency

### 5. Networking (8 patterns)
Protocol optimization, connection reuse, HTTP/2, gRPC, efficient serialization, compression, persistent connections

### 6. Network (6 patterns)
Request batching, GraphQL optimization, API gateway patterns, circuit breakers, rate limiting, request deduplication

### 7. Caching (2 patterns)
Multi-level caching, cache invalidation strategies, data deduplication, distributed caching

### 8. Resource (2 patterns)
Resource limits, dynamic allocation, memory management, CPU throttling

### 9. Data (3 patterns)
Efficient serialization formats, pagination, streaming, data compression

### 10. Async (3 patterns)
Event-driven architecture, reactive streams, polling elimination, non-blocking I/O

### 11. Code (4 patterns)
Algorithm optimization, code efficiency, garbage collection tuning, memory profiling

### 12. Monitoring (3 patterns)
Energy monitoring, performance profiling, APM tools, observability patterns

### 13. Microservices (4 patterns)
Service decomposition, colocation strategies, graceful shutdown, service mesh optimization

### 14. Infrastructure (4 patterns)
Alpine containers, Infrastructure as Code, renewable energy regions, container optimization

### 15. General (8 patterns)
Feature flags, incremental processing, precomputation, background jobs, workflow optimization

## Output Files

All outputs are saved to the `data/` directory:

- `repositories.json` - Repository metadata
- `commits.json` - Extracted commit data
- `analysis_results.json` - Pattern analysis results
- `aggregated_statistics.json` - Summary statistics
- `green_analysis_results.csv` - CSV export for spreadsheets
- `green_microservices_analysis.md` - Final report

## Development

```bash
# Clone repository
git clone https://github.com/adam-bouafia/greenmining.git
cd greenmining

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=greenmining tests/

# Format code
black greenmining/ tests/
ruff check greenmining/ tests/
```

## Requirements

- Python 3.9+
- PyGithub >= 2.1.1
- gitpython >= 3.1.0
- lizard >= 1.17.0
- pandas >= 2.2.0

**Optional dependencies:**

```bash
pip install greenmining[energy]      # psutil, codecarbon (energy measurement)
pip install greenmining[dashboard]   # flask (web dashboard)
pip install greenmining[dev]         # pytest, black, ruff, mypy (development)
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Links

- **GitHub**: https://github.com/adam-bouafia/greenmining
- **PyPI**: https://pypi.org/project/greenmining/
- **Docker Hub**: https://hub.docker.com/r/adambouafia/greenmining
- **Documentation**: https://github.com/adam-bouafia/greenmining#readme


