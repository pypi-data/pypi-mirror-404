"""Pixel-based similarity methods with caching support."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from PIL import Image

from .base import SimilarityMethod


class MSEMethod(SimilarityMethod[npt.NDArray[np.float32]]):
    """Mean Squared Error method for pixel-level comparison."""

    def __init__(self, image_size: int) -> None:
        super().__init__("mse")
        self.image_size = image_size

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare standardized image for MSE comparison."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        img = img.resize((self.image_size, self.image_size), Image.Resampling.LANCZOS)
        return np.array(img, dtype=np.float32)

    def _compare_prepared(self, prep1: npt.NDArray[np.float32], prep2: npt.NDArray[np.float32]) -> float:
        """Compare images using MSE converted to similarity score."""
        mse = float(np.mean((prep1 - prep2) ** 2))
        # Convert MSE to similarity score using exponential decay
        return float(np.exp(-mse / 1000.0))


class PSNRMethod(SimilarityMethod[npt.NDArray[np.float32]]):
    """Peak Signal-to-Noise Ratio method for image quality comparison."""

    def __init__(self, image_size: int, max_value: float) -> None:
        super().__init__("psnr")
        self.image_size = image_size
        self.max_value = max_value

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare standardized image for PSNR comparison."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        img = img.resize((self.image_size, self.image_size), Image.Resampling.LANCZOS)
        return np.array(img, dtype=np.float32)

    def _compare_prepared(self, prep1: npt.NDArray[np.float32], prep2: npt.NDArray[np.float32]) -> float:
        """Compare images using PSNR converted to similarity score."""
        mse = float(np.mean((prep1 - prep2) ** 2))

        if mse == 0:
            return 1.0  # Perfect similarity

        psnr = 20 * np.log10(self.max_value / np.sqrt(mse))
        # Convert PSNR to similarity score (0-1)
        # PSNR typically ranges from ~10 (poor) to ~50+ (excellent)
        return float(min(1.0, max(0.0, (psnr - 10.0) / 40.0)))
