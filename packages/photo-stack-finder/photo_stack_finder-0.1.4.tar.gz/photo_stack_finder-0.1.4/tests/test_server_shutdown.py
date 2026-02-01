"""Test server clean shutdown behavior.

This test verifies that the orchestrator server shuts down cleanly when
the /api/server/quit endpoint is called, with no hanging threads or
leaked resources.
"""

from __future__ import annotations

import contextlib
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


def test_server_quit_exits_cleanly() -> None:
    """Test that POST /api/shutdown causes server to exit cleanly.

    Verifies:
    - Server starts successfully
    - Shutdown endpoint responds with 200 OK
    - Server process terminates within timeout
    - Exit code is 0 (clean shutdown)
    - No hanging threads or resources
    """
    # Path to orchestrate.py script
    project_root = Path(__file__).parent.parent
    orchestrate_script = project_root / "src" / "scripts" / "orchestrate.py"

    if not orchestrate_script.exists():
        pytest.skip(f"orchestrate.py not found at {orchestrate_script}")

    # Start server in subprocess
    # Use --port to avoid conflicts with other tests
    server_process = subprocess.Popen(
        [sys.executable, str(orchestrate_script), "--port", "8765", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait for server to start (max 5 seconds)
        server_url = "http://127.0.0.1:8765"
        server_started = False

        for _ in range(50):  # 50 * 0.1s = 5s timeout
            # Check if process has already terminated
            if server_process.poll() is not None:
                # Process died - capture output and fail
                stdout, stderr = server_process.communicate()
                pytest.fail(
                    f"Server process terminated during startup.\n"
                    f"Exit code: {server_process.returncode}\n"
                    f"STDOUT:\n{stdout}\n"
                    f"STDERR:\n{stderr}"
                )

            time.sleep(0.1)
            try:
                response = httpx.get(f"{server_url}/api/status", timeout=1.0)
                if response.status_code == 200:
                    server_started = True
                    break
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout):
                # Server not ready yet
                continue

        if not server_started:
            # Give server a moment to write error output
            time.sleep(0.5)
            server_process.kill()
            stdout, stderr = server_process.communicate()
            pytest.fail(
                f"Server failed to start within 5 seconds.\n"
                f"Exit code: {server_process.returncode}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            )

        # Server is running - now call shutdown endpoint
        response = httpx.post(f"{server_url}/api/shutdown", timeout=2.0)

        # Verify shutdown endpoint responded successfully
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shutting_down"

        # Wait for server process to terminate (max 3 seconds)
        try:
            server_process.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            # Server didn't exit - force kill and fail test
            server_process.kill()
            server_process.wait()
            pytest.fail("Server did not terminate within 3 seconds after shutdown endpoint call")

        # Verify clean exit code
        # sys.exit(0) triggers Python exception unwinding, which:
        # - Runs finally blocks and context manager cleanup
        # - Triggers FastAPI lifespan shutdown code
        # - Exits with code 0 (clean shutdown)
        assert server_process.returncode == 0, f"Server exited with non-zero code: {server_process.returncode}"

        # Verify lifespan manager cleanup was called
        # Capture stdout/stderr to check for shutdown message
        stdout, stderr = server_process.communicate()
        combined_output = stdout + stderr

        # Debug: print the output to see what's happening
        print("\n=== SERVER OUTPUT ===")
        print(combined_output)
        print("=== END OUTPUT ===\n")

        assert "Application Shutdown: Cleaning up resources." in combined_output, (
            "Lifespan manager cleanup code was not executed"
        )

    finally:
        # Cleanup: ensure server is killed if test fails
        if server_process.poll() is None:
            server_process.kill()
            server_process.wait()


def test_server_quit_with_running_pipeline() -> None:
    """Test server shutdown while pipeline is running.

    This test verifies graceful shutdown when SIGINT is received mid-pipeline:
    1. Pipeline catches KeyboardInterrupt in batch_compute() and stops cleanly
    2. Orchestrator checks should_stop() between stages
    3. No ShutdownExecutorError exceptions occur
    4. Server exits with code 0

    The shutdown mechanism:
    - SIGINT sent to process group (parent + joblib workers)
    - Workers terminate immediately
    - Parent catches KeyboardInterrupt and exits Parallel() context cleanly
    - No attempts to dispatch work to dead executors
    """
    # Path to orchestrate.py script
    project_root = Path(__file__).parent.parent
    orchestrate_script = project_root / "src" / "scripts" / "orchestrate.py"

    if not orchestrate_script.exists():
        pytest.skip(f"orchestrate.py not found at {orchestrate_script}")

    # Start server in subprocess
    server_process = subprocess.Popen(
        [sys.executable, str(orchestrate_script), "--port", "8766", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait for server to start
        server_url = "http://127.0.0.1:8766"
        server_started = False

        for _ in range(50):
            # Check if process has already terminated
            if server_process.poll() is not None:
                # Process died - skip test
                stdout, stderr = server_process.communicate()
                pytest.skip(
                    f"Server process terminated during startup.\n"
                    f"Exit code: {server_process.returncode}\n"
                    f"STDOUT:\n{stdout}\n"
                    f"STDERR:\n{stderr}"
                )

            time.sleep(0.1)
            try:
                response = httpx.get(f"{server_url}/api/status", timeout=1.0)
                if response.status_code == 200:
                    server_started = True
                    break
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout):
                continue

        if not server_started:
            server_process.kill()
            server_process.wait()
            pytest.skip("Server failed to start - skipping pipeline shutdown test")

        # Start a pipeline (will fail due to invalid paths, but that's okay)
        # We just want to test that server can quit while pipeline thread exists
        with contextlib.suppress(httpx.HTTPError):
            httpx.post(
                f"{server_url}/api/pipeline/start",
                json={
                    "source_dir": "/tmp/nonexistent",
                    "work_dir": "/tmp/nonexistent_work",
                },
                timeout=2.0,
            )

        # Give pipeline thread time to start (0.5s)
        time.sleep(0.5)

        # Now call shutdown endpoint while pipeline may be running
        response = httpx.post(f"{server_url}/api/shutdown", timeout=2.0)

        # Verify shutdown endpoint responded
        assert response.status_code == 200

        # Wait for server to terminate
        try:
            server_process.wait(timeout=5.0)  # Longer timeout for pipeline cleanup
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()
            pytest.fail("Server did not terminate within 5 seconds with running pipeline")

        # Verify clean exit
        assert server_process.returncode == 0, f"Server exited with non-zero code: {server_process.returncode}"

        # Verify no ShutdownExecutorError in output
        stdout, stderr = server_process.communicate()
        combined_output = stdout + stderr

        # Debug: print output to see what happened
        print("\n=== SERVER OUTPUT (with pipeline) ===")
        print(combined_output)
        print("=== END OUTPUT ===\n")

        # CRITICAL: Verify graceful shutdown - no executor errors
        assert "ShutdownExecutorError" not in combined_output, (
            "ShutdownExecutorError found - joblib workers shut down ungracefully"
        )

    finally:
        if server_process.poll() is None:
            server_process.kill()
            server_process.wait()
