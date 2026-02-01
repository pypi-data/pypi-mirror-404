r"""Comprehensive end-to-end test for ComputeBenchmarks.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions.

DATA REQUIREMENT:
This test requires real pipeline output data. To enable:
1. Run the full pipeline on a test dataset
2. Set BENCHMARK_TEST_DATA environment variable to the forest_final.pkl path
3. Re-run tests

If no data is available, the test will be skipped.

TEST COVERAGE:
- __init__()
- prepare() - pair generation, clustering, work unit creation
- stage_worker() - lazy preparation, timing measurement, scoring
- accumulate_results() - score and timing aggregation
- finalise() - timing calculation, post_analysis integration
"""

import os
import pickle
import time
from pathlib import Path
from typing import Any

import pytest
import src.utils.compute_benchmarks as benchmark_module
from src.utils.compute_benchmarks import ComputeBenchmarks

from tests.fixtures.cache_loader import MockInputPort


def load_test_data() -> dict[str, Any] | None:
    """Load test data if available.

    Checks BENCHMARK_TEST_DATA environment variable for path to forest_final.pkl.
    If not set or file doesn't exist, returns None (test will be skipped).

    Returns:
        Dict with 'forest' and 'photofiles' keys, or None if data unavailable
    """
    # Check for environment variable
    data_path_str = os.environ.get("BENCHMARK_TEST_DATA")
    if not data_path_str:
        return None

    data_path = Path(data_path_str)
    if not data_path.exists():
        return None

    # Load forest
    with data_path.open("rb") as f:
        forest = pickle.load(f)

    # Check forest structure - Handle 5-tuple format (forest_working, seq_review, id_review, ref_photos, ref_seqs)
    if isinstance(forest, tuple) and len(forest) == 5:
        forest_working, _seq_review, _id_review, _ref_photos, _ref_seqs = forest
        if isinstance(forest_working, tuple) and len(forest_working) == 2:
            forest, _bins = forest_working
        else:
            forest = forest_working

    # Extract photofiles from forest (flatten to get all nested sequences)
    photofiles = {}
    for sequence in forest:
        _, leaf_series_list = sequence.flatten()
        for series in leaf_series_list:
            for photo in series.values():
                photofiles[photo.id] = photo

    # Filter to sequences with multiple photos (needed for positive pairs)
    # Take first 20 sequences with >= 3 photos each for fast testing
    multi_photo_sequences = [seq for seq in forest if len(seq.series) >= 3]

    # Take small subset for fast end-to-end testing
    forest_subset = multi_photo_sequences[:20]

    # Return full photofiles dict (needed for nested sequence references)
    return {
        "forest": forest_subset,
        "photofiles": photofiles,
    }


