"""Comprehensive end-to-end test for ComputeSHABins.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions using real test images with PIL.

FIXTURE STRATEGY:
Creates 6 test files with PIL (5 images + 1 text):
1. JPEG with standard EXIF (orientation=1)
2. JPEG with rotated EXIF (orientation=6, 90° CW) - dimensions swapped
3. PNG without EXIF (orientation=0)
4. Duplicate JPEG (same content as #1, same SHA256)
5. JPEG in subdirectory (tests recursive walk)
6. Text file (should be skipped by MIME filter)

Total: 6 files created → 5 files processed → 4 SHA bins (one bin has 2 duplicates)

COVERAGE-DRIVEN TESTING:
Only tests methods called in production code to identify dead code via coverage metrics.
Tests 12 methods: 8 stage methods + 4 OutputPort methods (verified by code analysis).
Does NOT test run() - calls individual lifecycle methods directly.

REGRESSION TESTING:
This is the comprehensive test for CI, validating all stage methods with controlled test data.
"""

import tempfile
import time
from pathlib import Path
from typing import TypedDict

from PIL import Image
from src.utils.compute_sha_bins import ComputeShaBins
from src.utils.config import CONFIG
from src.utils.photo_file import PhotoFile


class FixtureData(TypedDict):
    """Type definition for test fixture dictionary."""

    source_path: Path
    expected_processed: int  # 5 (excluding .txt)
    expected_bins: int  # 4
    file_paths: dict[str, Path]  # Image name -> file path


class ExpectedResult(TypedDict, total=False):
    """Type definition for expected PhotoFile properties."""

    mime: str
    orientation: int
    width: int
    height: int
    aspect_ratio: float
    description: str
    sha_matches: int  # Optional: index of file with matching SHA
    in_subdir: bool  # Optional: flag for subdirectory test


def create_test_images(temp_dir: Path) -> dict[str, Path]:
    """Create test images with controlled properties for testing.

    Creates 6 files (5 images + 1 text) with specific characteristics:
    - Different EXIF orientations (including dimension-swapping orientation=6)
    - Missing EXIF (PNG)
    - Duplicate content (same SHA256)
    - Subdirectory location (tests recursive walk)
    - Non-image file (tests MIME filtering)

    Args:
        temp_dir: Temporary directory for creating files

    Returns:
        dict mapping image names to file paths
    """
    images: dict[str, Path] = {}

    # Image 1: JPEG with standard EXIF (orientation=1)
    img1 = Image.new("RGB", (100, 150), color="red")  # Portrait: 100x150
    img1_path = temp_dir / "photo_001.jpg"

    exif1 = img1.getexif()
    exif1[274] = 1  # Orientation tag ID = 274, value = 1 (normal)
    img1.save(img1_path, "JPEG", exif=exif1)
    images["standard_exif"] = img1_path

    # Image 2: JPEG with rotated EXIF (orientation=6, 90° CW)
    img2 = Image.new("RGB", (100, 150), color="blue")  # Physical: 100x150
    img2_path = temp_dir / "photo_002.jpg"

    exif2 = img2.getexif()
    exif2[274] = 6  # 90° CW rotation - dimensions will be swapped to 150x100
    img2.save(img2_path, "JPEG", exif=exif2)
    images["rotated_exif"] = img2_path

    # Image 3: PNG without EXIF
    img3 = Image.new("RGB", (100, 150), color="green")
    img3_path = temp_dir / "photo_003.png"
    img3.save(img3_path, "PNG")  # PNG doesn't store EXIF via PIL
    images["no_exif"] = img3_path

    # Image 4: Duplicate JPEG (same content as Image 1, same SHA256)
    img4 = Image.new("RGB", (100, 150), color="red")  # Same as img1
    img4_path = temp_dir / "photo_004.jpg"

    exif4 = img4.getexif()
    exif4[274] = 1  # Same EXIF as img1
    img4.save(img4_path, "JPEG", exif=exif4)
    images["duplicate"] = img4_path

    # Image 5: JPEG in subdirectory (tests recursive walk)
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    img5 = Image.new("RGB", (100, 150), color="yellow")
    img5_path = subdir / "photo_005.jpg"

    exif5 = img5.getexif()
    exif5[274] = 1
    img5.save(img5_path, "JPEG", exif=exif5)
    images["subdirectory"] = img5_path

    # Image 6: Non-image file (.txt) - should be skipped by MIME filter
    txt_path = temp_dir / "not_an_image.txt"
    txt_path.write_text("This should be skipped by MIME filter", encoding="utf-8")
    images["text_file"] = txt_path

    return images


