"""Comprehensive tests for rotation-aware photo comparison.

Tests the rotation logic in GateSequence.compare_with_rotation() which:
1. Normalizes photos to landscape orientation
2. Attempts comparison at normalized rotation first
3. Attempts 180° rotation of reference if first fails
4. Uses cached preparations when available to avoid pixel loading
"""

from __future__ import annotations

import numpy as np
import pytest

from src.utils import CONFIG
from src.utils.comparison_gates import GateSequence
from src.utils.photo_file import PhotoFile


class TestRotationAwareComparison:
    """Test rotation-aware comparison logic."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Configure comparison gates for testing."""
        # Save original config
        self.original_gates = CONFIG.processing.COMPARISON_GATES
        self.original_thresholds = CONFIG.processing.GATE_THRESHOLDS.copy()

        # Set test config (single hash method for simplicity)
        CONFIG.processing.COMPARISON_GATES = ["dhash"]
        CONFIG.processing.GATE_THRESHOLDS = {"dhash": 0.70}

        yield

        # Restore config
        CONFIG.processing.COMPARISON_GATES = self.original_gates
        CONFIG.processing.GATE_THRESHOLDS = self.original_thresholds

    def create_test_photo(
        self,
        photo_id: int,
        width: int,
        height: int,
        dhash_0: bytes,
        dhash_180: bytes | None = None,
        dhash_90: bytes | None = None,
        dhash_270: bytes | None = None,
    ) -> PhotoFile:
        """Create a test photo with cached hash values.

        Args:
            photo_id: Unique photo ID
            width: Image width
            height: Image height
            dhash_0: Hash at rotation 0°
            dhash_180: Hash at rotation 180° (for landscape photos)
            dhash_90: Hash at rotation 90° (for portrait photos)
            dhash_270: Hash at rotation 270° (for portrait photos)

        Returns:
            PhotoFile with cached dimensions and hash preparations
        """
        photo = PhotoFile(
            path=None,  # Test fixture - no file needed
            mime="image/jpeg",
            size_bytes=1000000,
            pixels=width * height,
            sha256=f"sha{photo_id:03d}{'0' * 61}",
            orientation=0,
            file_id=photo_id,
        )

        # Cache dimensions (required for path=None)
        photo.cache["aspect_ratio"] = width / height
        photo.cache["width"] = width
        photo.cache["height"] = height

        # Cache hash preparations with tuple keys (method_name, rotation)
        photo.cache[("dhash", 0)] = dhash_0

        # Determine normalization rotation
        is_landscape = width >= height

        if is_landscape:
            # Landscape: cache rotation 180
            if dhash_180 is not None:
                photo.cache[("dhash", 180)] = dhash_180
        else:
            # Portrait: cache rotations 90 and 270
            if dhash_90 is not None:
                photo.cache[("dhash", 90)] = dhash_90
            if dhash_270 is not None:
                photo.cache[("dhash", 270)] = dhash_270

        return photo

    def test_landscape_photos_use_0_and_180_rotations(self) -> None:
        """Landscape photos should try rotations 0° and 180°."""
        # Create two landscape photos (1600x1200)
        # Both have same hash at 0°, different at 180°
        same_hash = bytes([0xFF] * 8)
        diff_hash = bytes([0x00] * 8)

        photo1 = self.create_test_photo(1, 1600, 1200, same_hash, diff_hash)
        photo2 = self.create_test_photo(2, 1600, 1200, same_hash, same_hash)

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        # Should match at rotation 0° (both have same_hash)
        passes, scores, final_score = gates.compare_with_rotation(photo1, photo2)

        assert passes, "Should match at rotation 0°"
        assert scores["dhash"] >= 0.70, "Score should exceed threshold"

    def test_portrait_photos_use_90_and_270_rotations(self) -> None:
        """Portrait photos should try rotations 90° and 270°."""
        # Create two portrait photos (1200x1600)
        # Normalization rotation = 90° for portrait
        hash_90 = bytes([0xFF] * 8)
        hash_270 = bytes([0x00] * 8)

        photo1 = self.create_test_photo(3, 1200, 1600, bytes([0xAA] * 8), dhash_90=hash_90, dhash_270=hash_270)
        photo2 = self.create_test_photo(4, 1200, 1600, bytes([0xBB] * 8), dhash_90=hash_90, dhash_270=hash_90)

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        # Should match at rotation 90° (first attempt)
        passes, scores, final_score = gates.compare_with_rotation(photo1, photo2)

        assert passes, "Should match at rotation 90°"

    def test_180_rotation_fallback_when_first_fails(self) -> None:
        """Should try 180° rotation if first attempt fails."""
        # Create landscape photos that only match after 180° rotation
        # Comparison logic:
        # - First attempt: ref.0° vs cand.0° → FAIL (0xFF vs 0xAA)
        # - Second attempt: ref.180° vs cand.0° → PASS (0xAA vs 0xAA)
        hash_ref_0 = bytes([0xFF] * 8)  # Different from candidate
        hash_ref_180 = bytes([0xAA] * 8)  # Matches candidate at 0°
        hash_cand_0 = bytes([0xAA] * 8)  # Will match ref at 180°

        photo_ref = self.create_test_photo(5, 1600, 1200, hash_ref_0, hash_ref_180)
        photo_cand = self.create_test_photo(6, 1600, 1200, hash_cand_0, bytes([0xBB] * 8))

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        # Should fail at 0° but pass at 180°
        passes, scores, final_score = gates.compare_with_rotation(photo_ref, photo_cand)

        assert passes, "Should match at rotation 180° after first attempt fails"

    def test_cache_hit_avoids_pixel_loading(self) -> None:
        """Cached preparations should be used without loading pixels."""
        # Create photos with path=None (cannot load pixels)
        same_hash = bytes([0xFF] * 8)
        photo1 = self.create_test_photo(7, 1600, 1200, same_hash, same_hash)
        photo2 = self.create_test_photo(8, 1600, 1200, same_hash, same_hash)

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        # Should complete without error (would fail if pixels needed)
        passes, scores, final_score = gates.compare_with_rotation(photo1, photo2)

        assert passes, "Should complete using cached preparations"
        # If this passes, it proves pixels were not loaded (would throw AssertionError)

    def test_best_result_selection_prefers_higher_score(self) -> None:
        """Should select rotation attempt with higher score."""
        # Create photos where 180° rotation has better score
        # Score at 0°: 0.60 (below threshold 0.70)
        # Score at 180°: 0.80 (above threshold)
        hash_ref_0 = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00])
        hash_ref_180 = bytes([0xFF] * 8)
        hash_cand = bytes([0xFF] * 8)

        photo_ref = self.create_test_photo(9, 1600, 1200, hash_ref_0, hash_ref_180)
        photo_cand = self.create_test_photo(10, 1600, 1200, hash_cand, hash_cand)

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        passes, scores, final_score = gates.compare_with_rotation(photo_ref, photo_cand)

        # Should pass because 180° rotation has better score
        assert passes, "Should pass using 180° rotation result"
        assert final_score > 0.70, "Final score should be from 180° rotation"

    def test_mixed_orientations_landscape_vs_portrait(self) -> None:
        """Comparing landscape and portrait photos uses normalized rotations."""
        # Landscape (1600x1200): norm_rotation = 0
        # Portrait (1200x1600): norm_rotation = 90
        # After normalization, both are landscape, so we compare:
        # - landscape at 0° vs portrait at 90°
        # - landscape at 180° vs portrait at 90°

        hash_match = bytes([0xFF] * 8)
        photo_landscape = self.create_test_photo(11, 1600, 1200, hash_match, hash_match)
        photo_portrait = self.create_test_photo(
            12, 1200, 1600, bytes([0x00] * 8), dhash_90=hash_match, dhash_270=hash_match
        )

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        # Should match (landscape.0° vs portrait.90°)
        passes, scores, final_score = gates.compare_with_rotation(photo_landscape, photo_portrait)

        assert passes, "Should match landscape vs portrait after normalization"

    def test_square_images_treated_as_landscape(self) -> None:
        """Square images (w==h) should be treated as landscape (norm_rotation=0)."""
        hash_same = bytes([0xFF] * 8)
        photo1 = self.create_test_photo(13, 1000, 1000, hash_same, hash_same)
        photo2 = self.create_test_photo(14, 1000, 1000, hash_same, hash_same)

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        passes, scores, final_score = gates.compare_with_rotation(photo1, photo2)

        assert passes, "Square images should match as landscape"

    def test_short_circuit_stops_at_first_gate_failure(self) -> None:
        """With short_circuit=True, should stop at first gate failure."""
        # Use multi-gate sequence
        CONFIG.processing.COMPARISON_GATES = ["dhash", "phash", "ahash"]
        CONFIG.processing.GATE_THRESHOLDS = {
            "dhash": 0.70,
            "phash": 0.70,
            "ahash": 0.70,
        }

        # Create photos that fail dhash but would pass other gates
        hash_fail = bytes([0xFF] * 8)
        hash_pass = bytes([0x00] * 8)

        photo1 = self.create_test_photo(15, 1600, 1200, hash_fail, hash_fail)
        photo2 = self.create_test_photo(16, 1600, 1200, hash_pass, hash_pass)

        # Pre-cache phash and ahash to avoid loading pixels
        photo1.cache[("phash", 0)] = hash_pass
        photo1.cache[("phash", 180)] = hash_pass
        photo1.cache[("ahash", 0)] = hash_pass
        photo1.cache[("ahash", 180)] = hash_pass
        photo2.cache[("phash", 0)] = hash_pass
        photo2.cache[("phash", 180)] = hash_pass
        photo2.cache[("ahash", 0)] = hash_pass
        photo2.cache[("ahash", 180)] = hash_pass

        gates = GateSequence(CONFIG.processing.COMPARISON_GATES)

        passes, scores, final_score = gates.compare_with_rotation(photo1, photo2, short_circuit=True)

        # Should fail (dhash fails)
        assert not passes, "Should fail at first gate"
        # With short_circuit, should only have dhash score
        assert "dhash" in scores, "Should have dhash score"


