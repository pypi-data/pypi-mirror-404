# Allow running greenmining as a module: python -m greenmining
# This is a library - use Python API for programmatic access.

from greenmining import __version__

if __name__ == "__main__":
    print(f"greenmining v{__version__}")
    print("This is a Python library for analyzing green software patterns.")
    print("\nUsage:")
    print("  from greenmining import GSF_PATTERNS, is_green_aware, get_pattern_by_keywords")
    print("  from greenmining.services import GitHubFetcher, CommitExtractor, DataAnalyzer")
    print("\nDocumentation: https://github.com/adam-bouafia/greenmining")