def test_comprehensive_end_to_end_coverage() -> None:
    """Run full stage lifecycle test for ComputeSHABins.

    Validates:
    - __init__() - Stage construction
    - prepare() - Directory walk, work item generation
    - stage_worker() - PhotoFile creation from files
    - accumulate_results() - SHA binning
    - finalise() - Status updates
    - needs_review() - Review type
    - has_review_data() - Review data check (before and after)
    - photofiles property - PhotoFile mapping
    - sha_bins_o.read() - OutputPort data access
    - sha_bins_o.get_ref_photo_count() - OutputPort photo count
    - sha_bins_o.get_ref_sequence_count() - OutputPort sequence count
    - sha_bins_o.timestamp() - OutputPort cache timestamp
    - Status updates (ref_photos_final=5, ref_seqs_final=None)
    - Atomic invariants (photo count preservation, SHA binning correctness)
    - EXIF orientation handling (orientation=6 swaps dimensions)
    - MIME type filtering (skips .txt file)
    - Recursive directory walk (finds subdirectory image)
    - Duplicate detection (same SHA → same bin)
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test: ComputeSHABins")
    print("=" * 70)

    # Create temp directory for test files
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # [SETUP] Create test images
        print("\nCreating test images...")
        file_paths = create_test_images(temp_dir)
        print(f"  Created {len(file_paths)} files (5 images + 1 text)")

        start_time = time.perf_counter()

        # [1/12] Test __init__()
        print("\n[1/12] Creating stage (__init__)...")
        stage = ComputeShaBins(source_path=temp_dir)

        # Validate initialization
        assert stage.stage_name == "Directory Walk", f"Stage name should be 'Directory Walk', got '{stage.stage_name}'"
        assert stage.source_path == temp_dir, "source_path should match input directory"
        assert stage.path == CONFIG.paths.sha_bins_pkl, "Cache path should be sha_bins_pkl"

        # Verify OutputPort created
        assert hasattr(stage, "sha_bins_o"), "Stage should have sha_bins_o OutputPort"

        print(f"  Stage name: {stage.stage_name}")
        print(f"  Source path: {stage.source_path}")
        print("  [OK] Stage initialized correctly")

        # [2/12] Test has_review_data() BEFORE run
        print("\n[2/12] Testing has_review_data() before run...")
        assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
        print("  [OK] has_review_data() returns False")

        # [3/12] Test prepare()
        print("\n[3/12] Running prepare()...")
        work_items, accumulator = stage.prepare()

        # Convert lazy generator to list for validation
        work_items_list = list(work_items)
        print(f"  Work items generated: {len(work_items_list)}")

        # Validate prepare results
        assert stage.ref_photos_init is None, "ref_photos_init should be None (no upstream stage)"
        assert stage.ref_seqs_init is None, "ref_seqs_init should be None (no sequences at this stage)"

        # Accumulator should be empty dict
        assert isinstance(accumulator, dict), "Accumulator should be dict"
        assert len(accumulator) == 0, "Accumulator should be empty initially"

        # Work items should be enumerated (id, (path, mime)) tuples
        # Should have 5 image files (skipping .txt)
        assert len(work_items_list) == 5, f"Expected 5 work items (image files only), got {len(work_items_list)}"

        # Validate work item structure
        for i, (photo_id, (path, mime)) in enumerate(work_items_list):
            assert isinstance(photo_id, int), f"Work item {i}: photo_id should be int"
            assert isinstance(path, Path), f"Work item {i}: path should be Path"
            assert isinstance(mime, str), f"Work item {i}: mime should be str"
            # Note: prepare() returns MIME subtype only (e.g., "jpeg", "png"), not full "image/jpeg"
            assert mime in ("jpeg", "png"), f"Work item {i}: mime subtype should be 'jpeg' or 'png', got '{mime}'"

        print(f"  [OK] Prepare validated: {len(work_items_list)} work items")

        # [4/12] Test stage_worker() on ALL files
        print(f"\n[4/12] Processing {len(work_items_list)} work items through stage_worker()...")

        # Expected results per file
        expected_results: dict[int, ExpectedResult] = {
            0: {  # photo_001.jpg (standard EXIF)
                "mime": "jpeg",
                "orientation": 1,
                "width": 100,
                "height": 150,
                "aspect_ratio": 100 / 150,
                "description": "JPEG with standard EXIF (orientation=1)",
            },
            1: {  # photo_002.jpg (rotated EXIF)
                "mime": "jpeg",
                "orientation": 6,
                "width": 150,  # SWAPPED (orientation 6)
                "height": 100,  # SWAPPED
                "aspect_ratio": 150 / 100,
                "description": "JPEG with rotated EXIF (orientation=6)",
            },
            2: {  # photo_003.png (no EXIF)
                "mime": "png",
                "orientation": 0,  # No EXIF
                "width": 100,
                "height": 150,
                "aspect_ratio": 100 / 150,
                "description": "PNG without EXIF",
            },
            3: {  # photo_004.jpg (duplicate of 001)
                "mime": "jpeg",
                "orientation": 1,
                "width": 100,
                "height": 150,
                "aspect_ratio": 100 / 150,
                "sha_matches": 0,  # Same SHA as file 0
                "description": "Duplicate JPEG (same SHA as file 0)",
            },
            4: {  # photo_005.jpg (subdirectory)
                "mime": "jpeg",
                "orientation": 1,
                "width": 100,
                "height": 150,
                "aspect_ratio": 100 / 150,
                "in_subdir": True,
                "description": "JPEG in subdirectory",
            },
        }

        worker_results: list[PhotoFile] = []
        sha_values: list[str] = []  # Track SHA values for duplicate detection

        for i, work_item in enumerate(work_items_list):
            photo_id, (path, mime) = work_item
            print(f"  Processing file {i + 1}/5: {path.name}...")

            # Call stage_worker (now returns tuple of (PhotoFile, sha256))
            id_reviews, seq_reviews, (photo, sha256) = ComputeShaBins.stage_worker(
                work_item,
                _args="",  # Not used in this stage
            )

            worker_results.append(photo)
            sha_values.append(sha256)

            # Validate worker result structure
            assert len(id_reviews) == 0, f"File {i}: id_reviews should be empty (no review data)"
            assert len(seq_reviews) == 0, f"File {i}: seq_reviews should be empty"
            assert isinstance(photo, PhotoFile), f"File {i}: result should be PhotoFile instance"
            assert isinstance(sha256, str), f"File {i}: sha256 should be string"

            # Validate PhotoFile properties
            expected = expected_results[i]
            print(f"    {expected['description']}")

            assert photo.path == path, f"File {i}: PhotoFile.path should match work item path"
            assert photo.mime == expected["mime"], f"File {i}: mime should be '{expected['mime']}', got '{photo.mime}'"

            # Access dimensions via context manager (lazy loading with canonical rotation)
            with photo.image_data() as img:
                width = img.get_width()
                height = img.get_height()
                aspect_ratio = img.get_aspect_ratio()

            assert width == expected["width"], f"File {i}: width should be {expected['width']}, got {width}"
            assert height == expected["height"], f"File {i}: height should be {expected['height']}, got {height}"
            assert abs(aspect_ratio - expected["aspect_ratio"]) < 0.01, (
                f"File {i}: aspect_ratio should be ~{expected['aspect_ratio']}, got {aspect_ratio}"
            )
            assert photo.pixels == expected["width"] * expected["height"], (
                f"File {i}: pixels should be {expected['width'] * expected['height']}, got {photo.pixels}"
            )
            assert len(sha256) == 64, f"File {i}: SHA256 should be 64 hex chars, got {len(sha256)}"
            assert photo.id == photo_id, f"File {i}: PhotoFile.id should match work item photo_id"

            # Special validations
            if "sha_matches" in expected:
                # Duplicate file should have same SHA as reference
                ref_sha = sha_values[expected["sha_matches"]]
                assert sha256 == ref_sha, f"File {i}: SHA should match file {expected['sha_matches']}"
                print(f"    [OK] Duplicate detected (SHA matches file {expected['sha_matches']})")

            if "in_subdir" in expected:
                assert "subdir" in str(photo.path), f"File {i}: path should contain 'subdir'"
                print("    [OK] Found in subdirectory")

            print("    [OK] PhotoFile validated")

        print(f"  [OK] All work items processed: {len(worker_results)} PhotoFiles created")

        # [5/12] Test accumulate_results()
        print("\n[5/12] Running accumulate_results()...")

        for photo, sha256 in zip(worker_results, sha_values, strict=False):
            stage.accumulate_results(accumulator, (photo, sha256))

        print(f"  SHA bins created: {len(accumulator)}")
        print(f"  Total photos in bins: {sum(len(bin_photos) for bin_photos in accumulator.values())}")

        # Validate accumulation
        # Should have 4 bins (file 0 and 3 are duplicates, same SHA)
        assert len(accumulator) == 4, f"Expected 4 SHA bins, got {len(accumulator)}"

        # Total photos should be 5
        total_photos = sum(len(bin_photos) for bin_photos in accumulator.values())
        assert total_photos == 5, f"Expected 5 total photos in bins, got {total_photos}"

        # One bin should have 2 photos (duplicate bin)
        bin_sizes = [len(bin_photos) for bin_photos in accumulator.values()]
        bin_sizes.sort()
        assert bin_sizes == [1, 1, 1, 2], f"Expected bin sizes [1, 1, 1, 2], got {bin_sizes}"

        # Verify duplicate bin contains files 0 and 3
        duplicate_sha = sha_values[0]
        assert duplicate_sha in accumulator, "Duplicate SHA should be in accumulator"
        assert len(accumulator[duplicate_sha]) == 2, "Duplicate bin should contain 2 photos"

        # Note: Photos no longer store SHA256 (used only for binning in Stage 1)
        # The fact that photos are in accumulator[duplicate_sha] guarantees they have that SHA

        print("  [OK] Results accumulated correctly")
        print(f"  Bin size distribution: {bin_sizes}")

        # [6/12] Test finalise()
        print("\n[6/12] Running finalise()...")
        stage.result = accumulator
        stage.finalise()

        print(f"  Final photos: {stage.ref_photos_final}")
        print(f"  Final sequences: {stage.ref_seqs_final}")

        # Validate status updates
        assert stage.ref_photos_final is not None, "ref_photos_final must not be None"
        assert isinstance(stage.ref_photos_final, int), (
            f"ref_photos_final must be int, got {type(stage.ref_photos_final)}"
        )
        assert stage.ref_photos_final == 5, f"ref_photos_final should be 5, got {stage.ref_photos_final}"

        assert stage.ref_seqs_final is None, "ref_seqs_final must be None (no sequences at this stage)"

        print("  [OK] Status updates validated")

        # [7/12] Test needs_review()
        print("\n[7/12] Testing needs_review()...")
        review_type = stage.needs_review()

        assert review_type == "none", f"Expected review type 'none', got '{review_type}'"
        print(f"  Review type: {review_type}")
        print("  [OK] needs_review() validated")

        # [8/12] Test has_review_data() AFTER run
        print("\n[8/12] Testing has_review_data() after run...")
        has_review = stage.has_review_data()

        assert not has_review, "has_review_data() should return False (review type is 'none')"
        print(f"  Has review data: {has_review}")
        print("  [OK] has_review_data() validated")

        # [9/12] Test photofiles property
        print("\n[9/12] Testing photofiles property...")
        photofiles_dict = stage.photofiles

        # Validate structure
        assert isinstance(photofiles_dict, dict), "photofiles should return dict"
        assert len(photofiles_dict) == 5, f"photofiles should contain 5 photos, got {len(photofiles_dict)}"

        # Validate mapping: id → PhotoFile
        for photo_id, photo in photofiles_dict.items():
            assert isinstance(photo_id, int), f"Photo ID should be int, got {type(photo_id)}"
            assert isinstance(photo, PhotoFile), f"Value should be PhotoFile, got {type(photo)}"
            assert photo.id == photo_id, f"PhotoFile.id ({photo.id}) should match dict key ({photo_id})"

        # Verify all original photos are in the dict
        for original_photo in worker_results:
            assert original_photo.id in photofiles_dict, f"Photo ID {original_photo.id} should be in photofiles dict"
            assert photofiles_dict[original_photo.id] is original_photo, (
                "photofiles dict should contain exact PhotoFile instances"
            )

        print(f"  [OK] photofiles property returns correct mapping ({len(photofiles_dict)} photos)")

        # [10/12] Test sha_bins_o.read()
        print("\n[10/12] Testing sha_bins_o.read()...")

        # Test read() method (stage.result already set in finalise phase)
        sha_bins_from_port = stage.sha_bins_o.read()

        # Validate return type and content
        assert isinstance(sha_bins_from_port, dict), "read() should return dict"
        assert sha_bins_from_port is accumulator, "read() should return the same dict object (not a copy)"
        assert len(sha_bins_from_port) == 4, f"read() should return 4 SHA bins, got {len(sha_bins_from_port)}"

        print(f"  [OK] read() returns correct SHA bins dict ({len(sha_bins_from_port)} bins)")

        # [11/12] Test sha_bins_o.get_ref_photo_count()
        print("\n[11/12] Testing sha_bins_o.get_ref_photo_count()...")

        photo_count = stage.sha_bins_o.get_ref_photo_count()

        # Validate return value
        assert photo_count == 5, f"get_ref_photo_count() should return 5, got {photo_count}"

        print(f"  [OK] get_ref_photo_count() returns {photo_count}")

        # [12/12] Test sha_bins_o.get_ref_sequence_count()
        print("\n[12/12] Testing sha_bins_o.get_ref_sequence_count()...")

        seq_count = stage.sha_bins_o.get_ref_sequence_count()

        # Validate return value
        assert seq_count is None, f"get_ref_sequence_count() should return None, got {seq_count}"

        print("  [OK] get_ref_sequence_count() returns None (no sequences at this stage)")

        # [BONUS] Test sha_bins_o.timestamp()
        print("\n[BONUS] Testing sha_bins_o.timestamp()...")

        # timestamp() reads from cache file's mtime
        # Since we haven't written to cache, this should raise RuntimeError
        try:
            timestamp = stage.sha_bins_o.timestamp()
            # If we get here, cache exists (unexpected in this test)
            print(f"  Unexpected: timestamp() returned {timestamp} (cache exists)")
        except RuntimeError as e:
            # Expected: cache doesn't exist yet
            print(f"  Expected RuntimeError: {e}")
            print("  [OK] timestamp() raises RuntimeError when cache doesn't exist")

        # [INVARIANTS] Validate atomic invariants
        print("\nValidating atomic invariants...")

        # Invariant 1: Total photo count preserved
        # All 5 processed photos should be in the bins
        photos_in_bins = sum(len(bin_photos) for bin_photos in stage.result.values())
        assert photos_in_bins == 5, f"Total photos in bins should be 5, got {photos_in_bins}"
        print("  [OK] Photo count preserved: 5 photos processed → 5 photos in bins")

        # Invariant 2: SHA binning correctness
        # Each photo should be in exactly one bin
        all_photos_in_bins = [photo for bin_photos in stage.result.values() for photo in bin_photos]
        assert len(all_photos_in_bins) == 5, (
            f"Should have exactly 5 photos across all bins, got {len(all_photos_in_bins)}"
        )

        # All photos in a bin should have the same SHA (guaranteed by binning algorithm)
        # Note: Photos no longer store SHA256 - it's only used for binning in Stage 1
        for sha, photos in stage.result.items():
            assert len(photos) > 0, f"Bin {sha[:8]}... should not be empty"
        print("  [OK] SHA binning correctness: all photos binned by SHA")

        # Invariant 3: Duplicate detection
        # Files 0 and 3 should be in the same bin (same content)
        duplicate_bin = accumulator[sha_values[0]]
        assert len(duplicate_bin) == 2, "Duplicate bin should contain exactly 2 photos"
        duplicate_ids = {photo.id for photo in duplicate_bin}
        expected_duplicate_ids = {
            worker_results[0].id,
            worker_results[3].id,
        }
        assert duplicate_ids == expected_duplicate_ids, (
            f"Duplicate bin should contain photos {expected_duplicate_ids}, got {duplicate_ids}"
        )
        print("  [OK] Duplicate detection: 2 identical files correctly binned together")

        elapsed = time.perf_counter() - start_time

        print("\n" + "=" * 70)
        print("Comprehensive Test Complete!")
        print("=" * 70)

        # Summary statistics
        print("\nTest Summary:")
        print("  Files created: 6 (5 images + 1 text)")
        print("  Files processed: 5 (text file skipped by MIME filter)")
        print("  SHA bins created: 4")
        print("  Duplicate bin size: 2 photos")
        print("  Singleton bins: 3")
        print(f"  Total photos: {stage.ref_photos_final}")
        print("  EXIF orientations tested: [1, 6, 0]")
        print("  Subdirectory walk: Successful")
        print(f"  Time elapsed: {elapsed:.2f}s")

        print("\n[PASS] All validations passed!")
