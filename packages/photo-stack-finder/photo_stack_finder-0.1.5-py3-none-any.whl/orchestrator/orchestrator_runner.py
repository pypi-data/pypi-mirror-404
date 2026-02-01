"""Async wrapper for PipelineOrchestrator for web interface integration.

This module provides a thread-safe async interface for running the orchestrator
in the background while exposing progress status to the web UI.
"""

from __future__ import annotations

import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NotRequired, TypedDict, TypeVar, cast

from orchestrator.build_pipeline import build_pipeline
from orchestrator.pipeline_orchestrator import PipelineOrchestrator
from utils import CONFIG

T = TypeVar("T")


def extract_typed(
    data: dict[str, Any],
    key: str,
    expected_type: type[T] | tuple[type, ...],
    default: T,
) -> T:
    """Extract value from dict with type validation.

    Consolidates the common pattern:
        value = data.get("key")
        if isinstance(value, ExpectedType):
            result = value
        else:
            result = default

    Into:
        result = extract_typed(data, "key", ExpectedType, default)

    Args:
        data: Dictionary to extract from
        key: Key to extract
        expected_type: Expected type or tuple of types
        default: Default value if key missing or wrong type

    Returns:
        Extracted value if present and correct type, otherwise default

    Example:
        # Before:
        state = exec_status.get("state")
        if isinstance(state, str):
            completed = state == "complete"

        # After:
        state = extract_typed(exec_status, "state", str, "")
        completed = state == "complete"
    """
    value = data.get(key, default)
    if isinstance(value, expected_type):
        return cast(T, value)  # Cast to satisfy mypy strict mode
    return default


@dataclass
class OrchestratorStatus:
    """Current orchestrator execution status for web UI."""

    running: bool = False
    completed: bool = False
    error: str | None = None
    message: str = ""
    # Progress tracking (populated from orchestrator.get_execution_status())
    current_stage: str | None = None
    stage_number: int = 0
    total_stages: int = 0
    stage_progress: float = 0.0
    overall_progress: float = 0.0


class PipelineStatusDict(TypedDict):
    """Typed dictionary for pipeline status returned to web UI.

    This structure is sent via websocket every 500ms to provide
    throttled status updates to the frontend.
    """

    running: bool
    completed: bool
    error: str | None
    message: str
    stage: str | None  # Current stage name
    stage_number: int  # 1-based stage number
    total_stages: int
    progress: float  # Current stage progress (0-100)
    overall_progress: float  # Overall pipeline progress (0-100)
    # Legacy fields for backward compatibility
    current_count: int
    total_count: int | None
    rate: float
    eta: str
    # Optional: stages list with statistics (only when orchestrator is running)
    stages: NotRequired[list[dict[str, str | int | bool | list[str] | None]]]
    # Optional: overall pipeline summary (only when completed)
    initial_photos: NotRequired[int]
    final_photos: NotRequired[int]
    reduction_pct: NotRequired[float]
    final_sequences: NotRequired[int]
    total_elapsed_seconds: NotRequired[float]
    average_throughput: NotRequired[float]  # items per second


