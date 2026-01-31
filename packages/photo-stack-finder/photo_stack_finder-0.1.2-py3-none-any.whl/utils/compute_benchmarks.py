"""PipelineStage for computing benchmark results."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any, cast, get_args

import pandas as pd
import psutil

from photo_compare import ComparisonMethodName, create_comparison_method

from .benchmark_utils import cluster_pairs_for_scoring, generate_benchmark_pairs, post_analysis
from .config import CONFIG
from .photo_file import PhotoFile, load_normalized_pixels
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import InputPort
from .sequence import PhotoSequence

# Type definitions for this specific stage:
type Pair = tuple[int, int]
type Score = float
type TimingStats = dict[str, float]  # {"prep_time": float, "compare_time": float, "prep_count": int}
# S: Work Item (Method to run + Cluster of pairs + Photo paths for worker file access)
# T: Worker Result Data (List of calculated scores + timing stats)
# R: Accumulator (Mapping MethodName -> Pair -> Score + timing stats)
type _S = tuple[ComparisonMethodName, list[Pair], dict[int, str]]
type _T = tuple[list[tuple[ComparisonMethodName, Pair, Score]], TimingStats]
type _R = tuple[
    dict[ComparisonMethodName, dict[Pair, Score]],  # scores
    dict[ComparisonMethodName, TimingStats],  # timing per method
]

# Extract list of comparison methods from the Literal type
COMPARISON_METHODS: list[ComparisonMethodName] = list(get_args(ComparisonMethodName))


def get_available_memory() -> int:
    """Get available system memory in bytes using psutil.

    Returns:
        Available memory in bytes
    """
    return psutil.virtual_memory().available


def calculate_max_cluster_size(
    num_workers: int | None = None,
    max_prep_size: int = 8 * 1024 * 1024,  # 8 MB per photo
    memory_fraction: float = 0.8,
) -> int:
    """Calculate maximum photos per cluster based on available memory.

    Formula: photos_per_cluster * prep_size * num_workers < available_memory

    Args:
        num_workers: Number of parallel worker processes (defaults to CONFIG.processing.MAX_WORKERS)
        max_prep_size: Maximum memory per prepared photo (bytes)
        memory_fraction: Fraction of available memory to use (0.0-1.0)

    Returns:
        Maximum number of photos allowed in a single cluster
    """
    if num_workers is None:
        num_workers = CONFIG.processing.MAX_WORKERS

    available_memory = get_available_memory()
    usable_memory = int(available_memory * memory_fraction)
    max_photos = usable_memory // (max_prep_size * num_workers)
    return max(max_photos, 10)  # Minimum 10 photos per cluster  # Minimum 10 photos per cluster


class ComputeBenchmarks(PipelineStage[_S, _T, _R]):
    """Pipeline stage for generating photo benchmark pairs, clustering them into work units.

    Calculates scores using various comparison methods in parallel,
    and performs a final analysis.
    """

    # --- Port Declarations ---
    # Class attributes for InputPorts and OutputPorts
    forest_i: InputPort[list[PhotoSequence]]
    photofiles_i: InputPort[Mapping[int, PhotoFile]]

    # --- Data Storage for Finalise ---
    positive_pairs: list[Pair]
    different_pairs: list[Pair]

    def __init__(self) -> None:
        """Initialize the benchmark stage."""
        super().__init__(
            path=CONFIG.paths.benchmark_scores_pkl,
            stage_name="Photo Comparison Benchmark",
        )

        # Initialize instance attributes
        self.positive_pairs = []
        self.different_pairs = []
        # Result is a tuple: (scores_dict, timing_dict)
        self.result: _R = ({}, {})
        self.args = ""  # Not strictly necessary for this stage

        # Define input ports (InputPort only needs a name)
        self.forest_i = InputPort("forest_data")
        self.photofiles_i = InputPort("photofiles_map")

    def prepare(self) -> PrepareResult[_S, _R]:
        """Generate benchmark pairs, cluster them, and create work units.

        1. Generate Similar/Dissimilar pairs from the forest.
        2. Cluster the pairs into connected components of limited size.
        3. Create work units: (ComparisonMethodName, ClusterOfPairs, PhotoPaths).

        Returns:
            Tuple of (work_units, initial_accumulator).
        """
        # --- 1. Load Inputs ---
        # InputPort.load() is used to read data from upstream stages
        forest: list[PhotoSequence] = self.forest_i.read()
        photofiles: Mapping[int, PhotoFile] = self.photofiles_i.read()

        # Get reference counts from upstream for UI statistics tracking
        self.ref_photos_init = self.forest_i.get_ref_photo_count()
        self.ref_seqs_init = self.forest_i.get_ref_sequence_count()

        # --- 2. Generate Pairs ---
        n_different = CONFIG.benchmark.N_DIFFERENT_PAIRS
        seed = CONFIG.processing.DEFAULT_RANDOM_SEED

        # Calculate max cluster size based on available memory
        # Uses CONFIG.processing.MAX_WORKERS
        max_cluster_size = calculate_max_cluster_size(
            max_prep_size=CONFIG.benchmark.MAX_PREP_SIZE_BYTES,
            memory_fraction=CONFIG.benchmark.MEMORY_FRACTION,
        )

        self.positive_pairs, self.different_pairs, unique_ids = generate_benchmark_pairs(
            forest=forest,
            n_different=n_different,
            seed=seed,
        )

        # Store for use in finalise()
        self.positive_pairs: list[Pair] = self.positive_pairs
        self.different_pairs: list[Pair] = self.different_pairs

        all_pairs: list[Pair] = self.positive_pairs + self.different_pairs

        # --- 3. Cluster Pairs ---
        cluster_list = cluster_pairs_for_scoring(
            pairs=all_pairs,
            max_cluster_size=max_cluster_size,
        )

        # --- 4. Build photo_paths dict for worker file access ---
        photo_paths: dict[int, str] = {photo_id: str(photofiles[photo_id].path) for photo_id in unique_ids}

        # --- 5. Create Work Units ---
        work_units: list[_S] = []
        for method in COMPARISON_METHODS:
            for _, cluster_pairs in cluster_list:
                work_units.append((method, cluster_pairs, photo_paths))

        # --- 6. Initialize Accumulator ---
        # Accumulator is a tuple: (scores_dict, timing_dict)
        scores_dict: dict[ComparisonMethodName, dict[Pair, Score]] = {}
        timing_dict: dict[ComparisonMethodName, TimingStats] = {}

        for method in COMPARISON_METHODS:
            scores_dict[method] = {}
            timing_dict[method] = {
                "prep_time": 0.0,
                "compare_time": 0.0,
                "prep_count": 0.0,
            }

        initial_accum: _R = (scores_dict, timing_dict)

        return work_units, initial_accum

    @classmethod
    def stage_worker(
        cls,
        job: _S,
        _args: str,
    ) -> WorkerResult[_T]:
        """Process an individual work unit: calculate scores for all pairs in a cluster.

        Uses a single comparison method with lazy preparation and local caching:
        - Photos are prepared on-demand (first use)
        - Prepared data is cached locally for reuse
        - Minimizes redundant file I/O and preparation
        - Measures preparation and comparison timing

        Args:
            job: 3-tuple (method_name, cluster_pairs, photo_paths)
            _args: Unused worker arguments

        Returns:
            WorkerResult with calculated scores and timing statistics

        Raises:
            FileNotFoundError: If photo file is missing (critical error, must surface)
        """
        method_name, cluster_pairs, photo_paths = job

        # Create comparison method instance
        method = create_comparison_method(method_name)

        # Local cache for prepared photo data (photo_id -> prepared_data)
        local_cache: dict[int, Any] = {}

        calculated_scores: list[tuple[ComparisonMethodName, Pair, Score]] = []

        # Track timing statistics
        prep_time = 0.0
        compare_time = 0.0
        prep_count = 0

        for a_id, b_id in cluster_pairs:
            # Lazy preparation: prepare photo only if not in cache
            if a_id not in local_cache:
                t0 = time.perf_counter()
                pixels = load_normalized_pixels(photo_paths[a_id])
                local_cache[a_id] = method.prepare(pixels)
                prep_time += time.perf_counter() - t0
                prep_count += 1

            if b_id not in local_cache:
                t0 = time.perf_counter()
                pixels = load_normalized_pixels(photo_paths[b_id])
                local_cache[b_id] = method.prepare(pixels)
                prep_time += time.perf_counter() - t0
                prep_count += 1

            # Measure comparison time
            t0 = time.perf_counter()
            score: float = method.compare(local_cache[a_id], local_cache[b_id])
            compare_time += time.perf_counter() - t0

            calculated_scores.append((method_name, (a_id, b_id), score))

        timing_stats: TimingStats = {
            "prep_time": prep_time,
            "compare_time": compare_time,
            "prep_count": float(prep_count),
        }

        return [], [], (calculated_scores, timing_stats)

    def accumulate_results(
        self,
        accum: _R,
        job_result: _T,
    ) -> None:
        """Merges worker results into the main accumulator dictionary.

        Accumulates both scores and timing statistics per comparison method.

        Args:
            accum: Tuple of (scores_dict, timing_dict)
            job_result: Tuple of (scores_list, timing_stats)
        """
        scores_list, timing_stats = job_result
        scores_dict, timing_dict = accum

        # Early return if no scores to accumulate
        if not scores_list:
            return

        # Accumulate scores
        for method_name, pair, score in scores_list:
            scores_dict[method_name][pair] = score

        # Accumulate timing stats (sum across workers for each method)
        # All scores in a work unit are for the same method
        method_name = scores_list[0][0]
        if method_name not in timing_dict:
            timing_dict[method_name] = {
                "prep_time": 0.0,
                "compare_time": 0.0,
                "prep_count": 0.0,
            }
        timing_dict[method_name]["prep_time"] += timing_stats["prep_time"]
        timing_dict[method_name]["compare_time"] += timing_stats["compare_time"]
        timing_dict[method_name]["prep_count"] += timing_stats["prep_count"]

    def finalise(self) -> None:
        """Perform post-analysis and save results.

        Includes calculating metrics, generating reports, and saving outputs,
        as per the original benchmarks.py script. Also saves timing statistics.
        """
        # Extract scores and timing from accumulator
        scores_dict, timing_dict = self.result

        # Update status with initial info
        total_pairs = len(self.positive_pairs) + len(self.different_pairs)
        if self._progress_tracker:
            self._progress_tracker.set_status(f"Analyzing {total_pairs:,} pairs across {len(scores_dict)} methods...")

        # Calculate derived timing metrics for each method
        timing_summary = {}
        for method_name, stats in timing_dict.items():
            prep_time = stats["prep_time"]
            compare_time = stats["compare_time"]
            prep_count = int(stats["prep_count"])
            num_pairs = len(scores_dict.get(method_name, {}))

            # Calculate derived metrics
            timing_summary[method_name] = {
                "prep_time_seconds": prep_time,
                "compare_time_seconds": compare_time,
                "total_time_seconds": prep_time + compare_time,
                "prep_count": prep_count,
                "num_pairs": num_pairs,
                "prep_time_per_photo_ms": (prep_time / prep_count * 1000) if prep_count > 0 else 0.0,
                "compare_time_per_pair_us": (compare_time / num_pairs * 1_000_000) if num_pairs > 0 else 0.0,
                "photos_per_second": prep_count / prep_time if prep_time > 0 else 0.0,
                "comparisons_per_second": num_pairs / compare_time if compare_time > 0 else 0.0,
            }

        # Save timing data to JSON
        timing_output_path = CONFIG.paths.work_dir / "benchmark_timing.json"
        timing_output_path.parent.mkdir(parents=True, exist_ok=True)
        with timing_output_path.open("w", encoding="utf-8") as f:
            json.dump(timing_summary, f, indent=2)

        # Perform the full analysis (pass only scores_dict)
        # Cast to expected type for post_analysis (dict[str, dict[Pair, Score]])
        post_analysis(
            final_scores=cast(dict[str, dict[Pair, Score]], scores_dict),
            positive_pairs=self.positive_pairs,  # Now correctly stored from prepare()
            different_pairs=self.different_pairs,  # Now correctly stored from prepare()
            output_dir=CONFIG.paths.work_dir,
        )

        # Read back the best results and update status with findings
        metrics_path = CONFIG.paths.work_dir / "method_metrics.csv"
        if metrics_path.exists():
            df_metrics = pd.read_csv(metrics_path, index_col=0)
            best_method = df_metrics["f1"].idxmax()
            best_f1 = df_metrics.loc[best_method, "f1"]
            best_auc = df_metrics.loc[best_method, "auc"]

            if self._progress_tracker:
                self._progress_tracker.set_status(
                    f"Best: {best_method} (F1={best_f1:.4f}, AUC={best_auc:.4f}) | {total_pairs:,} pairs tested"
                )

        # Update stage statistics (required by BasePipelineStage)
        self.ref_photos_final = self.ref_photos_init
        self.ref_seqs_final = self.ref_seqs_init
