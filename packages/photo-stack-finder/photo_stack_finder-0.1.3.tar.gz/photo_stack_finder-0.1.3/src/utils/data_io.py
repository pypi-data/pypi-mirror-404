"""Data I/O utilities for CSV file handling with error handling.

This module provides standardized functions for loading and saving CSV files
with consistent error handling, logging, and user feedback.
"""

import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Configure logger for this module
logger = logging.getLogger(__name__)


def load_required_csv(
    path: Path,
    error_message: str,
    **pandas_kwargs: Any,
) -> pd.DataFrame:
    """Load a CSV file or exit with error message if not found.

    This function is designed for user-facing scripts that require specific
    input files. If the file doesn't exist, it prints an error message and
    exits the program with status code 1.

    Args:
        path: Path to the CSV file to load
        error_message: Error message to display if file doesn't exist
        **pandas_kwargs: Additional keyword arguments to pass to pd.read_csv()

    Returns:
        The loaded DataFrame

    Raises:
        SystemExit: If the file doesn't exist (exits with code 1)

    Example:
        >>> df = load_required_csv(
        ...     Path("data/scores.csv"),
        ...     "scores.csv not found. Run benchmark first.",
        ...     index_col=0
        ... )
    """
    if not path.exists():
        logger.error(error_message)
        sys.exit(1)

    # read_csv returns DataFrame, but mypy doesn't infer this from **kwargs
    result: pd.DataFrame = pd.read_csv(path, **pandas_kwargs)
    return result


def save_dataframe_with_logging(
    df: pd.DataFrame,
    path: Path,
    description: str,
    **pandas_kwargs: Any,
) -> None:
    """Save DataFrame to CSV with logging.

    Saves the DataFrame and prints a confirmation message indicating
    what was saved and where.

    Args:
        df: DataFrame to save
        path: Path where the CSV should be saved
        description: Human-readable description of what's being saved (for logging)
        **pandas_kwargs: Additional keyword arguments to pass to pd.to_csv()

    Example:
        >>> save_dataframe_with_logging(
        ...     outliers_df,
        ...     output_dir / "outliers.csv",
        ...     "outlier pairs",
        ...     index=False
        ... )
        # Prints: "Saved 42 outlier pairs to output/outliers.csv"
    """
    df.to_csv(path, **pandas_kwargs)
    logger.info(f"Saved {len(df)} {description} to {path}")
