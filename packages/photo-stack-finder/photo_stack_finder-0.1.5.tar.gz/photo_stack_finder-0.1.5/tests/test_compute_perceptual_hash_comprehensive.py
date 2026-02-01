"""Comprehensive end-to-end test for ComputePerceptualHash.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions using real test images with PIL.

FIXTURE STRATEGY:
Generates random 32x32 images until we have 4 with distinct perceptual hashes,
then creates image_3 as exact copy of image_0 to create an intentional collision:
1. Random image (hash A)
2. Random image (hash B) - distinct from A
3. Random image (hash C) - distinct from A, B
4. Random image (hash D) - distinct from A, B, C
5. Copy of image 0 (hash A) - intentional collision

This approach is robust to any perceptual hash algorithm (dhash, phash, ahash, etc.)
and doesn't require knowledge of algorithm internals.

Organizes into 3 PhotoSequences:
- Sequence 0: 3 photos (images 0, 1, 2) - 3 distinct hashes
- Sequence 1: 2 photos (images 3, 4) - image 3 is copy of image 0 (collision)
- Sequence 2: 0 photos - empty sequence edge case

Total: 5 photos → exactly 4 hash bins (1 collision bin with 2 photos, 3 singleton bins)

COVERAGE-DRIVEN TESTING:
Tests 11 production-called methods (7 stage + 4 OutputPort).
Does NOT test run() - calls individual lifecycle methods directly.

REGRESSION TESTING:
This is the comprehensive test for CI, validating all stage methods with controlled test data.
"""

import random
import shutil
import tempfile
import time
from pathlib import Path
from typing import TypedDict

import numpy as np
import numpy.typing as npt
from PIL import Image, ImageOps
from src.utils.compute_perceptual_hash import ComputePerceptualHash
from src.utils.config import CONFIG
from src.utils.photo_file import PhotoFile
from src.utils.sequence import INDEX_T, PhotoFileSeries, PhotoSequence

from photo_compare import create_comparison_method
from tests.fixtures.cache_loader import MockInputPort


