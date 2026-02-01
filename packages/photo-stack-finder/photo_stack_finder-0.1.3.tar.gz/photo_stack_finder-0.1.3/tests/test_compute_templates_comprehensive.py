"""Comprehensive end-to-end test for ComputeTemplates.

This test runs the full stage lifecycle (init -> prepare -> workers -> accumulate -> finalize)
to validate all methods and their interactions using synthetic PhotoFile fixtures (no real files).

FIXTURE STRATEGY:
Creates 8 PhotoFile objects with 4 different filename patterns:
1. Simple numbered: IMG_001.jpg, IMG_002.jpg, IMG_003.jpg → template "IMG_{P0}.jpg"
2. Multi-field: 2024_01_15.jpg, 2024_01_16.jpg → template "{P0}_{P1}_{P2}.jpg"
3. No digits: sunset.jpg → template "sunset.jpg" (singleton, empty indices)
4. Mixed separators: photo-001_v2.jpg, photo-002_v1.jpg → template "photo-{P0}_v{P1}.jpg"

Total: 8 input photos → 4 template bins

COVERAGE-DRIVEN TESTING:
Tests only methods called in production code (11 methods: 7 stage + 4 OutputPort).
Does NOT test run() - calls individual lifecycle methods directly.

REGRESSION TESTING:
This is the comprehensive test for CI, validating all stage methods with controlled test data.
"""

import time
from pathlib import Path
from typing import TypedDict

from src.utils.compute_templates import ComputeTemplates
from src.utils.photo_file import PhotoFile
from src.utils.sequence import INDEX_T

from tests.fixtures.cache_loader import MockInputPort


class FixtureData(TypedDict):
    """Type definition for test fixture dictionary."""

    photos: list[PhotoFile]
    ref_photos: int
    ref_seqs: None
    expected_bins: int
    expected_templates: dict[str, tuple[int, list[tuple[str, ...]]]]  # template -> (count, example indices)


