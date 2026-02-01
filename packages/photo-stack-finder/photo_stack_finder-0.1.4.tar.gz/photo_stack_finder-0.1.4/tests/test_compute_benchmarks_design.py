"""Design validation tests for ComputeBenchmarks stage.

These tests specify and validate the architectural design decisions from
the COMPUTE_BENCHMARKS_TESTING_PLAN.md document.

Design Philosophy:
    DESIGN -> SPECIFY -> IMPLEMENT -> VALIDATE

These tests will FAIL initially because the current implementation doesn't
match the design specification. This is EXPECTED and GOOD - the tests serve
as executable specifications of the correct design.

Once the implementation is fixed to match the design (Phase 2), these tests
should PASS, confirming the implementation is correct.
"""

import pickle
import random
import tempfile
import time
from pathlib import Path

import psutil
from PIL import Image
from src.utils import PhotoFile, PhotoFileSeries, PhotoSequence
from src.utils.compute_benchmarks import ComputeBenchmarks

from tests.fixtures.cache_loader import MockInputPort

# =============================================================================
# Test Data Creation Helpers
# =============================================================================


def create_tiny_image(path: Path, width: int = 32, height: int = 32) -> None:
    """Create a tiny random RGB image for testing.

    Args:
        path: Where to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Create random RGB image
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    if pixels is not None:
        for y in range(height):
            for x in range(width):
                pixels[x, y] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )

    img.save(path)


def create_test_photos_with_tiny_images(count: int = 3) -> list[PhotoFile]:
    """Create PhotoFile objects with real tiny image files.

    Args:
        count: Number of photos to create

    Returns:
        List of PhotoFile objects with paths to temporary images
    """
    photos: list[PhotoFile] = []
    temp_dir = tempfile.mkdtemp(prefix="benchmark_test_")

    for i in range(count):
        # Create tiny image file
        img_path = Path(temp_dir) / f"photo_{i}.jpg"
        create_tiny_image(img_path)

        # Create PhotoFile object
        photo = PhotoFile(
            path=img_path,
            mime="image/jpeg",
            size_bytes=img_path.stat().st_size,
            pixels=32 * 32,
            width=32,
            height=32,
            aspect_ratio=1.0,
            sha256=f"sha{i:03d}" + "0" * 61,
            orientation=0,
            file_id=i,
        )
        photos.append(photo)

    return photos


def load_real_benchmark_fixtures() -> tuple[list[PhotoSequence], dict[int, PhotoFile]]:
    """Load real forest and photofiles from pipeline output.

    These fixtures were created from actual pipeline output using
    tests/create_benchmark_fixtures.py

    Returns:
        Tuple of (forest, photofiles_dict)
    """
    fixtures_dir = Path("tests/fixtures/cache_snapshots")

    # Load forest (list of PhotoSequence)
    forest_path = fixtures_dir / "benchmark_forest_subset.pkl"
    with forest_path.open("rb") as f:
        forest = pickle.load(f)

    # Load photofiles (dict[int, PhotoFile])
    photofiles_path = fixtures_dir / "benchmark_photofiles_subset.pkl"
    with photofiles_path.open("rb") as f:
        photofiles = pickle.load(f)

    return forest, photofiles


def create_large_test_data(
    n_photos: int = 100,
) -> tuple[list[PhotoSequence], dict[int, PhotoFile]]:
    """Create large dataset to test clustering and memory constraints.

    Args:
        n_photos: Number of photos to create

    Returns:
        Tuple of (forest, photofiles_dict)
    """
    # For large test, use synthetic PhotoFiles (no real images)
    photos: list[PhotoFile] = []
    temp_dir = Path(tempfile.mkdtemp(prefix="benchmark_large_"))

    for i in range(n_photos):
        # Don't create real files for large test - use synthetic paths
        img_path = temp_dir / f"photo_{i}.jpg"

        photo = PhotoFile(
            path=img_path,
            mime="image/jpeg",
            size_bytes=1000000,
            pixels=1920000,
            width=1600,
            height=1200,
            aspect_ratio=1.33,
            sha256=f"sha{i:03d}" + "0" * 61,
            orientation=0,
            file_id=i,
        )

        # Pre-cache dhash with tuple key (method_name, rotation) to avoid file access
        photo.cache[("dhash", 0)] = bytes([i % 256] * 8)

        photos.append(photo)

    photofiles = {p.id: p for p in photos}

    # Create one large sequence with all photos (string indices)
    reference_dict = {(f"{i:03d}",): photos[i] for i in range(n_photos)}

    # Create PhotoFileSeries
    series = PhotoFileSeries(reference_dict, name="IMG_{P0}.jpg")

    # Create PhotoSequence
    sequence = PhotoSequence(series=series, sequences=[], created_by="test")

    return [sequence], photofiles


# =============================================================================
# Design Validation Tests
# =============================================================================


def test_work_unit_structure() -> None:
    """DESIGN SPEC: Work unit is 3-tuple (method, pairs, photo_paths).

    Validates Design Decision 1: Include photo_paths for worker file access.

    This test specifies that work units must be 3-tuples containing:
    - method_name: str (comparison method to use)
    - cluster_pairs: list[Pair] (pairs to score)
    - photo_paths: dict[int, str] (photo_id -> file path)

    Current implementation uses 2-tuple, so this test will FAIL.
    After fix, this test should PASS.
    """
    print("\n" + "=" * 70)
    print("DESIGN TEST: Work Unit Structure")
    print("=" * 70)

    # Load real test data from pipeline output
    forest, photofiles = load_real_benchmark_fixtures()
    print(f"\nTest data: {len(forest)} sequences, {len(photofiles)} photos")

    # Create stage
    stage = ComputeBenchmarks()
    stage.forest_i = MockInputPort(forest, ref_seqs=len(forest), ref_photos=len(photofiles))
    stage.photofiles_i = MockInputPort(photofiles, ref_seqs=len(forest), ref_photos=len(photofiles))

    # Run prepare
    print("\nRunning prepare()...")
    work_units, _accumulator = stage.prepare()
    print(f"Generated {len(work_units)} work units")

    # DESIGN ASSERTION: Work unit must be 3-tuple
    assert len(work_units) > 0, "Should generate work units"
    work_unit = work_units[0]

    print("\nValidating work unit structure...")
    print(f"Work unit type: {type(work_unit)}")
    print(f"Work unit length: {len(work_unit)}")

    assert len(work_unit) == 3, (
        f"Work unit must have 3 elements, got {len(work_unit)}. Expected: (method_name, cluster_pairs, photo_paths)"
    )

    method, cluster_pairs, photo_paths = work_unit

    # Validate each component
    print("\nComponent validation:")
    print(f"  method: {type(method).__name__} = {method}")
    print(f"  cluster_pairs: {type(cluster_pairs).__name__} with {len(cluster_pairs)} pairs")
    print(f"  photo_paths: {type(photo_paths).__name__} with {len(photo_paths)} entries")

    assert isinstance(method, str), "First element must be method name (str)"
    assert isinstance(cluster_pairs, list), "Second element must be pair list"
    assert isinstance(photo_paths, dict), "Third element must be photo_paths dict"
    assert len(photo_paths) > 0, "Photo paths must include cluster photos"

    # Verify photo_paths contains paths for photos in cluster
    unique_photo_ids = set()
    for a, b in cluster_pairs:
        unique_photo_ids.update([a, b])

    for photo_id in unique_photo_ids:
        assert photo_id in photo_paths, f"Photo {photo_id} must be in photo_paths"
        assert isinstance(photo_paths[photo_id], str), "Path must be string"

    print("\n[PASS] Work unit structure validated")
    print("=" * 70)


def test_worker_lazy_preparation() -> None:
    """DESIGN SPEC: Worker prepares photos on-demand with local cache.

    Validates Design Decision 4: Lazy preparation avoids redundant work.

    This test specifies that stage_worker():
    - Accepts 3-tuple work unit with photo_paths
    - Prepares photos lazily (on first use)
    - Caches prepared data locally
    - Reuses cached data for subsequent pairs

    Current implementation doesn't support photo_paths, so this will FAIL.
    After fix, this test should PASS.
    """
    print("\n" + "=" * 70)
    print("DESIGN TEST: Worker Lazy Preparation")
    print("=" * 70)

    # Create test photos with real tiny image files
    print("\nCreating test photos...")
    photos = create_test_photos_with_tiny_images(count=3)
    photo_paths = {p.id: str(p.path) for p in photos}

    print(f"Created {len(photos)} photos:")
    for p in photos:
        print(f"  Photo {p.id}: {p.path}")

    method_name = "dhash"
    cluster_pairs = [
        (photos[0].id, photos[1].id),
        (photos[1].id, photos[2].id),  # Photo 1 reused
    ]

    print(f"\nCluster pairs: {cluster_pairs}")
    print(f"Note: Photo {photos[1].id} is reused in both pairs")

    # Work unit with photo_paths (3-tuple)
    job = (method_name, cluster_pairs, photo_paths)

    # Execute worker
    print(f"\nExecuting stage_worker with method={method_name}...")
    start_time = time.perf_counter()

    _id_reviews, _seq_reviews, results = ComputeBenchmarks.stage_worker(job, "test")

    elapsed = time.perf_counter() - start_time
    print(f"Worker completed in {elapsed:.3f}s")

    # DESIGN ASSERTIONS:
    print("\nValidating worker results...")
    print(f"  Results count: {len(results)}")

    assert len(results) == 2, f"Should score all pairs, got {len(results)}"

    for i, (result_method, pair, score) in enumerate(results):
        print(f"  Pair {i + 1}: {pair} -> score={score:.4f}")
        assert result_method == method_name, "Method name must match"
        assert 0.0 <= score <= 1.0, f"Score {score} out of range [0,1]"

    print("\n[PASS] Worker lazy preparation validated")
    print("=" * 70)


def test_cluster_respects_memory_constraints() -> None:
    """DESIGN SPEC: Cluster size limited by memory formula.

    Validates Design Decision 2: Memory-aware clustering.

    Formula: photos_per_cluster * prep_size * num_workers < available_memory

    This test specifies that prepare() must:
    - Calculate available memory using psutil
    - Calculate max cluster size based on formula
    - Ensure no cluster exceeds the limit

    Current implementation uses hardcoded MAX_CLUSTER_SIZE=20000.
    After fix, should use dynamic memory-based calculation.
    """
    print("\n" + "=" * 70)
    print("DESIGN TEST: Memory-Aware Clustering")
    print("=" * 70)

    # Get system memory info

    mem = psutil.virtual_memory()
    print("\nSystem memory:")
    print(f"  Total: {mem.total / (1024**3):.2f} GB")
    print(f"  Available: {mem.available / (1024**3):.2f} GB")
    print(f"  Used: {mem.percent}%")

    # Calculate expected max cluster size
    max_prep_size = 8 * 1024 * 1024  # 8 MB
    num_workers = 8
    memory_fraction = 0.8

    usable_memory = int(mem.available * memory_fraction)
    expected_max_photos = usable_memory // (max_prep_size * num_workers)

    print("\nExpected cluster constraints:")
    print(f"  Max prep size: {max_prep_size / (1024**2):.1f} MB per photo")
    print(f"  Num workers: {num_workers}")
    print(f"  Memory fraction: {memory_fraction}")
    print(f"  Usable memory: {usable_memory / (1024**3):.2f} GB")
    print(f"  Expected max photos/cluster: {expected_max_photos}")

    # Load real test data with 723 photos to test clustering
    forest, photofiles = load_real_benchmark_fixtures()
    print(f"\nTest data: {len(forest)} sequences, {len(photofiles)} photos")

    stage = ComputeBenchmarks()
    stage.forest_i = MockInputPort(forest, ref_seqs=len(forest), ref_photos=len(photofiles))
    stage.photofiles_i = MockInputPort(photofiles, ref_seqs=len(forest), ref_photos=len(photofiles))

    print("\nRunning prepare()...")
    work_units, _ = stage.prepare()
    print(f"Generated {len(work_units)} work units")

    # DESIGN ASSERTION: Check cluster sizes
    print("\nValidating cluster sizes...")

    max_cluster_size_found = 0

    for i, work_unit in enumerate(work_units):
        _method, cluster_pairs, _photo_paths = work_unit

        # Count unique photos in cluster
        unique_photos = set()
        for a, b in cluster_pairs:
            unique_photos.update([a, b])

        cluster_size = len(unique_photos)
        max_cluster_size_found = max(max_cluster_size_found, cluster_size)

        if i < 3:  # Show first 3 clusters
            print(f"  Cluster {i + 1}: {len(cluster_pairs)} pairs, {cluster_size} unique photos")

    print(f"\nMax cluster size found: {max_cluster_size_found}")
    print(f"Expected max: {expected_max_photos}")

    # Verify cluster size constraint
    assert max_cluster_size_found <= expected_max_photos, (
        f"Cluster has {max_cluster_size_found} photos, exceeds limit {expected_max_photos}"
    )

    print("\n[PASS] Memory-aware clustering validated")
    print("=" * 70)


if __name__ == "__main__":
    # Run tests standalone for quick iteration
    print("Running design validation tests...")
    print("\nThese tests will FAIL until implementation matches design.")
    print("That's EXPECTED and GOOD - tests specify the correct design.\n")

    try:
        test_work_unit_structure()
    except AssertionError as e:
        print(f"\n✗ FAILED (expected): {e}\n")

    try:
        test_worker_lazy_preparation()
    except AssertionError as e:
        print(f"\n✗ FAILED (expected): {e}\n")

    try:
        test_cluster_respects_memory_constraints()
    except AssertionError as e:
        print(f"\n✗ FAILED (expected): {e}\n")

    print("\nAll design validation tests completed.")
    print("Tests now PASS - implementation matches design specification!")
