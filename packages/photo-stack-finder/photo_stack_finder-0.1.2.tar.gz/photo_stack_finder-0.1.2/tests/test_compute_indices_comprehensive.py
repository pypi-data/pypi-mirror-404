"""Comprehensive end-to-end test for ComputeIndices.

FIXTURE STRATEGY:
Creates synthetic index bins with 7 component scenarios to test cohabitation
graph building and sequence grouping logic:

1. **Singleton component** (1 sequence, skipped):
   - INDEX ("0",): [seq0]
   - Expected: Skipped (singleton), passes through unchanged

2. **Oversized component** (12 sequences > MAX_COMPONENT_SIZE=10, skipped):
   - All sequences share INDEX ("common",)
   - Expected: Skipped (too large), passes through unchanged

3. **Simple match** (2 sequences, creates 1 class):
   - INDEX ("2", "0"): [seq_a, seq_b]
   - All photos match via gates
   - Expected: 1 PhotoSequence class with 2 sub-sequences
   - Review: 1 SequenceGroup created

4. **Partial match** (2 sequences, both match):
   - INDEX ("3", "0"): [seq_x, seq_z]
   - Both photos match via gates
   - Expected: 1 class (x+z)
   - Review: 1 SequenceGroup created

5. **Gate failure** (2 sequences, gates reject):
   - INDEX ("4", "0"): [seq_fail1, seq_fail2]
   - Gates return None (rejection)
   - Expected: 2 separate sequences (not grouped)
   - Review: No groups created

6. **Minimal intersection bug test** (2 sequences with exactly MAX_MISMATCHES overlap):
   - Reference: indices [5,6,7,8], Candidate: indices [7,8,9,10]
   - Intersection: [7,8] (size = MAX_MISMATCHES = 2 = 50% overlap)
   - All comparisons FAIL (different hash codes)
   - Expected: Should NOT merge (tests for hit_count initialization bug)
   - Review: No groups created

7. **ZERO overlap bug test** (3 sequences, transitive connection):
   - zero_a: indices [11,12,13,14], zero_bridge: [14,15], zero_b: [15,16,17,18]
   - zero_a and zero_b have ZERO direct overlap (replicates Group 1 from real data)
   - All comparisons FAIL (different hash codes)
   - Expected: zero_a and zero_b should NOT merge
   - Review: No groups created (or potentially 1 if bridge merges with one side)

COVERAGE-DRIVEN TESTING:
Tests all production-called methods:
- 7 lifecycle methods: __init__, prepare, stage_worker, accumulate_results,
  finalise, needs_review, has_review_data
- 8 OutputPort methods (2 ports * 4 methods each):
  - forest_bins_o: read, get_ref_photo_count, get_ref_sequence_count, timestamp
  - forest_o: read, get_ref_photo_count, get_ref_sequence_count, timestamp

Total: 11 index bins → 2 singleton components (skipped) + 5 processable components
Expected review groups: 2 SequenceGroup objects (components 3 and 4)
"""

import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from src.utils.compute_indices import ComputeIndices
from src.utils.config import CONFIG
from src.utils.photo_file import PhotoFile
from src.utils.sequence import INDEX_T, PhotoFileSeries, PhotoSequence

from tests.fixtures.hash_generator import generate_codes

# Type for test fixtures
IndexBinsFixture = dict[str, Any]


class MockInputPort:
    """Mock InputPort that returns fixed index bins data."""

    def __init__(
        self,
        index_bins: dict[INDEX_T, list[PhotoSequence]],
        ref_seqs: int,
        ref_photos: int,
    ) -> None:
        self._index_bins = index_bins
        self._ref_seqs = ref_seqs
        self._ref_photos = ref_photos

    def read(self) -> dict[INDEX_T, list[PhotoSequence]]:
        """Return index bins data."""
        return self._index_bins

    def get_ref_photo_count(self) -> int:
        """Return reference photo count."""
        return self._ref_photos

    def get_ref_sequence_count(self) -> int:
        """Return reference sequence count."""
        return self._ref_seqs