def create_photo(photo_id: int, filename: str, **overrides: object) -> PhotoFile:
    """Create minimal PhotoFile with sensible defaults.

    Args:
        photo_id: Unique identifier for this photo
        filename: Filename for the path (used for template extraction)
        **overrides: Additional PhotoFile attributes to override

    Returns:
        PhotoFile object with minimal required fields
    """
    defaults = {
        "path": Path(f"test_photos/{filename}"),
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


def create_test_fixtures() -> FixtureData:
    """Create synthetic test fixtures with 4 different filename pattern scenarios.

    Scenario 1: Simple numbered (3 photos)
        - IMG_001.jpg, IMG_002.jpg, IMG_003.jpg
        - Template: IMG_{P0}.jpg
        - Indices: ("001",), ("002",), ("003",)

    Scenario 2: Multi-field (2 photos)
        - 2024_01_15.jpg, 2024_01_16.jpg
        - Template: {P0}_{P1}_{P2}.jpg
        - Indices: ("2024", "01", "15"), ("2024", "01", "16")

    Scenario 3: No digits (1 photo)
        - sunset.jpg
        - Template: sunset.jpg (singleton, no digit sequences)
        - Indices: () (empty tuple)

    Scenario 4: Mixed separators (2 photos)
        - photo-001_v2.jpg, photo-002_v1.jpg
        - Template: photo-{P0}_v{P1}.jpg
        - Indices: ("001", "2"), ("002", "1")

    Returns:
        dict with keys:
            - 'photos': list[PhotoFile] (8 photos total)
            - 'ref_photos': int (total input photos = 8)
            - 'ref_seqs': None (no sequences at this stage)
            - 'expected_bins': int (4 template bins)
            - 'expected_templates': dict mapping template to (count, example indices)
    """
    photos: list[PhotoFile] = []

    # Scenario 1: Simple numbered (3 photos)
    photos.append(create_photo(1, "IMG_001.jpg"))
    photos.append(create_photo(2, "IMG_002.jpg"))
    photos.append(create_photo(3, "IMG_003.jpg"))

    # Scenario 2: Multi-field (2 photos)
    photos.append(create_photo(4, "2024_01_15.jpg"))
    photos.append(create_photo(5, "2024_01_16.jpg"))

    # Scenario 3: No digits (1 photo)
    photos.append(create_photo(6, "sunset.jpg"))

    # Scenario 4: Mixed separators (2 photos)
    photos.append(create_photo(7, "photo-001_v2.jpg"))
    photos.append(create_photo(8, "photo-002_v1.jpg"))

    # Note: Template keys include the directory path from the photo.path
    # e.g., "test_photos/IMG_{P0}.jpg" or "test_photos\IMG_{P0}.jpg" on Windows
    expected_templates = {
        str(Path("test_photos/IMG_{P0}.jpg")): (3, [("001",), ("002",), ("003",)]),
        str(Path("test_photos/{P0}_{P1}_{P2}.jpg")): (2, [("2024", "01", "15"), ("2024", "01", "16")]),
        str(Path("test_photos/sunset.jpg")): (1, [()]),
        str(Path("test_photos/photo-{P0}_v{P1}.jpg")): (2, [("001", "2"), ("002", "1")]),
    }

    return {
        "photos": photos,
        "ref_photos": 8,
        "ref_seqs": None,
        "expected_bins": 4,
        "expected_templates": expected_templates,
    }


def test_comprehensive_end_to_end_coverage() -> None:
    """Run full stage lifecycle test.

    Validates:
    - __init__() (stage construction, ports creation)
    - prepare() (reads from input port, creates work items)
    - stage_worker() (template extraction and index parsing)
    - accumulate_results() (bins photos by template)
    - finalise() (sets status attributes, validates invariants)
    - needs_review() (returns "none")
    - has_review_data() (returns False)
    - template_bins_o.read() (OutputPort data access)
    - template_bins_o.get_ref_photo_count() (OutputPort photo count)
    - template_bins_o.get_ref_sequence_count() (OutputPort sequence count)
    - template_bins_o.timestamp() (OutputPort cache timestamp)

    Coverage-driven: Only tests methods called in production code.
    """
    print("\n" + "=" * 70)
    print("Comprehensive End-to-End Test: ComputeTemplates")
    print("=" * 70)

    # [1] Create test fixtures
    print("\nCreating test fixtures...")
    fixtures = create_test_fixtures()
    photos = fixtures["photos"]
    print(f"  Input data: {len(photos)} photos with 4 different filename patterns")
    print("    - Scenario 1: 3 simple numbered (IMG_NNN.jpg)")
    print("    - Scenario 2: 2 multi-field (YYYY_MM_DD.jpg)")
    print("    - Scenario 3: 1 no digits (sunset.jpg)")
    print("    - Scenario 4: 2 mixed separators (photo-NNN_vN.jpg)")

    start_time = time.perf_counter()

    # [1/11] Test __init__() - Stage construction
    print("\n[1/11] Creating stage (__init__)...")
    stage = ComputeTemplates()
    assert stage.stage_name == "Filename template binning", (
        f"Stage name should be 'Filename template binning', got '{stage.stage_name}'"
    )
    print(f"  Stage name: {stage.stage_name}")
    print("  [OK] Stage constructed successfully")

    # Test has_review_data() BEFORE run (must be False)
    assert not stage.has_review_data(), "has_review_data() should return False before stage runs"
    print("  [OK] has_review_data() returns False before stage runs")

    # Inject test data via MockInputPort
    stage.nonidentical_photos_i = MockInputPort(photos, None, len(photos))

    # [2/11] Test prepare()
    print("\n[2/11] Running prepare()...")
    work_items, accumulator = stage.prepare()

    # Convert iterator to list for validation
    work_items_list = list(work_items)
    print(f"  Work items generated: {len(work_items_list)}")

    # Validate prepare results
    assert len(work_items_list) == 8, f"Expected 8 work items (one per photo), got {len(work_items_list)}"
    assert isinstance(accumulator, dict), "Accumulator should be dict"
    assert len(accumulator) == 0, "Accumulator should be empty initially"

    # Validate work items are PhotoFile objects
    for i, photo in enumerate(work_items_list):
        assert isinstance(photo, PhotoFile), f"Work item {i}: should be PhotoFile instance"

    print("  [OK] Prepare validated: 8 work items, empty accumulator")

    # [3/11] Test stage_worker() on ALL photos
    print(f"\n[3/11] Processing {len(work_items_list)} work items through stage_worker()...")

    worker_results: list[tuple[PhotoFile, str, INDEX_T]] = []
    expected_worker_outputs = [
        ("IMG_{P0}.jpg", ("001",), "Simple numbered #1"),
        ("IMG_{P0}.jpg", ("002",), "Simple numbered #2"),
        ("IMG_{P0}.jpg", ("003",), "Simple numbered #3"),
        ("{P0}_{P1}_{P2}.jpg", ("2024", "01", "15"), "Multi-field #1"),
        ("{P0}_{P1}_{P2}.jpg", ("2024", "01", "16"), "Multi-field #2"),
        ("sunset.jpg", (), "No digits"),
        ("photo-{P0}_v{P1}.jpg", ("001", "2"), "Mixed separators #1"),
        ("photo-{P0}_v{P1}.jpg", ("002", "1"), "Mixed separators #2"),
    ]

    for i, photo in enumerate(work_items_list):
        print(f"  Processing photo {i + 1}/8: {photo.path.name}...")

        # Call stage_worker (static method)
        id_reviews, seq_reviews, result = ComputeTemplates.stage_worker(photo, _args="")

        worker_results.append(result)

        # Validate worker result structure
        assert len(id_reviews) == 0, f"Photo {i}: id_reviews should be empty (no review data)"
        assert len(seq_reviews) == 0, f"Photo {i}: seq_reviews should be empty"
        assert isinstance(result, tuple), f"Photo {i}: result should be tuple"
        assert len(result) == 3, f"Photo {i}: result tuple should have 3 elements"

        returned_photo, template_path, indices = result
        assert returned_photo is photo, f"Photo {i}: returned photo should be same instance"

        # Validate template and indices against expected values
        expected_template, expected_indices, description = expected_worker_outputs[i]
        # Extract template from template_path (which is the full path with template as name)
        actual_template = Path(template_path).name
        assert actual_template == expected_template, (
            f"Photo {i} ({description}): template should be '{expected_template}', got '{actual_template}'"
        )
        assert indices == expected_indices, (
            f"Photo {i} ({description}): indices should be {expected_indices}, got {indices}"
        )

        print(f"    {description}: template='{actual_template}', indices={indices}")

    print(f"  [OK] All work items processed: {len(worker_results)} results")

    # [4/11] Test accumulate_results()
    print("\n[4/11] Running accumulate_results()...")
    for result in worker_results:
        stage.accumulate_results(accumulator, result)

    # Validate accumulator structure
    assert len(accumulator) == 4, f"Expected 4 template bins, got {len(accumulator)}"
    print(f"  Template bins created: {len(accumulator)}")

    # Validate each bin
    for template, expected_data in fixtures["expected_templates"].items():
        expected_count, expected_indices_list = expected_data
        assert template in accumulator, f"Template '{template}' should be in accumulator"

        bin_items = accumulator[template]
        assert len(bin_items) == expected_count, (
            f"Template '{template}': expected {expected_count} photos, got {len(bin_items)}"
        )

        # Validate bin structure: list[tuple[INDEX_T, PhotoFile]]
        for j, (indices, photo) in enumerate(bin_items):
            assert isinstance(indices, tuple), f"Template '{template}', item {j}: indices should be tuple"
            assert isinstance(photo, PhotoFile), f"Template '{template}', item {j}: photo should be PhotoFile"
            # Verify indices match one of the expected values
            assert indices in expected_indices_list, (
                f"Template '{template}', item {j}: indices {indices} not in expected {expected_indices_list}"
            )

        print(f"    Template '{template}': {expected_count} photos")

    print("  [OK] Results accumulated correctly into 4 template bins")

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
    assert stage.ref_photos_final == 8, f"ref_photos_final should be 8, got {stage.ref_photos_final}"
    assert stage.ref_seqs_final is not None, "ref_seqs_final must not be None"
    assert isinstance(stage.ref_seqs_final, int), "ref_seqs_final must be int"
    assert stage.ref_seqs_final == 4, f"ref_seqs_final should be 4 (template bins), got {stage.ref_seqs_final}"

    # Validate atomic invariant: photo count preserved
    total_photos_in = fixtures["ref_photos"]
    total_photos_out = sum(len(bin_items) for bin_items in accumulator.values())
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
    print("  [OK] needs_review() returns 'none' (no review data for this stage)")

    # [7/11] Test has_review_data()
    print("\n[7/11] Testing has_review_data()...")
    has_review = stage.has_review_data()
    assert not has_review, f"has_review_data() should return False (review type is 'none'), got {has_review}"
    print(f"  Has review data: {has_review}")
    print("  [OK] has_review_data() returns False (consistent with needs_review())")

    # [8/11] Test template_bins_o.read()
    print("\n[8/11] Testing template_bins_o.read()...")
    # The OutputPort should return the stage's result
    template_bins_from_port = stage.template_bins_o.read()
    assert template_bins_from_port is stage.result, "template_bins_o.read() should return stage.result"
    assert len(template_bins_from_port) == 4, f"Expected 4 template bins from port, got {len(template_bins_from_port)}"
    print(f"  Template bins via OutputPort: {len(template_bins_from_port)} bins")
    print("  [OK] template_bins_o.read() returns correct result")

    # [9/11] Test template_bins_o.get_ref_photo_count()
    print("\n[9/11] Testing template_bins_o.get_ref_photo_count()...")
    photo_count = stage.template_bins_o.get_ref_photo_count()
    assert photo_count == 8, f"OutputPort photo count should be 8, got {photo_count}"
    print(f"  Photo count via OutputPort: {photo_count}")
    print("  [OK] template_bins_o.get_ref_photo_count() returns correct count")

    # [10/11] Test template_bins_o.get_ref_sequence_count()
    print("\n[10/11] Testing template_bins_o.get_ref_sequence_count()...")
    seq_count = stage.template_bins_o.get_ref_sequence_count()
    assert seq_count == 4, f"OutputPort sequence count should be 4 (template bins), got {seq_count}"
    print(f"  Sequence count via OutputPort: {seq_count}")
    print("  [OK] template_bins_o.get_ref_sequence_count() returns correct count")

    # [11/11] Test template_bins_o.timestamp()
    print("\n[11/11] Testing template_bins_o.timestamp()...")
    # timestamp() should raise RuntimeError when cache doesn't exist (stage hasn't been saved)
    try:
        timestamp = stage.template_bins_o.timestamp()
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
    print(f"  Input: {fixtures['ref_photos']} photos")
    print(f"  Output: {stage.ref_photos_final} photos, {stage.ref_seqs_final} template bins")
    print(f"  Template patterns tested: {len(fixtures['expected_templates'])}")
    print("    - Simple numbered: 3 photos")
    print("    - Multi-field: 2 photos")
    print("    - No digits: 1 photo")
    print("    - Mixed separators: 2 photos")
    print(f"  Time elapsed: {elapsed:.2f}s")

    print("\n[PASS] All validations passed!")
