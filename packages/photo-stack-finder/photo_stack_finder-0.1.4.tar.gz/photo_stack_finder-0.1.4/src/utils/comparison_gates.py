"""Comparison gates for orchestrating photo similarity detection.

Gates provide orchestration layer between PhotoFile and photo_compare algorithms:
- Manage caching of prepared data
- Apply thresholds from CONFIG
- Support sequence-based short-circuit evaluation
"""

from __future__ import annotations

from abc import ABC, abstractmethod

# Any is appropriate here: comparison methods prepare heterogeneous data types
# (hash values, feature descriptors, tensors) that cannot be statically typed
# without complex TypeVar threading through the class hierarchy
from typing import Any, Literal, Protocol

import numpy as np
import numpy.typing as npt

from photo_compare import (
    ComparisonMethodName,
    SimilarityMethod,
    create_comparison_method,
)

from .config import CONFIG
from .photo_file import ImageData, PhotoFile

# GateName extends ComparisonMethodName to include "aspect_ratio"
# Explicit Literal type for mypy compatibility (unpacking syntax not fully supported)
GateName = Literal[
    "aspect_ratio",  # Additional gate
    "ahash",
    "dhash",
    "phash",
    "whash",  # Hash methods
    "sift",
    "akaze",
    "orb",
    "brisk",  # Feature methods
    "ssim",
    "ms_ssim",
    "hog",  # Structural methods
    "mse",
    "psnr",  # Pixel methods
    "colour_histogram",
    "hsv_histogram",  # Histogram methods
]


class ComparisonGate(Protocol):
    """Protocol for comparison gates."""

    @property
    def name(self) -> str:
        """Get the gate name."""
        ...

    def compare(
        self,
        photo1: PhotoFile,
        photo2: PhotoFile,
        pixels1: npt.NDArray[np.uint8] | None = None,
        pixels2: npt.NDArray[np.uint8] | None = None,
    ) -> tuple[bool, float]:
        """Compare two photos.

        Args:
                photo1: First photo
                photo2: Second photo
                pixels1: Optional pre-loaded pixel array for photo1
                pixels2: Optional pre-loaded pixel array for photo2

        Returns:
                Tuple of (passes_threshold, score)
        """
        ...


class BaseGate(ABC):
    """Abstract base class for comparison gates.

    Gates manage thresholds and orchestration logic.
    Thresholds are read from CONFIG, falling back to defaults.
    """

    def __init__(self, name: str):
        """Initialize base gate.

        Args:
                name: Gate name (used for CONFIG lookup)
        """
        self._name = name
        self._threshold = self._get_threshold_from_config()

    @property
    def name(self) -> str:
        """Get the gate name."""
        return self._name

    @property
    def threshold(self) -> float:
        """Get the threshold for this gate."""
        return self._threshold

    def _get_threshold_from_config(self) -> float:
        """Get threshold from CONFIG or use default.

        Returns:
                Threshold value
        """
        thresholds = CONFIG.processing.GATE_THRESHOLDS or {}
        return thresholds.get(self._name, self._get_default_threshold())

    @abstractmethod
    def _get_default_threshold(self) -> float:
        """Get default threshold for this gate.

        Returns:
                Default threshold value
        """
        ...

    # Note: compare() is NOT abstract because AspectRatioGate and MethodGate
    # have different signatures. GateSequence uses isinstance checks to dispatch.