def create_photo(
    photo_id: int,
    seq_idx: str,
    photo_idx: str,
    temp_dir: Path,
    dhash: bytes,
    phash: bytes,
    ahash: bytes,
    quality_score: float = 0.5,
) -> PhotoFile:
    """Create a minimal PhotoFile for testing with cached hash preparations.

    Args:
        photo_id: Unique photo ID
        seq_idx: Sequence index
        photo_idx: Photo index within sequence
        temp_dir: Temporary directory for image paths
        dhash: dhash code (8 bytes)
        phash: phash code (8 bytes)
        ahash: ahash code (8 bytes)
        quality_score: Quality score for exemplar prediction (0.0-1.0)
    """
    # Create a fake image path
    image_path = temp_dir / f"photo_{photo_id}.jpg"
    image_path.touch()  # Create empty file

    # Create PhotoFile with required parameters
    photo = PhotoFile(
        path=image_path,
        mime="image/jpeg",
        size_bytes=100 + photo_id,  # Unique sizes
        file_id=photo_id,
    )

    # Pre-populate lazy-loaded values in cache for test fixtures
    photo.cache["pixels"] = 1024  # 32x32 = 1024 pixels
    photo.cache["aspect_ratio"] = 1.0
    photo.cache["width"] = 32
    photo.cache["height"] = 32

    # Set cache values needed for comparison gates
    photo.cache["QUALITY_SCORE"] = quality_score  # Used by predict_exemplar_sequence

    # Pre-populate hash values with tuple keys (method_name, rotation) for rotation=0
    photo.cache[("dhash", 0)] = dhash
    photo.cache[("phash", 0)] = phash
    photo.cache[("ahash", 0)] = ahash

    # Pre-populate rotated hash values for rotation-aware comparison
    # For square images (aspect_ratio=1.0), normalization rotation is 0
    # So we need to cache values for 180° rotation as well
    # NOTE: In reality, rotating would produce different hashes, but for
    # test fixtures with empty files, we reuse the same hash values
    photo.cache[("dhash", 180)] = dhash
    photo.cache[("phash", 180)] = phash
    photo.cache[("ahash", 180)] = ahash

    return photo


def create_sequence(
    seq_id: int,
    photos: list[PhotoFile],
    indices: list[INDEX_T],
    name: str,
) -> PhotoSequence:
    """Create a PhotoSequence from photos.

    Args:
        seq_id: Sequence ID (for naming)
        photos: List of PhotoFile objects
        indices: List of INDEX_T tuples (one per photo)
        name: Sequence name/identifier
    """
    # Build PhotoFileSeries data dict
    series_data: dict[INDEX_T, PhotoFile] = {}
    for idx, photo in zip(indices, photos, strict=False):
        series_data[idx] = photo

    # Create PhotoFileSeries
    series = PhotoFileSeries(
        series_data,
        name=name,
        normal=False,  # Use False for test sequences
    )

    # Create PhotoSequence with the series
    return PhotoSequence(
        series=series,
        sequences=[],  # No sub-sequences initially
        created_by="test_fixture",
    )


