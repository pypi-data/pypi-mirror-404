"""Comprehensive tests for PhotoFile.get_pixel_array() method.

These tests establish the contract for pixel array format that all
comparison methods will depend on after the pixel array refactoring.

CRITICAL: These tests must pass before and after the refactoring to ensure
that the pixel array implementation provides a stable foundation.
"""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageOps
from src.utils.photo_file import PhotoFile


class TestPixelArrayContract:
    """Test PhotoFile.get_pixel_array() contract and correctness."""

    @pytest.fixture
    def sample_jpeg(self, tmp_path: Path) -> Path:
        """Create a simple test JPEG image (100x50 red)."""
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 50), color="red")
        img.save(img_path, format="JPEG")
        return img_path

    @pytest.fixture
    def sample_png(self, tmp_path: Path) -> Path:
        """Create a simple test PNG image (80x60 blue)."""
        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (80, 60), color="blue")
        img.save(img_path, format="PNG")
        return img_path

    @pytest.fixture
    def grayscale_png(self, tmp_path: Path) -> Path:
        """Create a grayscale PNG image (should convert to RGB)."""
        img_path = tmp_path / "gray.png"
        img = Image.new("L", (50, 50), color=128)
        img.save(img_path, format="PNG")
        return img_path

    @pytest.fixture
    def rgba_png(self, tmp_path: Path) -> Path:
        """Create an RGBA PNG image (should convert to RGB)."""
        img_path = tmp_path / "rgba.png"
        img = Image.new("RGBA", (60, 40), color=(255, 0, 0, 128))
        img.save(img_path, format="PNG")
        return img_path

    @pytest.fixture
    def exif_oriented_jpeg(self, tmp_path: Path) -> tuple[Path, int, int]:
        """Create a JPEG with EXIF orientation tag 6 (90° CCW rotation).

        Returns:
            Tuple of (path, expected_width_after_orientation, expected_height_after_orientation)
        """
        img_path = tmp_path / "oriented.jpg"

        # Create 100x200 image (wide)
        img = Image.new("RGB", (100, 200), color="green")

        # Save with EXIF orientation 6 (rotate 90° CCW)
        # After applying orientation, should be 200x100 (tall)
        exif_data = img.getexif()
        exif_data[0x0112] = 6  # Orientation tag
        img.save(img_path, format="JPEG", exif=exif_data)

        # After EXIF transpose, dimensions should be swapped
        return img_path, 200, 100

    @pytest.fixture
    def photo_from_path(self) -> callable:
        """Factory to create PhotoFile from a path."""

        def _create(path: Path, file_id: int = 1) -> PhotoFile:
            with Image.open(path) as img:
                # Apply EXIF orientation for dimensions
                oriented = ImageOps.exif_transpose(img)
                width, height = oriented.size
                exif_data = img.getexif()
                orientation = exif_data.get(0x0112, 0) if exif_data else 0

            return PhotoFile(
                path=path,
                mime="image/jpeg",
                size_bytes=path.stat().st_size,
                pixels=width * height,
                width=width,
                height=height,
                aspect_ratio=width / height,
                sha256="a" * 64,
                orientation=orientation,
                file_id=file_id,
            )

        return _create

    def test_get_pixel_array_returns_rgb_uint8(self, sample_jpeg: Path, photo_from_path: callable) -> None:
        """Verify pixel array has correct shape (H, W, 3) and dtype uint8."""
        photo = photo_from_path(sample_jpeg)
        pixels = photo.get_pixel_array()

        # Check dtype
        assert pixels.dtype == np.uint8, f"Expected uint8, got {pixels.dtype}"

        # Check shape (height, width, 3 channels)
        assert pixels.ndim == 3, f"Expected 3D array, got {pixels.ndim}D"
        assert pixels.shape[2] == 3, f"Expected 3 channels (RGB), got {pixels.shape[2]}"

        # Check dimensions match PhotoFile properties
        assert pixels.shape[0] == photo.height, f"Height mismatch: array={pixels.shape[0]}, photo={photo.height}"
        assert pixels.shape[1] == photo.width, f"Width mismatch: array={pixels.shape[1]}, photo={photo.width}"

    def test_get_pixel_array_applies_exif_orientation(
        self, exif_oriented_jpeg: tuple[Path, int, int], photo_from_path: callable
    ) -> None:
        """Verify EXIF orientation is applied correctly."""
        img_path, expected_width, expected_height = exif_oriented_jpeg
        photo = photo_from_path(img_path)
        pixels = photo.get_pixel_array()

        # Check that dimensions are post-orientation (swapped from original)
        assert pixels.shape[0] == expected_height, (
            f"Height after orientation: expected {expected_height}, got {pixels.shape[0]}"
        )
        assert pixels.shape[1] == expected_width, (
            f"Width after orientation: expected {expected_width}, got {pixels.shape[1]}"
        )

        # Verify pixels match what ImageOps.exif_transpose would produce
        with Image.open(img_path) as img:
            oriented_pil = ImageOps.exif_transpose(img)
            if oriented_pil.mode != "RGB":
                oriented_pil = oriented_pil.convert("RGB")
            expected_pixels = np.array(oriented_pil, dtype=np.uint8)

        np.testing.assert_array_equal(
            pixels, expected_pixels, err_msg="Pixel array doesn't match ImageOps.exif_transpose result"
        )

    def test_get_pixel_array_handles_different_formats(
        self, sample_jpeg: Path, sample_png: Path, grayscale_png: Path, rgba_png: Path, photo_from_path: callable
    ) -> None:
        """Verify different image formats are correctly loaded as RGB uint8."""
        test_cases = [
            (sample_jpeg, "JPEG"),
            (sample_png, "PNG"),
            (grayscale_png, "Grayscale PNG"),
            (rgba_png, "RGBA PNG"),
        ]

        for img_path, fmt_name in test_cases:
            photo = photo_from_path(img_path)
            pixels = photo.get_pixel_array()

            # All formats should produce RGB uint8
            assert pixels.dtype == np.uint8, f"{fmt_name}: Expected uint8, got {pixels.dtype}"
            assert pixels.ndim == 3, f"{fmt_name}: Expected 3D array"
            assert pixels.shape[2] == 3, f"{fmt_name}: Expected 3 channels (RGB)"

            # Verify conversion worked (compare with PIL's result)
            with Image.open(img_path) as img:
                oriented = ImageOps.exif_transpose(img)
                if oriented.mode != "RGB":
                    oriented = oriented.convert("RGB")
                expected = np.array(oriented, dtype=np.uint8)

            np.testing.assert_array_equal(
                pixels, expected, err_msg=f"{fmt_name}: Pixel values don't match PIL conversion"
            )

    def test_get_pixel_array_raises_for_none_path(self) -> None:
        """Verify clear error when path=None (test fixtures)."""
        photo = PhotoFile(
            path=None,  # type: ignore  # Intentionally invalid for testing
            mime="image/jpeg",
            size_bytes=1000,
            pixels=100,
            width=10,
            height=10,
            aspect_ratio=1.0,
            sha256="a" * 64,
            orientation=0,
            file_id=999,
        )

        with pytest.raises(AssertionError) as exc_info:
            photo.get_pixel_array()

        error_msg = str(exc_info.value)
        assert "path is None" in error_msg, f"Error message should mention None path: {error_msg}"
        assert "999" in error_msg, f"Error message should include photo ID: {error_msg}"

    def test_get_pixel_array_deterministic(self, sample_jpeg: Path, photo_from_path: callable) -> None:
        """Verify same pixels returned on repeated calls (deterministic)."""
        photo = photo_from_path(sample_jpeg)

        # Call multiple times
        pixels1 = photo.get_pixel_array()
        pixels2 = photo.get_pixel_array()
        pixels3 = photo.get_pixel_array()

        # All should be identical
        np.testing.assert_array_equal(pixels1, pixels2, err_msg="Pixels differ between first and second call")
        np.testing.assert_array_equal(pixels2, pixels3, err_msg="Pixels differ between second and third call")

    def test_get_pixel_array_not_cached(self, sample_jpeg: Path, photo_from_path: callable) -> None:
        """Verify pixel array is NOT cached in PhotoFile.cache (too large)."""
        photo = photo_from_path(sample_jpeg)
        pixels = photo.get_pixel_array()

        # Cache should not contain pixel array
        # (Methods may cache their own prepared data, but not raw pixels)
        assert "pixel_array" not in photo.cache, "Pixel array should not be cached (would cause memory bloat)"
        assert "pixels" not in photo.cache or photo.cache["pixels"] == photo.pixels, (
            "Cache 'pixels' key should only be the pixel count, not the array"
        )

        # Verify pixels object is a new array on each call
        pixels_again = photo.get_pixel_array()
        assert pixels is not pixels_again, "get_pixel_array should return a new array each time (not cached)"