class MethodGate(BaseGate):
    """Gate for photo_compare similarity methods.

    Uses local cache to cache prepared data for reuse.
    Delegates comparison to photo_compare SimilarityMethod.
    """

    def __init__(self, method_name: ComparisonMethodName):
        """Initialize method gate.

        Args:
                method_name: Name of photo_compare method
        """
        super().__init__(method_name)
        self.method: SimilarityMethod[Any] = create_comparison_method(method_name)
        # Cache key: (photo.id, rotation)
        self.cache: dict[tuple[int, int], Any] = {}

    def _get_default_threshold(self) -> float:
        """Get default threshold from CONFIG defaults.

        Returns:
                Default threshold value
        """
        defaults = CONFIG.processing.DEFAULT_THRESHOLDS or {}
        return defaults.get(self._name, 0.9)

    def _get_prepared(
        self,
        photo: PhotoFile,
        pixels: npt.NDArray[np.uint8] | None,
        rotation: int = 0,
    ) -> Any:
        """Get prepared data with caching, optionally with rotation.

        Priority:
        1. MethodGate instance cache (fastest)
        2. PhotoFile.cache with tuple key (method_name, rotation)
        3. Compute from pixels

        Args:
                photo: Photo to prepare
                pixels: RGB pixel array (H, W, 3), dtype uint8. None if not loaded.
                rotation: Cumulative rotation from original (0, 90, 180, 270)

        Returns:
                Prepared data for comparison
        """
        # Always use tuple cache key for consistency
        cache_key = (self._name, rotation)

        # Check instance cache (use photo.id as key - rotation handled by cache_key)
        instance_cache_key = (photo.id, rotation)
        if instance_cache_key in self.cache:
            return self.cache[instance_cache_key]

        # Check PhotoFile cache
        cached_prep = photo.cache.get(cache_key)
        if cached_prep is not None:
            self.cache[instance_cache_key] = cached_prep
            return cached_prep

        # Cache miss - need pixels
        assert pixels is not None, f"Cache miss for {cache_key} on photo {photo.id}, but pixels not provided."

        # Compute from pixels
        prep = self.method.prepare(pixels)

        # Store in instance cache
        self.cache[instance_cache_key] = prep

        # Store in PhotoFile cache for persistence
        if self._should_cache_in_photofile(prep):
            photo.cache[cache_key] = prep

        return prep

    def _should_cache_in_photofile(self, prep: Any) -> bool:
        """Determine if preparation should be cached in PhotoFile for lazy persistence.

        Strategy: Cache small preparations (hashes) but not large ones (ssim arrays)
        to avoid memory bloat.

        Args:
                prep: Prepared data to check

        Returns:
                True if preparation should be stored in PhotoFile.cache
        """
        # Hash methods produce small bytes objects (~10 bytes)
        # Don't cache large numpy arrays by default
        # (but they can still be pre-cached in test fixtures)
        return isinstance(prep, bytes) and len(prep) < 100

    def compare(
        self,
        photo1: PhotoFile,
        photo2: PhotoFile,
        pixels1: npt.NDArray[np.uint8] | None = None,
        pixels2: npt.NDArray[np.uint8] | None = None,
        rotation1: int = 0,
        rotation2: int = 0,
    ) -> tuple[bool, float]:
        """Compare two photos using similarity method.

        Args:
                photo1: First photo
                photo2: Second photo
                pixels1: Pixel array for photo1 (None if not yet loaded)
                pixels2: Pixel array for photo2 (None if not yet loaded)
                rotation1: Cumulative rotation for photo1 (0, 90, 180, 270)
                rotation2: Cumulative rotation for photo2 (0, 90, 180, 270)

        Returns:
                Tuple of (passes_threshold, score)
        """
        prep1 = self._get_prepared(photo1, pixels1, rotation1)
        prep2 = self._get_prepared(photo2, pixels2, rotation2)
        score = self.method.compare(prep1, prep2)
        return score >= self._threshold, score


class AspectRatioGate(BaseGate):
    """Gate for aspect ratio compatibility.

    Normalizes aspect ratios to portrait orientation before comparing.
    This allows matching of landscape and portrait photos.

    Example:
        Landscape 1600x1200 (AR=1.33) vs Portrait 1200x1600 (AR=0.75)
        After normalization: 0.75 vs 0.75 -> Match!
    """

    def __init__(self) -> None:
        """Initialize aspect ratio gate."""
        super().__init__("aspect_ratio")

    def _get_default_threshold(self) -> float:
        """Get default threshold from CONFIG.

        Returns:
                Default aspect ratio threshold (0.98)
        """
        return CONFIG.processing.ASPECT_RATIO_THRESHOLD

    def compare(
        self,
        img1: ImageData,
        img2: ImageData,
    ) -> tuple[bool, float]:
        """Compare aspect ratios of two photos.

        Uses aspect ratios from ImageData.
        Lazily triggers dimension extraction if not already cached.

        Args:
                img1: ImageData for first photo
                img2: ImageData for second photo

        Returns:
                Tuple of (passes_threshold, similarity_score)

        """
        # Get aspect ratios (may trigger lazy dimension extraction)
        # This may load pixels if dimensions not yet cached
        ratio1 = img1.get_aspect_ratio()
        ratio2 = img2.get_aspect_ratio()

        # Normalize to portrait orientation (AR < 1.0)
        # This allows matching landscape ↔ portrait photos
        normalized1 = ratio1 if ratio1 < 1.0 else 1.0 / ratio1
        normalized2 = ratio2 if ratio2 < 1.0 else 1.0 / ratio2

        # Compare normalized ratios
        larger = max(normalized1, normalized2)
        smaller = min(normalized1, normalized2)
        score = smaller / larger
        return score >= self._threshold, score


