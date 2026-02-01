"""Base classes for image similarity methods with timing statistics."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, TypeVar

import numpy as np
import numpy.typing as npt

# Type variable for the prepared data type (hidden from external users)
PreparedT = TypeVar("PreparedT")
BinKeyT = TypeVar("BinKeyT")


@dataclass
class TimingStats:
    """Statistics for method timing."""

    total_wall_time: float = 0.0
    total_cpu_time: float = 0.0
    call_count: int = 0

    def add_timing(self, wall_time: float, cpu_time: float) -> None:
        """Add timing data from a single call."""
        self.total_wall_time += wall_time
        self.total_cpu_time += cpu_time
        self.call_count += 1

    @property
    def avg_wall_time(self) -> float:
        """Average wall clock time per call."""
        return self.total_wall_time / max(1, self.call_count)

    @property
    def avg_cpu_time(self) -> float:
        """Average CPU time per call."""
        return self.total_cpu_time / max(1, self.call_count)

    def accumulate(self, other: TimingStats) -> None:
        """Accumulate timing stats from another TimingStats instance."""
        self.total_wall_time += other.total_wall_time
        self.total_cpu_time += other.total_cpu_time
        self.call_count += other.call_count


class SimilarityMethod[PreparedT](ABC):
    """Base class for all similarity methods with timing statistics.

    Caching is handled externally by the parent application (e.g., PhotoFile objects).
    This class provides the core prepare and compare operations with optional timing.
    """

    def __init__(self, method_name: ComparisonMethodName):
        self.method_name: ComparisonMethodName = method_name

        # Timing statistics
        self._prepare_timing = TimingStats()
        self._compare_timing = TimingStats()

    @abstractmethod
    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> PreparedT:
        """Implement the actual preparation logic.

        Args:
                pixels: RGB pixel array with shape (height, width, 3), dtype uint8.
                        EXIF orientation already applied. Full resolution.

        Returns:
                Prepared data for comparison
        """
        pass

    @abstractmethod
    def _compare_prepared(self, prep1: PreparedT, prep2: PreparedT) -> float:
        """Compare two prepared items.

        Args:
                prep1: First prepared item
                prep2: Second prepared item

        Returns:
                Similarity score 0-1 (higher is more similar)
        """
        pass

    def _prepare_single_timed(self, pixels: npt.NDArray[np.uint8]) -> PreparedT:
        """Wrapper for _prepare_single that tracks timing."""
        wall_start = time.perf_counter()
        cpu_start = time.process_time()

        result = self._prepare_single(pixels)

        wall_elapsed = time.perf_counter() - wall_start
        cpu_elapsed = time.process_time() - cpu_start
        self._prepare_timing.add_timing(wall_elapsed, cpu_elapsed)

        return result

    def _compare_prepared_timed(self, prep1: PreparedT, prep2: PreparedT) -> float:
        """Wrapper for _compare_prepared that tracks timing."""
        wall_start = time.perf_counter()
        cpu_start = time.process_time()

        result = self._compare_prepared(prep1, prep2)

        wall_elapsed = time.perf_counter() - wall_start
        cpu_elapsed = time.process_time() - cpu_start
        self._compare_timing.add_timing(wall_elapsed, cpu_elapsed)

        return result

    def prepare(self, pixels: npt.NDArray[np.uint8]) -> PreparedT:
        """Prepare pixel array for comparison.

        Args:
                pixels: RGB pixel array with shape (height, width, 3), dtype uint8.
                        EXIF orientation already applied. Full resolution.

        Returns:
                Prepared data for comparison

        Example:
                >>> from photo_compare import create_comparison_method
                >>> method = create_comparison_method('dhash')
                >>> with photo1.image_data() as img1, photo2.image_data() as img2:
                ...     pixels1 = img1.get_pixels()
                ...     pixels2 = img2.get_pixels()
                ...     prep1 = method.prepare(pixels1)
                ...     prep2 = method.prepare(pixels2)
                ...     similarity = method.compare(prep1, prep2)
        """
        return self._prepare_single_timed(pixels)

    def compare(self, prep1: PreparedT, prep2: PreparedT) -> float:
        """Compare two prepared items.

        Args:
                prep1: First prepared item
                prep2: Second prepared item

        Returns:
                Similarity score 0-1 (higher is more similar)
        """
        return self._compare_prepared_timed(prep1, prep2)

    def timing_stats(self) -> dict[str, dict[str, float]]:
        """Get timing statistics for both preparation and comparison operations.

        Returns:
                Dictionary with 'preparation' and 'comparison' timing stats
        """
        return {
            "preparation": {
                "total_wall_time": self._prepare_timing.total_wall_time,
                "total_cpu_time": self._prepare_timing.total_cpu_time,
                "call_count": self._prepare_timing.call_count,
                "avg_wall_time": self._prepare_timing.avg_wall_time,
                "avg_cpu_time": self._prepare_timing.avg_cpu_time,
            },
            "comparison": {
                "total_wall_time": self._compare_timing.total_wall_time,
                "total_cpu_time": self._compare_timing.total_cpu_time,
                "call_count": self._compare_timing.call_count,
                "avg_wall_time": self._compare_timing.avg_wall_time,
                "avg_cpu_time": self._compare_timing.avg_cpu_time,
            },
        }


class BinningSimilarityMethod[PreparedT, BinKeyT](SimilarityMethod[PreparedT]):
    """Base class for methods that support binning (like hash-based methods).

    Binning allows grouping of prepared items by their key for efficient
    duplicate detection. Bins are maintained separately from the main cache.
    """

    def __init__(self, method_name: ComparisonMethodName):
        super().__init__(method_name)
        self._bins: dict[BinKeyT, set[int]] = defaultdict(set)
        self._file_to_bin: dict[int, BinKeyT] = {}

    @abstractmethod
    def _get_bin_key(self, prepared: PreparedT) -> BinKeyT:
        """Extract the binning key from prepared data.

        Args:
                prepared: Prepared data

        Returns:
                Bin key for grouping
        """
        pass

    def prepare_and_bin(self, file_id: int, pixels: npt.NDArray[np.uint8]) -> PreparedT:
        """Prepare pixel array and add to bins.

        Args:
                file_id: Unique identifier for the file
                pixels: RGB pixel array (height, width, 3), dtype uint8

        Returns:
                Prepared data for comparison
        """
        prepared = self.prepare(pixels)
        bin_key = self._get_bin_key(prepared)
        self._bins[bin_key].add(file_id)
        self._file_to_bin[file_id] = bin_key
        return prepared

    def add_to_bin(self, file_id: int, prepared: PreparedT) -> None:
        """Add a prepared item to bins without re-preparing.

        Args:
                file_id: Unique identifier for the file
                prepared: Pre-prepared data
        """
        bin_key = self._get_bin_key(prepared)
        self._bins[bin_key].add(file_id)
        self._file_to_bin[file_id] = bin_key

    def get_bin_candidates(self, file_id: int) -> set[int]:
        """Get all files in the same bin as the given file.

        Args:
                file_id: File ID to get candidates for

        Returns:
                Set of file IDs in same bin (excluding the query file)
        """
        if file_id not in self._file_to_bin:
            return set()
        bin_key = self._file_to_bin[file_id]
        return self._bins[bin_key] - {file_id}  # Exclude self

    def get_all_bins(self) -> dict[BinKeyT, set[int]]:
        """Get all bins for analysis.

        Returns:
                Dictionary mapping bin keys to sets of file IDs
        """
        return dict(self._bins)

    def get_duplicate_groups(self, min_group_size: int) -> list[set[int]]:
        """Get all bins with at least min_group_size files.

        Args:
                min_group_size: Minimum number of files in a group

        Returns:
                List of file ID sets representing potential duplicate groups
        """
        return [file_set for file_set in self._bins.values() if len(file_set) >= min_group_size]

    def clear_bins(self) -> None:
        """Clear all bin data."""
        self._bins.clear()
        self._file_to_bin.clear()


ComparisonMethodName = Literal[
    # Hash methods
    "ahash",
    "dhash",
    "phash",
    "whash",
    # Feature methods
    "sift",
    "akaze",
    "orb",
    "brisk",
    # Structural methods
    "ssim",
    "ms_ssim",
    "hog",
    # Pixel methods
    "mse",
    "psnr",
    # Histogram methods
    "colour_histogram",
    "hsv_histogram",
]
