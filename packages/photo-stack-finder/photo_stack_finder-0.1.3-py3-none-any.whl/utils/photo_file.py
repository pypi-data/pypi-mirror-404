"""PhotoFile: Lightweight photo file record with lazy computation and caching.

This module provides a minimal PhotoFile class that stores only essential data
from the directory walk and uses a cache dictionary for all computed values.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import pillow_heif
from PIL import ExifTags, Image, ImageOps

from .config import CONFIG

pillow_heif.register_heif_opener()

# EXIF tag mappings
_EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}
_GPS_INFO_TAG = _EXIF_TAGS.get("GPSInfo")

# Type alias for preference tuple
PreferenceTuple = tuple[int, int, str, int]


class ImageData:
    """Lazy image data accessor for PhotoFile.

    Provides lazy access to dimensions, aspect ratio, and pixels.
    Caches pixels during context manager scope only.
    Stores dimensions and aspect ratio in PhotoFile permanently.

    Supports rotation-aware pixel access for comparison purposes:
    - Rotated pixels cached in _pixels_cache during context scope
    - Normalization detection (portrait→landscape) cached
    """

    def __init__(self, photo: PhotoFile):
        """Initialize with reference to PhotoFile.

        Args:
            photo: PhotoFile to provide data for
        """
        self._photo = photo
        self._pixels: npt.NDArray[np.uint8] | None = None
        self._pixels_cache: dict[int, npt.NDArray[np.uint8]] = {}  # rotation → pixels
        self._original_rotation: int | None = None  # track normalization rotation

    def get_aspect_ratio(self) -> float:
        """Get aspect ratio (may trigger pixel loading to get dimensions).

        If dimensions not yet cached:
        1. Load raw pixels
        2. Extract dimensions
        3. Store dimensions and aspect ratio in PhotoFile
        4. Return aspect ratio

        If dimensions already cached:
        1. Return cached aspect ratio from PhotoFile

        Returns:
            Aspect ratio (width/height)
        """
        if "aspect_ratio" not in self._photo.cache:
            # Need to load pixels to get dimensions
            raw_pixels = self._photo._load_raw_pixels()
            h, w = raw_pixels.shape[:2]
            aspect_ratio = w / h if h > 0 else 0.0

            # Store in PhotoFile permanently
            self._photo.cache["aspect_ratio"] = aspect_ratio
            self._photo.cache["width"] = w
            self._photo.cache["height"] = h

            return aspect_ratio
        # Already calculated, return cached value
        return cast(float, self._photo.cache["aspect_ratio"])

    def get_pixels(self) -> npt.NDArray[np.uint8]:
        """Get pixels (EXIF orientation applied).

        If pixels already loaded:
        1. Return cached pixels from self._pixels

        If pixels not loaded:
        1. Load raw pixels
        2. Cache dimensions if not already done
        3. Cache in self._pixels
        4. Return pixels

        Returns:
            RGB pixel array (H, W, 3) uint8 with EXIF orientation applied
        """
        # Check if already loaded
        if self._pixels is not None:
            return self._pixels

        # Load raw pixels
        raw_pixels = self._photo._load_raw_pixels()

        # Cache dimensions if not already done
        if "aspect_ratio" not in self._photo.cache:
            h, w = raw_pixels.shape[:2]
            aspect_ratio = w / h if h > 0 else 0.0
            self._photo.cache["aspect_ratio"] = aspect_ratio
            self._photo.cache["width"] = w
            self._photo.cache["height"] = h

        # Cache in context manager scope
        self._pixels = raw_pixels
        return raw_pixels

    def get_width(self) -> int:
        """Get width (triggers dimension extraction if needed).

        Returns:
            Width in pixels
        """
        # Ensure dimensions are cached
        if "width" not in self._photo.cache:
            _ = self.get_aspect_ratio()  # Triggers dimension extraction
        return cast(int, self._photo.cache["width"])

    def get_height(self) -> int:
        """Get height (triggers dimension extraction if needed).

        Returns:
            Height in pixels
        """
        # Ensure dimensions are cached
        if "height" not in self._photo.cache:
            _ = self.get_aspect_ratio()  # Triggers dimension extraction
        return cast(int, self._photo.cache["height"])

    def get_normalization_rotation(self) -> int:
        """Get rotation needed to normalize photo to landscape.

        Returns:
            0 if already landscape (w >= h), 90 if portrait (w < h)
        """
        if self._original_rotation is not None:
            return self._original_rotation

        # Get dimensions (may trigger dimension extraction)
        width = self.get_width()
        height = self.get_height()

        # Portrait photos need 90° CCW rotation to become landscape
        self._original_rotation = 90 if width < height else 0
        return self._original_rotation

    def get_pixels_with_rotation(self, rotation: int) -> npt.NDArray[np.uint8]:
        """Get pixels with specified cumulative rotation applied.

        Args:
            rotation: Cumulative rotation from original (0, 90, 180, 270)

        Returns:
            Rotated pixel array (H, W, 3) uint8

        Notes:
            - Rotation 0: Original pixels (EXIF-oriented)
            - Rotation 90: Rotated 90° CCW (portrait normalized to landscape)
            - Rotation 180: Rotated 180°
            - Rotation 270: Rotated 270° (= 90° + 180°)
        """
        # Check cache first
        if rotation in self._pixels_cache:
            return self._pixels_cache[rotation]

        # Load original pixels if needed
        if 0 not in self._pixels_cache:
            original_pixels = self.get_pixels()  # Load and cache original
            self._pixels_cache[0] = original_pixels
        else:
            original_pixels = self._pixels_cache[0]

        # Apply rotation using numpy
        if rotation == 0:
            rotated_pixels = original_pixels
        elif rotation == 90:
            rotated_pixels = np.rot90(original_pixels, k=1)  # 90° CCW
        elif rotation == 180:
            rotated_pixels = np.rot90(original_pixels, k=2)  # 180°
        elif rotation == 270:
            rotated_pixels = np.rot90(original_pixels, k=3)  # 270° CCW (= 90° CW)
        else:
            raise ValueError(f"Invalid rotation angle: {rotation}. Must be 0, 90, 180, or 270.")

        # Cache and return
        self._pixels_cache[rotation] = rotated_pixels
        return rotated_pixels

    def get_normalized_pixels(self) -> tuple[npt.NDArray[np.uint8], int]:
        """Get pixels normalized to landscape orientation.

        Returns:
            Tuple of (normalized_pixels, cumulative_rotation)
            - cumulative_rotation: 0 for landscape, 90 for portrait (rotated to landscape)
        """
        norm_rotation = self.get_normalization_rotation()
        norm_pixels = self.get_pixels_with_rotation(norm_rotation)
        return norm_pixels, norm_rotation


def load_normalized_pixels(path: Path | str) -> npt.NDArray[np.uint8]:
    """Load image with EXIF orientation applied and convert to RGB.

    Utility function for loading images with standardized normalization:
    - Applies EXIF orientation tag to rotate image correctly
    - Converts to RGB color space (canonical representation)
    - Returns as numpy array

    This centralizes the common pattern used across multiple modules for
    loading images before comparison or hashing.

    Args:
        path: Path to image file

    Returns:
        RGB pixel array (H, W, 3) as uint8 numpy array with EXIF orientation applied

    Example:
        >>> pixels = load_normalized_pixels("photo.jpg")
        >>> pixels.shape  # (height, width, 3)
        (1200, 1600, 3)
    """
    with Image.open(path) as opened_img:
        # Apply EXIF orientation to get canonical orientation
        img = ImageOps.exif_transpose(opened_img)

        # Convert to RGB (canonical color space)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Convert to numpy array
        return np.array(img, dtype=np.uint8)


class PhotoFile:
    """Photo file record with minimal eager properties and lazy computation.

    Only essential file metadata is computed during tree walk: path, mime, size_bytes.
    All image-derived data (pixels, dimensions, EXIF) is lazy-loaded via cache.

    Attributes:
            id: Unique identifier (assigned externally)
            path: Path to the photo file
            mime: MIME type of the file
            size_bytes: File size in bytes
            cache: Dictionary for lazy-loaded computed values

    Cache keys (examples):
            'pixels': int - Total pixel count (width * height, rotation-invariant)
            'file_tmpl': str - Filename template with digit placeholders
            'file_digits': list[str] - Extracted digit groups from filename
            'EXIF': dict - EXIF metadata (full)
            'image_props': dict - Additional PIL Image properties (format, mode)
            'google_meta': dict - Google Photos sidecar metadata
            'xmp_meta': dict - XMP sidecar metadata
            'supplemental_meta': dict - Supplemental metadata
            'width': int - Image width in pixels
            'height': int - Image height in pixels
            'aspect_ratio': float - Aspect ratio (width/height)
            '<method_name>': Any - Comparison method prepared data (e.g., 'dhash')
    """

    def __init__(
        self,
        path: Path | None,
        mime: str,
        size_bytes: int,
        file_id: int,
    ):
        """Create a PhotoFile record with core properties.

        Core properties computed during tree walk: path, mime, size_bytes.
        All other properties (pixels, dimensions, EXIF) are computed lazily.

        Args:
                path: Path to the photo file (None for anonymized test fixtures)
                mime: MIME type
                size_bytes: File size in bytes
                file_id: Unique identifier
        """
        self.id: int = file_id
        self.path: Path | None = path
        self.mime: str = mime
        self.size_bytes: int = size_bytes

        # Cache for lazy-loaded values (pixels, dimensions, EXIF, method preparations)
        self.cache: dict[str | tuple[str, int], Any] = {}

    @property
    def pixels(self) -> int:
        """Get pixel count (lazy-loaded and cached).

        Computes width * height on first access by opening the image.
        Cached for subsequent accesses.

        Returns:
                Total pixel count (width * height, rotation-invariant)
        """
        if "pixels" not in self.cache:
            self.cache["pixels"] = self._compute_pixels()
        result: int = self.cache["pixels"]
        return result

    def _compute_pixels(self) -> int:
        """Compute pixel count by opening the image.

        Returns:
                Total pixels (width * height)
        """
        assert self.path is not None, f"Photo {self.id} has None path - cannot compute pixels"
        with Image.open(self.path) as img:
            width: int = img.width
            height: int = img.height
            return width * height

    @contextmanager
    def image_data(self) -> Iterator[ImageData]:
        """Context manager for lazy image data access.

        Provides ImageData object that lazily loads pixels and extracts dimensions
        only when get_aspect_ratio() or get_pixels() are called.

        For test fixtures with path=None, dimension values must be
        pre-populated in cache (aspect_ratio, width, height).

        Returns:
            ImageData accessor for lazy loading of pixels and aspect ratio

        Raises:
            AssertionError: If path is None and dimension values not in cache

        Example:
            >>> with photo.image_data() as img:
            ...     # No pixels loaded yet
            ...     if img.get_aspect_ratio() < 0.5:
            ...         return  # Early exit, pixels never loaded
            ...     # Only load pixels if needed
            ...     pixels = img.get_pixels()
        """
        # For test fixtures: Allow path=None if dimension values are pre-populated
        if self.path is None:
            required_keys = {"aspect_ratio", "width", "height"}
            cache_str_keys = {k for k in self.cache if isinstance(k, str)}
            missing_keys = required_keys - cache_str_keys
            assert not missing_keys, (
                f"Cannot get image data for photo {self.id}: path is None. "
                f"Test fixtures must pre-populate: {missing_keys}"
            )

        # Create lazy accessor
        data = ImageData(self)

        try:
            yield data
        finally:
            # ImageData._pixels will be garbage collected
            # PhotoFile.cache dimensions persist
            pass

    def _load_raw_pixels(self) -> npt.NDArray[np.uint8]:
        """Load pixels with EXIF orientation applied (no rotation detection).

        Internal method used by ImageData for lazy loading.

        Returns:
            RGB pixel array (H, W, 3) uint8, EXIF orientation applied

        Raises:
            AssertionError: If self.path is None (test fixtures without files)
        """
        assert self.path is not None, f"Cannot load pixels for photo {self.id}: path is None."
        return load_normalized_pixels(self.path)

    def prefer(self) -> PreferenceTuple:
        """Get preference tuple for picking exemplars.

        The tuple is designed for use with min() to pick the "best" photo:
        - Prefer higher pixel count (negated)
        - Prefer larger file size (negated)
        - Use path as tiebreaker
        - Use ID as final tiebreaker

        Returns:
                Tuple of (-pixels, -size_bytes, path_str, id)

        """
        return -self.pixels, -self.size_bytes, str(self.path), self.id

    # === Lazy-loading properties for metadata ===

    @property
    def exif_data(self) -> dict[str, Any]:  # pragma: no cover - Reserved for future metadata features
        """Get EXIF data (lazy-loaded and cached).

        Returns:
                Dictionary of EXIF tags and values
        """
        if "EXIF" not in self.cache:
            self.cache["EXIF"] = self._load_exif()
        result: dict[str, Any] = self.cache["EXIF"]
        return result

    @property
    def image_properties(self) -> dict[str, Any]:  # pragma: no cover - Reserved for future metadata features
        """Get PIL Image properties (format/mode/size lazy-loaded).

        Note: Width, height, and aspect_ratio are no longer included here.
        Use image_data() context manager to access canonical dimensions.

        Returns:
                Dictionary of PIL Image properties (format, mode, size)
        """
        if "image_props" not in self.cache:
            self.cache["image_props"] = self._load_image_format()

        return cast(dict[str, Any], self.cache["image_props"])

    @property
    def google_metadata(self) -> dict[str, Any]:  # pragma: no cover - Reserved for future metadata features
        """Get Google Photos sidecar metadata (lazy-loaded and cached).

        Returns:
                Dictionary of Google Photos metadata
        """
        assert self.path is not None, f"Photo {self.id} has None path - cannot load sidecar metadata"
        if "google_meta" not in self.cache:
            sidecar_path: Path = self.path.with_name(self.path.name + CONFIG.paths.GOOGLE_SIDECAR_SUFFIX)
            self.cache["google_meta"] = load_json_sidecar(sidecar_path)
        result: dict[str, Any] = self.cache["google_meta"]
        return result

    @property
    def xmp_metadata(self) -> dict[str, Any]:  # pragma: no cover - Reserved for future metadata features
        """Get XMP sidecar metadata (lazy-loaded and cached).

        Returns:
                Dictionary of XMP metadata
        """
        assert self.path is not None, f"Photo {self.id} has None path - cannot load sidecar metadata"
        if "xmp_meta" not in self.cache:
            sidecar_path: Path = self.path.with_suffix(CONFIG.paths.XMP_SIDECAR_SUFFIX)
            self.cache["xmp_meta"] = load_json_sidecar(sidecar_path)
        result: dict[str, Any] = self.cache["xmp_meta"]
        return result

    @property
    def supplemental_metadata(self) -> dict[str, Any]:  # pragma: no cover - Reserved for future metadata features
        """Get supplemental metadata (lazy-loaded and cached).

        Returns:
                Dictionary of supplemental metadata
        """
        assert self.path is not None, f"Photo {self.id} has None path - cannot load sidecar metadata"
        if "supplemental_meta" not in self.cache:
            sidecar_path: Path = self.path.with_name(self.path.name + CONFIG.paths.SUPPLEMENTAL_SIDECAR_SUFFIX)
            self.cache["supplemental_meta"] = load_json_sidecar(sidecar_path)
        result: dict[str, Any] = self.cache["supplemental_meta"]
        return result

    # === Internal metadata loaders ===

    def _load_exif(self) -> dict[str, Any]:  # pragma: no cover - Reserved for future metadata features
        """Load EXIF data from the image.

        Returns:
                Dictionary with EXIF tags as keys and values
        """
        assert self.path is not None, f"Photo {self.id} has None path - cannot load EXIF"
        with Image.open(self.path) as img:
            exif_data: Any = img.getexif()

        # Convert numeric tags to human-readable names
        result: dict[str, Any] = {}
        for tag_id, value in exif_data.items():
            tag_name_raw = ExifTags.TAGS.get(tag_id, tag_id)
            tag_name: str = tag_name_raw if isinstance(tag_name_raw, str) else str(tag_name_raw)

            # Special handling for GPS data
            if tag_id == _GPS_INFO_TAG and isinstance(value, dict):
                gps_data: dict[str, Any] = {
                    (gps_tag if isinstance(gps_tag := ExifTags.GPSTAGS.get(k, k), str) else str(gps_tag)): v
                    for k, v in value.items()
                }
                result[tag_name] = gps_data
            else:
                result[tag_name] = value

        return result

    def _load_image_format(self) -> dict[str, Any]:  # pragma: no cover - Reserved for future metadata features
        """Load PIL Image format and mode (lightweight properties).

        Note: Width, height, aspect_ratio are no longer eager properties.
        Use image_data() context manager for canonical dimensions.

        Returns:
                Dictionary of image format properties (format, mode, size tuple)
        """
        assert self.path is not None, f"Photo {self.id} has None path - cannot load image format"
        with Image.open(self.path) as img:
            # Get format/mode/size from PIL Image
            # Note: This is raw size, not EXIF-rotated or canonically rotated
            return {
                "format": img.format,
                "mode": img.mode,
                "size": (img.width, img.height),  # Raw image dimensions
            }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"PhotoFile(id={self.id}, path={'None' if self.path is None else self.path.name}, pixels={self.pixels}, cache_keys={list(self.cache.keys())})"


# === Utility Functions ===


def pick_exemplar_from_class(photos: dict[int, PhotoFile], cl: set[int]) -> int:
    """Pick the best photo ID from a set using the prefer() function.

    Args:
            photos: Dictionary mapping photo IDs to PhotoFile objects
            cl: Set of photo IDs to choose from

    Returns:
            Photo ID with the best (minimum) prefer() value

    Example:
            >>> exemplar = pick_exemplar_from_class(photos, {1, 2, 3})
    """
    return min(cl, key=lambda pid: photos[pid].prefer())


def load_json_sidecar(path: Path) -> dict[str, Any]:
    """Load JSON sidecar file if it exists.

    Args:
            path: Path to the sidecar JSON file

    Returns:
            Dictionary of metadata, or empty dict if file not found

    Raises:
            PermissionError: If file exists but cannot be read
            json.JSONDecodeError: If file contains invalid JSON
            ValueError: If file contains non-dict JSON
    """
    if not path.exists():
        return {}

    text: str = path.read_text(encoding="utf-8")
    data: Any = json.loads(text)
    if not isinstance(data, dict):
        msg = f"Sidecar file {path} contains non-dict JSON"
        raise ValueError(msg)
    return data
