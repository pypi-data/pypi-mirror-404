"""Core data structures and base classes for overlap_metrics library."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np
import numpy.typing as npt
import pandas as pd

from .config import NUMERICS, VALIDATION
from .utils import make_grid

# Type aliases
ArrayLike1D = npt.NDArray[np.float64] | pd.Series | Sequence[float]
PDF = Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]]


class EstimatorName(Enum):
    """Available density estimator types."""

    HIST = "hist"
    BETA = "beta"
    LOGIT_KDE = "logit_kde"
    # Reserved for future implementation
    BETA_MIX = "beta_mix"


class MetricName(Enum):
    """Available separation/overlap metrics."""

    SEPARATION_OVL = "separation_ovl"
    BHATTACHARYYA_DISTANCE = "bhattacharyya_distance"
    JENSEN_SHANNON = "js_divergence"
    HELLINGER = "hellinger_distance"
    TOTAL_VARIATION = "total_variation"
    WASSERSTEIN_1D = "wasserstein_1d"
    KS_STAT = "ks_stat"


@dataclass(frozen=True)
class ScoreSamples:
    """Container for positive and negative score samples."""

    pos: npt.NDArray[np.float64]
    neg: npt.NDArray[np.float64]

    def __post_init__(self) -> None:
        """Validate sample arrays after construction."""
        if len(self.pos) < VALIDATION.MIN_SAMPLES:
            raise ValueError(f"Need at least {VALIDATION.MIN_SAMPLES} positive samples, got {len(self.pos)}")
        if len(self.neg) < VALIDATION.MIN_SAMPLES:
            raise ValueError(f"Need at least {VALIDATION.MIN_SAMPLES} negative samples, got {len(self.neg)}")

        if self.pos.ndim != 1:
            raise ValueError(f"Positive samples must be 1D, got shape {self.pos.shape}")
        if self.neg.ndim != 1:
            raise ValueError(f"Negative samples must be 1D, got shape {self.neg.shape}")

    @staticmethod
    def to_ndarray1d(x: ArrayLike1D, dropna: bool, clip01: bool) -> npt.NDArray[np.float64]:
        """Convert array-like input to 1D float64 numpy array."""
        vals: npt.NDArray[np.float64]
        if isinstance(x, pd.Series):
            vals = x.to_numpy(copy=False, dtype=NUMERICS.DTYPE_FLOAT)
            if dropna:
                vals = vals[~pd.isna(vals)]
        else:
            vals = np.asarray(x, dtype=NUMERICS.DTYPE_FLOAT)

        if clip01:
            vals = np.clip(vals, NUMERICS.SCORE_MIN, NUMERICS.SCORE_MAX)

        if vals.ndim != 1:
            raise ValueError(f"Expected 1D scores, got shape {vals.shape}")

        return vals

    @classmethod
    def from_arrays(
        cls,
        pos: ArrayLike1D,
        neg: ArrayLike1D,
        dropna: bool = True,
        clip01: bool = True,
    ) -> ScoreSamples:
        """Create ScoreSamples from two array-like objects."""
        pos_array: npt.NDArray[np.float64] = cls.to_ndarray1d(pos, dropna=dropna, clip01=clip01)
        neg_array: npt.NDArray[np.float64] = cls.to_ndarray1d(neg, dropna=dropna, clip01=clip01)
        return cls(pos=pos_array, neg=neg_array)

    @classmethod
    def from_frame(
        cls,
        df: pd.DataFrame,
        pos_col: str,
        neg_col: str,
        dropna: bool = True,
        clip01: bool = True,
    ) -> ScoreSamples:
        """Create ScoreSamples from DataFrame columns."""
        return cls.from_arrays(df[pos_col], df[neg_col], dropna=dropna, clip01=clip01)


@dataclass(frozen=True)
class MetricResult:
    """Result of a metric computation with metadata."""

    name: str
    value: float
    lower_is_better: bool
    bounds: tuple[float, float]
    estimator_name: str
    details: dict[str, float]
    meta: dict[str, float]

    def __post_init__(self) -> None:
        """Validate metric result after construction."""
        if not np.isfinite(self.value):
            raise ValueError(f"Metric value must be finite, got {self.value}")

        bound_min: float
        bound_max: float
        bound_min, bound_max = self.bounds
        if not (bound_min <= self.value <= bound_max):
            # Allow slight numerical tolerance for bounds checking
            tolerance: float = 1e-10
            if not (bound_min - tolerance <= self.value <= bound_max + tolerance):
                raise ValueError(f"Metric value {self.value} outside bounds {self.bounds} for {self.name}")


class DensityEstimatorBase(ABC):
    """Abstract base class for density estimators on [0,1]."""

    def __init__(self, name: str):
        self.name: str = name
        self._fitted: bool = False

    @abstractmethod
    def fit(
        self,
        samples: npt.NDArray[np.float64],
        weights: npt.NDArray[np.float64] | None = None,
        random_state: int | None = None,
    ) -> None:
        """Learn parameters from samples in [0,1].

        Args:
                samples: 1D array of samples in [0,1]
                weights: Optional sample weights (non-negative, sum arbitrary)
                random_state: Random seed for stochastic initialization
        """
        pass

    @abstractmethod
    def pdf(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Evaluate fitted PDF at points x in [0,1].

        Args:
                x: Points to evaluate, should be in [0,1]

        Returns:
                PDF values (non-negative)
        """
        pass

    def integral(self, n_grid: int, grid: str) -> float:
        """Compute integral of PDF over [0,1] using trapezoidal rule."""
        if not self._fitted:
            raise RuntimeError(f"Estimator {self.name} must be fitted before computing integral")

        xs: npt.NDArray[np.float64] = make_grid(n_grid=n_grid, mode=grid)
        ys: npt.NDArray[np.float64] = np.maximum(self.pdf(xs), 0.0)
        integral_val: float = float(np.trapezoid(ys, xs))
        return integral_val

    def _mark_fitted(self) -> None:
        """Mark estimator as fitted (call from subclass fit methods)."""
        self._fitted = True

    def _check_fitted(self) -> None:
        """Raise error if estimator not fitted."""
        if not self._fitted:
            raise RuntimeError(f"Estimator {self.name} must be fitted before use")


