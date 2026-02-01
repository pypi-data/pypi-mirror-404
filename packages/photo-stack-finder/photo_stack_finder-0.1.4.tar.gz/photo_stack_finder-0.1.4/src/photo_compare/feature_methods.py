"""Feature-based similarity methods with caching support."""

from __future__ import annotations

from abc import abstractmethod

import cv2 as cv
import numpy as np
import numpy.typing as npt
from PIL import Image

from .base import ComparisonMethodName, SimilarityMethod


class FeatureMethodBase(SimilarityMethod[npt.NDArray[np.float32] | npt.NDArray[np.uint8]]):
    """Base class for feature-based similarity methods."""

    def __init__(self, method_name: ComparisonMethodName, match_threshold: float) -> None:
        super().__init__(method_name)
        self.match_threshold = match_threshold

    @abstractmethod
    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32] | npt.NDArray[np.uint8]:
        """Implement the actual preparation logic for feature descriptors."""
        pass

    @abstractmethod
    def _get_matcher(self) -> cv.FlannBasedMatcher | cv.BFMatcher:
        """Get the appropriate matcher for this feature type."""
        pass

    def _compare_prepared(
        self,
        prep1: npt.NDArray[np.float32] | npt.NDArray[np.uint8],
        prep2: npt.NDArray[np.float32] | npt.NDArray[np.uint8],
    ) -> float:
        """Compare feature descriptors using matching ratio."""
        min_features: int = min(len(prep1), len(prep2))
        if min_features < 2:
            return 0.0  # Not enough features to compare

        matcher: cv.FlannBasedMatcher | cv.BFMatcher = self._get_matcher()
        matches: list[tuple[cv.DMatch, ...]] = matcher.knnMatch(prep1, prep2, k=2)

        good_matches: list[cv.DMatch] = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < self.match_threshold * n.distance:
                    good_matches.append(m)

        return len(good_matches) / min_features


class SIFTMethod(FeatureMethodBase):
    """SIFT (Scale-Invariant Feature Transform) keypoint method."""

    LOWE_RATIO_THRESHOLD = 0.7  # Algorithmic constant

    def __init__(self, max_features: int = 0, match_threshold: float = LOWE_RATIO_THRESHOLD) -> None:
        super().__init__("sift", match_threshold)
        self.max_features = max_features

    def _get_matcher(self) -> cv.FlannBasedMatcher | cv.BFMatcher:
        """SIFT uses FLANN matcher for float descriptors."""
        return cv.FlannBasedMatcher()

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.float32]:
        """Prepare SIFT keypoint descriptors for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        gray: npt.NDArray[np.uint8] = np.array(img.resize((512, 512), Image.Resampling.LANCZOS))

        # noinspection PyUnresolvedReferences
        sift: cv.SIFT = cv.SIFT_create(nfeatures=self.max_features)
        _keypoints, desc = sift.detectAndCompute(gray, None)

        if desc is None:
            # Return empty array with correct shape (0 features, 128 dimensions)
            return np.array([], dtype=np.float32).reshape(0, 128)

        # SIFT always returns float32 descriptors
        return desc.astype(np.float32)


class AKAZEMethod(FeatureMethodBase):
    """AKAZE (Accelerated-KAZE) keypoint method."""

    LOWE_RATIO_THRESHOLD = 0.75  # May need slight adjustment for binary features

    def __init__(self, match_threshold: float = LOWE_RATIO_THRESHOLD) -> None:
        super().__init__("akaze", match_threshold)

    def _get_matcher(self) -> cv.FlannBasedMatcher | cv.BFMatcher:
        """AKAZE uses BF matcher for binary descriptors."""
        return cv.BFMatcher(cv.NORM_HAMMING, crossCheck=False)

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
        """Prepare AKAZE keypoint descriptors for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        gray: npt.NDArray[np.uint8] = np.array(img.resize((512, 512), Image.Resampling.LANCZOS))

        # noinspection PyUnresolvedReferences
        akaze = cv.AKAZE_create()
        _keypoints, desc = akaze.detectAndCompute(gray, None)

        if desc is None:
            # Return empty array with correct shape (0 features, 61 bytes for AKAZE)
            return np.array([], dtype=np.uint8).reshape(0, 61)

        # AKAZE returns binary (uint8) descriptors
        return desc.astype(np.uint8)


class ORBMethod(FeatureMethodBase):
    """ORB (Oriented FAST and Rotated BRIEF) keypoint method."""

    LOWE_RATIO_THRESHOLD = 0.75  # May need slight adjustment for binary features

    def __init__(self, max_features: int = 0, match_threshold: float = LOWE_RATIO_THRESHOLD) -> None:
        super().__init__("orb", match_threshold)
        self.max_features = max_features

    def _get_matcher(self) -> cv.FlannBasedMatcher | cv.BFMatcher:
        """ORB uses BF matcher for binary descriptors."""
        return cv.BFMatcher(cv.NORM_HAMMING, crossCheck=False)

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
        """Prepare ORB keypoint descriptors for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        gray: npt.NDArray[np.uint8] = np.array(img.resize((512, 512), Image.Resampling.LANCZOS))

        orb = cv.ORB_create(nfeatures=self.max_features)
        _keypoints, desc = orb.detectAndCompute(gray, None)

        if desc is None:
            # Return empty array with correct shape (0 features, 32 bytes for ORB)
            return np.array([], dtype=np.uint8).reshape(0, 32)

        # ORB returns binary (uint8) descriptors
        return desc.astype(np.uint8)


class BRISKMethod(FeatureMethodBase):
    """BRISK (Binary Robust Invariant Scalable Keypoints) method."""

    LOWE_RATIO_THRESHOLD = 0.75  # May need slight adjustment for binary features

    def __init__(self, match_threshold: float = LOWE_RATIO_THRESHOLD) -> None:
        super().__init__("brisk", match_threshold)

    def _get_matcher(self) -> cv.FlannBasedMatcher | cv.BFMatcher:
        """BRISK uses BF matcher for binary descriptors."""
        return cv.BFMatcher(cv.NORM_HAMMING, crossCheck=False)

    def _prepare_single(self, pixels: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
        """Prepare BRISK keypoint descriptors for the image."""
        img = Image.fromarray(pixels, mode="RGB")
        img = img.convert("L")
        gray: npt.NDArray[np.uint8] = np.array(img.resize((512, 512), Image.Resampling.LANCZOS))

        # noinspection PyUnresolvedReferences
        brisk = cv.BRISK_create()
        _keypoints, desc = brisk.detectAndCompute(gray, None)

        if desc is None:
            # Return empty array with correct shape (0 features, 64 bytes for BRISK)
            return np.array([], dtype=np.uint8).reshape(0, 64)

        # BRISK returns binary (uint8) descriptors
        return desc.astype(np.uint8)
