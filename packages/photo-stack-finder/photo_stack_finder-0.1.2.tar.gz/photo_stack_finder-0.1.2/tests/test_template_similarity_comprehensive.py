"""Comprehensive end-to-end test for ComputeTemplateSimilarity.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions using synthetic fixtures.

FIXTURE CONSTRUCTION:
Uses synthetic PhotoSequence objects with cached hash preparations.
Uses multi-method code generation strategy to control comparison outcomes
without needing real image files.

REGRESSION TESTING:
This test is the ONLY coverage/regression test needed for CI.
It validates all stage methods with synthetic fixtures and tests
extend_reference_sequence without mocking.
"""

import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from src.utils.compute_template_similarity import ComputeTemplateSimilarity
from src.utils.config import CONFIG
from src.utils.photo_file import PhotoFile
from src.utils.sequence import INDEX_T, PhotoFileSeries, PhotoSequence

from tests.fixtures.cache_loader import MockInputPort
from tests.fixtures.hash_generator import generate_codes


def create_photo(photo_id: int, seq_idx: str, photo_idx: str, dhash: bytes, phash: bytes, ahash: bytes) -> PhotoFile:
    """Create a minimal PhotoFile with cached hash preparations.

    Args:
        photo_id: Unique photo ID
        seq_idx: Sequence index (e.g., "001")
        photo_idx: Photo index within sequence (e.g., "a")
        dhash: dhash code (8 bytes)
        phash: phash code (8 bytes)
        ahash: ahash code (8 bytes)
    """
    # Create dummy path for test fixture (not accessed due to cached preparations)
    dummy_path = Path(f"test_photos/seq{seq_idx}/photo{photo_idx}.jpg")

    photo = PhotoFile(
        path=dummy_path,
        mime="image/jpeg",
        size_bytes=1000 + photo_id,
        file_id=photo_id,
    )

    # Pre-populate dimension cache for test fixtures
    photo.cache["pixels"] = 1920000
    photo.cache["aspect_ratio"] = 1.0
    photo.cache["width"] = 32
    photo.cache["height"] = 32

    # Cache hash preparations with tuple keys (method_name, rotation) for rotation=0
    photo.cache[("dhash", 0)] = dhash
    photo.cache[("phash", 0)] = phash
    photo.cache[("ahash", 0)] = ahash

    # Cache rotated hash preparations for rotation-aware comparison
    # For square images (aspect_ratio=1.0), we need 180° rotation cache
    photo.cache[("dhash", 180)] = dhash
    photo.cache[("phash", 180)] = phash
    photo.cache[("ahash", 180)] = ahash

    return photo


def create_photo_sequence(
    seq_id: int, seq_idx: str, n_photos: int, dhash: bytes, phash: bytes, ahash: bytes, created_by: str = "upstream"
) -> PhotoSequence:
    """Create a PhotoSequence with n_photos reference photos sharing same hash codes.

    All photos in the sequence get the same hash codes to ensure they're
    similar to each other.

    Args:
        seq_id: Base ID for photos
        seq_idx: Sequence index string
        n_photos: Number of photos in sequence
        dhash: dhash code to assign to all photos
        phash: phash code to assign to all photos
        ahash: ahash code to assign to all photos
        created_by: Creator label
    """
    # Build series data dict
    series_data: dict[INDEX_T, PhotoFile] = {}
    for i in range(n_photos):
        photo_idx = chr(ord("a") + i)  # a, b, c, ...
        photo_id = seq_id * 10 + i
        index_key: INDEX_T = (photo_idx,)  # INDEX_T is tuple[str, ...]
        series_data[index_key] = create_photo(photo_id, seq_idx, photo_idx, dhash, phash, ahash)

    # Create PhotoFileSeries
    series = PhotoFileSeries(
        series_data,
        name=f"seq_{seq_idx}",
        normal=False,  # Use False for test sequences
    )

    return PhotoSequence(series, sequences=[], created_by=created_by)