class MetricBase(ABC):
    """Abstract base class for separation/overlap metrics."""

    def __init__(self, name: str, lower_is_better: bool, bounds: tuple[float, float]):
        self.name: str = name
        self.lower_is_better: bool = lower_is_better
        self.bounds: tuple[float, float] = bounds

    @abstractmethod
    def from_pdfs(
        self,
        p: PDF,
        q: PDF,
        n_grid: int,
        grid: str,
    ) -> MetricResult:
        """Compute metric from two PDF functions by integration on [0,1] grid."""
        pass

    def from_samples(
        self,
        samples: ScoreSamples,
        estimator: DensityEstimatorBase,
        n_grid: int,
        grid: str,
        weights_pos: npt.NDArray[np.float64] | None = None,
        weights_neg: npt.NDArray[np.float64] | None = None,
        random_state: int | None = None,
    ) -> MetricResult:
        """Compute metric from samples using density estimation."""
        start_time: float = time.perf_counter()

        # Create fresh estimator instances
        estimator_type: type[DensityEstimatorBase] = type(estimator)
        estimator_pos: DensityEstimatorBase = estimator_type(estimator.name)
        estimator_neg: DensityEstimatorBase = estimator_type(estimator.name)

        # Fit both estimators
        estimator_pos.fit(samples.pos, weights=weights_pos, random_state=random_state)
        estimator_neg.fit(samples.neg, weights=weights_neg, random_state=random_state)

        # Compute metric from PDFs
        result: MetricResult = self.from_pdfs(estimator_pos.pdf, estimator_neg.pdf, n_grid=n_grid, grid=grid)

        # Add runtime metadata
        runtime_ms: float = (time.perf_counter() - start_time) * 1000.0

        # Create updated result with metadata
        updated_meta: dict[str, float] = {
            **result.meta,
            "n_pos": float(len(samples.pos)),
            "n_neg": float(len(samples.neg)),
            "runtime_ms": runtime_ms,
        }

        return MetricResult(
            name=result.name,
            value=result.value,
            lower_is_better=result.lower_is_better,
            bounds=result.bounds,
            estimator_name=result.estimator_name,
            details=result.details,
            meta=updated_meta,
        )


class SampleBasedMetric(MetricBase):
    """Base class for metrics that operate directly on samples."""

    def from_pdfs(
        self,
        p: PDF,
        q: PDF,
        n_grid: int,
        grid: str,
    ) -> MetricResult:
        """Sample-based metrics cannot be computed from PDFs."""
        raise NotImplementedError(
            f"Metric {self.name} is sample-based and cannot be computed from PDFs. Use from_samples() instead."
        )

    @abstractmethod
    def from_samples(
        self,
        samples: ScoreSamples,
        estimator: DensityEstimatorBase,
        n_grid: int,
        grid: str,
        weights_pos: npt.NDArray[np.float64] | None = None,
        weights_neg: npt.NDArray[np.float64] | None = None,
        random_state: int | None = None,
    ) -> MetricResult:
        """Compute metric directly from samples."""
        pass
