"""Comprehensive end-to-end test for ComputeVersions.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions using minimal anonymized fixtures.

FIXTURE CONSTRUCTION:
For regenerating or updating the minimal test fixtures, see:
    tests/create_versions_test_fixtures.py

Construction workflow:
    python tests/create_versions_test_fixtures.py

REGRESSION TESTING:
This test is the ONLY coverage/regression test needed for CI.
It uses pre-generated minimal fixtures and validates all stage methods.

NOTE: The ComputeVersions stage currently has known issues. This test defines
correct behavior and may fail initially - that's expected and helps guide debugging.
"""

import pickle
import time
import traceback
from pathlib import Path

from src.utils.compute_versions import ComputeVersions
from src.utils.config import CONFIG
from src.utils.sequence import count_forest_ref_photos, count_forest_total_photos

from tests.fixtures.cache_loader import MockInputPort


def load_minimal_inputs() -> dict:
    """Load minimal fixtures for end-to-end testing.

    Returns:
        dict with keys:
            - 'template_bins': dict[str, list[tuple[INDEX_T, PhotoFile]]]
            - 'ref_seqs': int
            - 'ref_photos': int
    """
    fixture_path = Path("tests/fixtures/cache_snapshots/template_bins_minimal.pkl")

    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture file not found: {fixture_path}\nRun: python tests/create_versions_test_fixtures.py"
        )

    with fixture_path.open("rb") as f:
        data = pickle.load(f)

    # Unpack 5-tuple format: (template_bins, [], [], ref_photos, ref_seqs)
    template_bins, _seq_review, _id_review, ref_photos, ref_seqs = data

    return {
        "template_bins": template_bins,
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
    - forest_template_bins_o.read()
    - forest_template_bins_o.get_ref_photo_count()
    - forest_template_bins_o.get_ref_sequence_count()
    - forest_template_bins_o.timestamp()
    - template_remainder_bins_o.read()
    - template_remainder_bins_o.get_ref_photo_count()
    - template_remainder_bins_o.get_ref_sequence_count()
    - template_remainder_bins_o.timestamp()
    - Status updates (ref_photos_final, ref_seqs_final) for UI display
    - Atomic invariants (photo and sequence counts preserved)
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test: ComputeVersions")
    print("=" * 70)

    # Configure gates for multi-method code generation strategy
    # Use only hash methods we control (dhash, phash, ahash)
    # Set threshold to 0.70 (gives margin: 68.75% max similarity vs 70% threshold)
    original_gates = CONFIG.processing.COMPARISON_GATES
    original_thresholds = CONFIG.processing.GATE_THRESHOLDS.copy()

    CONFIG.processing.COMPARISON_GATES = ["dhash", "phash", "ahash"]
    CONFIG.processing.GATE_THRESHOLDS = {
        "dhash": 0.70,
        "phash": 0.70,
        "ahash": 0.70,
    }
    print(f"\nUsing comparison gates: {CONFIG.processing.COMPARISON_GATES}")
    print(f"Using thresholds: {CONFIG.processing.GATE_THRESHOLDS}")

    try:
        # Load minimal fixtures
        print("\nLoading minimal fixtures...")
        inputs = load_minimal_inputs()
        print(f"  Template bins: {len(inputs['template_bins'])} bins")
        print(f"  Reference sequences: {inputs['ref_seqs']}")
        print(f"  Reference photos: {inputs['ref_photos']}")

        # Show bin details
        print("\n  Bin details:")
        for i, (template, photos) in enumerate(inputs["template_bins"].items(), 1):
            print(f"    {i}. {template}: {len(photos)} photos")

        start_time = time.perf_counter()

        # [1] Create stage (tests __init__)
        print("\n[1/15] Creating stage (__init__)...")
        stage = ComputeVersions()
        print(f"  Stage name: {stage.stage_name}")
        print(f"  Output path: {stage.path}")
        assert stage.stage_name == "Version Detection", "Stage name must be 'Version Detection'"

        # Test has_review_data() before stage runs (should return False)
        assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
        print("  [OK] has_review_data() returns False before stage runs")

        # Inject test data
        stage.template_bins_i = MockInputPort(inputs["template_bins"], inputs["ref_seqs"], inputs["ref_photos"])

        # [2] Run prepare (tests prepare)
        print("[2/15] Running prepare()...")
        work_items, accumulator = stage.prepare()
        print(f"  Work items generated: {len(work_items)}")

        # Show work items sorted by size
        work_sizes = [len(item[1]) for item in work_items]
        print(f"  Work items sorted by size (descending): {work_sizes}")

        # Validate prepare results
        assert len(work_items) == inputs["ref_seqs"], (
            f"Work item count should match input sequences: {len(work_items)} != {inputs['ref_seqs']}"
        )

        # Verify sorting (largest first)
        for i in range(len(work_sizes) - 1):
            assert work_sizes[i] >= work_sizes[i + 1], (
                f"Work items not sorted by size: {work_sizes[i]} < {work_sizes[i + 1]}"
            )

        # Verify total photo count
        total_photos_in_work = sum(len(item[1]) for item in work_items)
        assert total_photos_in_work == inputs["ref_photos"], (
            f"Total photos in work items should match: {total_photos_in_work} != {inputs['ref_photos']}"
        )

        print(f"  [OK] Work items validated: {len(work_items)} items, {total_photos_in_work} photos")

        # [3] Process ALL work items through stage_worker (tests stage_worker)
        print("[3/15] Processing ALL work items through stage_worker()...")
        worker_results = []
        validation_failures = []  # Collect all failures to report at end

        # Expected behavior for each bin (defines correct version detection)
        expected_results = {
            "TEST_F_{P0}_{P1}.jpg": {
                "should_detect_versions": False,  # Too many unique values (>10)
                "expected_version_count": None,
                "description": "Field has >MAX_COMPONENT_SIZE unique values",
            },
            "TEST_E_{P0}_{P1}_{P2}.jpg": {
                "should_detect_versions": True,
                "expected_version_count": 6,  # 3 versions (P1: va,vb,vc) x 2 sub-versions (P2: s1,s2) = 6 combos
                "expected_ref_photos": 5,  # One reference photo per P0 value (001-005)
                "description": "Multi-field versions: both P1 and P2 are version fields",
            },
            "TEST_D_{P0}_{P1}.jpg": {
                "should_detect_versions": True,
                "expected_version_count": 2,  # P1 has 2 versions: v1, v2
                "expected_ref_photos": 5,  # One reference per P0 value (001-005)
                "description": "Simple version detection: P1 is version field",
            },
            "TEST_G_{P0}_{P1}.jpg": {
                "should_detect_versions": True,  # Hash-only gates pass (aspect_ratio not in gate list)
                "expected_version_count": 2,  # P1 has 2 versions: v1, v2
                "expected_ref_photos": 4,  # One reference per P0 value (001-004)
                "description": "Hash gates pass (aspect_ratio gate not active in test config)",
            },
            "TEST_C_{P0}_{P1}.jpg": {
                "should_detect_versions": False,  # All photos are different
                "expected_version_count": None,
                "description": "No versions - all photos have unique values",
            },
            "TEST_B_{P0}.jpg": {
                "should_detect_versions": True,  # Single-field IS the version
                "expected_version_count": 3,  # 3 versions: v1, v2, v3
                "expected_ref_photos": 1,  # One exemplar chosen even when all fields are version fields
                "description": "Single-field version: exemplar selection when template has only version fields",
            },
            "TEST_A_{P0}.jpg": {
                "should_detect_versions": False,  # Singleton - early exit
                "expected_version_count": None,
                "description": "Singleton bin - early exit",
            },
            "TEST_H_{P0}_{P1}.jpg": {
                "should_detect_versions": False,  # Asymmetric - not all groups pass
                "expected_version_count": None,
                "description": "Asymmetric matching: group 001 fails, group 002 passes (reject hypothesis)",
            },
            "TEST_I_{P0}_{P1}.jpg": {
                "should_detect_versions": False,  # 3 mismatches > MAX_MISMATCHES=2
                "expected_version_count": None,
                "description": "Boundary case: 3 mismatches exceeds MAX_MISMATCHES=2",
            },
            "TEST_J_{P0}_{P1}.jpg": {
                "should_detect_versions": False,  # One group has >MAX_MISMATCHES
                "expected_version_count": None,
                "description": "Per-group threshold: group 3 has 3 mismatches > MAX_MISMATCHES=2",
            },
        }

        for i, work_item in enumerate(work_items):
            template_key, photos = work_item
            print(f"  Processing bin {i + 1}/{len(work_items)}: {template_key} ({len(photos)} photos)...")

            try:
                # stage_worker returns (id_reviews, seq_reviews, result)
                _id_reviews, _seq_reviews, result = ComputeVersions.stage_worker(work_item, created_by="test")
                worker_results.append(result)

                # Show result details
                print(f"    Result: {result.n_photos} photos, is_class={result.is_class()}")
                if result.is_class():
                    print(f"    Version sequences: {len(result.sequences)}")
                    for j, version_seq in enumerate(result.sequences):
                        print(f"      Version {j + 1}: {version_seq.n_ref_photos} photos")

                # Validate against expected behavior
                expected = expected_results.get(template_key)
                if expected:
                    print(f"    Expected: {expected['description']}")

                    # Check if version detection matches expectations
                    if expected["should_detect_versions"]:
                        if not result.is_class():
                            error_msg = (
                                f"Bin {template_key} should detect versions but didn't. "
                                f"Expected: {expected['description']}"
                            )
                            validation_failures.append(error_msg)
                            print(f"    [FAIL] {error_msg}")
                        elif (
                            expected.get("expected_version_count")
                            and len(result.sequences) != expected["expected_version_count"]
                        ):
                            error_msg = (
                                f"Bin {template_key} detected {len(result.sequences)} versions "
                                f"but expected {expected['expected_version_count']}. "
                                f"Expected: {expected['description']}"
                            )
                            validation_failures.append(error_msg)
                            print(f"    [FAIL] {error_msg}")
                        elif (
                            expected.get("expected_ref_photos") is not None
                            and result.n_ref_photos != expected["expected_ref_photos"]
                        ):
                            error_msg = (
                                f"Bin {template_key} has {result.n_ref_photos} reference photos "
                                f"but expected {expected['expected_ref_photos']}"
                            )
                            validation_failures.append(error_msg)
                            print(f"    [FAIL] {error_msg}")
                        else:
                            print("    [OK] Version detection correct")
                    elif result.is_class():
                        error_msg = (
                            f"Bin {template_key} should NOT detect versions but did. "
                            f"Detected {len(result.sequences)} versions. "
                            f"Expected: {expected['description']}"
                        )
                        validation_failures.append(error_msg)
                        print(f"    [FAIL] {error_msg}")
                    else:
                        print("    [OK] Correctly did not detect versions")

            except AssertionError as e:
                # Catch assertion errors and continue
                validation_failures.append(f"Bin {template_key}: {e!s}")
                print(f"    [FAIL] Assertion error: {e}")
            except Exception as e:
                print(f"    ERROR in stage_worker: {e}")

                traceback.print_exc()
                raise

        # Report validation results
        if validation_failures:
            print(f"\n  [VALIDATION FAILURES] {len(validation_failures)} bin(s) failed:")
            for failure in validation_failures:
                print(f"    - {failure}")
        else:
            print("\n  [OK] All bins validated successfully")

        # Validate worker results
        total_photos_in_results = sum(r.n_photos for r in worker_results)
        assert total_photos_in_results == inputs["ref_photos"], (
            f"Total photos in results should match: {total_photos_in_results} != {inputs['ref_photos']}"
        )
        print(f"  [OK] All work items processed: {len(worker_results)} results")

        # [4] Accumulate results (tests accumulate_results)
        print("[4/15] Running accumulate_results()...")
        for result_seq in worker_results:
            stage.accumulate_results(accumulator, result_seq)

        forest, template_bins = accumulator
        print(f"  Total sequences accumulated: {len(forest)}")
        print(f"  Template remainder bins: {len(template_bins)} groups")

        # Validate accumulation
        assert len(forest) == len(worker_results), (
            f"Forest should have one sequence per result: {len(forest)} != {len(worker_results)}"
        )
        print("  [OK] Results accumulated successfully")

        # [5] Finalize stage (tests finalise)
        print("[5/15] Running finalise()...")
        stage.result = accumulator
        stage.finalise()
        print(f"  Final sequences: {stage.ref_seqs_final}")
        print(f"  Final photos: {stage.ref_photos_final}")

        # Validate status updates (for UI display)
        print("\n  Validating status updates...")
        assert stage.ref_photos_final is not None, "ref_photos_final must not be None"
        assert stage.ref_seqs_final is not None, "ref_seqs_final must not be None"
        assert isinstance(stage.ref_photos_final, int), (
            f"ref_photos_final must be int, got {type(stage.ref_photos_final)}"
        )
        assert isinstance(stage.ref_seqs_final, int), f"ref_seqs_final must be int, got {type(stage.ref_seqs_final)}"

        # ComputeVersions is FIRST grouping stage - must preserve TOTAL photos internally
        # The atomic invariant (total photos in = total photos out) is checked by finalise()
        # which will raise ValueError if violated.

        # ref_photos_final is the count of REFERENCE photos (not versions) for downstream stages
        # This will be less than total_photos if version grouping occurred

        expected_ref_photos = count_forest_ref_photos(forest)
        expected_total_photos = count_forest_total_photos(forest)

        # Verify ref_photos_final is correct for downstream stages
        assert stage.ref_photos_final == expected_ref_photos, (
            f"ref_photos_final should match reference count in forest: "
            f"{stage.ref_photos_final} != {expected_ref_photos}"
        )

        # Verify total photos were preserved (atomic invariant)
        # This is also checked in finalise(), but verify here for test clarity
        assert expected_total_photos == inputs["ref_photos"], (
            f"Total photos must be preserved: started {inputs['ref_photos']}, ended {expected_total_photos}"
        )

        # ref_photos_final should be <= total photos (some photos become versions)
        assert stage.ref_photos_final <= expected_total_photos, (
            f"Reference photos ({stage.ref_photos_final}) cannot exceed total photos ({expected_total_photos})"
        )

        assert stage.ref_seqs_final == inputs["ref_seqs"], (
            f"Sequence count should match input bins: started {inputs['ref_seqs']}, ended {stage.ref_seqs_final}"
        )

        print(f"  [OK] Status updates valid: photos={stage.ref_photos_final}, seqs={stage.ref_seqs_final}")

        # [6] Test review methods
        print("[6/15] Testing needs_review()...")
        review_type = stage.needs_review()
        assert review_type == "sequences", f"Expected review type 'sequences', got '{review_type}'"
        print(f"  Review type: {review_type}")

        print("[7/15] Testing has_review_data()...")
        has_review = stage.has_review_data()
        print(f"  Has review data: {has_review}")

        # [8] Test forest_template_bins_o.read()
        print("\n[8/15] Testing forest_template_bins_o.read()...")
        full_result = stage.forest_template_bins_o.read()
        assert full_result is stage.result, "forest_template_bins_o.read() should return stage.result"
        assert isinstance(full_result, tuple), f"Result should be tuple, got {type(full_result)}"
        assert len(full_result) == 2, f"Result tuple should have 2 elements, got {len(full_result)}"
        result_forest, result_bins = full_result
        assert len(result_forest) == len(forest), (
            f"Forest from port should match: {len(result_forest)} != {len(forest)}"
        )
        print(f"  Full result via OutputPort: {len(result_forest)} sequences, {len(result_bins)} template bins")
        print("  [OK] forest_template_bins_o.read() returns correct result")

        # [9] Test forest_template_bins_o.get_ref_photo_count()
        print("\n[9/15] Testing forest_template_bins_o.get_ref_photo_count()...")
        photo_count = stage.forest_template_bins_o.get_ref_photo_count()
        assert photo_count == stage.ref_photos_final, (
            f"OutputPort photo count should match ref_photos_final: {photo_count} != {stage.ref_photos_final}"
        )
        print(f"  Photo count via OutputPort: {photo_count}")
        print("  [OK] forest_template_bins_o.get_ref_photo_count() returns correct count")

        # [10] Test forest_template_bins_o.get_ref_sequence_count()
        print("\n[10/15] Testing forest_template_bins_o.get_ref_sequence_count()...")
        seq_count = stage.forest_template_bins_o.get_ref_sequence_count()
        assert seq_count == stage.ref_seqs_final, (
            f"OutputPort sequence count should match ref_seqs_final: {seq_count} != {stage.ref_seqs_final}"
        )
        print(f"  Sequence count via OutputPort: {seq_count}")
        print("  [OK] forest_template_bins_o.get_ref_sequence_count() returns correct count")

        # [11] Test forest_template_bins_o.timestamp()
        print("\n[11/15] Testing forest_template_bins_o.timestamp()...")
        try:
            timestamp = stage.forest_template_bins_o.timestamp()
            # If we get here, the stage's cache exists (unexpected in this test)
            print(f"  Timestamp: {timestamp}")
            print("  [NOTE] Cache exists, timestamp returned (not expected in isolated test)")
        except RuntimeError as e:
            # Expected behavior: cache doesn't exist in isolated test
            print(f"  RuntimeError raised (expected): {e}")
            print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

        # [12] Test template_remainder_bins_o.read()
        print("\n[12/15] Testing template_remainder_bins_o.read()...")
        remainder_bins = stage.template_remainder_bins_o.read()
        assert remainder_bins is stage.result[1], "template_remainder_bins_o.read() should return stage.result[1]"
        assert len(remainder_bins) == len(template_bins), (
            f"Template bins from port should match: {len(remainder_bins)} != {len(template_bins)}"
        )
        print(f"  Template remainder bins via OutputPort: {len(remainder_bins)} bins")
        print("  [OK] template_remainder_bins_o.read() returns correct result")

        # [13] Test template_remainder_bins_o.get_ref_photo_count()
        print("\n[13/15] Testing template_remainder_bins_o.get_ref_photo_count()...")
        photo_count_bins = stage.template_remainder_bins_o.get_ref_photo_count()
        # This port returns just template_bins, so photo count should still be ref_photos_final
        assert photo_count_bins == stage.ref_photos_final, (
            f"OutputPort photo count should match ref_photos_final: {photo_count_bins} != {stage.ref_photos_final}"
        )
        print(f"  Photo count via OutputPort: {photo_count_bins}")
        print("  [OK] template_remainder_bins_o.get_ref_photo_count() returns correct count")

        # [14] Test template_remainder_bins_o.get_ref_sequence_count()
        print("\n[14/15] Testing template_remainder_bins_o.get_ref_sequence_count()...")
        seq_count_bins = stage.template_remainder_bins_o.get_ref_sequence_count()
        # OutputPort returns stage-level count, not port-specific count
        assert seq_count_bins == stage.ref_seqs_final, (
            f"OutputPort sequence count should match ref_seqs_final: {seq_count_bins} != {stage.ref_seqs_final}"
        )
        print(f"  Sequence count via OutputPort: {seq_count_bins}")
        print(f"  [NOTE] OutputPort returns stage-level count ({seq_count_bins}), not dict keys ({len(template_bins)})")
        print("  [OK] template_remainder_bins_o.get_ref_sequence_count() returns correct count")

        # [15] Test template_remainder_bins_o.timestamp()
        print("\n[15/15] Testing template_remainder_bins_o.timestamp()...")
        try:
            timestamp_bins = stage.template_remainder_bins_o.timestamp()
            # If we get here, the stage's cache exists (unexpected in this test)
            print(f"  Timestamp: {timestamp_bins}")
            print("  [NOTE] Cache exists, timestamp returned (not expected in isolated test)")
        except RuntimeError as e:
            # Expected behavior: cache doesn't exist in isolated test
            print(f"  RuntimeError raised (expected): {e}")
            print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

        # Validate review data structure if present
        if has_review:
            print("\n  Examining review data...")
        classes_found = sum(1 for seq in forest if seq.is_class())
        print(f"    Classes (version groups) found: {classes_found}")

        # Examine class structures
        for i, seq in enumerate(forest):
            if seq.is_class():
                print(f"    Class {i + 1}: {seq.name}")
                print(f"      Reference photos: {seq.n_ref_photos}")
                print(f"      Total photos: {seq.n_photos}")
                print(f"      Version sequences: {len(seq.sequences)}")

                # Show version sequence details
                for j, version_seq in enumerate(seq.sequences):
                    print(f"        Version {j + 1}: {version_seq.name} ({version_seq.n_ref_photos} photos)")
        print("    No version classes detected (all preliminary sequences)")

        elapsed = time.perf_counter() - start_time

        print("\n" + "=" * 70)
        print("Comprehensive Test Complete!")
        print("=" * 70)

        # Summary statistics
        print("\nTest Summary:")
        print(f"  Bins tested: {len(inputs['template_bins'])}")
        print(f"  Photos processed: {inputs['ref_photos']}")
        print(f"  Sequences created: {len(forest)}")
        if has_review:
            print(f"  Version classes detected: {classes_found}")
        print(f"  Time elapsed: {elapsed:.2f}s")

        # Final validation check
        if validation_failures:
            print(f"\n[FAIL] {len(validation_failures)} bin validation failure(s)")
            raise AssertionError(
                f"{len(validation_failures)} bin(s) failed validation:\n"
                + "\n".join(f"  - {f}" for f in validation_failures)
            )
        print("\n[PASS] All bins passed validation!")

    finally:
        # Restore original comparison gates and thresholds
        CONFIG.processing.COMPARISON_GATES = original_gates
        CONFIG.processing.GATE_THRESHOLDS = original_thresholds


if __name__ == "__main__":
    test_comprehensive_end_to_end_coverage()