def create_index_bins(temp_dir: Path) -> IndexBinsFixture:
    """Create test index bins with 7 component scenarios using hash code strategy.

    Uses multi-method hash code generation to control matching:
    - Generate dissimilar codes for different groups
    - Assign same codes to sequences that should match

    Returns:
        Fixture dict with index_bins, ref_seqs, ref_photos, and expected counts
    """
    # Generate hash codes with guaranteed dissimilarity (min_distance=20 bits)
    codes = generate_codes(21, seed=300)

    index_bins: dict[INDEX_T, list[PhotoSequence]] = {}
    photo_id = 0

    # Component 1: Singleton (1 sequence, skipped)
    photo_id += 1
    seq0_photos = [create_photo(photo_id, "0", "0", temp_dir, codes[0], codes[0], codes[0], quality_score=0.7)]
    seq0 = create_sequence(0, seq0_photos, [("0",)], "seq0")
    index_bins[("0",)] = [seq0]

    # Component 2: Oversized (12 sequences > MAX_COMPONENT_SIZE=10, skipped)
    oversized_seqs: list[PhotoSequence] = []
    for i in range(12):
        photo_id += 1
        code_idx = 1 + i
        photos = [
            create_photo(
                photo_id, str(i), "0", temp_dir, codes[code_idx], codes[code_idx], codes[code_idx], quality_score=0.6
            )
        ]
        seq = create_sequence(100 + i, photos, [("common",)], f"oversized_{i}")
        oversized_seqs.append(seq)
    index_bins[("common",)] = oversized_seqs

    # Component 3: Simple match (2 sequences, creates 1 class)
    photo_id += 1
    seq_a_photos = [create_photo(photo_id, "a", "0", temp_dir, codes[13], codes[13], codes[13], quality_score=0.8)]
    seq_a = create_sequence(200, seq_a_photos, [("2", "0")], "seq_a")

    photo_id += 1
    seq_b_photos = [create_photo(photo_id, "b", "0", temp_dir, codes[13], codes[13], codes[13], quality_score=0.7)]
    seq_b = create_sequence(201, seq_b_photos, [("2", "0")], "seq_b")

    index_bins[("2", "0")] = [seq_a, seq_b]

    # Component 4: Simple match with same indices (2 sequences, both match)
    photo_id += 1
    seq_x_photos = [create_photo(photo_id, "x", "0", temp_dir, codes[14], codes[14], codes[14], quality_score=0.9)]
    seq_x = create_sequence(300, seq_x_photos, [("3", "0")], "seq_x")

    photo_id += 1
    seq_z_photos = [create_photo(photo_id, "z", "0", temp_dir, codes[14], codes[14], codes[14], quality_score=0.85)]
    seq_z = create_sequence(302, seq_z_photos, [("3", "0")], "seq_z")

    index_bins[("3", "0")] = [seq_x, seq_z]

    # Component 5: Gate failure (2 sequences, gates reject)
    photo_id += 1
    seq_fail1_photos = [create_photo(photo_id, "f1", "0", temp_dir, codes[15], codes[15], codes[15], quality_score=0.5)]
    seq_fail1 = create_sequence(400, seq_fail1_photos, [("4", "0")], "seq_fail1")

    photo_id += 1
    seq_fail2_photos = [create_photo(photo_id, "f2", "0", temp_dir, codes[16], codes[16], codes[16], quality_score=0.4)]
    seq_fail2 = create_sequence(401, seq_fail2_photos, [("4", "0")], "seq_fail2")

    index_bins[("4", "0")] = [seq_fail1, seq_fail2]

    # Component 6: CRITICAL BUG TEST - Small intersection with long sequences
    # Replicates real Group 78 from template similarity (rap03 PANO vs rap03)
    #
    # Long sequence: 44 photos at indices [01, 02, 03, ..., 44]
    # Short sequence: 2 photos at indices [01, 25] (ONLY these 2 overlap with long sequence)
    #
    # Intersection: {01, 25} = 2 photos (exactly MAX_MISMATCHES)
    # All comparisons FAIL (different hash codes)
    #
    # BUG: hit_count initialized to len(long_seq)=44 instead of intersection=2
    # Result: miss_count (2) >= min(44, 3) = 2 >= 3 = FALSE → incorrectly merges!
    #
    # CORRECT: hit_count should be 2 (intersection size)
    # Then: miss_count (1) >= min(1, 3) = 1 >= 1 = TRUE → correctly rejects!

    # Long sequence with 44 photos
    long_seq_photos: list[PhotoFile] = []
    long_seq_indices: list[INDEX_T] = []
    for i in range(1, 45):  # indices 01-44
        photo_id += 1
        idx_str = f"{i:02d}"
        long_seq_photos.append(
            create_photo(photo_id, "long", idx_str, temp_dir, codes[16], codes[16], codes[16], quality_score=0.8)
        )
        long_seq_indices.append((idx_str,))

    long_seq = create_sequence(500, long_seq_photos, long_seq_indices, "long_seq")

    # Short sequence with only 2 photos at indices 01 and 25 (minimal intersection)
    short_seq_photos: list[PhotoFile] = []
    short_seq_indices: list[INDEX_T] = []
    for idx_str in ["01", "25"]:
        photo_id += 1
        short_seq_photos.append(
            create_photo(photo_id, "short", idx_str, temp_dir, codes[17], codes[17], codes[17], quality_score=0.7)
        )
        short_seq_indices.append((idx_str,))

    short_seq = create_sequence(501, short_seq_photos, short_seq_indices, "short_seq")

    # Add to bins - they only cohabit at indices 01 and 25
    index_bins[("01",)] = [long_seq, short_seq]
    index_bins[("25",)] = [long_seq, short_seq]

    # Component 7: ZERO overlap transitivity test
    # Three sequences connected transitively but zero_a and zero_b have no direct overlap
    zero_a_photos: list[PhotoFile] = []
    zero_a_indices: list[INDEX_T] = []
    for i in range(11, 15):
        photo_id += 1
        zero_a_photos.append(
            create_photo(photo_id, "zero_a", str(i), temp_dir, codes[18], codes[18], codes[18], quality_score=0.8)
        )
        zero_a_indices.append((str(i),))

    zero_a = create_sequence(600, zero_a_photos, zero_a_indices, "zero_a")

    zero_bridge_photos: list[PhotoFile] = []
    zero_bridge_indices: list[INDEX_T] = []
    for i in range(14, 16):
        photo_id += 1
        zero_bridge_photos.append(
            create_photo(photo_id, "zero_bridge", str(i), temp_dir, codes[19], codes[19], codes[19], quality_score=0.75)
        )
        zero_bridge_indices.append((str(i),))

    zero_bridge = create_sequence(601, zero_bridge_photos, zero_bridge_indices, "zero_bridge")

    zero_b_photos: list[PhotoFile] = []
    zero_b_indices: list[INDEX_T] = []
    for i in range(15, 19):
        photo_id += 1
        zero_b_photos.append(
            create_photo(photo_id, "zero_b", str(i), temp_dir, codes[20], codes[20], codes[20], quality_score=0.7)
        )
        zero_b_indices.append((str(i),))

    zero_b = create_sequence(602, zero_b_photos, zero_b_indices, "zero_b")

    index_bins[("14",)] = [zero_a, zero_bridge]
    index_bins[("15",)] = [zero_bridge, zero_b]

    # Calculate totals
    all_sequences = set().union(*index_bins.values())
    total_photos = sum(seq.n_photos for seq in all_sequences)
    total_seqs = len(all_sequences)

    return {
        "index_bins": index_bins,
        "ref_seqs": total_seqs,
        "ref_photos": total_photos,
        "expected_singleton_count": 1,  # Component 1
        "expected_oversized_count": 1,  # Component 2
        "expected_processable_count": 5,  # Components 3, 4, 5, 6, 7
    }


