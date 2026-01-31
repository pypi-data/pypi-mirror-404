"""Self-contained configuration for photo_compare library.

This module provides default configuration values that can be overridden
by the parent project via configure() function. All config classes are
frozen dataclasses for immutability and safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast


@dataclass(frozen=True)
class ThresholdConfig:
    """Similarity thresholds for comparison methods.

    All thresholds are in the range [0, 1+] where higher values mean
    images must be more similar to be considered duplicates. Most thresholds
    are based on empirical benchmark results.

    Hash methods (0-1 range):
            AHASH: Average hash threshold
            DHASH: Difference hash threshold (best hash method)
            PHASH: Perceptual hash threshold
            WHASH: Wavelet hash threshold

    Feature methods (0-2 range, match ratio):
            SIFT: SIFT feature matching threshold
            AKAZE: AKAZE feature matching threshold
            ORB: ORB feature matching threshold
            BRISK: BRISK feature matching threshold (very high)

    Structural methods (0-1 range):
            SSIM: SSIM threshold (best overall)
            MS_SSIM: Multi-scale SSIM threshold
            HOG: HOG features threshold

    Histogram methods (0-1 range):
            COLOR_HISTOGRAM: RGB histogram correlation threshold
            HSV_HISTOGRAM: HSV histogram correlation threshold

    Pixel methods (0-1 range):
            MSE: Mean squared error threshold
            PSNR: Peak signal-to-noise ratio threshold
    """

    # Hash methods
    AHASH: float = 0.95313
    DHASH: float = 0.75000
    PHASH: float = 0.71875
    WHASH: float = 0.96875

    # Feature methods
    SIFT: float = 0.61538
    AKAZE: float = 0.66667
    ORB: float = 0.55556
    BRISK: float = 1.52381

    # Structural methods
    SSIM: float = 0.9  # 0.56363 - this number is too small
    MS_SSIM: float = 0.65609
    HOG: float = 0.83389

    # Histogram methods
    COLOR_HISTOGRAM: float = 0.0
    HSV_HISTOGRAM: float = 0.0

    # Pixel methods
    MSE: float = 0.0
    PSNR: float = 0.0


@dataclass(frozen=True)
class ImageProcessingConfig:
    """Image processing parameters.

    These parameters control how images are prepared for comparison.
    Larger values generally mean more detail but slower processing.

    Attributes:
            BASIC_HASH_SIZE: Hash size for hash methods (8 = 64 bits)
            SIFT_MAX_FEATURES: Maximum SIFT keypoints to detect
            ORB_MAX_FEATURES: Maximum ORB keypoints to detect
            SSIM_SIDE_SIZE: Image resize dimension for SSIM
            HOG_ORIENTATIONS: Number of HOG gradient orientations
            HOG_PIXELS_PER_CELL: HOG cell size in pixels
            COLOR_HIST_BINS: Number of bins per RGB channel
            HSV_HIST_BINS: Number of bins for H, S, V channels
    """

    BASIC_HASH_SIZE: int = 8
    SIFT_MAX_FEATURES: int = 500
    ORB_MAX_FEATURES: int = 500
    SSIM_SIDE_SIZE: int = 256
    HOG_ORIENTATIONS: int = 9
    HOG_PIXELS_PER_CELL: tuple[int, int] = (8, 8)
    COLOR_HIST_BINS: int = 32
    HSV_HIST_BINS: tuple[int, int, int] = (16, 16, 16)


@dataclass(frozen=True)
class FeatureConfig:
    """Feature matching parameters.

    Attributes:
            LOWE_RATIO: Lowe's ratio test threshold (0.7 is standard)
    """

    LOWE_RATIO: float = 0.7


@dataclass
class PhotoCompareConfig:
    """Central configuration for photo_compare library.

    This is a mutable container for the three frozen config sections.
    Use configure() to create updated versions.
    """

    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    image_processing: ImageProcessingConfig = field(default_factory=ImageProcessingConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)


# Global configuration instance
_config = PhotoCompareConfig()


def get_config() -> PhotoCompareConfig:
    """Get the current configuration.

    Returns:
            Current PhotoCompareConfig instance
    """
    return _config


def configure(
    thresholds: dict[str, float] | None = None,
    image_processing: dict[str, int | tuple[int, int] | tuple[int, int, int]] | None = None,
    features: dict[str, float] | None = None,
) -> None:
    """Configure the photo_compare library by creating new frozen config sections.

    Since config sections are frozen dataclasses, this function creates new
    instances with updated values and replaces the global config.

    Args:
            thresholds: Dictionary of threshold values to override
            image_processing: Dictionary of image processing parameters to override
            features: Dictionary of feature matching parameters to override

    Raises:
            AttributeError: If attempting to set unknown config parameter

    Example:
            >>> configure(
            ...     thresholds={'AHASH': 0.95, 'DHASH': 0.75},
            ...     image_processing={'BASIC_HASH_SIZE': 16}
            ... )
    """
    global _config  # noqa: PLW0603
    # Standard library config pattern (like logging.basicConfig)

    # Build new threshold config if needed
    new_thresholds: ThresholdConfig
    if thresholds:
        # Get current values as dict
        threshold_dict: dict[str, float] = _config.thresholds.__dict__.copy()
        # Update with new values
        key: str
        value: float
        for key, value in thresholds.items():
            if key not in threshold_dict:
                raise AttributeError(f"Unknown threshold parameter: {key}")
            threshold_dict[key] = value
        # Create new frozen instance
        new_thresholds = ThresholdConfig(**threshold_dict)
    else:
        new_thresholds = _config.thresholds

    # Build new image processing config if needed
    new_image_processing: ImageProcessingConfig
    if image_processing:
        ip_dict: dict[str, int | tuple[int, int] | tuple[int, int, int]] = _config.image_processing.__dict__.copy()
        ip_key: str
        ip_value: int | tuple[int, int] | tuple[int, int, int]
        for ip_key, ip_value in image_processing.items():
            if ip_key not in ip_dict:
                raise AttributeError(f"Unknown image_processing parameter: {ip_key}")
            ip_dict[ip_key] = ip_value
        # Use cast to handle union type unpacking - we know the dict is structurally correct
        new_image_processing = ImageProcessingConfig(**cast(Any, ip_dict))
    else:
        new_image_processing = _config.image_processing

    # Build new features config if needed
    new_features: FeatureConfig
    if features:
        feat_dict: dict[str, float] = _config.features.__dict__.copy()
        feat_key: str
        feat_value: float
        for feat_key, feat_value in features.items():
            if feat_key not in feat_dict:
                raise AttributeError(f"Unknown features parameter: {feat_key}")
            feat_dict[feat_key] = feat_value
        new_features = FeatureConfig(**feat_dict)
    else:
        new_features = _config.features

    # Replace global config
    _config = PhotoCompareConfig(
        thresholds=new_thresholds, image_processing=new_image_processing, features=new_features
    )


def reset_config() -> None:
    """Reset configuration to defaults.

    Creates a new PhotoCompareConfig with default values.
    """
    global _config  # noqa: PLW0603
    # Standard library config pattern (like logging.basicConfig)
    _config = PhotoCompareConfig()