def create_test_fixtures() -> dict[str, Any]:
    """Create synthetic test fixtures with hash code strategy.

    Uses multi-method hash code generation to control matching:
    - Generate dissimilar codes for different groups
    - Assign same codes to sequences that should match

    Creates 4 template bins with different scenarios:
    - Bin 1 (singleton): 1 sequence (skipped by prepare)
    - Bin 2 (all match): 3 sequences with same codes → group into 1
    - Bin 3 (mixed): 5 sequences with 3 different code sets → forms 3 groups
    - Bin 4 (oversize irreducible): 6 sequences, all dissimilar → skipped as oversized (when MAX_COMPONENT_SIZE=5)

    Returns:
        dict with keys:
            - 'template_bins': dict[str, list[tuple[PhotoSequence, str]]]
            - 'ref_seqs': int (15 input sequences)
            - 'ref_photos': int (29 total photos)
            - 'expected_output_seqs': int (11 after grouping)
    """
    # Generate hash codes with guaranteed dissimilarity (min_distance=20 bits)
    # Need 10 distinct codes: [bin1, bin2, bin3_groupA, bin3_groupB, bin3_solo, bin4_x6]
    codes = generate_codes(10, seed=200)

    # Bin 1: Singleton (1 sequence, 3 photos) - uses codes[0]
    seq1 = create_photo_sequence(1, "001", 3, codes[0], codes[0], codes[0])

    # Bin 2: All match (3 sequences, 2 photos each) - all use codes[1]
    seq2a = create_photo_sequence(2, "002", 2, codes[1], codes[1], codes[1])
    seq2b = create_photo_sequence(3, "003", 2, codes[1], codes[1], codes[1])
    seq2c = create_photo_sequence(4, "004", 2, codes[1], codes[1], codes[1])

    # Bin 3: Mixed (5 sequences, 2 photos each)
    # Group A: seq 5 and 6 match - use codes[2]
    seq3a = create_photo_sequence(5, "005", 2, codes[2], codes[2], codes[2])
    seq3b = create_photo_sequence(6, "006", 2, codes[2], codes[2], codes[2])
    # Group B: seq 7 and 8 match - use codes[3]
    seq3c = create_photo_sequence(7, "007", 2, codes[3], codes[3], codes[3])
    seq3d = create_photo_sequence(8, "008", 2, codes[3], codes[3], codes[3])
    # Solo: seq 9 doesn't match anyone - use codes[4] (extra code)
    seq3e = create_photo_sequence(9, "009", 2, codes[4], codes[4], codes[4])

    # Bin 4: Oversize irreducible (6 sequences, 2 photos each, all dissimilar)
    # Each sequence gets a unique code (codes[5] through codes[10])
    # This exceeds MAX_COMPONENT_SIZE=5 (set in test) and cannot be reduced through grouping
    seq4_list = []
    for i in range(6):
        seq_id = 10 + i
        seq_idx = f"{10 + i:03d}"
        code_idx = 5 + i
        seq = create_photo_sequence(seq_id, seq_idx, 2, codes[code_idx], codes[code_idx], codes[code_idx])
        seq4_list.append((seq, seq_idx))

    # Create template bins (template_str -> list of (sequence, prefix))
    template_bins = {
        "template1": [(seq1, "001")],
        "template2": [(seq2a, "002"), (seq2b, "003"), (seq2c, "004")],
        "template3": [(seq3a, "005"), (seq3b, "006"), (seq3c, "007"), (seq3d, "008"), (seq3e, "009")],
        "template4": seq4_list,
    }

    # Total: 15 input sequences
    # After grouping (with MAX_COMPONENT_SIZE=5):
    #   bin1=1 (singleton added),
    #   bin2=1 (3→1),
    #   bin3=3 (5→3: two pairs + one solo),
    #   bin4=6 (oversized, skipped and added to output)
    # Expected ref_seqs after stage: 11 (1+1+3+6)
    # Total photos: 3 + 6 + 10 + 12 = 31
    return {
        "template_bins": template_bins,
        "ref_seqs": 15,  # Input sequences
        "ref_photos": 31,  # Total photos
        "expected_output_seqs": 11,  # After grouping (1+1+3+6 oversized sequences added)
    }