def test_comprehensive_end_to_end_coverage() -> None:  # noqa: PLR0915
    """Run full stage lifecycle test.

    This test validates:
    - __init__()
    - prepare() - pair generation, clustering, work units
    - stage_worker() - scoring with timing measurement
    - accumulate_results() - score and timing aggregation
    - finalise() - derived metrics, post_analysis

    Skips if test data is not available.
    """
    # Load test data
    inputs = load_test_data()
    if inputs is None:
        pytest.skip(
            "Benchmark test data not available. "
            "Set BENCHMARK_TEST_DATA=/path/to/forest_final.pkl to enable this test."
        )

    print("\n" + "=" * 70)
    print("ComputeBenchmarks Comprehensive End-to-End Test")
    print("=" * 70)
    print(f"\n  Forest: {len(inputs['forest'])} sequences")
    print(f"  Photofiles: {len(inputs['photofiles'])} photos")

    start_time = time.perf_counter()

    # [1] Create stage (tests __init__)
    print("\n[1/5] Creating stage (__init__)...")
    stage = ComputeBenchmarks()
    print("  [OK] Stage created")

    # Limit to 3 comparison methods for speed (user requested)
    original_methods = benchmark_module.COMPARISON_METHODS
    benchmark_module.COMPARISON_METHODS = ["dhash", "phash", "whash"]
    print(f"  Limited to {len(benchmark_module.COMPARISON_METHODS)} methods for speed")

    # Inject test data
    stage.forest_i = MockInputPort(  # type: ignore[assignment]
        inputs["forest"], ref_seqs=len(inputs["forest"]), ref_photos=len(inputs["photofiles"])
    )
    stage.photofiles_i = MockInputPort(  # type: ignore[assignment]
        inputs["photofiles"], ref_seqs=len(inputs["forest"]), ref_photos=len(inputs["photofiles"])
    )

    # [2] Run prepare (tests prepare)
    print("\n[2/5] Running prepare()...")
    work_units_iter, initial_accum = stage.prepare()
    work_units = list(work_units_iter)  # Convert to list for len() and indexing
    print(f"  Work units generated: {len(work_units)}")
    print(f"  Positive pairs: {len(stage.positive_pairs)}")
    print(f"  Different pairs: {len(stage.different_pairs)}")

    # Validate prepare results
    assert len(work_units) > 0, "Should generate work units"
    assert len(stage.positive_pairs) > 0, "Should have positive pairs"
    assert len(stage.different_pairs) > 0, "Should have different pairs"

    # Validate work unit structure (3-tuple)
    work_unit = work_units[0]
    assert len(work_unit) == 3, f"Work unit must be 3-tuple, got {len(work_unit)}"
    method_name, cluster_pairs, photo_paths = work_unit
    assert isinstance(method_name, str), "First element must be method name"
    assert isinstance(cluster_pairs, list), "Second element must be pairs list"
    assert isinstance(photo_paths, dict), "Third element must be photo_paths dict"
    print("  [OK] Work unit structure validated")

    # Validate initial accumulator structure
    scores_dict, timing_dict = initial_accum
    assert isinstance(scores_dict, dict), "Accumulator must have scores dict"
    assert isinstance(timing_dict, dict), "Accumulator must have timing dict"
    print("  [OK] Initial accumulator structure validated")

    # [3] Process ALL work units through stage_worker (tests stage_worker)
    print("\n[3/5] Processing work units through stage_worker()...")
    print(f"  Processing ALL {len(work_units)} work units (required for post_analysis)")

    worker_results = []
    for _i, job in enumerate(work_units):
        _method, pairs, _paths = job
        # stage_worker returns (id_reviews, seq_reviews, (scores_list, timing_stats))
        _id_reviews, _seq_reviews, result = ComputeBenchmarks.stage_worker(job, "test")
        worker_results.append(result)

        # Validate worker result structure
        scores_list, timing_stats = result
        assert isinstance(scores_list, list), "Worker must return scores list"
        assert isinstance(timing_stats, dict), "Worker must return timing dict"
        assert "prep_time" in timing_stats, "Timing must include prep_time"
        assert "compare_time" in timing_stats, "Timing must include compare_time"
        assert "prep_count" in timing_stats, "Timing must include prep_count"

        # Validate all pairs were scored
        assert len(scores_list) == len(pairs), f"Worker must score all pairs: {len(scores_list)} != {len(pairs)}"

    print(f"  [OK] Processed {len(worker_results)} work units")

    # [4] Accumulate results (tests accumulate_results)
    print("\n[4/5] Accumulating results...")
    for result in worker_results:
        stage.accumulate_results(initial_accum, result)

    # Validate accumulated scores
    scores_dict, timing_dict = initial_accum
    assert len(scores_dict) > 0, "Should have accumulated scores"
    assert len(timing_dict) > 0, "Should have accumulated timing data"

    # Validate structure: scores_dict[method][pair_type] = [scores]
    for method, method_scores in scores_dict.items():
        assert isinstance(method, str), "Method key must be string"
        assert isinstance(method_scores, dict), "Method scores must be dict"
        for pair_type, scores in method_scores.items():
            assert pair_type in ("positive", "different"), f"Invalid pair type: {pair_type}"  # type: ignore[comparison-overlap]
            assert isinstance(scores, list), "Scores must be list"  # type: ignore[unreachable]
            assert all(isinstance(s, (int, float)) for s in scores), "All scores must be numeric"  # type: ignore[unreachable]

    print(f"  Accumulated scores for {len(scores_dict)} methods")
    print(f"  Accumulated timing for {len(timing_dict)} methods")
    print("  [OK] Accumulation validated")

    # [5] Finalize (tests finalise)
    print("\n[5/5] Running finalise()...")
    stage.result = initial_accum  # Set result before calling finalise
    stage.finalise()

    # Validate post_analysis results
    assert hasattr(stage, "post_analysis"), "Should generate post_analysis"
    assert isinstance(stage.post_analysis, dict), "post_analysis must be dict"

    # Validate post_analysis structure (method_name -> results dict)
    for method, results in stage.post_analysis.items():
        assert isinstance(method, str), "Method name must be string"
        assert isinstance(results, dict), "Results must be dict"

        # Check for AUC and threshold metrics
        assert "auc" in results, f"Method {method} missing AUC"
        assert "threshold" in results, f"Method {method} missing threshold"
        assert "optimal_f1" in results, f"Method {method} missing optimal_f1"

        # Validate metric ranges
        auc = results["auc"]
        assert 0 <= auc <= 1, f"AUC must be in [0,1], got {auc}"

    print(f"  Generated post_analysis for {len(stage.post_analysis)} methods")
    print("  [OK] Finalise validated")

    # Report timing
    elapsed = time.perf_counter() - start_time
    print(f"\n{'=' * 70}")
    print(f"Test completed in {elapsed:.2f}s")
    print(f"{'=' * 70}")

    # Restore original methods list
    benchmark_module.COMPARISON_METHODS = original_methods
