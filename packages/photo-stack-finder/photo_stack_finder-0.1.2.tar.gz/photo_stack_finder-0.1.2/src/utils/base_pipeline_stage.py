from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from .base_ports import StageProtocol
from .models import IdenticalGroup, ReviewType, SequenceGroup
from .ports import InputPort
from .progress import ProgressInfo, ProgressTracker


class BasePipelineStage(ABC, StageProtocol):
    """Base class for polymorphic PipelineStage for use in lists of pipeline stages."""

    path: Path
    stage_name: str
    stage_id: int | None
    description: str
    sequence_review_result: list[SequenceGroup]
    identical_review_result: list[IdenticalGroup]
    _progress_tracker: ProgressTracker | None
    _phase_callback: Callable[[str], None] | None  # Called by run() to notify phase changes
    ref_photos_init: int | None
    ref_photos_final: int | None
    ref_seqs_init: int | None
    ref_seqs_final: int | None
    total_photos: int | None  # Total photos including duplicates (invariant - should never change)

    def __init__(
        self,
        path: Path,
        stage_name: str,
    ):
        """Initialize pipeline stage with output path and name.

        Args:
            path: Path where stage results will be cached
            stage_name: Human-readable name for progress tracking
        """
        self.path = path
        self.stage_name = stage_name
        self.stage_id = None  # Set by PipelineGraph.compute_execution_order()
        self.description = ""  # Override in subclasses for UI tooltips
        self.sequence_review_result = []  # Pre-computed sequence review data (built during run())
        self.identical_review_result = []  # Pre-computed identical review data (built during run())  # Pre-computed identical review data (built during run())
        self._progress_tracker = None
        self._phase_callback = None  # Set by orchestrator before calling run()

        self.ref_photos_init = None
        self.ref_photos_final = None
        self.ref_seqs_init = None
        self.ref_seqs_final = None
        self.total_photos = None

        # Performance metrics (set after stage completes)
        self.elapsed_seconds: float | None = None
        self.throughput: float | None = None  # items per second

    def get_ref_photo_count(self) -> int | None:
        """Get count of reference photos after stage has run.

        Returns:
            Number of reference photos after stage has run (None if there are none or the stage has not run).
        """
        return self.ref_photos_final

    def get_ref_sequence_count(self) -> int | None:
        """Get count of reference sequences after stage has run.

        Returns:
            Number of reference sequences after stage has run (None if there are none or the stage has not run).
        """
        return self.ref_seqs_final

    @abstractmethod
    def run(self) -> None:
        """Execute pipeline stage - must be implemented by subclass."""
        ...

    @abstractmethod
    def finalise(self) -> None:
        """Hook to call at the end of run - must be implemented by subclass."""
        ...

    @abstractmethod
    def needs_review(self) -> ReviewType:
        """Discover what type of review this stage produces.

        This allows the orchestrator to dynamically discover which stages
        produce reviewable output without hard-coding stage names.

        Returns:
            - "none": No reviewable output (default)
            - "photos": Produces photo groups (byte-identical duplicates)
            - "sequences": Produces sequence groups (similar sequences)
        """
        ...

    @abstractmethod
    def has_review_data(self) -> bool:
        """Check if review data is ACTUALLY available for this stage.

        Checks three conditions:
        1. Stage has completed (cache file exists)
        2. Stage is capable of producing review data (needs_review() != "none")
        3. Review data actually exists (review lists not empty)

        Returns:
            True if stage has completed and has reviewable data available
        """
        ...

    def get_progress(self) -> ProgressInfo | None:
        """Get current progress information for UI polling.

        Returns:
            ProgressInfo with formatted progress data if stage is currently executing,
            None if stage is not running

        Note:
            This method is called by the orchestrator during execution to poll
            progress for UI updates.
        """
        # Direct access with combined check for type narrowing
        if self._progress_tracker is None:
            return None
        return self._progress_tracker.get_snapshot()

    def get_cache_timestamp(self) -> float:
        """Get the modification time of the cache file.

        Returns:
            Cache file's mtime (seconds since epoch), or raises RuntimeError if cache doesn't exist
        """
        if self.path.exists():
            mtime = self.path.stat().st_mtime
            if mtime is None:
                raise RuntimeError("mtime is None for existing file")
            return mtime
        raise RuntimeError(f"{self.stage_name} get_cache_timestamp called before cache file has been created")

    def _cache_is_valid(self) -> bool:
        """Check if cache exists and is newer than all input port dependencies.

        Uses isinstance() check on __dict__ items to avoid triggering property getters
        and causing errors when stages haven't run yet.

        Returns:
            True if cache is valid and can be used, False otherwise
        """
        if not self.path.exists():
            return False

        cache_mtime = self.get_cache_timestamp()

        # Check if any input port dependency is newer than our cache
        # Use __dict__ to avoid triggering property getters
        for attr_value in self.__dict__.values():
            # Check for InputPort type directly
            if isinstance(attr_value, InputPort) and attr_value.is_bound():
                upstream_timestamp = attr_value.timestamp()

                if upstream_timestamp is None:
                    raise ValueError(f"{self.__class__.__name__} getting None timestamp from upstream")

                if upstream_timestamp > cache_mtime:
                    # Upstream data is newer, our cache is stale
                    return False

        return True
