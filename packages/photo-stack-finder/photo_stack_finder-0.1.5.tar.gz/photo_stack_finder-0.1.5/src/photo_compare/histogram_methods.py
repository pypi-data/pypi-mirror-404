"""Histogram-based similarity methods with caching support."""

from __future__ import annotations

from abc import abstractmethod

import cv2 as cv
import numpy as np
import numpy.typing as npt
from PIL import Image

from .base import ComparisonMethodName, SimilarityMethod


class HistogramMethodBase(SimilarityMethod[npt.NDArray[np.float32]]):
    """Base class for histogram-based similarity methods."""

    def __init__(self, method_name: ComparisonMethodName, comparison_method: str) -> None:
        super().__init__(method_name)
        self.comparison_method = comparison_method

    @abstractmethod
    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Implement the actual histogram preparation logic.

        Args:
            pixels: RGB pixel array with shape (height, width, 3), dtype uint8.
                    EXIF orientation already applied. Full resolution.

        Returns:
            Normalized histogram as float32 array
        """
        ...

    def _compare_histograms(self, hist1: npt.NDArray[np.float32], hist2: npt.NDArray[np.float32]) -> float:
        """Compare histograms using OpenCV methods."""
        methods: dict[str, int] = {
            "correlation": cv.HISTCMP_CORREL,
            "chi_square": cv.HISTCMP_CHISQR,
            "intersection": cv.HISTCMP_INTERSECT,
            "bhattacharyya": cv.HISTCMP_BHATTACHARYYA,
        }

        method: int = methods.get(self.comparison_method, cv.HISTCMP_CORREL)
        similarity: float = cv.compareHist(hist1.astype(np.float32), hist2.astype(np.float32), method)

        # Normalize to 0-1 scale where higher is more similar
        if self.comparison_method == "chi_square":
            return float(1.0 / (1.0 + similarity))
        if self.comparison_method == "bhattacharyya":
            return float(1.0 - similarity)
        return float(max(0.0, similarity))


class ColorHistogramMethod(HistogramMethodBase):
    """RGB colour histogram method for colour-based similarity."""

    def __init__(self, bins: int, comparison_method: str) -> None:
        super().__init__("colour_histogram", comparison_method)
        self.bins = bins

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare RGB color histograms for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        arr = np.array(img)

        hist_r: npt.NDArray[np.float32] = cv.calcHist([arr], [0], None, [self.bins], [0, 256]).flatten()
        hist_g: npt.NDArray[np.float32] = cv.calcHist([arr], [1], None, [self.bins], [0, 256]).flatten()
        hist_b: npt.NDArray[np.float32] = cv.calcHist([arr], [2], None, [self.bins], [0, 256]).flatten()

        # Normalize
        hist_r = hist_r / (hist_r.sum() + 1e-10)
        hist_g = hist_g / (hist_g.sum() + 1e-10)
        hist_b = hist_b / (hist_b.sum() + 1e-10)

        # Concatenate into single array for consistent interface
        return np.concatenate([hist_r, hist_g, hist_b])

    def _compare_prepared(self, prep1: npt.NDArray[np.float32], prep2: npt.NDArray[np.float32]) -> float:
        """Compare RGB histograms by averaging across channels."""
        # Split back into R, G, B channels
        bins: int = len(prep1) // 3
        r1: npt.NDArray[np.float32] = prep1[:bins]
        g1: npt.NDArray[np.float32] = prep1[bins : 2 * bins]
        b1: npt.NDArray[np.float32] = prep1[2 * bins :]
        r2: npt.NDArray[np.float32] = prep2[:bins]
        g2: npt.NDArray[np.float32] = prep2[bins : 2 * bins]
        b2: npt.NDArray[np.float32] = prep2[2 * bins :]

        r_sim: float = self._compare_histograms(r1, r2)
        g_sim: float = self._compare_histograms(g1, g2)
        b_sim: float = self._compare_histograms(b1, b2)
        return (r_sim + g_sim + b_sim) / 3.0


class HSVHistogramMethod(HistogramMethodBase):
    """HSV colour histogram method - often better than RGB for colour similarity."""

    def __init__(self, bins: tuple[int, int, int], comparison_method: str) -> None:
        super().__init__("hsv_histogram", comparison_method)
        self.bins = bins

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare HSV color histogram for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        arr = np.array(img)
        hsv = cv.cvtColor(arr, cv.COLOR_RGB2HSV)

        hist: npt.NDArray[np.float32] = cv.calcHist([hsv], [0, 1, 2], None, list(self.bins), [0, 180, 0, 256, 0, 256])
        hist = hist.flatten()
        normalized: npt.NDArray[np.float32] = (hist / (hist.sum() + 1e-10)).astype(np.float32)
        return normalized

    def _compare_prepared(self, prep1: npt.NDArray[np.float32], prep2: npt.NDArray[np.float32]) -> float:
        """Compare HSV histograms using specified method."""
        return self._compare_histograms(prep1, prep2)
