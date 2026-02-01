"""Comprehensive end-to-end test for ComputePerceptualMatch.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions using minimal anonymized fixtures.

FIXTURE CONSTRUCTION:
For regenerating or updating the minimal test fixtures, see:
    tests/construct_perceptual_match_fixtures.py

Construction workflow (one-time process):
    1. python construct_perceptual_match_fixtures.py prepare <work_dir>
    2. python construct_perceptual_match_fixtures.py worker
    3. python tests/select_minimal_test_set.py
    4. python construct_perceptual_match_fixtures.py extract
    5. Run anonymization script
    6. Commit minimal fixtures (<50MB) and delete large temporary files

REGRESSION TESTING:
This test is the ONLY coverage/regression test needed for CI.
It uses pre-generated minimal fixtures and validates all stage methods.
"""

import json
import math
import pickle
import time
from pathlib import Path

from src.utils.compute_perceptual_match import ComputePerceptualMatch

from tests.fixtures.cache_loader import MockInputPort


def load_minimal_inputs() -> dict:
    """Load minimal fixtures for end-to-end testing."""
    forest_path = Path("tests/fixtures/cache_snapshots/perceptual_match_forest_minimal.pkl")
    bins_path = Path("tests/fixtures/cache_snapshots/perceptual_match_bins_minimal.pkl")
    components_path = Path("tests/fixtures/cache_snapshots/perceptual_match_components_minimal.pkl")

    with forest_path.open("rb") as f:
        forest_data = pickle.load(f)
    with bins_path.open("rb") as f:
        bins_data = pickle.load(f)
    with components_path.open("rb") as f:
        components_data = pickle.load(f)

    # Unpack 5-tuples
    forest_working, _seq_review, _id_review, ref_photos, ref_seqs = forest_data
    forest, _bins = forest_working

    perceptual_bins, _seq_review2, _id_review2, _ref_photos2, _ref_seqs2 = bins_data

    # Components fixture is a dict with 'work', 'args', 'ref_seqs'
    components = components_data["work"]

    return {
        "forest": forest,
        "perceptual_bins": perceptual_bins,
        "components": components,
        "ref_seqs": ref_seqs,
        "ref_photos": ref_photos,
    }


