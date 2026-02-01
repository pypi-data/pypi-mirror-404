"""Base class for all pipeline stages."""

from __future__ import annotations

import os
import pickle
import tempfile
from abc import abstractmethod
from collections.abc import Iterable, Iterator, Sized
from pathlib import Path
from typing import cast, final

from joblib import Parallel, delayed

from .base_pipeline_stage import BasePipelineStage
from .config import CONFIG
from .graph_context import get_active_graph
from .logger import get_logger
from .models import IdenticalGroup, ReviewType, SequenceGroup
from .progress import ProgressTracker

# Type aliases for pipeline stage method signatures (must be defined outside class)
type PrepareResult[S, R] = tuple[Iterable[S], R]
type WorkerResult[T] = tuple[list[IdenticalGroup], list[SequenceGroup], T]


class PipelineStage[S, T, R](BasePipelineStage):
    """Abstract base class for pipeline stages with parallel processing support.

    Stages define three abstract methods for parallel execution:
    - prepare(): Set up work items and result accumulator
    - stage_worker(): Process individual work items (runs in parallel)
    - accumulate_results(): Merge worker results into final output

    Type safety is provided by port declarations (InputPort[T], OutputPort[T])
    rather than class-level generic parameters.

    Review Data Architecture:
    - result: Working data that flows through pipeline (may be nested)
    - review_result: Pre-computed review data for UI (always flat, per-stage)
    """

    result: R

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
        super().__init__(path, stage_name)

        # Auto-register with active graph if within PipelineBuilder context
        active_graph = get_active_graph()
        if active_graph is not None:
            active_graph.add_node(self)

    @abstractmethod
    def prepare(self) -> PrepareResult[S, R]:
        """Prepare input for parallel processing by reading from input ports.

        This method reads data from input ports and prepares work items for parallel
        processing.

        Returns:
            Tuple of (work_items, accumulator) where work_items will be processed
            in parallel and results accumulated into accumulator
        """
        ...

    @staticmethod
    @abstractmethod
    def stage_worker(job: S, args: str) -> WorkerResult[T]:
        """This method performs the core, isolated, and concurrent work."""
        ...

    @abstractmethod
    def accumulate_results(self, result: R, job: T) -> None:
        """Accumulate worker result into final output.

        Args:
            result: Accumulator to update (returned from prepare)
            job: Result from stage_worker to incorporate
        """
        ...

    # === Review Interface (for orchestrator discovery) ===

    def needs_review(self) -> ReviewType:
        """Discover what type of review this stage produces.

        This allows the orchestrator to dynamically discover which stages
        produce reviewable output without hard-coding stage names.

        Returns:
            - "none": No reviewable output (default)
            - "photos": Produces photo groups (byte-identical duplicates)
            - "sequences": Produces sequence groups (similar sequences)
        """
        return "none"

    def _unpack_cache(
        self,
        loaded_cache: (
            tuple[R, list[SequenceGroup], list[IdenticalGroup], int | None, int | None]
            | tuple[R, list[SequenceGroup], list[IdenticalGroup], int | None, int | None, float | None, float | None]
        ),
    ) -> None:
        """Unpack cache tuple with backward compatibility.

        Handles both old 5-element format (before performance metrics) and new 7-element format.
        """
        if len(loaded_cache) == 5:
            # Old format: (result, seq_review, id_review, ref_photos, ref_seqs)
            (
                self.result,
                self.sequence_review_result,
                self.identical_review_result,
                self.ref_photos_final,
                self.ref_seqs_final,
            ) = loaded_cache
            self.elapsed_seconds = None
            self.throughput = None
        else:
            # New format: (result, seq_review, id_review, ref_photos, ref_seqs, elapsed, throughput)
            (
                self.result,
                self.sequence_review_result,
                self.identical_review_result,
                self.ref_photos_final,
                self.ref_seqs_final,
                self.elapsed_seconds,
                self.throughput,
            ) = loaded_cache

    def has_review_data(self) -> bool:
        """Check if review data is available for this stage.

        Returns:
            True if stage has completed and has reviewable data available
        """
        return self.needs_review() != "none"

    def batch_compute(self, work: Iterable[S], args: str) -> Iterator[WorkerResult[T]]:
        """Orchestrates parallel or sequential processing with graceful shutdown support.

        This implementation uses Joblib for efficient parallel processing with automatic
        load balancing. The batch_size="auto" allows Joblib to optimize batching based
        on measured task duration, which works well with sorted work items.

        IMPORTANT: This function preserves lazy evaluation of iterators. If work is a
        generator/iterator, it will be consumed lazily without materializing the entire
        sequence in memory. Progress tracking will show indeterminate progress (no total).

        Graceful Shutdown: When SIGINT (Ctrl+C) is received, joblib workers are terminated
        and this method catches KeyboardInterrupt, logging the cancellation and returning
        cleanly. This prevents ShutdownExecutorError from occurring.

        Args:
            work: An iterable of work items (e.g., file paths) to be processed.
            args: Arguments to pass to the stage worker function.

        Yields:
            WorkerResult tuple containing (identical_groups, sequence_groups, work_data)
        """
        # Check if work supports len() without materializing
        # Use hasattr to avoid forcing evaluation of generators
        total_count: int | None
        try:
            # Cast to Sized since we know it has __len__ (hasattr check)
            total_count = len(cast(Sized, work)) if hasattr(work, "__len__") else None
        # This is a best effort so ok to handle any exceptions
        except:  # noqa E722
            # Some iterables don't support len() even with __len__ attribute
            total_count = None

        with ProgressTracker(self.stage_name, total=total_count) as progress:
            # Expose progress tracker for UI polling (see get_progress())
            self._progress_tracker = progress

            try:
                if CONFIG.processing.DEBUG_MODE:
                    # Sequential processing for debugging
                    for j in work:
                        r = self.__class__.stage_worker(j, args)
                        yield r
                        progress.update()
                else:
                    # Parallel processing with Joblib
                    # batch_size="auto" lets Joblib optimize batching automatically
                    # return_as="generator" provides streaming results
                    # IMPORTANT: Pass work directly (don't materialize) - Joblib handles iterators
                    results = Parallel(
                        n_jobs=CONFIG.processing.MAX_WORKERS,
                        backend="loky",  # Robust process-based backend
                        prefer="processes",  # Good for jobs with variable time requirements
                        batch_size="auto",  # Automatic batch size optimization
                        return_as="generator_unordered",  # Stream results as they complete
                    )(delayed(self.__class__.stage_worker)(item, args) for item in work)

                    # Yield results as they complete with progress tracking
                    for result in results:
                        yield result
                        progress.update()

            except KeyboardInterrupt:
                # SIGINT received (Ctrl+C or shutdown endpoint called)
                # Joblib workers have been terminated by the signal
                # Exit cleanly without trying to dispatch more work
                logger = get_logger()
                logger.info(f"{self.stage_name}: Received shutdown signal, stopping batch processing")
                return  # Exit generator cleanly (don't re-raise)

            finally:
                # Don't clear tracker here - let orchestrator clear after marking complete
                # This keeps progress visible during finalise() and cache save
                pass

    # ========================================================================
    # Port-Based Connectivity (Phase 1: Infrastructure - Optional for now)
    # ========================================================================
    #
    # Stages declare typed ports explicitly in __init__ method:
    # - Input ports: InputPort[Type] for receiving data from upstream stages
    # - Output ports: OutputPort[Type] for sending data to downstream stages
    #
    # Graph builder wires ports explicitly with compile-time type checking
    # by binding consumer input ports to producer output ports.
    #
    # No dynamic discovery needed - static types ensure correctness.

    # ============================================================================
    # DO NOT REMOVE @final DECORATOR - PREVENTS ARCHITECTURAL VIOLATIONS
    # ============================================================================
    # The @final decorator prevents subclasses from overriding run().
    # This is CRITICAL to maintain separation of concerns:
    #
    # - run() handles: caching, batch processing, logging, result storage
    # - prepare() handles: reading inputs from ports, stage-specific logic
    #
    # Previously, stages overrode run() which led to:
    # - Redundant _execute_impl() pattern (removed in refactor)
    # - Duplicate code across stages
    # - Broken caching when stages forgot to call parent
    # - 149 lines of unnecessary complexity
    #
    # If you need stage-specific behavior, override prepare().
    # NEVER remove @final and override run() - this violates the pattern.
    # ============================================================================
    @final
    def run(self) -> None:
        """Execute pipeline stage with dependency-aware caching support.

        This method is final and cannot be overridden by subclasses.

        If cached results exist and are newer than all dependencies, loads and returns them.
        Otherwise, prepares work (reading from input ports), processes in parallel,
        accumulates results, saves to cache, and returns final result.

        Stages must store their worker arguments in self.args during __init__.

        NEW: Also builds and caches review data alongside working data for stages
        that produce reviews (needs_review() != "none").

        Phase callbacks notify orchestrator of current execution phase:
        - cache_load: Loading results from cache
        - prepare: Reading inputs and setting up work
        - compute: Processing work items in parallel
        - finalise: Computing final statistics and validating results
        - save: Writing results to cache

        Returns:
            Accumulated results (working data for pipeline flow)
        """
        if self._cache_is_valid():
            # Notify phase: loading from cache
            if self._phase_callback:
                self._phase_callback("cache_load")

            # Load from cache and store in instance (tuple unpacking with type annotation)
            # Cache contains FINAL counts and performance metrics (what this stage produced)
            loaded_cache: (
                tuple[R, list[SequenceGroup], list[IdenticalGroup], int | None, int | None]
                | tuple[
                    R, list[SequenceGroup], list[IdenticalGroup], int | None, int | None, float | None, float | None
                ]
            ) = atomic_pickle_load(self.path)
            self._unpack_cache(loaded_cache)

            return

        # Not cached - compute result
        # Notify phase: preparing work
        if self._phase_callback:
            self._phase_callback("prepare")

        # prepare() reads from input ports and stores inputs as instance vars
        work: Iterable[S]
        work, result = self.prepare()

        # Notify phase: computing (parallel processing)
        if self._phase_callback:
            self._phase_callback("compute")

        # Process work items in parallel
        for r in self.batch_compute(work, self.stage_name):
            # Extract review and work data from worker result
            identical_review, sequence_review, work_item = r

            # Generic review accumulation (just extend lists, update dicts)
            self.identical_review_result.extend(identical_review)
            self.sequence_review_result.extend(sequence_review)

            # Stage-specific work accumulation
            self.accumulate_results(result, work_item)

        # Capture performance metrics from progress tracker (after context manager exits)
        if self._progress_tracker:
            self.elapsed_seconds = self._progress_tracker.elapsed_seconds
            self.throughput = self._progress_tracker.final_rate

        # Store result in instance BEFORE finalise (stages need to access self.result)
        self.result = result

        # Notify phase: finalizing results
        if self._phase_callback:
            self._phase_callback("finalise")

        # Update progress status for finalization
        if self._progress_tracker:
            self._progress_tracker.set_status("Finalizing results...")

        self.finalise()

        # Notify phase: saving to cache
        if self._phase_callback:
            self._phase_callback("save")

        # Update progress status for cache save
        if self._progress_tracker:
            self._progress_tracker.set_status("Saving to cache...")

        # Save working data, review data, ref counts, and performance metrics to cache (as typed tuple)
        # Save FINAL counts and metrics (set by finalise()) so downstream stages know what we produced
        saved_cache: tuple[
            R, list[SequenceGroup], list[IdenticalGroup], int | None, int | None, float | None, float | None
        ] = (
            self.result,  # Use self.result (already assigned above)
            self.sequence_review_result,
            self.identical_review_result,
            self.ref_photos_final,  # Final photo count (what THIS stage produced)
            self.ref_seqs_final,  # Final sequence count (what THIS stage produced)
            self.elapsed_seconds,  # Stage execution time in seconds
            self.throughput,  # Items per second
        )

        atomic_pickle_dump(saved_cache, self.path)


def atomic_pickle_load[T](
    path: Path,
    expected_type: type[T] | None = None,  # noqa: ARG001
) -> T:
    """Load object from pickle file with optional type hint.

    Args:
        path: Path to pickle file
        expected_type: Optional type parameter for explicit type checking (unused at runtime,
            exists only to satisfy mypy's requirement that TypeVar appears in parameters)

    Returns:
        Unpickled object of type T

    Note:
        Type safety comes from explicit annotations at call sites:
            loaded: tuple[R, ...] = atomic_pickle_load(path)
    """
    with path.open("rb") as f:
        result: T = pickle.load(f)
    return result


def atomic_pickle_dump[T](obj: T, path: Path) -> None:
    """Write pickle file atomically using temp file + os.replace.

    Args:
        obj: Object to pickle
        path: Destination file path
    """
    # Write to temp file in same directory as target
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    # os.fdopen returns BufferedWriter which is compatible with SupportsWrite[bytes]
    # Type checker is being overly strict here
    # Must use os.fdopen rather than Path.open otherwise file handles trip over each other
    with os.fdopen(temp_fd, "wb") as f:
        # noinspection PyTypeChecker
        pickle.dump(obj, f)
    # Atomic replace
    Path(temp_path).replace(path)