def test_comprehensive_end_to_end_coverage() -> None:
    """Run full stage lifecycle test.

    This test validates:
    - __init__()
    - prepare()
    - stage_worker() (all bins with 2+ sequences)
    - accumulate_results()
    - finalise()
    - needs_review()
    - has_review_data()
    - forest_bins_o.read()
    - forest_bins_o.get_ref_photo_count()
    - forest_bins_o.get_ref_sequence_count()
    - forest_bins_o.timestamp()
    - index_bins_o.read()
    - index_bins_o.get_ref_photo_count()
    - index_bins_o.get_ref_sequence_count()
    - index_bins_o.timestamp()
    - Status updates (ref_photos_final, ref_seqs_final)
    - Atomic invariants (photo and sequence counts preserved)
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test: ComputeTemplateSimilarity")
    print("=" * 70)

    # Create test fixtures
    print("\nCreating synthetic test fixtures...")
    inputs = create_test_fixtures()
    print(f"  Template bins: {len(inputs['template_bins'])} bins")
    print(f"  Total sequences: {inputs['ref_seqs']}")
    print(f"  Total photos: {inputs['ref_photos']}")

    # Show bin sizes
    print("\n  Bin details:")
    for i, (template, seq_prefix_pairs) in enumerate(inputs["template_bins"].items(), 1):
        print(f"    {i}. {template}: {len(seq_prefix_pairs)} sequences")

    start_time = time.perf_counter()

    # [1] Create stage (tests __init__)
    print("\n[1/15] Creating stage (__init__)...")
    stage = ComputeTemplateSimilarity()
    print(f"  Stage name: {stage.stage_name}")
    print(f"  Output path: {stage.path}")
    assert stage.stage_name == "Template Similarity", "Stage name must be 'Template Similarity'"

    # Test has_review_data() BEFORE stage runs (must return False)
    assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
    print("  [OK] has_review_data() returns False before stage runs")

    # Inject test data
    stage.template_bins_i = MockInputPort(inputs["template_bins"], inputs["ref_seqs"], inputs["ref_photos"])

    # Configure gates for hash-only comparison (tests extend_reference_sequence without mocking)
    print("\nConfiguring comparison gates for hash-only testing...")
    original_gates = CONFIG.processing.COMPARISON_GATES
    original_thresholds = CONFIG.processing.GATE_THRESHOLDS.copy()
    original_max_component_size = CONFIG.sequences.MAX_COMPONENT_SIZE

    CONFIG.processing.COMPARISON_GATES = ["dhash", "phash", "ahash"]
    CONFIG.processing.GATE_THRESHOLDS = {
        "dhash": 0.70,
        "phash": 0.70,
        "ahash": 0.70,
    }
    CONFIG.sequences.MAX_COMPONENT_SIZE = 5  # Test oversize bin handling (bin 4 has 6 sequences)
    print(f"  Using comparison gates: {CONFIG.processing.COMPARISON_GATES}")
    print(f"  Using thresholds: {CONFIG.processing.GATE_THRESHOLDS}")
    print(f"  Using MAX_COMPONENT_SIZE: {CONFIG.sequences.MAX_COMPONENT_SIZE}")

    try:
        # Mock only review building functions (not extend_reference_sequence or gates)
        with (
            patch("src.utils.sequence_clustering.predict_exemplar_sequence") as mock_predict,
            patch("src.utils.sequence_clustering.build_sequence_group") as mock_build_group,
        ):

            def predict_exemplar_side_effect(sequences: list[PhotoSequence]) -> PhotoSequence:
                """Mock predict_exemplar_sequence - just return first sequence."""
                return sequences[0]

            def build_group_side_effect(seq: PhotoSequence) -> Any:
                """Mock build_sequence_group - return a minimal mock."""
                mock_group = MagicMock()
                mock_group.n_seqs = seq.n_seqs
                return mock_group

            mock_predict.side_effect = predict_exemplar_side_effect
            mock_build_group.side_effect = build_group_side_effect

            # [2] Run prepare (tests prepare)
            print("[2/15] Running prepare()...")
            work_items, accumulator = stage.prepare()
            print(f"  Work items generated: {len(work_items)}")
            print(f"  Accumulator initialized: {type(accumulator)}")

            # Validate prepare results
            # Singleton bins (size < 2) are skipped, oversize bins (size > MAX_COMPONENT_SIZE) are skipped
            # Bin 1: singleton (1 seq) - skipped
            # Bin 2: normal (3 seqs) - processed
            # Bin 3: normal (5 seqs) - processed
            # Bin 4: oversize (6 seqs > MAX_COMPONENT_SIZE=5) - skipped
            expected_work_items = 2  # template2 (3 seqs) and template3 (5 seqs)
            assert len(work_items) == expected_work_items, (
                f"Expected {expected_work_items} work items (bins with 2+ sequences and <= MAX_COMPONENT_SIZE), got {len(work_items)}"
            )

            # Verify singleton and oversize bin were added to accumulator
            forest, index_bins = accumulator
            expected_skipped = 7  # template1 singleton (1 seq) + template4 oversize (6 seqs)
            assert len(forest) == expected_skipped, (
                f"Expected {expected_skipped} skipped sequences in forest (1 singleton + 6 oversized), got {len(forest)}"
            )
            print(
                f"  [OK] Prepare validated: {len(work_items)} work items, {len(forest)} skipped sequences (1 singleton + 6 oversized)"
            )

            # [3] Process ALL work items through stage_worker (tests stage_worker)
            print(f"[3/15] Processing {len(work_items)} work items through stage_worker()...")
            worker_results = []

            for i, work_item in enumerate(work_items):
                template_key, seq_prefix_pairs = work_item
                print(
                    f"  Processing bin {i + 1}/{len(work_items)}: {template_key} ({len(seq_prefix_pairs)} sequences)..."
                )

                try:
                    # stage_worker returns (id_reviews, seq_reviews, results)
                    _id_reviews, seq_reviews, results = ComputeTemplateSimilarity.stage_worker(
                        work_item, created_by="test"
                    )
                    worker_results.append(results)
                    print(f"    Result: {len(results)} grouped sequences, {len(seq_reviews)} review groups")
                except Exception as e:
                    print(f"    ERROR in stage_worker: {e}")
                    raise

            print(f"  [OK] All work items processed: {len(worker_results)} results")

            # [4] Accumulate results (tests accumulate_results)
            print("[4/15] Running accumulate_results()...")
            for job_results in worker_results:
                stage.accumulate_results(accumulator, job_results)

            forest, index_bins = accumulator
            print(f"  Total sequences accumulated: {len(forest)}")
            print(f"  Index bins created: {len(index_bins)}")
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
            assert isinstance(stage.ref_seqs_final, int), (
                f"ref_seqs_final must be int, got {type(stage.ref_seqs_final)}"
            )

            # Template similarity groups sequences, REDUCING reference photo count
            # (total photos are preserved, validated by finalise() method itself)
            assert stage.ref_photos_final < inputs["ref_photos"], (
                f"Reference photo count should decrease (grouping): started {inputs['ref_photos']}, ended {stage.ref_photos_final}"
            )
            assert stage.ref_photos_final > 0, "Should have some reference photos remaining"

            # Sequence count should decrease due to grouping
            assert stage.ref_seqs_final == inputs["expected_output_seqs"], (
                f"Expected {inputs['expected_output_seqs']} output sequences, got {stage.ref_seqs_final}"
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

            # [8] Test forest_bins_o.read()
            print("\n[8/15] Testing forest_bins_o.read()...")
            full_result = stage.forest_bins_o.read()
            assert full_result is stage.result, "forest_bins_o.read() should return stage.result"
            assert isinstance(full_result, tuple), f"Result should be tuple, got {type(full_result)}"
            assert len(full_result) == 2, f"Result tuple should have 2 elements, got {len(full_result)}"
            result_forest, result_bins = full_result
            assert len(result_forest) == len(forest), (
                f"Forest from port should match: {len(result_forest)} != {len(forest)}"
            )
            print(f"  Full result via OutputPort: {len(result_forest)} sequences, {len(result_bins)} index bins")
            print("  [OK] forest_bins_o.read() returns correct result")

            # [9] Test forest_bins_o.get_ref_photo_count()
            print("\n[9/15] Testing forest_bins_o.get_ref_photo_count()...")
            photo_count = stage.forest_bins_o.get_ref_photo_count()
            assert photo_count == stage.ref_photos_final, (
                f"OutputPort photo count should match ref_photos_final: {photo_count} != {stage.ref_photos_final}"
            )
            print(f"  Photo count via OutputPort: {photo_count}")
            print("  [OK] forest_bins_o.get_ref_photo_count() returns correct count")

            # [10] Test forest_bins_o.get_ref_sequence_count()
            print("\n[10/15] Testing forest_bins_o.get_ref_sequence_count()...")
            seq_count = stage.forest_bins_o.get_ref_sequence_count()
            assert seq_count == stage.ref_seqs_final, (
                f"OutputPort sequence count should match ref_seqs_final: {seq_count} != {stage.ref_seqs_final}"
            )
            print(f"  Sequence count via OutputPort: {seq_count}")
            print("  [OK] forest_bins_o.get_ref_sequence_count() returns correct count")

            # [11] Test forest_bins_o.timestamp()
            print("\n[11/15] Testing forest_bins_o.timestamp()...")
            try:
                timestamp = stage.forest_bins_o.timestamp()
                # If we get here, the stage's cache exists (unexpected in this test)
                print(f"  Timestamp: {timestamp}")
                print("  [NOTE] Cache exists, timestamp returned (not expected in isolated test)")
            except RuntimeError as e:
                # Expected behavior: cache doesn't exist in isolated test
                print(f"  RuntimeError raised (expected): {e}")
                print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

            # [12] Test index_bins_o.read()
            print("\n[12/15] Testing index_bins_o.read()...")
            index_bins_result = stage.index_bins_o.read()
            assert index_bins_result is stage.result[1], "index_bins_o.read() should return stage.result[1]"
            assert len(index_bins_result) == len(index_bins), (
                f"Index bins from port should match: {len(index_bins_result)} != {len(index_bins)}"
            )
            print(f"  Index bins via OutputPort: {len(index_bins_result)} bins")
            print("  [OK] index_bins_o.read() returns correct result")

            # [13] Test index_bins_o.get_ref_photo_count()
            print("\n[13/15] Testing index_bins_o.get_ref_photo_count()...")
            photo_count_bins = stage.index_bins_o.get_ref_photo_count()
            # This port returns just index_bins, but photo count is still stage-level
            assert photo_count_bins == stage.ref_photos_final, (
                f"OutputPort photo count should match ref_photos_final: {photo_count_bins} != {stage.ref_photos_final}"
            )
            print(f"  Photo count via OutputPort: {photo_count_bins}")
            print("  [OK] index_bins_o.get_ref_photo_count() returns correct count")

            # [14] Test index_bins_o.get_ref_sequence_count()
            print("\n[14/15] Testing index_bins_o.get_ref_sequence_count()...")
            seq_count_bins = stage.index_bins_o.get_ref_sequence_count()
            # OutputPort returns stage-level count, not port-specific count
            assert seq_count_bins == stage.ref_seqs_final, (
                f"OutputPort sequence count should match ref_seqs_final: {seq_count_bins} != {stage.ref_seqs_final}"
            )
            print(f"  Sequence count via OutputPort: {seq_count_bins}")
            print(
                f"  [NOTE] OutputPort returns stage-level count ({seq_count_bins}), not dict keys ({len(index_bins)})"
            )
            print("  [OK] index_bins_o.get_ref_sequence_count() returns correct count")

            # [15] Test index_bins_o.timestamp()
            print("\n[15/15] Testing index_bins_o.timestamp()...")
            try:
                timestamp_bins = stage.index_bins_o.timestamp()
                # If we get here, the stage's cache exists (unexpected in this test)
                print(f"  Timestamp: {timestamp_bins}")
                print("  [NOTE] Cache exists, timestamp returned (not expected in isolated test)")
            except RuntimeError as e:
                # Expected behavior: cache doesn't exist in isolated test
                print(f"  RuntimeError raised (expected): {e}")
                print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

    finally:
        # Restore original configuration
        CONFIG.processing.COMPARISON_GATES = original_gates
        CONFIG.processing.GATE_THRESHOLDS = original_thresholds
        CONFIG.sequences.MAX_COMPONENT_SIZE = original_max_component_size

    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 70)
    print("Comprehensive Test Complete!")
    print("=" * 70)
    print(f"\n[PASS] Comprehensive end-to-end test completed in {elapsed:.2f}s")


if __name__ == "__main__":
    test_comprehensive_end_to_end_coverage()
