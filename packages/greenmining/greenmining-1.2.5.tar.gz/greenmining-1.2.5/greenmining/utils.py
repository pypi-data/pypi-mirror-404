# Utility functions for green microservices mining CLI.

import json
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    # Format timestamp in ISO 8601 format.
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json_file(path: Path) -> dict[str, Any]:
    # Load JSON data from file.
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: dict[str, Any], path: Path, indent: int = 2) -> None:
    # Save data to JSON file.
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def save_csv_file(df: pd.DataFrame, path: Path) -> None:
    # Save DataFrame to CSV file.
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 2.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,),
) -> Callable:
    # Decorator to retry function on exception.

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise

                    colored_print(f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}", "yellow")
                    colored_print(f"Retrying in {current_delay:.1f} seconds...", "yellow")

                    time.sleep(current_delay)

                    if exponential_backoff:
                        current_delay *= 2

            return None

        return wrapper

    return decorator


def colored_print(text: str, color: str = "white") -> None:
    # Print colored text to console.
    color_map = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE,
    }

    color_code = color_map.get(color.lower(), Fore.WHITE)
    print(f"{color_code}{text}{Style.RESET_ALL}")


def format_number(num: int) -> str:
    # Format large numbers with thousand separators.
    return f"{num:,}"


def format_percentage(value: float, decimals: int = 1) -> str:
    # Format percentage value.
    return f"{value:.{decimals}f}%"
