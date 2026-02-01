"""Structural similarity methods with caching support."""

from __future__ import annotations

from collections.abc import Sequence

import cv2 as cv
import numpy as np
import numpy.typing as npt
from PIL import Image
from skimage.feature import hog
from skimage.metrics import structural_similarity as ssim

from .base import SimilarityMethod


class SSIMMethod(SimilarityMethod[npt.NDArray[np.float32]]):
    """SSIM (Structural Similarity Index) method using scikit-image."""

    def __init__(self, image_size: int) -> None:
        super().__init__("ssim")
        self.image_size = image_size

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare image for SSIM comparison."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        img = img.resize((self.image_size, self.image_size), Image.Resampling.LANCZOS)
        return np.array(img, dtype=np.float32) / 255.0

    def _compare_prepared(self, prep1: npt.NDArray[np.float32], prep2: npt.NDArray[np.float32]) -> float:
        """Compare prepared images using SSIM."""
        return float(ssim(prep1, prep2, data_range=1.0))


class MultiScaleSSIMMethod(SimilarityMethod[npt.NDArray[np.float32]]):
    """Multi-scale SSIM method for more robust comparison."""

    def __init__(self, image_size: int, scales: Sequence[float]) -> None:
        super().__init__("ms_ssim")
        self.image_size = image_size
        self.scales = scales

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare image for multi-scale SSIM comparison."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        img = img.resize((self.image_size, self.image_size), Image.Resampling.LANCZOS)
        return np.array(img, dtype=np.float32) / 255.0

    def _compare_prepared(self, prep1: npt.NDArray[np.float32], prep2: npt.NDArray[np.float32]) -> float:
        """Compare prepared images using multi-scale SSIM."""
        scores: list[float] = []
        for scale in self.scales:
            if scale == 1.0:
                score: float = float(ssim(prep1, prep2, data_range=1.0))
            else:
                h: int
                w: int
                h, w = prep1.shape
                new_h: int = max(1, int(h * scale))
                new_w: int = max(1, int(w * scale))
                prep1_scaled: npt.NDArray[np.float32] = cv.resize(prep1, (new_w, new_h), interpolation=cv.INTER_AREA)
                prep2_scaled: npt.NDArray[np.float32] = cv.resize(prep2, (new_w, new_h), interpolation=cv.INTER_AREA)
                score = float(ssim(prep1_scaled, prep2_scaled, data_range=1.0))
            scores.append(score)
        return float(np.mean(scores))


class HOGMethod(SimilarityMethod[npt.NDArray[np.float32]]):
    """HOG (Histogram of Oriented Gradients) feature method using scikit-image."""

    def __init__(self, orientations: int, pixels_per_cell: tuple[int, int]) -> None:
        super().__init__("hog")
        self.orientations = orientations
        self.pixels_per_cell = pixels_per_cell

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare HOG features for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        img = img.resize((128, 128), Image.Resampling.LANCZOS)
        img_array: npt.NDArray[np.float32] = np.array(img, dtype=np.float32) / 255.0

        features: npt.NDArray[np.float32] = hog(
            img_array,
            orientations=self.orientations,
            pixels_per_cell=self.pixels_per_cell,
            cells_per_block=(2, 2),
            block_norm="L2-Hys",
            feature_vector=True,
        )
        return features.astype(np.float32)

    def _compare_prepared(self, prep1: npt.NDArray[np.float32], prep2: npt.NDArray[np.float32]) -> float:
        """Compare HOG features using cosine similarity."""
        dot_product = float(np.dot(prep1, prep2))
        norm_a = float(np.linalg.norm(prep1))
        norm_b = float(np.linalg.norm(prep2))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)
