"""Report generation utility with fluent API for consistent formatting.

This module provides a ReportBuilder class that simplifies the creation of
text-based reports with consistent formatting across the codebase.

Usage:
    report = (
        ReportBuilder()
        .add_title("Benchmark Results")
        .add_section("Performance Metrics")
        .add_metric("Accuracy", 0.95, ".2%")
        .add_blank_line()
        .build()
    )
"""

from pathlib import Path
from typing import Any, Self


class ReportBuilder:
    """Fluent API for building text reports with consistent formatting.

    Provides a chainable interface for adding formatted sections, metrics,
    and separators to text reports. All methods return self to enable
    method chaining.

    Example:
        >>> report = (
        ...     ReportBuilder()
        ...     .add_title("Results")
        ...     .add_metric("Score", 0.85, ".2f")
        ...     .build()
        ... )
    """

    def __init__(self) -> None:
        """Initialize an empty report builder."""
        self._lines: list[str] = []

    def add_title(self, text: str, width: int = 80) -> Self:
        """Add a centered title with separator lines above and below.

        Args:
            text: The title text to display
            width: Width of the separator lines (default: 80)

        Returns:
            Self for method chaining
        """
        self._lines.append("=" * width)
        self._lines.append(text.center(width))
        self._lines.append("=" * width)
        return self

    def add_section(self, header: str) -> Self:
        """Add a section header with a single underline.

        Args:
            header: The section header text

        Returns:
            Self for method chaining
        """
        self._lines.append("")
        self._lines.append(header)
        self._lines.append("-" * len(header))
        return self

    def add_metric(self, name: str, value: Any, format_spec: str = "") -> Self:
        """Add a formatted metric line.

        Args:
            name: The metric name (will be left-aligned)
            value: The metric value to format
            format_spec: Optional format specification (e.g., ".2f", ".2%")

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_metric("Accuracy", 0.95, ".2%")  # "Accuracy: 95.00%"
        """
        if format_spec:
            formatted_value = f"{value:{format_spec}}"
        else:
            formatted_value = str(value)
        self._lines.append(f"{name}: {formatted_value}")
        return self

    def add_blank_line(self) -> Self:
        """Add a blank line for spacing.

        Returns:
            Self for method chaining
        """
        self._lines.append("")
        return self

    def add_separator(self, char: str = "=", width: int = 80) -> Self:
        """Add a separator line.

        Args:
            char: The character to use for the separator (default: "=")
            width: Width of the separator line (default: 80)

        Returns:
            Self for method chaining
        """
        self._lines.append(char * width)
        return self

    def add_text(self, text: str) -> Self:
        """Add arbitrary text (can be multi-line).

        Args:
            text: The text to add (newlines will be preserved)

        Returns:
            Self for method chaining
        """
        self._lines.append(text)
        return self

    def build(self) -> str:
        """Build and return the complete report as a string.

        Returns:
            The formatted report with newline-separated lines
        """
        return "\n".join(self._lines)

    def save(self, path: Path) -> None:
        """Build the report and save it to a file.

        Args:
            path: The file path where the report should be saved
        """
        path.write_text(self.build(), encoding="utf-8")
