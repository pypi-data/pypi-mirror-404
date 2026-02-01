#!/usr/bin/env python3
"""Photo Deduplication Orchestrator - Web Interface Entry Point.

This provides a web-based interface for the photo deduplication pipeline.

Usage:
    python orchestrate.py

    Then open your browser to: http://localhost:8000

Options:
    --port PORT       Server port (default: 8000)
    --host HOST       Server host (default: 127.0.0.1)
    --coverage        Run with coverage instrumentation for testing
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
import webbrowser
from importlib.metadata import version
from pathlib import Path

import uvicorn

from orchestrator.app import app


def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for orchestrator CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Photo Dedup Orchestrator - Web Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This is a web interface for the photo deduplication pipeline.

For the web interface, just run:
  - python orchestrate.py
        """,
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on (default: 8000)")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage instrumentation (for testing/development)",
    )
    parser.add_argument(
        "--coverage-append",
        action="store_true",
        help="Append to existing coverage data (for multiple test runs)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't auto-open browser on startup (useful for automated testing)",
    )
    return parser


def print_banner(title: str, lines: list[str]) -> None:
    """Print formatted banner with title and content lines.

    Args:
        title: Banner title
        lines: Content lines to display within banner
    """
    print("=" * 70)
    print(title)
    print("=" * 70)
    for line in lines:
        if line:  # Only print non-empty lines
            print(line)
        else:
            print()  # Empty line for spacing


def run_with_coverage(args: argparse.Namespace) -> None:
    """Re-launch orchestrator through coverage instrumentation.

    This function handles subprocess orchestration for coverage collection,
    including both single-run and append modes.

    Args:
        args: Parsed command-line arguments
    """
    is_append = args.coverage_append

    # Print coverage mode banner
    if is_append:
        lines = [
            "Running with coverage instrumentation (APPEND mode)",
            "=" * 70,
            "Coverage data will be ADDED to existing .coverage file",
            "",
            "Workflow for testing both fresh and cached pipelines:",
            "  1. Run: python src/scripts/orchestrate.py --coverage",
            "     (test fresh pipeline, no caches)",
            "  2. Run: python src/scripts/orchestrate.py --coverage-append",
            "     (test cached pipeline, appends to coverage)",
            "  3. Reports will combine both runs",
        ]
    else:
        lines = [
            "Running with coverage instrumentation",
            "=" * 70,
            "Coverage data will be saved to .coverage",
            "",
            "To test multiple scenarios (fresh + cached):",
            "  - Use --coverage-append for additional runs",
        ]

    print_banner("", lines)  # Empty title since first line is the title
    print()

    # Set environment variable for subprocess coverage collection
    env = os.environ.copy()
    env["COVERAGE_PROCESS_START"] = str(Path.cwd() / "pyproject.toml")

    # Re-launch this script through coverage
    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--parallel-mode",  # Create separate .coverage.* files for each process
    ]
    if is_append:
        cmd.append("--append")  # Append to existing coverage data
    cmd.extend(
        [
            "--source=src",
            sys.argv[0],  # This script
            "--host",
            args.host,
            "--port",
            str(args.port),
            # Don't pass --coverage flags again (infinite loop)
        ]
    )
    try:
        subprocess.run(cmd, env=env, check=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped - coverage data saved")

    # Combine coverage data from all processes
    print_banner("Combining coverage data from all processes", [])
    print()

    subprocess.run(
        [sys.executable, "-m", "coverage", "combine"],
        check=False,
        capture_output=True,
        text=True,
    )

    # Check for .coverage.* files to see if we got multiprocess data
    coverage_files = list(Path.cwd().glob(".coverage.*"))
    if coverage_files:
        print(f"  Combined data from {len(coverage_files) + 1} processes")
    else:
        print("  Single process execution (no worker coverage files)")

    # Generate coverage reports (skip in append mode - user will run more tests)
    if is_append:
        lines = [
            "Coverage data appended",
            "=" * 70,
            "",
            "To see combined coverage after all test runs:",
            "  python -m coverage report",
            "  python -m coverage html",
            "",
        ]
        print_banner("", lines)
        return

    # Generate coverage reports for single run
    print_banner("Generating Coverage Reports", [])
    print()

    # Terminal report for all of src/
    print("Coverage summary (all of src/):")
    print("-" * 70)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "report",
            "--skip-empty",
        ],
        check=False,
    )
    print()

    # HTML report
    print("Generating detailed HTML report...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "html",
        ],
        check=False,
    )

    print()
    print("✓ HTML report: htmlcov/index.html")
    print()

    # Try to open HTML report in browser
    html_report = Path("htmlcov/index.html")
    if html_report.exists():
        try:
            webbrowser.open(str(html_report.absolute()))
            print("✓ Opened coverage report in browser")
        except Exception:
            print("  To view report, open: htmlcov/index.html")

    print()
    print("=" * 70)


def main() -> None:
    """Run the orchestrator server."""
    # Parse command-line arguments
    parser = build_arg_parser()
    args = parser.parse_args()

    # If coverage requested, re-launch through coverage
    if args.coverage or args.coverage_append:
        run_with_coverage(args)
        return

    # Build server URL
    url = f"http://{args.host}:{args.port}"

    # Get version from package metadata
    try:
        pkg_version = version("photo-stack-finder")
    except Exception:
        pkg_version = "unknown"

    # Detect Linux and auto-disable browser opening (doesn't work on WSL/Linux)
    is_linux = sys.platform.startswith("linux")
    open_browser_enabled = not args.no_browser and not is_linux

    # Print startup banner
    lines = [
        f"Photo Stack Finder v{pkg_version}",
        "=" * 70,
        f"Server starting at: {url}",
        "",
        "Features:",
        "  • Web-based configuration (no command-line arguments needed)",
        "  • Automatic pipeline execution",
        "  • Real-time progress tracking",
        "  • Integrated review interface",
        "",
    ]

    # Add platform-specific instructions
    if is_linux:
        lines.extend([
            "To access the web interface:",
            f"  Open your browser to: {url}",
            "",
        ])

    lines.append("Press Ctrl+C to stop the server")
    print_banner("", lines)

    # Open browser after a short delay (if enabled and not Linux)
    if open_browser_enabled:

        def open_browser() -> None:
            time.sleep(1.5)  # Wait for server to start
            try:
                webbrowser.open(url)
                print(f"✓ Opened browser to: {url}")
            except Exception as e:
                print(f"  Could not open browser: {e}")
                print(f"  Please open manually: {url}")

        threading.Thread(target=open_browser, daemon=True).start()

    # Start server
    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception:
        raise


if __name__ == "__main__":
    main()
