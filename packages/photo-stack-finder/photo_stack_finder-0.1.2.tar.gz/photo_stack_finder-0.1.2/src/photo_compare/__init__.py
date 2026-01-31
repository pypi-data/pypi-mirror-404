"""photo_compare: Image similarity comparison with multiple detection methods.

A self-contained library for image similarity comparison with hash-based,
feature-based, structural, histogram, and pixel-based methods. Designed for
high-performance duplicate photo detection with integrated caching.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Base classes
from .base import BinningSimilarityMethod, ComparisonMethodName, SimilarityMethod

# Configuration
from .config import configure, get_config, reset_config

# Distance/similarity functions
from .distance import hamming_distance, hamming_similarity

# Feature detection methods
from .feature_methods import (
    AKAZEMethod,
    BRISKMethod,
    FeatureMethodBase,
    ORBMethod,
    SIFTMethod,
)
from .file_hash import binary_files_equal, file_sha256

# Hash-based methods
from .hash_methods import AHashMethod, DHashMethod, PHashMethod, WHashMethod

# Histogram methods
from .histogram_methods import ColorHistogramMethod, HSVHistogramMethod

# Pixel-based methods
from .pixel_methods import MSEMethod, PSNRMethod

# Structural methods
from .structural_methods import HOGMethod, MultiScaleSSIMMethod, SSIMMethod

# Version information
__version__ = "1.0.0"
__author__ = "Photo Deduplication Team"
__description__ = "Image similarity methods with integrated caching and factory pattern"


def create_comparison_method(
    method_name: ComparisonMethodName,
) -> BinningSimilarityMethod[Any, Any] | SimilarityMethod[Any]:
    """Create a comparison method instance with configuration.

    Args:
            method_name: The name of the comparison method to create

    Returns:
            Configured comparison method instance

    Example:
            >>> method = create_comparison_method('dhash')
            >>> prep1 = method.prepare(Path("photo1.jpg"))
            >>> prep2 = method.prepare(Path("photo2.jpg"))
            >>> similarity = method.compare(prep1, prep2)
    """
    # Use factory dictionary to eliminate complexity warning from match statement
    # Each method is instantiated with its required configuration parameters
    config = get_config()

    # Factory functions that create configured method instances
    factories: dict[
        ComparisonMethodName,
        Callable[[], BinningSimilarityMethod[Any, Any] | SimilarityMethod[Any]],
    ] = {
        "ahash": lambda: AHashMethod(config.image_processing.BASIC_HASH_SIZE),
        "dhash": lambda: DHashMethod(config.image_processing.BASIC_HASH_SIZE),
        "phash": lambda: PHashMethod(config.image_processing.BASIC_HASH_SIZE),
        "whash": lambda: WHashMethod(config.image_processing.BASIC_HASH_SIZE),
        "sift": lambda: SIFTMethod(config.image_processing.SIFT_MAX_FEATURES, config.features.LOWE_RATIO),
        "akaze": lambda: AKAZEMethod(config.features.LOWE_RATIO),
        "orb": lambda: ORBMethod(config.image_processing.ORB_MAX_FEATURES, config.features.LOWE_RATIO),
        "brisk": lambda: BRISKMethod(config.features.LOWE_RATIO),
        "ssim": lambda: SSIMMethod(config.image_processing.SSIM_SIDE_SIZE),
        "ms_ssim": lambda: MultiScaleSSIMMethod(config.image_processing.SSIM_SIDE_SIZE, (1.0, 0.5, 0.25)),
        "hog": lambda: HOGMethod(
            config.image_processing.HOG_ORIENTATIONS,
            config.image_processing.HOG_PIXELS_PER_CELL,
        ),
        "mse": lambda: MSEMethod(64),
        "psnr": lambda: PSNRMethod(64, 255.0),
        "colour_histogram": lambda: ColorHistogramMethod(config.image_processing.COLOR_HIST_BINS, "correlation"),
        "hsv_histogram": lambda: HSVHistogramMethod(config.image_processing.HSV_HIST_BINS, "correlation"),
    }

    factory = factories.get(method_name)
    if factory is None:
        raise ValueError(f"Unknown comparison method: {method_name}")
    return factory()


__all__ = [
    # Hash methods
    "AHashMethod",
    "AKAZEMethod",
    "BRISKMethod",
    "BinningSimilarityMethod",
    # Histogram methods
    "ColorHistogramMethod",
    "ComparisonMethodName",
    "DHashMethod",
    # Feature methods
    "FeatureMethodBase",
    "HOGMethod",
    "HSVHistogramMethod",
    # Pixel methods
    "MSEMethod",
    "MultiScaleSSIMMethod",
    "ORBMethod",
    "PHashMethod",
    "PSNRMethod",
    "SIFTMethod",
    # Structural methods
    "SSIMMethod",
    # Base classes
    "SimilarityMethod",
    "WHashMethod",
    "__author__",
    "__description__",
    # Version info
    "__version__",
    "binary_files_equal",
    # Configuration
    "configure",
    # Factory
    "create_comparison_method",
    "file_sha256",
    "get_config",
    # Utility functions
    "hamming_distance",
    "hamming_similarity",
    "reset_config",
]