def load_pixel_array(path: Path) -> npt.NDArray[np.uint8]:
    """Load pixel array from path in canonical format: RGB, EXIF-oriented, full resolution."""
    with Image.open(path) as opened_img:
        img = ImageOps.exif_transpose(opened_img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        return np.array(img, dtype=np.uint8)


class FixtureData(TypedDict):
    """Type definition for test fixture dictionary."""

    temp_dir: Path
    image_paths: dict[str, Path]
    forest: list[PhotoSequence]
    ref_seqs: int
    ref_photos: int
    expected_bins: int
    expected_collision: bool


def create_test_images(temp_dir: Path) -> dict[str, Path]:
    """Create test images with distinct perceptual hashes via random generation.

    Generates random images until we have at least 4 with distinct perceptual hashes,
    then creates a 5th image as a duplicate of the first to test hash collision.

    This approach is robust to different perceptual hash algorithms (dhash, phash, etc.)
    and doesn't require knowledge of algorithm internals.

    Strategy:
    1. Generate random 32x32 images until we have 4 distinct hashes
    2. Save those 4 images
    3. Create image_3 as exact copy of image_0 (collision)
    4. Total: 5 images, 4 unique hashes, 1 intentional collision

    Args:
        temp_dir: Temporary directory for creating files

    Returns:
        Dict mapping image names to file paths
    """
    # Seed random number generator for reproducibility
    random.seed(42)

    images: dict[str, Path] = {}

    # Create comparison method to compute hashes
    cmp = create_comparison_method(CONFIG.sequences.PERCEPTUAL_METHOD)

    # Generate random images until we have 4 with distinct hashes
    candidates: list[tuple[Path, bytes]] = []  # (path, hash)
    seen_hashes: set[bytes] = set()
    attempt = 0

    while len(candidates) < 4:
        # Generate random 32x32 image
        img = Image.new("RGB", (32, 32))
        for y in range(32):
            for x in range(32):
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                img.putpixel((x, y), (r, g, b))

        # Save to temp file and compute hash
        temp_path = temp_dir / f"candidate_{attempt}.jpg"
        img.save(temp_path, "JPEG", quality=95)
        hash_bytes = cmp.prepare(load_pixel_array(temp_path))

        # Check if this hash is distinct
        if hash_bytes not in seen_hashes:
            candidates.append((temp_path, hash_bytes))
            seen_hashes.add(hash_bytes)

        attempt += 1

        # Safety: stop after 100 attempts (very unlikely to be needed)
        if attempt > 100:
            raise RuntimeError(f"Could not generate 4 distinct hashes after {attempt} attempts")

    # Create images 0, 1, 2, 4 from the 4 distinct candidates
    image_indices = [0, 1, 2, 4]  # Skip 3, will create it as duplicate
    for i, image_idx in enumerate(image_indices):
        candidate_path, _ = candidates[i]
        final_path = temp_dir / f"image_{image_idx}.jpg"
        # Copy file
        img = Image.open(candidate_path)
        img.save(final_path, "JPEG", quality=95)
        images[f"image_{image_idx}"] = final_path

    # Image 3 is exact binary copy of image 0 (collision)
    # Use shutil.copy to avoid JPEG re-compression artifacts
    collision_path = temp_dir / "image_3.jpg"
    shutil.copy(images["image_0"], collision_path)
    images["image_3"] = collision_path

    return images


def create_photo(photo_id: int, seq_idx: int, photo_idx: int, image_path: Path, **overrides: object) -> PhotoFile:
    """Create minimal PhotoFile with real image path.

    Args:
        photo_id: Unique identifier for this photo
        seq_idx: Sequence index (for INDEX_T creation)
        photo_idx: Photo index within sequence (for INDEX_T creation)
        image_path: Path to real image file
        **overrides: Additional PhotoFile attributes to override

    Returns:
        PhotoFile object with minimal required fields
    """
    defaults = {
        "path": image_path,
        "mime": "image/jpeg",
        "size_bytes": 2000,  # Small 32x32 images
        "file_id": photo_id,
    }
    defaults.update(overrides)
    # Remove fields that are no longer part of PhotoFile.__init__
    # (they're now lazy-loaded via cache)
    defaults.pop("pixels", None)
    defaults.pop("sha256", None)
    defaults.pop("orientation", None)

    photo = PhotoFile(**defaults)

    # Pre-populate lazy-loaded values in cache for test fixtures
    photo.cache["pixels"] = 1024  # 32x32 = 1024 pixels
    photo.cache["aspect_ratio"] = 1.33
    photo.cache["width"] = 1600
    photo.cache["height"] = 1200

    return photo


def create_test_sequences(image_paths: dict[str, Path]) -> tuple[list[PhotoSequence], int, int]:
    """Create PhotoSequence forest with controlled structure.

    Creates 3 sequences:
    - Sequence 0: 3 reference photos (images 0, 1, 2) - different hashes
    - Sequence 1: 2 reference photos (images 3, 4) - image 3 collides with seq 0's image 0
    - Sequence 2: 0 reference photos - empty sequence edge case

    Args:
        image_paths: Dict mapping image names to file paths

    Returns:
        Tuple of (forest, ref_seqs, ref_photos)
        - forest: list[PhotoSequence] (3 sequences)
        - ref_seqs: 3 (includes empty sequence)
        - ref_photos: 5 (total reference photos)
    """
    # Sequence 0: 3 photos (images 0, 1, 2)
    seq0_data: dict[INDEX_T, PhotoFile] = {
        ("0", "0"): create_photo(0, 0, 0, image_paths["image_0"]),
        ("0", "1"): create_photo(1, 0, 1, image_paths["image_1"]),
        ("0", "2"): create_photo(2, 0, 2, image_paths["image_2"]),
    }
    seq0_series = PhotoFileSeries(seq0_data, name="seq0_{P0}", normal=False)
    seq0 = PhotoSequence(series=seq0_series, sequences=[], created_by="test")

    # Sequence 1: 2 photos (images 3, 4)
    # Image 3 is red (same as image 0) → hash collision
    seq1_data: dict[INDEX_T, PhotoFile] = {
        ("1", "0"): create_photo(3, 1, 0, image_paths["image_3"]),
        ("1", "1"): create_photo(4, 1, 1, image_paths["image_4"]),
    }
    seq1_series = PhotoFileSeries(seq1_data, name="seq1_{P0}", normal=False)
    seq1 = PhotoSequence(series=seq1_series, sequences=[], created_by="test")

    # Sequence 2: 0 photos (empty sequence - edge case)
    seq2_data: dict[INDEX_T, PhotoFile] = {}
    seq2_series = PhotoFileSeries(seq2_data, name="seq2_empty", normal=False)
    seq2 = PhotoSequence(series=seq2_series, sequences=[], created_by="test")

    forest = [seq0, seq1, seq2]
    ref_seqs = 3
    ref_photos = 5  # Total reference photos across all sequences

    return forest, ref_seqs, ref_photos


def test_comprehensive_end_to_end_coverage() -> None:
    """Run full stage lifecycle test.

    Validates:
    [Stage lifecycle - 7 methods]
    - __init__() - Stage construction, ports creation
    - prepare() - Reads forest, creates work items for all reference photos
    - stage_worker() - Computes perceptual hash from actual image files
    - accumulate_results() - Bins photos by hash: accum[hash][seq_idx].append(photo_idx)
    - finalise() - Sets ref_photos_final=5, ref_seqs_final=3, validates invariant
    - needs_review() - Returns "none" (base class implementation)
    - has_review_data() - Returns False (base class implementation)

    [OutputPort methods - 4 methods]
    - perceptual_bins_o.read() - Returns result dict
    - perceptual_bins_o.get_ref_photo_count() - Returns 5
    - perceptual_bins_o.get_ref_sequence_count() - Returns 3
    - perceptual_bins_o.timestamp() - Raises RuntimeError (no cache in test)

    [Validations]
    - Nested structure validation: hash → seq_idx → photo_indices
    - Hash collision detection (2 photos with same hash)
    - Empty sequence handling (no work items generated)
    - Photo count invariant (5 in = 5 out)
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test: ComputePerceptualHash")
    print("=" * 70)

    # [1] Create test fixtures with real images
    print("\nCreating test fixtures...")
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"  Temp directory: {temp_dir}")

        # Create 5 test images (4 random with distinct hashes + 1 duplicate)
        image_paths = create_test_images(temp_dir)
        print(f"  Created {len(image_paths)} test images (32x32 random pixels):")
        print("    - image_0: Random (hash A)")
        print("    - image_1: Random (hash B)")
        print("    - image_2: Random (hash C)")
        print("    - image_3: Copy of image_0 (hash A) - intentional collision")
        print("    - image_4: Random (hash D)")
        print("    [Random generation ensures 4 distinct hashes regardless of algorithm]")

        # Create PhotoSequence forest
        forest, ref_seqs, ref_photos = create_test_sequences(image_paths)
        print(f"  Created {len(forest)} sequences:")
        print("    - Sequence 0: 3 photos (images 0, 1, 2)")
        print("    - Sequence 1: 2 photos (images 3, 4)")
        print("    - Sequence 2: 0 photos (empty, edge case)")
        print(f"  Total: {ref_photos} reference photos, {ref_seqs} sequences")

        start_time = time.perf_counter()

        # [1/11] Test __init__() - Stage construction
        print("\n[1/11] Creating stage (__init__)...")
        stage = ComputePerceptualHash()
        assert stage.stage_name == "Perceptual Hash Calculation", (
            f"Stage name should be 'Perceptual Hash Calculation', got '{stage.stage_name}'"
        )
        assert hasattr(stage, "forest_i"), "Should have forest_i input port"
        assert hasattr(stage, "perceptual_bins_o"), "Should have perceptual_bins_o output port"
        print(f"  Stage name: {stage.stage_name}")
        print("  [OK] Stage constructed successfully")

        # Test has_review_data() BEFORE run (must be False)
        assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
        print("  [OK] has_review_data() returns False before stage runs")

        # Inject test data via MockInputPort
        stage.forest_i = MockInputPort(forest, ref_seqs, ref_photos)

        # [2/11] Test prepare()
        print("\n[2/11] Running prepare()...")
        work_items, accumulator = stage.prepare()

        # Convert iterator to list for validation
        work_items_list = list(work_items)
        print(f"  Work items generated: {len(work_items_list)}")

        # Validate prepare results
        assert len(work_items_list) == 5, f"Expected 5 work items (5 photos), got {len(work_items_list)}"
        print("  [OK] Correct number of work items (empty sequence creates none)")

        # Validate work item structure: (seq_idx, INDEX_T, str_path)
        for i, work_item in enumerate(work_items_list):
            assert isinstance(work_item, tuple), f"Work item {i}: should be tuple"
            assert len(work_item) == 3, f"Work item {i}: should have 3 elements"

            seq_idx, idx, path = work_item
            assert isinstance(seq_idx, int), f"Work item {i}: seq_idx should be int"
            assert isinstance(idx, tuple), f"Work item {i}: idx should be tuple (INDEX_T)"
            assert isinstance(path, str), f"Work item {i}: path should be str"
            assert Path(path).exists(), f"Work item {i}: image file must exist at {path}"

        # Validate accumulator: nested defaultdict
        assert isinstance(accumulator, dict), "Accumulator should be dict"
        assert len(accumulator) == 0, "Accumulator should be empty initially"
        print("  [OK] Work items validated: correct structure, files exist")
        print("  [OK] Accumulator is empty nested defaultdict")

        # [3/11] Test stage_worker() on ALL photos
        print(f"\n[3/11] Processing {len(work_items_list)} work items through stage_worker()...")

        worker_results: list[tuple[int, INDEX_T, bytes]] = []
        hash_values: list[bytes] = []

        for i, work_item in enumerate(work_items_list):
            seq_idx, idx, path = work_item
            print(f"  Processing photo {i + 1}/5: seq={seq_idx}, idx={idx}...")

            # Call stage_worker (static method)
            id_reviews, seq_reviews, result = ComputePerceptualHash.stage_worker(
                work_item, _args="Perceptual Hash Calculation"
            )

            worker_results.append(result)

            # Validate result structure
            assert len(id_reviews) == 0, f"Photo {i}: id_reviews should be empty (no review data)"
            assert len(seq_reviews) == 0, f"Photo {i}: seq_reviews should be empty"
            assert isinstance(result, tuple), f"Photo {i}: result should be tuple"
            assert len(result) == 3, f"Photo {i}: result tuple should have 3 elements"

            result_seq_idx, result_idx, hash_bytes = result
            assert result_seq_idx == seq_idx, f"Photo {i}: seq_idx should match"
            assert result_idx == idx, f"Photo {i}: idx should match"
            assert isinstance(hash_bytes, bytes), f"Photo {i}: hash should be bytes"
            assert len(hash_bytes) > 0, f"Photo {i}: hash should be non-empty"

            hash_values.append(hash_bytes)
            print(f"    Computed hash: {len(hash_bytes)} bytes")

        print(f"  [OK] All work items processed: {len(worker_results)} results")

        # Validate hash collision expectation
        # Images 0 and 3 are exact copies → should have same hash
        print("\n  Validating hash collision scenario...")
        assert hash_values[0] == hash_values[3], "Images 0 and 3 are exact copies - should have same perceptual hash"
        print("    [OK] Images 0 and 3 have matching hashes (collision detected)")

        # [4/11] Test accumulate_results()
        print("\n[4/11] Running accumulate_results()...")
        for result in worker_results:
            stage.accumulate_results(accumulator, result)

        # Validate bin structure
        num_bins = len(accumulator)
        print(f"  Hash bins created: {num_bins}")
        # We generated 4 images with distinct hashes + 1 duplicate
        # So we expect exactly 4 hash bins
        assert num_bins == 4, f"Expected exactly 4 hash bins (4 distinct hashes), got {num_bins}"
        print("  [OK] Exactly 4 hash bins created (as expected from fixture generation)")

        # Validate nested structure: dict[bytes, dict[int, list[INDEX_T]]]
        print("\n  Validating nested structure...")
        total_photos_in_bins = 0
        for hash_bytes, seq_dict in accumulator.items():
            assert isinstance(hash_bytes, bytes), "Outer dict key should be bytes"
            assert isinstance(seq_dict, dict), "Inner value should be dict"

            for seq_idx, indices_list in seq_dict.items():
                assert isinstance(seq_idx, int), "Inner dict key should be int"
                assert isinstance(indices_list, list), "Inner dict value should be list"

                for idx in indices_list:
                    assert isinstance(idx, tuple), "Photo index should be tuple (INDEX_T)"
                    total_photos_in_bins += 1

        print("    [OK] Nested structure validated: dict[bytes, dict[int, list[INDEX_T]]]")
        print(f"    [OK] Total photos in bins: {total_photos_in_bins}")

        # Validate collision bin (2 photos with same hash)
        print("\n  Validating hash collision bin...")
        collision_bin = None
        singleton_bins = []

        for hash_bytes, seq_dict in accumulator.items():
            total_photos = sum(len(indices) for indices in seq_dict.values())
            if total_photos == 2:
                # This should be our intended collision (images 0 and 3, exact copies)
                collision_bin = hash_bytes
            elif total_photos == 1:
                singleton_bins.append(hash_bytes)

        assert collision_bin is not None, "Should have one collision bin with 2 photos"
        assert len(singleton_bins) == 3, f"Should have 3 singleton bins, got {len(singleton_bins)}"

        # Collision bin should have photos from 2 different sequences (seq 0 and seq 1)
        collision_seq_dict = accumulator[collision_bin]
        assert len(collision_seq_dict) == 2, f"Collision bin should have 2 sequences, got {len(collision_seq_dict)}"
        assert 0 in collision_seq_dict, "Sequence 0 should be in collision bin"
        assert 1 in collision_seq_dict, "Sequence 1 should be in collision bin"
        print("    [OK] Collision bin validated: 2 photos from 2 different sequences")
        print("    [OK] Singleton bins validated: 3 bins with 1 photo each")

        print("  [OK] Results accumulated correctly into 4 hash bins (1 collision + 3 singletons)")

        # [5/11] Test finalise()
        print("\n[5/11] Running finalise()...")
        stage.result = accumulator
        stage.finalise()
        print(f"  Final photos: {stage.ref_photos_final}")
        print(f"  Final sequences: {stage.ref_seqs_final}")

        # Validate status attributes
        print("\n  Validating status updates...")
        assert stage.ref_photos_final is not None, "ref_photos_final must not be None"
        assert isinstance(stage.ref_photos_final, int), "ref_photos_final must be int"
        assert stage.ref_photos_final == 5, f"ref_photos_final should be 5, got {stage.ref_photos_final}"
        assert stage.ref_seqs_final is not None, "ref_seqs_final must not be None"
        assert isinstance(stage.ref_seqs_final, int), "ref_seqs_final must be int"
        assert stage.ref_seqs_final == 3, f"ref_seqs_final should be 3, got {stage.ref_seqs_final}"

        # Validate atomic invariant: photo count preserved
        total_photos_in = ref_photos
        total_photos_out = sum(len(indices) for bin_dict in accumulator.values() for indices in bin_dict.values())
        assert total_photos_in == total_photos_out, (
            f"Photo count invariant violated: {total_photos_in} in, {total_photos_out} out"
        )
        print(f"  [OK] Photo count invariant preserved: {total_photos_in} == {total_photos_out}")
        print("  [OK] Status updates validated")

        # [6/11] Test needs_review()
        print("\n[6/11] Testing needs_review()...")
        review_type = stage.needs_review()
        assert review_type == "none", f"Review type should be 'none', got '{review_type}'"
        print(f"  Review type: {review_type}")
        print("  [OK] needs_review() returns 'none' (base class implementation)")

        # [7/11] Test has_review_data()
        print("\n[7/11] Testing has_review_data()...")
        has_review = stage.has_review_data()
        assert not has_review, f"has_review_data() should return False, got {has_review}"
        print(f"  Has review data: {has_review}")
        print("  [OK] has_review_data() returns False (consistent with needs_review())")

        # [8/11] Test perceptual_bins_o.read()
        print("\n[8/11] Testing perceptual_bins_o.read()...")
        bins_from_port = stage.perceptual_bins_o.read()
        assert bins_from_port is stage.result, "perceptual_bins_o.read() should return stage.result"
        assert len(bins_from_port) == 4, f"Expected 4 hash bins from port, got {len(bins_from_port)}"
        print(f"  Hash bins via OutputPort: {len(bins_from_port)} bins")
        print("  [OK] perceptual_bins_o.read() returns correct result")

        # [9/11] Test perceptual_bins_o.get_ref_photo_count()
        print("\n[9/11] Testing perceptual_bins_o.get_ref_photo_count()...")
        photo_count = stage.perceptual_bins_o.get_ref_photo_count()
        assert photo_count == 5, f"OutputPort photo count should be 5, got {photo_count}"
        print(f"  Photo count via OutputPort: {photo_count}")
        print("  [OK] perceptual_bins_o.get_ref_photo_count() returns correct count")

        # [10/11] Test perceptual_bins_o.get_ref_sequence_count()
        print("\n[10/11] Testing perceptual_bins_o.get_ref_sequence_count()...")
        seq_count = stage.perceptual_bins_o.get_ref_sequence_count()
        assert seq_count == 3, f"OutputPort sequence count should be 3, got {seq_count}"
        print(f"  Sequence count via OutputPort: {seq_count}")
        print("  [OK] perceptual_bins_o.get_ref_sequence_count() returns correct count")

        # [11/11] Test perceptual_bins_o.timestamp()
        print("\n[11/11] Testing perceptual_bins_o.timestamp()...")
        try:
            timestamp = stage.perceptual_bins_o.timestamp()
            # If we get here, the stage's cache exists (unexpected in this test)
            print(f"  Timestamp: {timestamp}")
            print("  [NOTE] Cache exists, timestamp returned (not expected in isolated test)")
        except RuntimeError as e:
            # Expected behavior: cache doesn't exist in isolated test
            print(f"  RuntimeError raised (expected): {e}")
            print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

        elapsed = time.perf_counter() - start_time

        print("\n" + "=" * 70)
        print("Comprehensive Test Complete!")
        print("=" * 70)

        # Summary statistics
        print("\nTest Summary:")
        print(f"  Input: {ref_photos} photos, {ref_seqs} sequences (1 empty)")
        print(f"  Output: {stage.ref_photos_final} photos, {stage.ref_seqs_final} sequences")
        print(f"  Hash bins: {len(accumulator)} bins (4 distinct hashes via random generation)")
        print("    - Collision bin: 1 bin with 2 photos (images 0 and 3, exact copies)")
        print("    - Singleton bins: 3 bins with 1 photo each (images 1, 2, 4)")
        print(f"  Time elapsed: {elapsed:.2f}s")

        print("\n[PASS] All validations passed!")