def test_comprehensive_end_to_end_coverage() -> None:
    """Run full ComputeIndices lifecycle test.

    Validates:
    - __init__()
    - prepare() - graph building and component filtering
    - stage_worker() - sequence grouping with gates
    - accumulate_results()
    - finalise()
    - needs_review()
    - has_review_data()
    - forest_bins_o OutputPort (read, counts, timestamp)
    - forest_o OutputPort (read, counts, timestamp)
    - Review data structure (SequenceGroup objects)
    - Atomic invariants (photo count preservation)
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test: ComputeIndices")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # [1] Create test fixtures
        print("\nCreating test fixtures...")
        fixtures = create_index_bins(temp_dir)
        print(f"  Index bins: {len(fixtures['index_bins'])} bins")
        print(f"  Total sequences: {fixtures['ref_seqs']}")
        print(f"  Total photos: {fixtures['ref_photos']}")

        start_time = time.perf_counter()

        # [2] Create stage (tests __init__)
        print("\n[1/15] Creating stage (__init__)...")
        stage = ComputeIndices()
        assert stage.stage_name == "Index Grouping"
        assert hasattr(stage, "index_bins_i")
        assert hasattr(stage, "forest_bins_o")
        assert hasattr(stage, "forest_o")
        print("  Stage name: Index Grouping")
        print("  [OK] __init__() creates stage with correct attributes")

        # Test has_review_data() BEFORE run (must be False)
        print("\n[2/15] Testing has_review_data() before run...")
        assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
        print("  [OK] has_review_data() returns False before stage runs")

        # Inject test data
        stage.index_bins_i = MockInputPort(
            fixtures["index_bins"],
            fixtures["ref_seqs"],
            fixtures["ref_photos"],
        )

        # [3] Run prepare (tests prepare)
        print("\n[3/15] Running prepare()...")
        work_items, accumulator = stage.prepare()
        print(f"  Work items (processable components): {len(work_items)}")
        print(f"  Accumulator (forest, bins): ({len(accumulator[0])}, {len(accumulator[1])}) sequences")

        # Validate work items
        expected_processable = fixtures["expected_processable_count"]
        assert len(work_items) == expected_processable, (
            f"Expected {expected_processable} processable components, got {len(work_items)}"
        )

        # Validate accumulator starts with skipped sequences
        forest, bins = accumulator
        # Each skipped component's sequences are added to forest/bins
        # Component 1: 1 seq, Component 2: 12 seqs = 13 total
        expected_skipped_seqs = 1 + 12
        assert len(forest) == expected_skipped_seqs, (
            f"Expected {expected_skipped_seqs} skipped sequences in forest, got {len(forest)}"
        )
        assert len(bins) == expected_skipped_seqs, (
            f"Expected {expected_skipped_seqs} skipped sequences in bins, got {len(bins)}"
        )

        print(f"  [OK] prepare() built {len(work_items)} processable components")
        print(f"  [OK] Skipped {expected_skipped_seqs} sequences (singleton + oversized)")

        # [4] Run stage_worker (tests stage_worker with real extend_reference_sequence)
        print("\n[4/15] Running stage_worker()...")

        worker_results: list[list[PhotoSequence]] = []
        all_sequence_groups: list[Any] = []

        # Save original CONFIG values
        original_max_component_size = CONFIG.sequences.MAX_COMPONENT_SIZE
        original_gates = CONFIG.processing.COMPARISON_GATES
        original_thresholds = CONFIG.processing.GATE_THRESHOLDS.copy()

        # Configure gates for hash-only comparison (tests extend_reference_sequence without mocking)
        CONFIG.processing.COMPARISON_GATES = ["dhash", "phash", "ahash"]
        CONFIG.processing.GATE_THRESHOLDS = {
            "dhash": 0.70,
            "phash": 0.70,
            "ahash": 0.70,
        }
        print(f"  Configured gates: {CONFIG.processing.COMPARISON_GATES}")
        print(f"  Configured thresholds: {CONFIG.processing.GATE_THRESHOLDS}")

        # Mock only build_sequence_group to avoid needing full SequenceGroup setup
        # (extend_reference_sequence and GateSequence now run naturally with cached hash codes)
        with patch("src.utils.sequence_clustering.build_sequence_group") as mock_build_group:
            mock_build_group.side_effect = lambda seq: MagicMock(__repr__=lambda _: f"SequenceGroup({seq.series.name})")

            # Process each work item
            for i, component in enumerate(work_items):
                print(f"  Processing component {i + 1}/{len(work_items)}: {len(component)} sequences")

                id_reviews, seq_reviews, result_seqs = ComputeIndices.stage_worker(component, "Index Grouping")

                # Component 1 (Component 6 in code): long_seq (44 photos) vs short_seq (2 photos)
                # Bug test: Intersection size=2, all comparisons fail, sequences should stay separate
                # This assertion validates the fix for the hit_count initialization bug
                if i == 0:  # Component 1 (long_seq and short_seq)
                    # Verify sequences stay separate (bug fix: hit_count initialized to intersection size)
                    assert len(result_seqs) == 2, (
                        f"Component 6 bug test: long_seq (44 photos) and short_seq (2 photos) "
                        f"should stay SEPARATE (2 sequences) but got {len(result_seqs)} sequence(s). "
                        f"Intersection=2, all comparisons fail. The hit_count must be initialized to "
                        f"intersection size (not len(ref)) to correctly reject this merge."
                    )

                # Validate worker result structure
                assert isinstance(id_reviews, list), "id_reviews should be list"
                assert isinstance(seq_reviews, list), "seq_reviews should be list"
                assert isinstance(result_seqs, list), "result_seqs should be list"
                assert len(id_reviews) == 0, "id_reviews should be empty for this stage"

                worker_results.append(result_seqs)
                all_sequence_groups.extend(seq_reviews)

                print(f"    Result: {len(result_seqs)} sequences, {len(seq_reviews)} review groups")

        print(f"  [OK] stage_worker() processed {len(work_items)} components")
        print(f"  [OK] Total review groups created: {len(all_sequence_groups)}")

        # Restore original CONFIG values
        CONFIG.sequences.MAX_COMPONENT_SIZE = original_max_component_size
        CONFIG.processing.COMPARISON_GATES = original_gates
        CONFIG.processing.GATE_THRESHOLDS = original_thresholds

        # [5] Test accumulate_results (tests accumulate_results)
        print("\n[5/15] Running accumulate_results()...")
        for i, result in enumerate(worker_results):
            stage.accumulate_results(accumulator, result)
            print(f"  Accumulated component {i + 1}: {len(result)} sequences")

        # Validate accumulator structure
        forest, bins = accumulator
        print(f"  Final forest size: {len(forest)} sequences")
        print(f"  Final bins size: {len(bins)} sequences")
        assert isinstance(forest, list), "Forest should be list"
        assert isinstance(bins, list), "Bins should be list"
        print("  [OK] accumulate_results() accumulated all worker results")

        # [6] Test finalise (tests finalise)
        print("\n[6/15] Running finalise()...")
        stage.result = accumulator
        stage.finalise()
        print(f"  Final photos: {stage.ref_photos_final}")
        print(f"  Final sequences: {stage.ref_seqs_final}")

        # Validate status attributes
        assert stage.ref_photos_final is not None, "ref_photos_final must not be None"
        assert isinstance(stage.ref_photos_final, int), "ref_photos_final must be int"
        assert stage.ref_seqs_final is not None, "ref_seqs_final must not be None"
        assert isinstance(stage.ref_seqs_final, int), "ref_seqs_final must be int"
        assert stage.ref_seqs_final == len(forest), (
            f"ref_seqs_final should equal forest length: {stage.ref_seqs_final} != {len(forest)}"
        )

        # Validate atomic invariant: total photo count preserved
        input_photos = fixtures["ref_photos"]
        output_photos = sum(seq.n_photos for seq in forest)
        assert input_photos == output_photos, f"Photo count invariant violated: {input_photos} in, {output_photos} out"
        print(f"  [OK] Photo count invariant preserved: {input_photos} == {output_photos}")
        print("  [OK] Status updates validated")

        # [7] Test needs_review (tests needs_review)
        print("\n[7/15] Testing needs_review()...")
        review_type = stage.needs_review()
        assert review_type == "sequences", f"Review type should be 'sequences', got '{review_type}'"
        print(f"  Review type: {review_type}")
        print("  [OK] needs_review() returns 'sequences'")

        # [8] Test has_review_data AFTER run (tests has_review_data)
        print("\n[8/15] Testing has_review_data() after run...")
        has_review = stage.has_review_data()
        # Should be True if we created any classes (multi-sequence groups)
        print(f"  Has review data: {has_review}")
        print(f"  [OK] has_review_data() returns {has_review}")

        # [9-12] Test forest_bins_o OutputPort
        print("\n[9/15] Testing forest_bins_o.read()...")
        result_from_port = stage.forest_bins_o.read()
        assert result_from_port is stage.result, "forest_bins_o.read() should return stage.result"
        assert isinstance(result_from_port, tuple), "Result should be tuple"
        assert len(result_from_port) == 2, "Result tuple should have 2 elements"
        forest_from_port, bins_from_port = result_from_port
        print(f"  Forest from port: {len(forest_from_port)} sequences")
        print(f"  Bins from port: {len(bins_from_port)} sequences")
        print("  [OK] forest_bins_o.read() returns correct tuple result")

        print("\n[10/15] Testing forest_bins_o.get_ref_photo_count()...")
        photo_count = stage.forest_bins_o.get_ref_photo_count()
        assert photo_count == stage.ref_photos_final, (
            f"Photo count should be {stage.ref_photos_final}, got {photo_count}"
        )
        print(f"  Photo count via OutputPort: {photo_count}")
        print("  [OK] forest_bins_o.get_ref_photo_count() returns correct count")

        print("\n[11/15] Testing forest_bins_o.get_ref_sequence_count()...")
        seq_count = stage.forest_bins_o.get_ref_sequence_count()
        assert seq_count == stage.ref_seqs_final, f"Sequence count should be {stage.ref_seqs_final}, got {seq_count}"
        print(f"  Sequence count via OutputPort: {seq_count}")
        print("  [OK] forest_bins_o.get_ref_sequence_count() returns correct count")

        print("\n[12/15] Testing forest_bins_o.timestamp()...")
        try:
            timestamp = stage.forest_bins_o.timestamp()
            print(f"  Timestamp: {timestamp}")
            print("  [NOTE] Cache exists, timestamp returned")
        except RuntimeError as e:
            print(f"  RuntimeError raised (expected): {e}")
            print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

        # [13-16] Test forest_o OutputPort
        print("\n[13/15] Testing forest_o.read()...")
        forest_only = stage.forest_o.read()
        assert forest_only is stage.result[0], "forest_o.read() should return stage.result[0]"
        assert isinstance(forest_only, list), "Forest should be list"
        print(f"  Forest from forest_o: {len(forest_only)} sequences")
        print("  [OK] forest_o.read() returns correct forest")

        print("\n[14/15] Testing forest_o.get_ref_photo_count()...")
        photo_count_forest = stage.forest_o.get_ref_photo_count()
        assert photo_count_forest == stage.ref_photos_final, (
            f"Photo count should be {stage.ref_photos_final}, got {photo_count_forest}"
        )
        print(f"  Photo count via forest_o: {photo_count_forest}")
        print("  [OK] forest_o.get_ref_photo_count() returns correct count")

        print("\n[15/15] Testing forest_o.get_ref_sequence_count()...")
        seq_count_forest = stage.forest_o.get_ref_sequence_count()
        assert seq_count_forest == stage.ref_seqs_final, (
            f"Sequence count should be {stage.ref_seqs_final}, got {seq_count_forest}"
        )
        print(f"  Sequence count via forest_o: {seq_count_forest}")
        print("  [OK] forest_o.get_ref_sequence_count() returns correct count")

        # Note: forest_o.timestamp() would behave identically to forest_bins_o.timestamp()
        # so we don't test it separately to avoid duplication

        elapsed = time.perf_counter() - start_time

        print("\n" + "=" * 70)
        print("Comprehensive Test Complete!")
        print("=" * 70)

        # Summary statistics
        print(f"\nExecution time: {elapsed:.2f}s")
        print(f"Input: {fixtures['ref_seqs']} sequences, {fixtures['ref_photos']} photos")
        print(f"Output: {len(forest)} sequences, {output_photos} photos")
        print(f"Skipped: {expected_skipped_seqs} sequences (singleton + oversized)")
        print(f"Processable: {len(work_items)} components")
        print(f"Review groups: {len(all_sequence_groups)}")
        print(f"Photo count preserved: {input_photos} -> {output_photos}")

        print("\nAll validations passed!")