class OrchestratorRunner:
    """Thread-safe orchestrator runner for background execution (singleton).

    Provides async interface for FastAPI integration while maintaining
    single-pipeline execution semantics.
    """

    # Class-level singleton instance
    _instance: OrchestratorRunner | None = None

    def __new__(cls) -> OrchestratorRunner:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _reset_singleton(cls) -> None:
        """Reset singleton instance for test isolation.

        WARNING: This should ONLY be called from test cleanup code.
        Never call this in production as it breaks singleton semantics
        and could allow multiple concurrent pipeline instances.
        """
        cls._instance = None

    def __init__(self) -> None:
        # Only initialize once (subsequent calls to __init__ are no-ops)
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.status = OrchestratorStatus()
        self.lock = threading.Lock()
        self.thread: threading.Thread | None = None
        self.orchestrator: PipelineOrchestrator | None = None
        self.stop_requested = False

    def start(self, config: dict[str, Any]) -> bool:
        """Start pipeline execution in background thread.

        Args:
            config: Configuration dictionary from web form

        Returns:
            True if started successfully, False if already running
        """
        with self.lock:
            if self.status.running:
                return False

            # Reset status
            self.status = OrchestratorStatus(running=True, message="Building pipeline...")
            self.stop_requested = False

            # Start background thread
            self.thread = threading.Thread(
                target=self._run_orchestrator,
                args=(config,),
                daemon=True,
            )
            self.thread.start()
            return True

    def stop(self) -> bool:
        """Request pipeline to stop.

        Returns:
            True if stop requested, False if no pipeline running
        """
        with self.lock:
            if not self.status.running:
                return False

            self.stop_requested = True
            self._update_status(
                running=False,
                error="Pipeline stopped by user",
                message="Stopped by user",
            )
            return True

    def get_stage(self, stage_name: str) -> Any:
        """Get a stage instance from the orchestrator.

        Args:
            stage_name: Name of the stage to retrieve

        Returns:
            Stage instance if orchestrator exists and has the stage

        Raises:
            KeyError: If stage not found
            RuntimeError: If orchestrator not initialized
        """
        with self.lock:
            if self.orchestrator is None:
                raise RuntimeError("Orchestrator not initialized")
            return self.orchestrator.get_stage(stage_name)

    def _extract_state_info(self, exec_status: dict[str, Any]) -> None:
        """Extract and update state information from execution status.

        Updates self.status.completed based on the 'state' field from execution status.
        Error details are set by the exception handler in _run_orchestrator.

        Args:
            exec_status: Execution status dictionary from orchestrator
        """
        state = extract_typed(exec_status, "state", str, "")
        if state:
            self.status.completed = state == "complete"
            # Error message is set by exception handler in _run_orchestrator with full details

    def _extract_stage_info(self, exec_status: dict[str, Any], stages_raw: list[dict[str, Any]]) -> None:
        """Extract and update stage information from execution status.

        Updates self.status.stage_number, self.status.total_stages, and
        self.status.current_stage based on the stages list.

        Args:
            exec_status: Execution status dictionary from orchestrator
            stages_raw: List of stage dictionaries
        """
        self.status.total_stages = len(stages_raw)

        # Find currently running stage
        current_stage_info: dict[str, Any] | None = None
        stage_number = 0

        for stage_item in stages_raw:
            if isinstance(stage_item, dict) and stage_item.get("status") == "running":
                current_stage_info = stage_item
                # Use the stage's 1-based position
                stage_number = extract_typed(stage_item, "position", int, 0)
                break

        # If no running stage found, use orchestrator's index
        if stage_number == 0 and self.orchestrator is not None:
            stage_number = self.orchestrator.current_stage_index

        self.status.stage_number = stage_number

        if current_stage_info:
            self.status.current_stage = extract_typed(current_stage_info, "name", str, None)

    def _extract_progress_info(self, exec_status: dict[str, Any]) -> tuple[int, int | None, float, str]:
        """Extract progress information from execution status.

        Args:
            exec_status: Execution status dictionary from orchestrator

        Returns:
            Tuple of (current_count, total_count, rate, eta)
        """
        current_progress = exec_status.get("current_progress")

        if isinstance(current_progress, dict):
            # Update stage progress percentage
            fraction = extract_typed(current_progress, "fraction_complete", (int, float), 0.0)
            self.status.stage_progress = float(fraction) * 100.0

            # Update status message
            self.status.message = extract_typed(current_progress, "status_message", str, "")

            # Extract legacy fields
            current_count = extract_typed(current_progress, "current_count", int, 0)
            total_count = extract_typed(current_progress, "total_count", int, None)
            rate = extract_typed(current_progress, "rate", (int, float), 0.0)
            eta = extract_typed(current_progress, "eta_display", str, "")

            return current_count, total_count, float(rate), eta
        # Fallback: use state_display as message
        self.status.message = extract_typed(exec_status, "state_display", str, "")
        return 0, None, 0.0, ""

    def _extract_summary_stats(self, result: PipelineStatusDict) -> None:
        """Add summary statistics to result if pipeline is completed.

        Modifies result dictionary in-place to add:
        - initial_photos
        - final_photos
        - reduction_pct
        - final_sequences
        - total_elapsed_seconds
        - average_throughput

        Args:
            result: Status dictionary to update
        """
        if not self.status.completed or self.orchestrator is None:
            return

        try:
            stages = self.orchestrator.graph.get_stages_in_order()
            if not stages:
                return

            # Get first stage's initial photo count
            first_stage = stages[0]
            initial_photos = first_stage.ref_photos_init

            # Get last stage's final counts
            last_stage = stages[-1]
            final_photos = last_stage.ref_photos_final
            final_sequences = last_stage.ref_seqs_final

            # Add to result if we have valid counts
            if initial_photos is not None and final_photos is not None:
                result["initial_photos"] = initial_photos
                result["final_photos"] = final_photos

                # Calculate reduction percentage
                if initial_photos > 0:
                    reduction = ((initial_photos - final_photos) / initial_photos) * 100
                    result["reduction_pct"] = reduction

            if final_sequences is not None:
                result["final_sequences"] = final_sequences

            # Calculate performance metrics from all stages
            total_elapsed = 0.0
            throughputs: list[float] = []
            for stage in stages:
                if stage.elapsed_seconds is not None:
                    total_elapsed += stage.elapsed_seconds
                if stage.throughput is not None:
                    throughputs.append(stage.throughput)

            if total_elapsed > 0:
                result["total_elapsed_seconds"] = total_elapsed

            if throughputs:
                # Average throughput across all stages
                result["average_throughput"] = sum(throughputs) / len(throughputs)
        except Exception:
            # If we can't get statistics, just omit them (don't fail status request)
            pass

    def get_status(self) -> PipelineStatusDict:
        """Get current pipeline status for web UI.

        Returns:
            Status dictionary matching FastAPI response format
        """
        with self.lock:
            # Initialize legacy fields (always present in response)
            current_count = 0
            total_count = None
            rate = 0.0
            eta = ""

            # If orchestrator exists, get its detailed status (even after completion)
            # This ensures stages list is populated even when pipeline finishes quickly
            if self.orchestrator is not None:
                exec_status = self.orchestrator.get_execution_status()

                # Extract state information (completed, error)
                self._extract_state_info(exec_status)

                # Extract stage information (stage_number, total_stages, current_stage)
                stages_raw = extract_typed(exec_status, "stages", list, [])
                if stages_raw:
                    self._extract_stage_info(exec_status, stages_raw)

                # Extract progress information (stage_progress, message, legacy fields)
                current_count, total_count, rate, eta = self._extract_progress_info(exec_status)

                # Calculate overall progress from pipeline_percentage
                pipeline_perc_str = extract_typed(exec_status, "pipeline_percentage", str, "0%")
                try:
                    self.status.overall_progress = float(pipeline_perc_str.rstrip("%"))
                except ValueError:
                    self.status.overall_progress = 0.0

            # Build base status dict (PipelineStatusDict)
            result: PipelineStatusDict = {
                "running": self.status.running,
                "completed": self.status.completed,
                "error": self.status.error,
                "message": self.status.message,
                "stage": self.status.current_stage,
                "stage_number": self.status.stage_number,
                "total_stages": self.status.total_stages,
                "progress": self.status.stage_progress,
                "overall_progress": self.status.overall_progress,
                # Legacy fields for backward compatibility (extracted from current_progress)
                "current_count": current_count,
                "total_count": total_count,
                "rate": rate,
                "eta": eta,
            }

            # Include stages list with statistics if orchestrator is available
            # Always include stages list (both during execution and after completion)
            if self.orchestrator is not None:
                stages_list = extract_typed(exec_status, "stages", list, None)
                if stages_list is not None:
                    result["stages"] = stages_list

            # Add overall summary statistics if pipeline is completed
            self._extract_summary_stats(result)

            return result

    def _update_status(self, **kwargs: Any) -> None:
        """Update status (thread-safe).

        Args:
            **kwargs: Status fields to update
        """
        with self.lock:
            for key, value in kwargs.items():
                setattr(self.status, key, value)

    def _apply_config(self, config: dict[str, Any]) -> None:
        """Apply configuration to CONFIG object.

        Args:
            config: Configuration dictionary from web form
        """
        # Update CONFIG with provided values
        if "source_dir" in config:
            CONFIG.paths.SOURCE_DIR = str(Path(config["source_dir"]))

        if config.get("work_dir"):
            CONFIG.paths.WORK_DIR = str(Path(config["work_dir"]))
        else:
            # Default work_dir if not provided
            source_path = Path(CONFIG.paths.SOURCE_DIR)
            CONFIG.paths.WORK_DIR = str(source_path.parent / "photo_dedup")

        # Update processing options
        if config.get("max_workers"):
            CONFIG.processing.MAX_WORKERS = config["max_workers"]

        if config.get("batch_size"):
            CONFIG.processing.BATCH_SIZE = config["batch_size"]

        if "debug_mode" in config:
            CONFIG.processing.DEBUG_MODE = config["debug_mode"]

        # Update gate thresholds if provided
        if config.get("gate_thresholds"):
            assert CONFIG.processing.GATE_THRESHOLDS is not None
            CONFIG.processing.GATE_THRESHOLDS.update(config["gate_thresholds"])

        # Update benchmarks enablement if provided
        if "enable_benchmarks" in config:
            CONFIG.benchmark.ENABLED = config["enable_benchmarks"]

    def _run_orchestrator(self, config: dict[str, Any]) -> None:
        """Run the orchestrator (executes in background thread).

        Args:
            config: Configuration dictionary
        """
        try:
            # Apply configuration
            self._update_status(message="Applying configuration...")
            self._apply_config(config)

            # Build pipeline graph
            self._update_status(message="Building pipeline graph...")
            source_dir = Path(CONFIG.paths.SOURCE_DIR)
            self.orchestrator = build_pipeline(source_dir)

            total_stages = len(self.orchestrator.graph.get_stages_in_order())
            self._update_status(
                message="Pipeline graph validated successfully",
                total_stages=total_stages,
            )

            # Execute pipeline
            self._update_status(message="Starting pipeline execution...")
            self.orchestrator.execute()

            # Pipeline complete
            self._update_status(
                running=False,
                completed=True,
                message="Pipeline completed successfully",
                overall_progress=100.0,
            )

        except Exception as e:
            # Handle errors
            error_msg = f"{type(e).__name__}: {e!s}\n{traceback.format_exc()}"
            self._update_status(
                running=False,
                error=error_msg,
                message=f"Pipeline failed: {e!s}",
            )


def get_runner() -> OrchestratorRunner:
    """Get or create the singleton orchestrator runner.

    Returns:
        Singleton OrchestratorRunner instance
    """
    return OrchestratorRunner()
