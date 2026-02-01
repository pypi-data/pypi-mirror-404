"""Comprehensive end-to-end test for ComputeIdentical.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions using synthetic fixtures with temp files.

FIXTURE STRATEGY:
Creates 4 SHA bins with tiny temp files:
1. Singleton bin (1 photo) - No comparison needed
2. All identical bin (3 photos, all match) - 1 exemplar, 2 duplicates
3. All different bin (3 photos, none match) - 3 exemplars
4. Mixed bin (5 photos: 2+2+1) - 3 exemplars, 2 duplicates

Total: 12 input photos → 8 output exemplars

REGRESSION TESTING:
This is the comprehensive test for CI, validating all stage methods with controlled test data.
"""

import tempfile
import time
from pathlib import Path
from typing import TypedDict

from src.utils.compute_identical import ComputeIdentical
from src.utils.photo_file import PhotoFile

from tests.fixtures.cache_loader import MockInputPort


class FixtureData(TypedDict):
    """Type definition for test fixture dictionary."""

    sha_bins: dict[str, list[PhotoFile]]
    ref_photos: int
    ref_seqs: None
    expected_exemplars: int
    expected_groups: int


def create_photo(photo_id: int, file_path: Path, **overrides: object) -> PhotoFile:
    """Create minimal PhotoFile with sensible defaults.

    Args:
        photo_id: Unique identifier for this photo
        file_path: Path to the actual file (for binary comparison)
        **overrides: Additional PhotoFile attributes to override

    Returns:
        PhotoFile object with minimal required fields
    """
    defaults = {
        "path": file_path,
        "mime": "image/jpeg",
        "size_bytes": 1000000,
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
    photo.cache["pixels"] = 1920000
    photo.cache["aspect_ratio"] = 1.33
    photo.cache["width"] = 1600
    photo.cache["height"] = 1200

    return photo


def create_test_fixtures(temp_dir: Path) -> FixtureData:
    """Create synthetic test fixtures with temp files for binary comparison.

    Creates 4 SHA bins with different duplicate scenarios:
    - Bin 1: Singleton (1 photo)
    - Bin 2: All identical (3 photos with same content)
    - Bin 3: All different (3 photos with different content)
    - Bin 4: Mixed (5 photos: 2 identical + 2 identical + 1 unique)

    Args:
        temp_dir: Temporary directory for creating test files

    Returns:
        dict with keys:
            - 'sha_bins': dict[str, list[PhotoFile]]
            - 'ref_photos': int (total input photos)
            - 'ref_seqs': None (no sequences at this stage)
            - 'expected_exemplars': int (expected output count)
            - 'expected_groups': int (expected IdenticalGroup count)
    """
    # Create temp files with known content
    # Bin 1: Singleton
    file1 = temp_dir / "photo1.jpg"
    file1.write_bytes(b"unique_content_1")

    # Bin 2: All identical (same content)
    file2a = temp_dir / "photo2a.jpg"
    file2b = temp_dir / "photo2b.jpg"
    file2c = temp_dir / "photo2c.jpg"
    identical_content = b"identical_content_2"
    file2a.write_bytes(identical_content)
    file2b.write_bytes(identical_content)
    file2c.write_bytes(identical_content)

    # Bin 3: All different
    file3a = temp_dir / "photo3a.jpg"
    file3b = temp_dir / "photo3b.jpg"
    file3c = temp_dir / "photo3c.jpg"
    file3a.write_bytes(b"unique_content_3a")
    file3b.write_bytes(b"unique_content_3b")
    file3c.write_bytes(b"unique_content_3c")

    # Bin 4: Mixed (2 identical + 2 identical + 1 unique)
    file4a = temp_dir / "photo4a.jpg"
    file4b = temp_dir / "photo4b.jpg"
    file4c = temp_dir / "photo4c.jpg"
    file4d = temp_dir / "photo4d.jpg"
    file4e = temp_dir / "photo4e.jpg"
    content_4_group1 = b"identical_content_4_group1"
    content_4_group2 = b"identical_content_4_group2"
    file4a.write_bytes(content_4_group1)
    file4b.write_bytes(content_4_group1)  # Identical to 4a
    file4c.write_bytes(content_4_group2)
    file4d.write_bytes(content_4_group2)  # Identical to 4c
    file4e.write_bytes(b"unique_content_4e")

    # Create PhotoFile objects
    # Use different SHA for each bin to simulate SHA binning
    sha_bins = {
        "sha_bin_1": [
            create_photo(1, file1, sha256="sha1" + "0" * 60),
        ],
        "sha_bin_2": [
            create_photo(2, file2a, sha256="sha2" + "0" * 60),
            create_photo(3, file2b, sha256="sha2" + "0" * 60),
            create_photo(4, file2c, sha256="sha2" + "0" * 60),
        ],
        "sha_bin_3": [
            create_photo(5, file3a, sha256="sha3" + "0" * 60),
            create_photo(6, file3b, sha256="sha3" + "0" * 60),
            create_photo(7, file3c, sha256="sha3" + "0" * 60),
        ],
        "sha_bin_4": [
            create_photo(8, file4a, sha256="sha4" + "0" * 60),
            create_photo(9, file4b, sha256="sha4" + "0" * 60),
            create_photo(10, file4c, sha256="sha4" + "0" * 60),
            create_photo(11, file4d, sha256="sha4" + "0" * 60),
            create_photo(12, file4e, sha256="sha4" + "0" * 60),
        ],
    }

    return {
        "sha_bins": sha_bins,
        "ref_photos": 12,  # Total input photos
        "ref_seqs": None,  # No sequences at this stage
        "expected_exemplars": 8,  # 1 + 1 + 3 + 3
        "expected_groups": 3,  # Bins 2, 4 have duplicates (bin 4 has 2 groups)
    }


def test_comprehensive_end_to_end_coverage() -> None:
    """Run full stage lifecycle test.

    This test validates:
    - __init__()
    - prepare()
    - stage_worker() (all 4 bins)
    - accumulate_results()
    - finalise()
    - needs_review()
    - has_review_data()
    - nonidentical_o.read()
    - nonidentical_o.get_ref_photo_count()
    - nonidentical_o.get_ref_sequence_count()
    - nonidentical_o.timestamp()
    - Status updates (ref_photos_final, ref_seqs_final)
    - Atomic invariants (photo count preservation)
    - Review data (IdenticalGroup objects)
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test: ComputeIdentical")
    print("=" * 70)

    # Create temp directory for test files
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Create test fixtures
        print("\nCreating test fixtures with temp files...")
        inputs = create_test_fixtures(temp_dir)
        print(f"  SHA bins: {len(inputs['sha_bins'])} bins")
        print(f"  Total photos: {inputs['ref_photos']}")

        # Show bin sizes
        print("\n  Bin details:")
        for i, (sha, photos) in enumerate(inputs["sha_bins"].items(), 1):
            print(f"    {i}. {sha}: {len(photos)} photos")

        start_time = time.perf_counter()

        # [1] Create stage (tests __init__)
        print("\n[1/11] Creating stage (__init__)...")
        stage = ComputeIdentical()
        print(f"  Stage name: {stage.stage_name}")
        print(f"  Output path: {stage.path}")
        assert stage.stage_name == "Byte-identical detection", "Stage name must be 'Byte-identical detection'"

        # Test has_review_data() BEFORE stage runs (must return False)
        assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
        print("  [OK] has_review_data() returns False before stage runs")

        # Inject test data
        stage.sha_bins_i = MockInputPort(inputs["sha_bins"], inputs["ref_seqs"], inputs["ref_photos"])

        # [2] Run prepare (tests prepare)
        print("[2/11] Running prepare()...")
        work_items, accumulator = stage.prepare()
        print(f"  Work items generated: {len(work_items)}")
        print(f"  Singleton bins (pre-filtered): {inputs['ref_photos'] - sum(len(item) for item in work_items)}")
        print(f"  Accumulator (exemplars): {len(accumulator)} photos")

        # Validate prepare results
        # Only bins with multiple photos should be work items
        expected_work_items = 3  # Bins 2, 3, 4 have multiple photos
        assert len(work_items) == expected_work_items, (
            f"Work item count should be {expected_work_items}, got {len(work_items)}"
        )

        # Singleton bin (bin 1) should be in accumulator
        assert len(accumulator) == 1, f"Accumulator should have 1 singleton, got {len(accumulator)}"

        # Total photos in work items + accumulator should equal input
        total_photos_in_work = sum(len(item) for item in work_items) + len(accumulator)
        assert total_photos_in_work == inputs["ref_photos"], (
            f"Total photos in work + accumulator should match input: {total_photos_in_work} != {inputs['ref_photos']}"
        )

        print(f"  [OK] Prepare validated: {len(work_items)} work items, {len(accumulator)} singletons")

        # [3] Process ALL work items through stage_worker (tests stage_worker)
        print(f"[3/11] Processing {len(work_items)} work items through stage_worker()...")

        # Expected results per bin
        expected_results = {
            1: {"exemplars": 1, "groups": 0, "description": "Singleton - pre-filtered"},
            2: {"exemplars": 1, "groups": 1, "description": "All identical - 3 photos"},
            3: {"exemplars": 3, "groups": 0, "description": "All different - 3 photos"},
            4: {"exemplars": 3, "groups": 2, "description": "Mixed - 2+2+1 photos"},
        }

        total_groups_found = 0
        worker_results = []
        # Initialize review result collection (normally done by pipeline framework)
        stage.identical_review_result = []

        for i, work_item in enumerate(work_items):
            bin_num = i + 2  # Work items are bins 2, 3, 4 (bin 1 is singleton)
            print(f"  Processing bin {bin_num}: {len(work_item)} photos...")

            # stage_worker returns (id_reviews, seq_reviews, exemplars)
            id_reviews, seq_reviews, exemplars = ComputeIdentical.stage_worker(work_item, "test")
            worker_results.append(exemplars)
            # Collect review data (normally done by pipeline framework)
            stage.identical_review_result.extend(id_reviews)

            # Validate results
            expected = expected_results[bin_num]
            print(f"    Exemplars: {len(exemplars)}, Groups: {len(id_reviews)}")
            print(f"    Expected: {expected['description']}")

            # Check exemplar count
            assert len(exemplars) == expected["exemplars"], (
                f"Bin {bin_num}: Expected {expected['exemplars']} exemplars, got {len(exemplars)}"
            )

            # Check group count
            assert len(id_reviews) == expected["groups"], (
                f"Bin {bin_num}: Expected {expected['groups']} groups, got {len(id_reviews)}"
            )

            # Validate group structure for bins with duplicates
            for group in id_reviews:
                assert hasattr(group, "photos"), f"Bin {bin_num}: Group missing 'photos' attribute"
                assert hasattr(group, "exemplar_id"), f"Bin {bin_num}: Group missing 'exemplar_id' attribute"
                # photos is a list of IdenticalPhoto objects
                photo_ids = [p.id for p in group.photos]
                assert group.exemplar_id in photo_ids, (
                    f"Bin {bin_num}: Exemplar ID {group.exemplar_id} not in photos list"
                )
                assert len(group.photos) >= 2, (
                    f"Bin {bin_num}: Group should have at least 2 photos, got {len(group.photos)}"
                )

            print("    [OK] Bin results validated")
            total_groups_found += len(id_reviews)

            # seq_reviews should always be empty for this stage
            assert len(seq_reviews) == 0, f"Bin {bin_num}: seq_reviews should be empty, got {len(seq_reviews)}"

        # Validate total groups
        assert total_groups_found == inputs["expected_groups"], (
            f"Expected {inputs['expected_groups']} total groups, got {total_groups_found}"
        )

        print(f"  [OK] All work items processed: {len(worker_results)} results, {total_groups_found} groups")

        # [4] Accumulate results (tests accumulate_results)
        print("[4/11] Running accumulate_results()...")
        for exemplars in worker_results:
            stage.accumulate_results(accumulator, exemplars)

        print(f"  Total exemplars accumulated: {len(accumulator)}")

        # Validate accumulation
        assert len(accumulator) == inputs["expected_exemplars"], (
            f"Expected {inputs['expected_exemplars']} total exemplars, got {len(accumulator)}"
        )
        print("  [OK] Results accumulated successfully")

        # [5] Finalize stage (tests finalise)
        print("[5/11] Running finalise()...")
        stage.result = accumulator
        stage.finalise()
        print(f"  Final photos: {stage.ref_photos_final}")
        print(f"  Final sequences: {stage.ref_seqs_final}")

        # Validate status updates
        print("\n  Validating status updates...")
        assert stage.ref_photos_final is not None, "ref_photos_final must not be None"
        assert stage.ref_seqs_final is None, "ref_seqs_final must be None (no sequences at this stage)"
        assert isinstance(stage.ref_photos_final, int), (
            f"ref_photos_final must be int, got {type(stage.ref_photos_final)}"
        )

        # ref_photos_final should be the count of unique exemplars
        assert stage.ref_photos_final == inputs["expected_exemplars"], (
            f"ref_photos_final should be {inputs['expected_exemplars']}, got {stage.ref_photos_final}"
        )

        # Validate atomic invariant: total photos preserved
        # Total photos = exemplars + duplicates
        total_duplicates = inputs["ref_photos"] - inputs["expected_exemplars"]
        total_photos_in_groups = sum(len(group.photos) for group in stage.identical_review_result)
        # Each group includes the exemplar, so duplicates = total_in_groups - num_groups
        duplicates_found = total_photos_in_groups - len(stage.identical_review_result)
        assert duplicates_found == total_duplicates, (
            f"Expected {total_duplicates} duplicates, found {duplicates_found} in review groups"
        )

        print(f"  [OK] Status updates valid: photos={stage.ref_photos_final}, seqs={stage.ref_seqs_final}")
        print(
            f"  [OK] Atomic invariant validated: {inputs['ref_photos']} photos in → "
            f"{stage.ref_photos_final} exemplars + {duplicates_found} duplicates = "
            f"{stage.ref_photos_final + duplicates_found} photos total"
        )

        # [6] Test review methods
        print("[6/11] Testing needs_review()...")
        review_type = stage.needs_review()
        assert review_type == "photos", f"Expected review type 'photos', got '{review_type}'"
        print(f"  Review type: {review_type}")

        print("[7/11] Testing has_review_data()...")
        has_review = stage.has_review_data()
        print(f"  Has review data: {has_review}")

        # Should have review data since we have duplicate groups
        assert has_review, "Should have review data (duplicate groups found)"

        # Validate review data structure (IdenticalGroup objects)
        print("\n  Validating review data structure (IdenticalGroup)...")
        print(f"    Identical groups: {len(stage.identical_review_result)}")
        assert len(stage.identical_review_result) == inputs["expected_groups"], (
            f"Expected {inputs['expected_groups']} review groups, got {len(stage.identical_review_result)}"
        )

        for i, group in enumerate(stage.identical_review_result):
            print(f"    Group {i + 1}: {len(group.photos)} photos (including exemplar)")

            # Validate IdenticalGroup structure
            assert hasattr(group, "photos"), f"Group {i + 1} missing 'photos' attribute"
            assert hasattr(group, "exemplar_id"), f"Group {i + 1} missing 'exemplar_id' attribute"
            assert isinstance(group.photos, list), f"Group {i + 1} photos must be list"
            assert len(group.photos) >= 2, f"Group {i + 1} should have at least 2 photos"
            photo_ids = [p.id for p in group.photos]
            assert group.exemplar_id in photo_ids, f"Group {i + 1} exemplar ID {group.exemplar_id} not in photos list"

            # Validate all photos in group are IdenticalPhoto objects with correct attributes
            for photo in group.photos:
                assert hasattr(photo, "id"), f"Group {i + 1} photo missing 'id' attribute"
                assert hasattr(photo, "path"), f"Group {i + 1} photo missing 'path' attribute"
                assert hasattr(photo, "is_exemplar"), f"Group {i + 1} photo missing 'is_exemplar' attribute"

        print("    [OK] All review groups validated")

        # [8] Test nonidentical_o.read()
        print("\n[8/11] Testing nonidentical_o.read()...")
        output_data = stage.nonidentical_o.read()
        assert output_data == stage.result, "nonidentical_o.read() should return stage.result"
        assert len(output_data) == inputs["expected_exemplars"], (
            f"nonidentical_o.read() should return {inputs['expected_exemplars']} exemplars, got {len(output_data)}"
        )
        print(f"  Exemplars via OutputPort: {len(output_data)} photos")
        print("  [OK] nonidentical_o.read() returns correct result")

        # [9] Test nonidentical_o.get_ref_photo_count()
        print("\n[9/11] Testing nonidentical_o.get_ref_photo_count()...")
        ref_photos = stage.nonidentical_o.get_ref_photo_count()
        assert ref_photos == stage.ref_photos_final, (
            f"OutputPort photo count should match ref_photos_final: {ref_photos} != {stage.ref_photos_final}"
        )
        print(f"  Photo count via OutputPort: {ref_photos}")
        print("  [OK] nonidentical_o.get_ref_photo_count() returns correct count")

        # [10] Test nonidentical_o.get_ref_sequence_count()
        print("\n[10/11] Testing nonidentical_o.get_ref_sequence_count()...")
        ref_seqs = stage.nonidentical_o.get_ref_sequence_count()
        assert ref_seqs == stage.ref_seqs_final, (
            f"OutputPort sequence count should match ref_seqs_final: {ref_seqs} != {stage.ref_seqs_final}"
        )
        print(f"  Sequence count via OutputPort: {ref_seqs}")
        print("  [OK] nonidentical_o.get_ref_sequence_count() returns correct count")

        # [11] Test nonidentical_o.timestamp()
        print("\n[11/11] Testing nonidentical_o.timestamp()...")
        try:
            timestamp = stage.nonidentical_o.timestamp()
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
        print(f"  Bins tested: {len(inputs['sha_bins'])}")
        print(f"  Photos processed: {inputs['ref_photos']}")
        print(f"  Exemplars output: {stage.ref_photos_final}")
        print(f"  Duplicate groups found: {len(stage.identical_review_result)}")
        print(f"  Duplicates identified: {duplicates_found}")
        print(f"  Time elapsed: {elapsed:.2f}s")

        print("\n[PASS] All validations passed!")


if __name__ == "__main__":
    test_comprehensive_end_to_end_coverage()