class GateSequence:
    """Sequence of gates for multi-stage comparison.

    Executes gates in order with optional short-circuit evaluation.
    Returns detailed results including all scores and final gate score.
    """

    # noinspection PyTypeHints
    def __init__(self, gate_names: list[GateName]) -> None:
        """Initialize gate sequence.

        Args:
            gate_names: List of gate names to execute in order
        """
        self.gates: list[BaseGate] = []
        for name in gate_names:
            if name == "aspect_ratio":
                self.gates.append(AspectRatioGate())
            else:
                # Must be a ComparisonMethodName
                self.gates.append(MethodGate(name))

    def compare(
        self,
        photo1: PhotoFile,
        photo2: PhotoFile,
        short_circuit: bool = True,
    ) -> tuple[bool, dict[str, float], float]:
        """Compare two photos through gate sequence with lazy pixel loading.

        Creates image data context managers for lazy pixel loading and dimension extraction.
        AspectRatioGate may trigger dimension extraction without loading full pixels.
        MethodGate triggers pixel loading if needed (on cache miss).
        Pixels are shared across all gates to minimize file I/O.

        Args:
            photo1: First photo
            photo2: Second photo
            short_circuit: If True, stop at first failure

        Returns:
            Tuple of (overall_pass, scores_dict, final_gate_score) where:
            - overall_pass: True if all gates pass (or up to short-circuit point)
            - scores_dict: Dictionary mapping gate name to score
            - final_gate_score: Score from the last executed gate
        """
        scores: dict[str, float] = {}
        overall_pass = True
        final_gate_score = 0.0

        # Create context managers for lazy loading
        with photo1.image_data() as img1, photo2.image_data() as img2:
            # Lazy pixel loading: pixels loaded on first get_pixels() call
            # Cached in ImageData._pixels for duration of context
            pixels1: npt.NDArray[np.uint8] | None = None
            pixels2: npt.NDArray[np.uint8] | None = None

            for gate in self.gates:
                if isinstance(gate, AspectRatioGate):
                    # Pass ImageData objects (may trigger dimension extraction)
                    # May load pixels if dimensions not yet cached
                    passes, score = gate.compare(img1, img2)
                elif isinstance(gate, MethodGate):
                    # MethodGate: check if pixels needed (cache miss detection)
                    # Only load pixels if we'll actually need them
                    # Note: cache keys are (method_name, rotation) tuples, always tuples even for rotation=0
                    will_need_pixels1 = (photo1.id, 0) not in gate.cache and (gate._name, 0) not in photo1.cache
                    will_need_pixels2 = (photo2.id, 0) not in gate.cache and (gate._name, 0) not in photo2.cache

                    if will_need_pixels1 or will_need_pixels2:
                        # Cache miss detected - load pixels if not already loaded
                        if pixels1 is None:
                            pixels1 = img1.get_pixels()
                        if pixels2 is None:
                            pixels2 = img2.get_pixels()

                    passes, score = gate.compare(photo1, photo2, pixels1, pixels2)
                else:
                    # Should never happen, but satisfy type checker
                    raise TypeError(f"Unknown gate type: {type(gate)}")

                scores[gate.name] = score
                final_gate_score = score  # Track most recent score

                if not passes:
                    overall_pass = False
                    if short_circuit:
                        break

        return overall_pass, scores, final_gate_score

    def compare_with_rotation(
        self,
        reference: PhotoFile,
        candidate: PhotoFile,
        short_circuit: bool = True,
        ref_img: ImageData | None = None,
        cand_img: ImageData | None = None,
    ) -> tuple[bool, dict[str, float], float]:
        """Compare reference against candidate with rotation attempts.

        Strategy:
        1. Normalize both photos to landscape (ImageData handles rotation)
        2. First attempt: compare at normalized rotations
        3. Second attempt: rotate reference additional 180° ONLY if first fails

        Only the reference photo is rotated (candidate stays normalized).
        Cache keys track cumulative rotation from original file.

        Uses lazy pixel loading: pixels only loaded when needed (on cache miss).

        Args:
            reference: Reference/exemplar photo (will be rotated if needed)
            candidate: Candidate photo (normalized only, never rotated)
            short_circuit: If True, stop at first successful match
            ref_img: Optional pre-created ImageData for reference (caller manages lifecycle)
            cand_img: Optional pre-created ImageData for candidate (caller manages lifecycle)

        Returns:
            Tuple of (overall_pass, scores_dict, final_gate_score)
        """
        # Flexible ImageData management: create contexts only for photos that don't have pre-created ImageData
        # Case 1: Both provided - use directly
        if ref_img is not None and cand_img is not None:
            return self._compare_with_rotation_impl(
                reference, candidate, ref_img, cand_img, short_circuit
            )

        # Case 2: Only ref provided - create context for candidate
        if ref_img is not None and cand_img is None:
            with candidate.image_data() as cand_img_ctx:
                return self._compare_with_rotation_impl(
                    reference, candidate, ref_img, cand_img_ctx, short_circuit
                )

        # Case 3: Only cand provided - create context for reference
        if ref_img is None and cand_img is not None:
            with reference.image_data() as ref_img_ctx:
                return self._compare_with_rotation_impl(
                    reference, candidate, ref_img_ctx, cand_img, short_circuit
                )

        # Case 4: Neither provided - create contexts for both (original pattern)
        with reference.image_data() as ref_img_new, candidate.image_data() as cand_img_new:
            return self._compare_with_rotation_impl(
                reference, candidate, ref_img_new, cand_img_new, short_circuit
            )

    def _compare_with_rotation_impl(
        self,
        reference: PhotoFile,
        candidate: PhotoFile,
        ref_img: ImageData,
        cand_img: ImageData,
        short_circuit: bool,
    ) -> tuple[bool, dict[str, float], float]:
        """Implementation of compare_with_rotation (extracted for ImageData reuse).

        Args:
            reference: Reference PhotoFile
            candidate: Candidate PhotoFile
            ref_img: ImageData for reference (already created)
            cand_img: ImageData for candidate (already created)
            short_circuit: If True, stop at first gate failure

        Returns:
            Tuple of (overall_pass, scores_dict, final_gate_score)
        """
        # Determine normalization rotations (no pixel loading)
        ref_norm_rotation = ref_img.get_normalization_rotation()
        cand_rotation = cand_img.get_normalization_rotation()

        # Track best result across rotation attempts
        best_pass = False
        best_scores: dict[str, float] = {}
        best_final_score = 0.0

        # Lazy pixel loading: only load when gates need them (cache miss)
        ref_pixels: npt.NDArray[np.uint8] | None = None
        cand_pixels: npt.NDArray[np.uint8] | None = None

        # First attempt: normalized rotation (0° offset)
        ref_rotation = ref_norm_rotation
        scores, overall_pass, final_gate_score, ref_pixels, cand_pixels = self._attempt_comparison(
            reference,
            candidate,
            ref_img,
            cand_img,
            ref_rotation,
            cand_rotation,
            ref_pixels,
            cand_pixels,
            short_circuit,
        )

        best_pass = overall_pass
        best_scores = scores
        best_final_score = final_gate_score

        # Second attempt: try 180° rotation ONLY if first failed
        if not overall_pass:
            ref_rotation_180 = ref_norm_rotation + 180
            scores_180, overall_pass_180, final_gate_score_180, ref_pixels, cand_pixels = self._attempt_comparison(
                reference,
                candidate,
                ref_img,
                cand_img,
                ref_rotation_180,
                cand_rotation,
                ref_pixels,
                cand_pixels,
                short_circuit,
            )

            # Use 180° result if it's better
            if overall_pass_180 or final_gate_score_180 > best_final_score:
                best_pass = overall_pass_180
                best_scores = scores_180
                best_final_score = final_gate_score_180

        return best_pass, best_scores, best_final_score

    def _attempt_comparison(
        self,
        reference: PhotoFile,
        candidate: PhotoFile,
        ref_img: ImageData,
        cand_img: ImageData,
        ref_rotation: int,
        cand_rotation: int,
        ref_pixels: npt.NDArray[np.uint8] | None,
        cand_pixels: npt.NDArray[np.uint8] | None,
        short_circuit: bool,
    ) -> tuple[dict[str, float], bool, float, npt.NDArray[np.uint8] | None, npt.NDArray[np.uint8] | None]:
        """Attempt comparison at specific rotation angles.

        Args:
            reference: Reference PhotoFile
            candidate: Candidate PhotoFile
            ref_img: Reference ImageData context
            cand_img: Candidate ImageData context
            ref_rotation: Reference cumulative rotation (0, 90, 180, 270)
            cand_rotation: Candidate cumulative rotation (0, 90, 180, 270)
            ref_pixels: Pre-loaded reference pixels at 0° (or None)
            cand_pixels: Pre-loaded candidate pixels at 0° (or None)
            short_circuit: If True, stop at first gate failure

        Returns:
            Tuple of (scores_dict, overall_pass, final_gate_score, ref_pixels, cand_pixels)
            - Returned pixels may be loaded during this attempt if needed
        """
        scores: dict[str, float] = {}
        overall_pass = True
        final_gate_score = 0.0

        for gate in self.gates:
            if isinstance(gate, AspectRatioGate):
                # AspectRatioGate doesn't need rotation handling
                # (both normalized to landscape, so always same orientation)
                passes, score = gate.compare(ref_img, cand_img)
            elif isinstance(gate, MethodGate):
                # Check if we need to load pixels (cache miss detection)
                # Cache keys are always (method_name, rotation) tuples
                will_need_ref_pixels = (reference.id, ref_rotation) not in gate.cache and (
                    gate._name,
                    ref_rotation,
                ) not in reference.cache
                will_need_cand_pixels = (candidate.id, cand_rotation) not in gate.cache and (
                    gate._name,
                    cand_rotation,
                ) not in candidate.cache

                # Load pixels lazily (only if needed and not yet loaded)
                if will_need_ref_pixels and ref_pixels is None:
                    ref_pixels_at_0 = ref_img.get_pixels()  # Load original
                    ref_img._pixels_cache[0] = ref_pixels_at_0
                    ref_pixels = ref_pixels_at_0

                if will_need_cand_pixels and cand_pixels is None:
                    cand_pixels_at_0 = cand_img.get_pixels()  # Load original
                    cand_img._pixels_cache[0] = cand_pixels_at_0
                    cand_pixels = cand_pixels_at_0

                # Get rotated pixels (uses cache if available)
                ref_pixels_rotated = ref_img.get_pixels_with_rotation(ref_rotation) if will_need_ref_pixels else None
                cand_pixels_rotated = (
                    cand_img.get_pixels_with_rotation(cand_rotation) if will_need_cand_pixels else None
                )

                # Pass rotated pixels and rotation angles for cache keys
                passes, score = gate.compare(
                    reference,
                    candidate,
                    ref_pixels_rotated,
                    cand_pixels_rotated,
                    ref_rotation,
                    cand_rotation,
                )
            else:
                raise TypeError(f"Unknown gate type: {type(gate)}")

            scores[gate.name] = score
            final_gate_score = score

            if not passes:
                overall_pass = False
                if short_circuit:
                    break

        return scores, overall_pass, final_gate_score, ref_pixels, cand_pixels

    @property
    def gate_names(self) -> list[str]:
        """Get list of gate names in this sequence.

        Returns:
            List of gate names
        """
        return [gate.name for gate in self.gates]
