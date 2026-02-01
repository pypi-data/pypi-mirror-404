"""Pipeline orchestrator for executing validated stage graphs.

The orchestrator is a minimal coordinator that:
- Executes stages in topological order (computed by PipelineGraph)
- Tracks execution state (ready, running, complete, failed)
- Provides formatted status for UI polling (backend-heavy pattern)
- Halts immediately on first stage failure (fail-fast)
- Has zero domain knowledge (just calls stage.run())

All formatting happens in the backend - the UI just displays values.

Architecture:
- Orchestrator receives validated graph from PipelineBuilder
- Calls stage.run() for each stage in dependency order
- Tracks current/completed/failed stages for status queries
- Formats all data for UI consumption (numbers, icons, CSS classes)
- Never modifies graph or stages (read-only after construction)

Usage:
    # Created automatically by PipelineBuilder.__exit__
    orchestrator = builder.orchestrator

    # Execute pipeline
    orchestrator.execute()

    # Query status (for UI polling)
    status = orchestrator.get_execution_status()
"""

from __future__ import annotations

import time
import traceback
from collections.abc import Callable

from utils import BasePipelineStage, PhotoFile, PipelineGraph, ProgressInfo, format_seconds_weighted, get_logger

logger = get_logger()


class PipelineOrchestrator:
    """Minimal coordinator that executes stages in topological order.

    The orchestrator has zero domain knowledge about stages - it just
    executes them in dependency order and tracks execution state.

    All formatting for UI display happens in the orchestrator (backend-heavy
    pattern) - the frontend just renders the pre-formatted strings.

    Attributes:
        graph: The validated PipelineGraph containing all stages
        current_stage_index: Index of currently executing stage (1-based, 0 = not started)
        current_phase: Current execution phase (cache_load, prepare, compute, finalise, save)
        failed: True if a stage has failed
        previous_photos_final: Running count of photos from previous stage (for statistics)
        previous_seqs_final: Running count of sequences from previous stage (for statistics)
    """

    get_photofiles: Callable[[], dict[int, PhotoFile]]

    def __init__(self, graph: PipelineGraph, should_stop: Callable[[], bool] | None = None) -> None:
        """Initialize orchestrator with validated graph.

        Args:
            graph: Validated PipelineGraph from PipelineBuilder
            should_stop: Optional callback that returns True when execution should stop

        Note:
            The graph must have been validated (cycles checked, ports connected)
            and execution order must have been computed before passing to orchestrator.
        """
        self.graph = graph
        self.current_stage_index: int = 0
        self.current_phase: str = ""
        self.failed: bool = False
        self.should_stop = should_stop

        # Track running counts from previous stage to support statistics display
        # for cached stages (which don't have init counts populated)
        self.previous_photos_final: int | None = None
        self.previous_seqs_final: int | None = None

    # Stage Index Helpers - Centralized 1-based indexing logic
    # =========================================================
    # Stage IDs are 1-based (1, 2, 3, ..., N)
    # current_stage_index semantics:
    #   0 = pipeline not started
    #   1..N = stage with that ID is currently running
    #   N+1 = all stages complete

    def _get_total_stages(self) -> int:
        """Get total number of stages in pipeline.

        Returns:
            Number of stages (same as max stage_id)
        """
        return len(self.graph.nodes)

    def _is_pipeline_not_started(self) -> bool:
        """Check if pipeline has not started yet.

        Returns:
            True if no stages have started (current_stage_index == 0)
        """
        return self.current_stage_index == 0

    def _is_pipeline_complete(self) -> bool:
        """Check if all pipeline stages have completed.

        Returns:
            True if current_stage_index > total stages (last stage incremented index)
        """
        return self.current_stage_index > self._get_total_stages()

    def _is_stage_complete(self, stage_id: int) -> bool:
        """Check if a stage has completed execution.

        Args:
            stage_id: 1-based stage ID to check

        Returns:
            True if stage_id < current_stage_index (stage finished and index advanced)
        """
        return stage_id < self.current_stage_index

    def _is_stage_running(self, stage_id: int) -> bool:
        """Check if a stage is currently executing.

        Args:
            stage_id: 1-based stage ID to check

        Returns:
            True if stage_id == current_stage_index (stage started but not finished)
        """
        return stage_id == self.current_stage_index

    def _is_stage_pending(self, stage_id: int) -> bool:
        """Check if a stage has not started yet.

        Args:
            stage_id: 1-based stage ID to check

        Returns:
            True if stage_id > current_stage_index (stage hasn't started)
        """
        return stage_id > self.current_stage_index

    # Stage Index Mutations - Centralized modification operations
    # ============================================================

    def _mark_stage_started(self, stage_id: int) -> None:
        """Mark a stage as started by setting current_stage_index to its ID.

        Args:
            stage_id: 1-based stage ID that is starting execution
        """
        logger.info(f"Stage {stage_id} starting (current_stage_index: {self.current_stage_index} -> {stage_id})")
        self.current_stage_index = stage_id

    def _mark_stage_completed(self, stage_id: int) -> None:
        """Mark a stage as completed by incrementing current_stage_index.

        Args:
            stage_id: 1-based stage ID that just completed execution
        """
        new_index = stage_id + 1
        logger.info(f"Stage {stage_id} completed (current_stage_index: {self.current_stage_index} -> {new_index})")
        self.current_stage_index = new_index

    def execute(self) -> None:
        """Execute all stages in dependency order with graceful cancellation support.

        Executes each stage by calling stage.run(). Stages are executed
        sequentially in topological order (dependencies run before dependents).

        The orchestrator supports graceful cancellation via the should_stop callback.
        Before/after each stage, it checks if cancellation was requested and halts
        cleanly if so. Within stages, KeyboardInterrupt is caught to handle SIGINT.

        The orchestrator is fail-fast: execution halts immediately on the
        first stage failure. The `self.failed` flag is set for status queries.

        Raises:
            Exception: Any exception raised by a stage (after logging)

        Note:
            Stages must implement their own caching and dependency checking.
            The orchestrator just calls run() and doesn't manage caching.
        """
        # Get stages in topological order (dependencies first)
        stages = self.graph.get_stages_in_order()

        for stage in stages:
            # Check for stop request BEFORE starting each stage
            if self.should_stop and self.should_stop():
                logger.info("Pipeline execution cancelled by user request")
                return

            # Mark stage as started (sets current_stage_index to stage's 1-based ID)
            assert stage.stage_id is not None, f"Stage {stage.stage_name} missing stage_id"
            self._mark_stage_started(stage.stage_id)
            self.current_phase = ""

            try:
                # Set phase callback to track execution phase
                stage._phase_callback = self._update_phase

                # Call stage's run method
                # Note: Stages handle their own caching and dependency checking
                #
                # KNOWN ISSUE (will be fixed in Phase 2):
                # Current PipelineStage.run() signature requires (prep, args) arguments.
                # The new orchestrator architecture is designed for port-based stages
                # where run() takes no arguments (inputs come from ports).
                # This mypy error will be resolved in Phase 2 when all stages are migrated
                # to the new port-based interface.
                stage.run()

                # Check for stop request AFTER stage completes
                # (allows current stage to finish, but prevents starting next stage)
                if self.should_stop and self.should_stop():
                    logger.info("Pipeline execution cancelled by user request")
                    return

                # Mark stage as completed (increments current_stage_index)
                self._mark_stage_completed(stage.stage_id)
                self.current_phase = ""

                # Clear progress tracker AFTER marking complete
                # (keeps progress visible through finalise() and save)
                stage._progress_tracker = None

                # Log completion with summary
                self._log_stage_completion(stage)

            except Exception as e:
                # Record failure and halt execution (fail-fast)
                self.failed = True
                logger.error(f"Stage '{stage.stage_name}' failed: {e} + {traceback.format_exc()}")
                raise  # Re-raise to halt pipeline  # Re-raise to halt pipeline  # Re-raise to halt pipeline

    def _update_phase(self, phase: str) -> None:
        """Update current execution phase (called by stage via phase callback).

        Args:
            phase: Current phase name (cache_load, prepare, compute, finalise, save)
        """
        self.current_phase = phase

    def _log_stage_completion(self, stage: BasePipelineStage) -> None:
        """Log stage completion with summary statistics.

        Displays final reference counts and percentage reduction achieved by the stage.
        Omits sequence counts in early stages where they don't exist.
        Shows execution time if stage was computed (not loaded from cache).

        Uses orchestrator's tracked counts from previous stage as init counts.
        This works for both cached stages (where stage.ref_photos_init is None)
        and computed stages, providing a single source of truth.

        Args:
            stage: The stage that just completed
        """
        # Build completion message with summary
        message_parts = [f"Stage '{stage.stage_name}' complete:"]

        # Add execution time if stage was computed (progress tracker exists)
        # Progress tracker is only created during compute phase, so its existence
        # indicates the stage was not loaded from cache
        if hasattr(stage, "_progress_tracker") and stage._progress_tracker is not None:
            elapsed = time.time() - stage._progress_tracker.start_time
            message_parts.append(f"{format_seconds_weighted(elapsed)}")

        # Add photo counts with reduction percentage if available
        if stage.ref_photos_final is not None:
            photo_msg = f"{stage.ref_photos_final} photos"

            # Calculate percentage reduction using orchestrator's tracked count from previous stage
            if self.previous_photos_final is not None and self.previous_photos_final > 0:
                reduction = ((self.previous_photos_final - stage.ref_photos_final) / self.previous_photos_final) * 100
                photo_msg += f" ({reduction:.1f}% reduction)"

            message_parts.append(photo_msg)

        # Add sequence counts with reduction percentage if available
        # Omit if None or 0 (early stages don't have sequences yet)
        if stage.ref_seqs_final is not None and stage.ref_seqs_final > 0:
            seq_msg = f"{stage.ref_seqs_final} sequences"

            # Calculate percentage reduction using orchestrator's tracked count from previous stage
            if self.previous_seqs_final is not None and self.previous_seqs_final > 0:
                reduction = ((self.previous_seqs_final - stage.ref_seqs_final) / self.previous_seqs_final) * 100
                seq_msg += f" ({reduction:.1f}% reduction)"

            message_parts.append(seq_msg)

        # Update tracked counts for next stage (single source of truth)
        self.previous_photos_final = stage.ref_photos_final
        self.previous_seqs_final = stage.ref_seqs_final

        # Add review data summary if available
        review_type = stage.needs_review()
        if review_type == "photos" and len(stage.identical_review_result) > 0:
            message_parts.append(f"Found {len(stage.identical_review_result)} identical groups")
        elif review_type == "sequences" and len(stage.sequence_review_result) > 0:
            message_parts.append(f"Found {len(stage.sequence_review_result)} sequence groups")

        # Add cache size if available
        if stage.path.exists():
            cache_size_mb = stage.path.stat().st_size / (1024 * 1024)
            message_parts.append(f"Cache saved ({cache_size_mb:.1f} MB)")

        logger.info(" | ".join(message_parts))

    # ========================================================================
    # UI Query Methods (Backend-Heavy Pattern)
    # ========================================================================
    #
    # All methods below return fully formatted data ready for UI display.
    # The UI just renders the strings, numbers, and CSS classes - no
    # formatting logic in JavaScript.

    # FIXME: Use a pydantic structure rather than a complicated dict.
    def get_execution_status(
        self,
    ) -> dict[
        str,
        str | dict[str, str] | list[dict[str, str | int | bool | list[str] | None]] | None,
    ]:
        """Get complete execution state with all formatting done (for UI polling).

        Returns fully formatted execution status including:
        - Pipeline state (ready/running/complete/failed)
        - Overall progress (stages completed, percentage)
        - Current execution phase (cache_load, prepare, compute, finalise, save)
        - Per-stage status (pending/running/complete/failed with icons)
        - Current stage progress (if running)
        - Stage statistics (formatted for display)

        All strings, numbers, and CSS classes are formatted in the backend.
        The UI just renders the values without any formatting logic.

        Returns:
            Dictionary with fully formatted execution status:
            {
                "state": "running",  # "ready" | "running" | "complete" | "failed"
                "state_display": "Running...",  # Human-readable state
                "pipeline_progress": "2 / 5 stages",  # Formatted progress
                "pipeline_percentage": "40%",  # Percentage as string
                "pipeline_bar_width": "40%",  # CSS width property
                "current_phase": "compute",  # Current execution phase (or "" if not running)
                "stages": [  # List of stages with formatted status
                    {
                        "position": 1,
                        "name": "discover_files",
                        "display_name": "Discover Files",
                        "status": "complete",
                        "status_icon": "check",
                        "status_class": "stage-complete",
                        "has_review": False
                    },
                    ...
                ],
                "current_progress": {  # Progress of current stage (if running)
                    "fraction_complete": 0.73,
                    "percentage_display": "73%",
                    "progress_bar_width": "73%",
                    "status_message": "Processing photos",
                    "items_display": "11,123 / 15,234",
                    "rate_display": "1,250 items/sec",
                    "eta_display": "3 seconds",
                    "stage_display": "Compute Identical"
                } or None
            }
        """
        progress = self.get_current_progress()

        # Calculate overall pipeline progress
        # Number of completed stages = current_stage_index - 1 (since index points to running stage)
        # Exception: when pipeline complete, current_stage_index = total + 1, so we clamp to total
        total = self._get_total_stages()
        completed = min(max(0, self.current_stage_index - 1), total)
        pipeline_percentage = int((completed / total) * 100) if total > 0 else 0

        return {
            "state": self._get_state(),  # "ready", "running", "complete", "failed"
            "state_display": self._format_state_display(),  # "Running...", "Complete ✓"
            # Overall pipeline progress (formatted)
            "pipeline_progress": f"{completed} / {total} stages",
            "pipeline_percentage": f"{pipeline_percentage}%",
            "pipeline_bar_width": f"{pipeline_percentage}%",
            # Current phase (cache_load, prepare, compute, finalise, save)
            "current_phase": self.current_phase,
            # Stage list with status and statistics
            "stages": self._format_stage_list(),
            # Current stage progress (if running)
            "current_progress": progress.__dict__ if progress else None,
        }

    def get_current_progress(self) -> ProgressInfo | None:
        """Get progress of currently running stage.

        Returns:
            ProgressInfo with formatted progress data, or None if no stage is running

        Note:
            Requires stages to implement get_progress() method (Phase 1.6)
        """
        if self._is_pipeline_not_started():
            return None  # Pipeline not started

        if self._is_pipeline_complete():
            return None  # All stages complete

        stages = self.graph.get_stages_in_order()

        # Find stage by matching stage_id (1-based) with current_stage_index
        current_stage = next(
            (s for s in stages if s.stage_id == self.current_stage_index),
            None,
        )

        if current_stage is None:
            return None  # Stage not found

        return current_stage.get_progress()

    def _get_state(self) -> str:
        """Get current pipeline state.

        Returns:
            One of: "ready", "running", "complete", "failed"
        """
        if self.failed:
            return "failed"

        if self._is_pipeline_complete():
            return "complete"

        if not self._is_pipeline_not_started() or self.current_phase:
            return "running"

        return "ready"

    def _format_state_display(self) -> str:
        """Format state for display.

        Returns:
            Human-readable state with emoji/symbol:
            - "Ready to execute"
            - "Running..."
            - "Complete ✓"
            - "Failed ✗"
        """
        state_display = {
            "ready": "Ready to execute",
            "running": "Running...",
            "complete": "Complete ✓",
            "failed": "Failed ✗",
        }
        return state_display[self._get_state()]

    def _format_stage_list(
        self,
    ) -> list[dict[str, str | int | bool | list[str] | None]]:
        """Format stage list with status indicators and statistics.

        Returns list of stages in execution order with:
        - Position (1-indexed)
        - Name and display name
        - Status (pending/running/complete/failed)
        - Status icon and CSS class
        - Whether stage has review data
        - Statistics (photo/sequence counts and reduction percentages)

        Returns:
            List of formatted stage dictionaries for UI rendering
        """
        stages = self.graph.get_stages_in_order()
        result: list[dict[str, str | int | bool | list[str] | None]] = []

        # Track previous stage's final counts for statistics calculation
        prev_photos_final: int | None = None
        prev_seqs_final: int | None = None

        for stage in stages:
            # Use stage's 1-based ID for status comparison
            assert stage.stage_id is not None, f"Stage {stage.stage_name} missing stage_id"
            stage_id = stage.stage_id

            # Determine status using centralized helper methods
            status: str
            icon: str
            css_class: str

            if self.failed and self._is_stage_running(stage_id):
                # Current stage failed
                status, icon, css_class = "failed", "X", "stage-failed"
            elif self._is_stage_complete(stage_id):
                # Stage completed
                status, icon, css_class = "complete", "check", "stage-complete"
            elif self._is_stage_running(stage_id):
                # Stage currently running
                status, icon, css_class = "running", "play", "stage-running"
            else:
                # Stage pending (not started yet)
                status, icon, css_class = "pending", " ", "stage-pending"

            # Build statistics strings for completed stages
            stats_parts: list[str] = []

            if self._is_stage_complete(stage_id):
                # Stage completed - calculate statistics
                # For photos
                if stage.ref_photos_final is not None:
                    photo_str = f"{stage.ref_photos_final:,} photos"
                    if prev_photos_final is not None and prev_photos_final > 0:
                        reduction = ((prev_photos_final - stage.ref_photos_final) / prev_photos_final) * 100
                        photo_str += f" ({reduction:.1f}% reduction)"
                    stats_parts.append(photo_str)

                # For sequences (omit if None or 0)
                if stage.ref_seqs_final is not None and stage.ref_seqs_final > 0:
                    seq_str = f"{stage.ref_seqs_final:,} sequences"
                    if prev_seqs_final is not None and prev_seqs_final > 0:
                        reduction = ((prev_seqs_final - stage.ref_seqs_final) / prev_seqs_final) * 100
                        seq_str += f" ({reduction:.1f}% reduction)"
                    stats_parts.append(seq_str)

                # Add performance metrics (elapsed time and throughput)
                if stage.elapsed_seconds is not None:
                    minutes = int(stage.elapsed_seconds // 60)
                    seconds = int(stage.elapsed_seconds % 60)
                    time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                    stats_parts.append(time_str)

                if stage.throughput is not None:
                    stats_parts.append(f"{stage.throughput:.0f} items/sec")

                # Update tracking for next stage
                prev_photos_final = stage.ref_photos_final
                prev_seqs_final = stage.ref_seqs_final

            result.append(
                {
                    "position": stage_id,  # Already 1-based from graph
                    "name": stage.stage_name,
                    "display_name": stage.stage_name,  # Frontend expects display_name
                    "status": status,
                    "status_icon": icon,
                    "status_class": css_class,
                    # Only show review data if stage completed (stage_id < current_stage_index)
                    "has_review": stage_id < self.current_stage_index and stage.has_review_data(),
                    # Statistics (formatted string, empty for pending/running stages)
                    "statistics": " | ".join(stats_parts) if stats_parts else None,
                }
            )

        return result

    # ========================================================================
    # Utility Methods (for Web UI)
    # ========================================================================

    def has_review_data(self, stage_name: str) -> bool:
        """Check if stage has review data in current run.

        Args:
            stage_name: Name of the stage

        Returns:
            True if stage completed in current run AND has reviewable data available

        Raises:
            KeyError: If stage name not found in graph
        """
        # Find stage by name
        stages = self.graph.get_stages_in_order()
        found_stage = next((s for s in stages if s.stage_name == stage_name), None)

        if found_stage is None:
            raise KeyError(f"Stage '{stage_name}' not found in graph")

        assert found_stage.stage_id is not None, f"Stage {stage_name} missing stage_id"

        # Must have completed in current run (stage_id < current_stage_index)
        if found_stage.stage_id >= self.current_stage_index:
            return False

        return found_stage.has_review_data()

    def get_stage(self, stage_name: str) -> BasePipelineStage:
        """Get stage instance (for review UI).

        Args:
            stage_name: Name of the stage

        Returns:
            BasePipelineStage instance

        Raises:
            KeyError: If stage name not found in graph
        """
        return self.graph.get_all_stages()[stage_name]
