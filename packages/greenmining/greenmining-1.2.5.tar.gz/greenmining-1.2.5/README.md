# greenmining

An empirical Python library for Mining Software Repositories (MSR) in Green IT research.

[![PyPI](https://img.shields.io/pypi/v/greenmining)](https://pypi.org/project/greenmining/)
[![Python](https://img.shields.io/pypi/pyversions/greenmining)](https://pypi.org/project/greenmining/)
[![License](https://img.shields.io/github/license/adam-bouafia/greenmining)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue)](https://greenmining.readthedocs.io/)

## Overview

`greenmining` is a research-grade Python library designed for **empirical Mining Software Repositories (MSR)** studies in **Green IT**. It enables researchers and practitioners to:

- **Mine repositories at scale** - Search, fetch, and clone GitHub repositories via GraphQL API with configurable filters
- **Classify green commits** - Detect 124 sustainability patterns from the Green Software Foundation (GSF) catalog using 332 keywords
- **Analyze any repository by URL** - Direct Git-based analysis with support for private repositories
- **Measure energy consumption** - RAPL, CodeCarbon, and CPU Energy Meter backends for power profiling
- **Carbon footprint reporting** - CO2 emissions calculation with 20+ country profiles and cloud region support
- **Method-level analysis** - Per-method complexity and metrics via Lizard integration
- **Generate research datasets** - Statistical analysis, temporal trends, and publication-ready reports

## Installation

### Via pip

```bash
pip install greenmining
```

### With energy measurement

```bash
pip install greenmining[energy]
```

### From source

```bash
git clone https://github.com/adam-bouafia/greenmining.git
cd greenmining
pip install -e .
```

## Quick Start

### Pattern Detection

```python
from greenmining import GSF_PATTERNS, is_green_aware, get_pattern_by_keywords

print(f"Total patterns: {len(GSF_PATTERNS)}")  # 124 patterns across 15 categories

commit_msg = "Optimize Redis caching to reduce energy consumption"
if is_green_aware(commit_msg):
    patterns = get_pattern_by_keywords(commit_msg)
    print(f"Matched patterns: {patterns}")
```

### Fetch Repositories

```python
from greenmining import fetch_repositories

repos = fetch_repositories(
    github_token="your_token",
    max_repos=50,
    min_stars=500,
    keywords="kubernetes cloud-native",
    languages=["Python", "Go"],
    created_after="2020-01-01",
    pushed_after="2023-01-01",
)

for repo in repos[:5]:
    print(f"- {repo.full_name} ({repo.stars} stars)")
```

### Clone Repositories

```python
from greenmining import fetch_repositories, clone_repositories

repos = fetch_repositories(github_token="your_token", max_repos=10, keywords="android")

# Clone into ./greenmining_repos/ with sanitized directory names
paths = clone_repositories(repos)
print(f"Cloned {len(paths)} repositories")
```

### Analyze Repositories by URL

```python
from greenmining import analyze_repositories

results = analyze_repositories(
    urls=[
        "https://github.com/kubernetes/kubernetes",
        "https://github.com/istio/istio",
    ],
    max_commits=100,
    parallel_workers=2,
    energy_tracking=True,
    energy_backend="auto",
    method_level_analysis=True,
    include_source_code=True,
    github_token="your_token",
    since_date="2020-01-01",
    to_date="2025-12-31",
)

for result in results:
    print(f"{result.name}: {result.green_commit_rate:.1%} green")
```

### Access Pattern Data

```python
from greenmining import GSF_PATTERNS

# Get patterns by category
cloud = {k: v for k, v in GSF_PATTERNS.items() if v['category'] == 'cloud'}
print(f"Cloud patterns: {len(cloud)}")

# All categories
categories = set(p['category'] for p in GSF_PATTERNS.values())
print(f"Categories: {sorted(categories)}")
```

### Energy Measurement

```python
from greenmining.energy import get_energy_meter, CPUEnergyMeter

# Auto-detect best backend
meter = get_energy_meter("auto")
meter.start()
# ... your workload ...
result = meter.stop()
print(f"Energy: {result.joules:.2f} J, Power: {result.watts_avg:.2f} W")
```

### Statistical Analysis

```python
from greenmining.analyzers import StatisticalAnalyzer, TemporalAnalyzer

stat = StatisticalAnalyzer()
temporal = TemporalAnalyzer(granularity="quarter")

# Pattern correlations, effect sizes, temporal trends
# See experiment notebook for full usage
```

### Metrics-to-Power Correlation

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
print(f"Feature importance: {correlator.feature_importance}")
```

## Features

### Core Capabilities

- **Pattern Detection**: 124 sustainability patterns across 15 categories from the GSF catalog
- **Keyword Analysis**: 332 green software detection keywords
- **Repository Fetching**: GraphQL API with date, star, and language filters
- **Repository Cloning**: Sanitized directory names in `./greenmining_repos/`
- **URL-Based Analysis**: Direct Git-based analysis from GitHub URLs (HTTPS and SSH)
- **Batch Processing**: Parallel analysis of multiple repositories
- **Private Repository Support**: Authentication via SSH keys or GitHub tokens

### Analysis & Measurement

- **Energy Measurement**: RAPL, CodeCarbon, and CPU Energy Meter backends
- **Carbon Footprint Reporting**: CO2 emissions with 20+ country profiles (AWS, GCP, Azure)
- **Metrics-to-Power Correlation**: Pearson and Spearman analysis between code metrics and power
- **Method-Level Analysis**: Per-method complexity metrics via Lizard integration
- **Source Code Access**: Before/after source code for refactoring detection
- **Process Metrics**: DMM size, complexity, interfacing via PyDriller
- **Statistical Analysis**: Correlations, effect sizes, and temporal trends
- **Multi-format Output**: JSON, CSV, pandas DataFrame

### Energy Backends

| Backend | Platform | Metrics | Requirements |
|---------|----------|---------|--------------|
| **RAPL** | Linux (Intel/AMD) | CPU/RAM energy (Joules) | `/sys/class/powercap/` access |
| **CodeCarbon** | Cross-platform | Energy + Carbon emissions (gCO2) | `pip install codecarbon` |
| **CPU Meter** | All platforms | Estimated CPU energy (Joules) | Optional: `pip install psutil` |
| **Auto** | All platforms | Best available backend | Automatic detection |

### GSF Pattern Categories

**124 patterns across 15 categories:**

| Category | Patterns | Examples |
|----------|----------|----------|
| Cloud | 42 | Auto-scaling, serverless, right-sizing, region selection |
| Web | 17 | CDN, caching, lazy loading, compression |
| AI/ML | 19 | Model pruning, quantization, edge inference |
| Database | 5 | Indexing, query optimization, connection pooling |
| Networking | 8 | Protocol optimization, HTTP/2, gRPC |
| Network | 6 | Request batching, GraphQL, circuit breakers |
| Microservices | 4 | Service decomposition, graceful shutdown |
| Infrastructure | 4 | Alpine containers, IaC, renewable regions |
| General | 8 | Feature flags, precomputation, background jobs |
| Others | 11 | Caching, resource, data, async, code, monitoring |

## Development

```bash
git clone https://github.com/adam-bouafia/greenmining.git
cd greenmining
pip install -e ".[dev]"

pytest tests/
black greenmining/ tests/
ruff check greenmining/ tests/
```

## Requirements

- Python 3.9+
- PyGithub, PyDriller, pandas, colorama, tqdm

**Optional:**

```bash
pip install greenmining[energy]      # psutil, codecarbon
pip install greenmining[dev]         # pytest, black, ruff, mypy
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Links

- **GitHub**: https://github.com/adam-bouafia/greenmining
- **PyPI**: https://pypi.org/project/greenmining/
- **Documentation**: https://greenmining.readthedocs.io/
- **Docker Hub**: https://hub.docker.com/r/adambouafia/greenmining