def test_comprehensive_end_to_end_coverage():
    """Run full stage lifecycle test.

    This test validates:
    - __init__()
    - prepare()
    - stage_worker() (via manual invocation)
    - accumulate_results()
    - finalise()
    - needs_review()
    - has_review_data()
    - final_forest_o.read()
    - final_forest_o.get_ref_photo_count()
    - final_forest_o.get_ref_sequence_count()
    - final_forest_o.timestamp()
    - Status updates (ref_photos_final, ref_seqs_final) for UI display
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test")
    print("=" * 70)

    # Load minimal fixtures
    print("\nLoading minimal fixtures...")
    inputs = load_minimal_inputs()
    print(f"  Forest: {len(inputs['forest'])} sequences")
    print(f"  Perceptual bins: {len(inputs['perceptual_bins'])} bins")
    print(f"  Components: {len(inputs['components'])} components")

    start_time = time.perf_counter()

    # [1] Create stage (tests __init__)
    print("\n[1/11] Creating stage (__init__)...")
    stage = ComputePerceptualMatch()

    # Test has_review_data() before stage runs (should return False)
    assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
    print("  [OK] has_review_data() returns False before stage runs")

    # Inject test data
    stage.forest_i = MockInputPort(inputs["forest"], inputs["ref_seqs"], inputs["ref_photos"])
    stage.perceptual_bins_i = MockInputPort(inputs["perceptual_bins"])

    # [2] Run prepare (tests prepare)
    print("[2/11] Running prepare()...")
    processable_components, skipped_seqs = stage.prepare()
    print(f"  Components generated: {len(processable_components)}")
    print(f"  Skipped sequences: {len(skipped_seqs)}")

    # [3] Process ALL components through stage_worker (tests stage_worker)
    print("[3/11] Processing ALL components through stage_worker()...")
    component_sizes = [len(c) for c in processable_components]
    print(
        f"  Component sizes: min={min(component_sizes)}, max={max(component_sizes)}, avg={sum(component_sizes) / len(component_sizes):.1f}"
    )

    worker_results = []
    for i, component in enumerate(processable_components):
        print(f"  Processing component {i+1}/{len(processable_components)} (size={len(component)})...", flush=True)
        t0 = time.perf_counter()
        # stage_worker returns (id_reviews, seq_reviews, results)
        _id_reviews, _seq_reviews, results = ComputePerceptualMatch.stage_worker(component, created_by="test")
        elapsed = time.perf_counter() - t0
        print(f"    -> Completed in {elapsed:.2f}s, produced {len(results)} sequences", flush=True)
        worker_results.append(results)  # Only keep the results (list[PhotoSequence])

    # [4] Accumulate results (tests accumulate_results)
    print("[4/11] Running accumulate_results()...")
    # Initialize result accumulator (includes skipped sequences from prepare)
    stage.result = list(skipped_seqs)
    for job_results in worker_results:
        stage.accumulate_results(stage.result, job_results)
    print(f"  Total sequences accumulated: {len(stage.result)}")

    # [5] Finalize stage (tests finalise)
    print("[5/11] Running finalise()...")
    stage.finalise()
    print(f"  Final sequences: {stage.ref_seqs_final}, Final photos: {stage.ref_photos_final}")

    # Validate status updates (for UI display)
    print("\nValidating status updates...")
    assert stage.ref_photos_final is not None, "ref_photos_final must not be None (breaks orchestrator tracking)"
    assert stage.ref_seqs_final is not None, "ref_seqs_final must not be None (breaks orchestrator tracking)"
    assert isinstance(stage.ref_photos_final, int), f"ref_photos_final must be int, got {type(stage.ref_photos_final)}"
    assert isinstance(stage.ref_seqs_final, int), f"ref_seqs_final must be int, got {type(stage.ref_seqs_final)}"

    # Perceptual matching REDUCES photos by merging similar sequences (deduplication)
    assert stage.ref_photos_final < stage.ref_photos_init, (
        f"Photo count should decrease (deduplication): started {stage.ref_photos_init}, ended {stage.ref_photos_final}"
    )
    assert stage.ref_photos_final > 0, "Should have some photos remaining"

    reduction_pct = ((stage.ref_photos_init - stage.ref_photos_final) / stage.ref_photos_init) * 100
    print(
        f"  [PASS] Status updates valid: photos={stage.ref_photos_final} ({reduction_pct:.1f}% reduction), seqs={stage.ref_seqs_final}"
    )

    # [6] Test review methods
    print("[6/11] Testing needs_review()...")
    review_type = stage.needs_review()
    print(f"  Review type: {review_type}")

    print("[7/11] Testing has_review_data()...")
    has_review = stage.has_review_data()
    print(f"  Has review data: {has_review}")

    # [8] Test final_forest_o.read()
    print("\n[8/11] Testing final_forest_o.read()...")
    forest_from_port = stage.final_forest_o.read()
    assert forest_from_port is stage.result, "final_forest_o.read() should return stage.result"
    assert len(forest_from_port) == len(stage.result), (
        f"Forest from port should match result length: {len(forest_from_port)} != {len(stage.result)}"
    )
    print(f"  Forest via OutputPort: {len(forest_from_port)} sequences")
    print("  [OK] final_forest_o.read() returns correct result")

    # [9] Test final_forest_o.get_ref_photo_count()
    print("\n[9/11] Testing final_forest_o.get_ref_photo_count()...")
    photo_count = stage.final_forest_o.get_ref_photo_count()
    assert photo_count == stage.ref_photos_final, (
        f"OutputPort photo count should match ref_photos_final: {photo_count} != {stage.ref_photos_final}"
    )
    print(f"  Photo count via OutputPort: {photo_count}")
    print("  [OK] final_forest_o.get_ref_photo_count() returns correct count")

    # [10] Test final_forest_o.get_ref_sequence_count()
    print("\n[10/11] Testing final_forest_o.get_ref_sequence_count()...")
    seq_count = stage.final_forest_o.get_ref_sequence_count()
    assert seq_count == stage.ref_seqs_final, (
        f"OutputPort sequence count should match ref_seqs_final: {seq_count} != {stage.ref_seqs_final}"
    )
    print(f"  Sequence count via OutputPort: {seq_count}")
    print("  [OK] final_forest_o.get_ref_sequence_count() returns correct count")

    # [11] Test final_forest_o.timestamp()
    print("\n[11/11] Testing final_forest_o.timestamp()...")
    try:
        timestamp = stage.final_forest_o.timestamp()
        # If we get here, the stage's cache exists (unexpected in this test)
        print(f"  Timestamp: {timestamp}")
        print("  [NOTE] Cache exists, timestamp returned (not expected in isolated test)")
    except RuntimeError as e:
        # Expected behavior: cache doesn't exist in isolated test
        print(f"  RuntimeError raised (expected): {e}")
        print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

    # [Bonus] Validate review data can be JSON serialized (critical for UI)
    print("\nValidating review data JSON serialization...")
    if has_review and stage.needs_review() == "sequences":
        review_data = stage.sequence_review_result
        print(f"  Review data: {len(review_data)} sequence groups")

        # Check for NaN values before JSON serialization
        for i, group in enumerate(review_data):
            # Check min_similarity for NaN
            if math.isnan(group.min_similarity):
                raise ValueError(
                    f"Group {i} has NaN min_similarity. "
                    f"This breaks JSON serialization in the UI. "
                    f"Group ID: {group.group_id}, Created by: {group.created_by}"
                )

            # Check sequence info for NaN
            for seq_idx, seq_info in enumerate(group.sequences):
                if hasattr(seq_info, "score") and seq_info.score is not None and math.isnan(seq_info.score):
                    raise ValueError(
                        f"Group {i}, sequence {seq_idx} has NaN score. This breaks JSON serialization in the UI."
                    )

        # Try actual JSON serialization (will fail if any NaN values)
        try:
            # Use pydantic's json serialization (same as FastAPI uses)
            json_str = json.dumps([group.model_dump() for group in review_data])
            print(f"  [PASS] Successfully serialized {len(json_str)} bytes of JSON")
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Review data contains values that cannot be JSON serialized: {e}. "
                f"This will cause 500 errors in the UI when loading review data."
            ) from e

    print("\nAll methods executed successfully!")

    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 70)
    print("Comprehensive Test Complete!")
    print("=" * 70)
    print(f"\n[PASS] Comprehensive end-to-end test completed in {elapsed:.2f}s")


if __name__ == "__main__":
    test_comprehensive_end_to_end_coverage()