class TestCacheKeyFormat:
    """Test that cache keys follow the correct format."""

    def test_cache_keys_are_always_tuples(self) -> None:
        """All hash cache keys should be (method_name, rotation) tuples."""
        photo = PhotoFile(
            path=None,
            mime="image/jpeg",
            size_bytes=1000000,
            pixels=1920000,
            sha256="sha001" + "0" * 58,
            orientation=0,
            file_id=100,
        )

        # Dimensions required for path=None
        photo.cache["aspect_ratio"] = 1600 / 1200
        photo.cache["width"] = 1600
        photo.cache["height"] = 1200

        # Set cache with tuple keys
        photo.cache[("dhash", 0)] = bytes([0xFF] * 8)
        photo.cache[("dhash", 180)] = bytes([0xAA] * 8)

        # Verify tuple keys work with 'in' operator
        assert ("dhash", 0) in photo.cache, "Tuple key should be found"
        assert ("dhash", 180) in photo.cache, "Tuple key should be found"

        # Verify string keys don't exist
        assert "dhash" not in photo.cache, "String keys should not exist"

    def test_cache_get_returns_correct_value_for_tuple_key(self) -> None:
        """cache.get() should work correctly with tuple keys."""
        photo = PhotoFile(
            path=None,
            mime="image/jpeg",
            size_bytes=1000000,
            pixels=1920000,
            sha256="sha002" + "0" * 58,
            orientation=0,
            file_id=101,
        )

        hash_0 = bytes([0xFF] * 8)
        hash_180 = bytes([0xAA] * 8)

        photo.cache[("dhash", 0)] = hash_0
        photo.cache[("dhash", 180)] = hash_180

        # Test .get() retrieval
        assert photo.cache.get(("dhash", 0)) == hash_0, "Should retrieve hash_0"
        assert photo.cache.get(("dhash", 180)) == hash_180, "Should retrieve hash_180"
        assert photo.cache.get(("dhash", 90)) is None, "Missing key should return None"
        assert photo.cache.get("dhash") is None, "String key should return None"
