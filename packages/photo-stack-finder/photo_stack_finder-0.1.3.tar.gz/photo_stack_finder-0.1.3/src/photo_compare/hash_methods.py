"""Hash-based similarity methods with caching support."""

from __future__ import annotations

import imagehash
import numpy as np
import numpy.typing as npt
from PIL import Image

from .base import BinningSimilarityMethod
from .distance import hamming_similarity


class AHashMethod(BinningSimilarityMethod[bytes, bytes]):
    """Average hash method - very fast, basic similarity detection."""

    def __init__(self, hash_size: int) -> None:
        super().__init__("ahash")
        self.hash_size = hash_size

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> bytes:
        """Prepare average hash for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        hash_obj = imagehash.average_hash(img, self.hash_size)
        return np.packbits(hash_obj.hash).tobytes()

    def _compare_prepared(self, prep1: bytes, prep2: bytes) -> float:
        """Compare hash bytes using Hamming similarity."""
        return hamming_similarity(prep1, prep2)

    def _get_bin_key(self, prepared: bytes) -> bytes:
        """Use the hash itself as the bin key for exact matches."""
        return prepared


class DHashMethod(BinningSimilarityMethod[bytes, bytes]):
    """Difference hash method - good for detecting crops and borders."""

    def __init__(self, hash_size: int) -> None:
        super().__init__("dhash")
        self.hash_size = hash_size

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> bytes:
        """Prepare difference hash for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        hash_obj = imagehash.dhash(img, self.hash_size)
        return np.packbits(hash_obj.hash).tobytes()

    def _compare_prepared(self, prep1: bytes, prep2: bytes) -> float:
        """Compare hash bytes using Hamming similarity."""
        return hamming_similarity(prep1, prep2)

    def _get_bin_key(self, prepared: bytes) -> bytes:
        """Use the hash itself as the bin key for exact matches."""
        return prepared


class PHashMethod(BinningSimilarityMethod[bytes, bytes]):
    """Perceptual hash method - DCT based, robust to minor changes."""

    def __init__(self, hash_size: int) -> None:
        super().__init__("phash")
        self.hash_size = hash_size

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> bytes:
        """Prepare perceptual hash for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        hash_obj = imagehash.phash(img, self.hash_size)
        return np.packbits(hash_obj.hash).tobytes()

    def _compare_prepared(self, prep1: bytes, prep2: bytes) -> float:
        """Compare hash bytes using Hamming similarity."""
        return hamming_similarity(prep1, prep2)

    def _get_bin_key(self, prepared: bytes) -> bytes:
        """Use the hash itself as the bin key for exact matches."""
        return prepared


class WHashMethod(BinningSimilarityMethod[bytes, bytes]):
    """Wavelet hash method - good for texture detection."""

    def __init__(self, hash_size: int) -> None:
        super().__init__("whash")
        self.hash_size = hash_size

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> bytes:
        """Prepare wavelet hash for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        hash_obj = imagehash.whash(img, self.hash_size)
        return np.packbits(hash_obj.hash).tobytes()

    def _compare_prepared(self, prep1: bytes, prep2: bytes) -> float:
        """Compare hash bytes using Hamming similarity."""
        return hamming_similarity(prep1, prep2)

    def _get_bin_key(self, prepared: bytes) -> bytes:
        """Use the hash itself as the bin key for exact matches."""
        return prepared
