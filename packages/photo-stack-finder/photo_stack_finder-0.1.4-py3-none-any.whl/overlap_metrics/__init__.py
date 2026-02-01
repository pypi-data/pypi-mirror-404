"""overlap_metrics: Distribution separation and overlap metrics library.

A NumPy-centric library for computing separation metrics between two labeled
score samples (positives vs negatives) with pandas-friendly adapters.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

# Check scipy version before importing anything else
import scipy
from packaging import version

from .config import OverlapMetricsConfig, configure, get_config
from .core import (
    ArrayLike1D,
    DensityEstimatorBase,
    EstimatorName,
    MetricBase,
    MetricName,
    MetricResult,
    ScoreSamples,
)
from .registry import create_estimator, create_metric

# Minimum version requirements:
# - scipy >= 1.2.0: gaussian_kde supports weights parameter
# - scipy >= 1.9.0: wasserstein_distance supports u_weights/v_weights parameters
MINIMUM_SCIPY_VERSION = "1.9.0"
if version.parse(scipy.__version__) < version.parse(MINIMUM_SCIPY_VERSION):
    raise ImportError(
        f"overlap_metrics requires scipy >= {MINIMUM_SCIPY_VERSION}, "
        f"but found scipy {scipy.__version__}. "
        f"Please upgrade: pip install 'scipy>={MINIMUM_SCIPY_VERSION}'"
    )

# Version info
__version__ = "1.0.0"
__author__ = "Photo Deduplication Team"
__description__ = "Distribution separation and overlap metrics with pluggable estimators"

# Default metric suite for compute_suite()
DEFAULT_SUITE: tuple[MetricName, ...] = (
    MetricName.SEPARATION_OVL,
    MetricName.BHATTACHARYYA_DISTANCE,
    MetricName.JENSEN_SHANNON,
    MetricName.HELLINGER,
    MetricName.TOTAL_VARIATION,
    MetricName.WASSERSTEIN_1D,
    MetricName.KS_STAT,
)


def compute_metric(
    samples: ScoreSamples | None = None,
    *,
    pos: ArrayLike1D | None = None,
    neg: ArrayLike1D | None = None,
    estimator: EstimatorName = EstimatorName.HIST,
    metric: MetricName = MetricName.SEPARATION_OVL,
    n_grid: int | None = None,
    dropna: bool = True,
    grid: str | None = None,
    weights_pos: npt.NDArray[np.float64] | None = None,
    weights_neg: npt.NDArray[np.float64] | None = None,
    random_state: int | None = None,
    **est_kwargs: Any,
) -> MetricResult:
    """Compute a single separation/overlap metric.

    Args:
            samples: Pre-constructed ScoreSamples object
            pos: Positive scores (alternative to samples)
            neg: Negative scores (alternative to samples)
            estimator: Density estimator to use
            metric: Metric to compute
            n_grid: Number of grid points for PDF integration
            dropna: Drop NaN values from pandas inputs
            grid: Grid type ('uniform' or 'edge_dense')
            weights_pos: Optional weights for positive samples
            weights_neg: Optional weights for negative samples
            random_state: Random seed for stochastic estimators
            **est_kwargs: Additional arguments for estimator constructor

    Returns:
            MetricResult with computed value and metadata
    """
    # Get config defaults
    config: OverlapMetricsConfig = get_config()
    if n_grid is None:
        n_grid = config.defaults.DEFAULT_N_GRID
    if grid is None:
        grid = config.defaults.DEFAULT_GRID_MODE

    # Resolve samples input
    if samples is None:
        if pos is None or neg is None:
            raise ValueError("Must provide either 'samples' or both 'pos' and 'neg'")
        samples = ScoreSamples.from_arrays(pos, neg, dropna=dropna, clip01=True)
    elif pos is not None or neg is not None:
        raise ValueError("Cannot provide both 'samples' and 'pos'/'neg' arguments")

    # Create estimator and metric instances
    estimator_instance: DensityEstimatorBase = create_estimator(estimator, **est_kwargs)
    metric_instance: MetricBase = create_metric(metric)

    # Compute metric
    result: MetricResult = metric_instance.from_samples(
        samples=samples,
        estimator=estimator_instance,
        n_grid=n_grid,
        grid=grid,
        weights_pos=weights_pos,
        weights_neg=weights_neg,
        random_state=random_state,
    )

    # Update estimator name in result
    return MetricResult(
        name=result.name,
        value=result.value,
        lower_is_better=result.lower_is_better,
        bounds=result.bounds,
        estimator_name=estimator.value,
        details=result.details,
        meta=result.meta,
    )


def compute_suite(
    samples: ScoreSamples | None = None,
    *,
    pos: ArrayLike1D | None = None,
    neg: ArrayLike1D | None = None,
    estimator: EstimatorName = EstimatorName.HIST,
    metric_names: tuple[MetricName, ...] = DEFAULT_SUITE,
    n_grid: int | None = None,
    dropna: bool = True,
    grid: str | None = None,
    weights_pos: npt.NDArray[np.float64] | None = None,
    weights_neg: npt.NDArray[np.float64] | None = None,
    random_state: int | None = None,
    **est_kwargs: Any,
) -> list[MetricResult]:
    """Compute multiple separation/overlap metrics efficiently.

    Args:
            samples: Pre-constructed ScoreSamples object
            pos: Positive scores (alternative to samples)
            neg: Negative scores (alternative to samples)
            estimator: Density estimator to use
            metric_names: Tuple of metrics to compute
            n_grid: Number of grid points for PDF integration
            dropna: Drop NaN values from pandas inputs
            grid: Grid type ('uniform' or 'edge_dense')
            weights_pos: Optional weights for positive samples
            weights_neg: Optional weights for negative samples
            random_state: Random seed for stochastic estimators
            **est_kwargs: Additional arguments for estimator constructor

    Returns:
            List of MetricResult objects, one per requested metric
    """
    # Get config defaults
    config: OverlapMetricsConfig = get_config()
    if n_grid is None:
        n_grid = config.defaults.DEFAULT_N_GRID
    if grid is None:
        grid = config.defaults.DEFAULT_GRID_MODE

    # Resolve samples input
    if samples is None:
        if pos is None or neg is None:
            raise ValueError("Must provide either 'samples' or both 'pos' and 'neg'")
        samples = ScoreSamples.from_arrays(pos, neg, dropna=dropna, clip01=True)
    elif pos is not None or neg is not None:
        raise ValueError("Cannot provide both 'samples' and 'pos'/'neg' arguments")

    # Compute each metric
    results: list[MetricResult] = []
    metric_name: MetricName
    for metric_name in metric_names:
        result: MetricResult = compute_metric(
            samples=samples,
            estimator=estimator,
            metric=metric_name,
            n_grid=n_grid,
            dropna=False,  # Already handled above
            grid=grid,
            weights_pos=weights_pos,
            weights_neg=weights_neg,
            random_state=random_state,
            **est_kwargs,
        )
        results.append(result)

    return results


def bootstrap_metric(
    samples: ScoreSamples,
    metric: MetricName,
    *,
    estimator: EstimatorName = EstimatorName.HIST,
    n_boot: int | None = None,
    ci: float | None = None,
    random_state: int | None = None,
    n_grid: int | None = None,
    grid: str | None = None,
    **est_kwargs: Any,
) -> MetricResult:
    """Compute metric with bootstrap confidence intervals.

    Args:
            samples: ScoreSamples object
            metric: Metric to compute
            estimator: Density estimator to use
            n_boot: Number of bootstrap samples
            ci: Confidence interval level (e.g., 0.95 for 95%)
            random_state: Random seed for reproducibility
            n_grid: Number of grid points for PDF integration
            grid: Grid type ('uniform' or 'edge_dense')
            **est_kwargs: Additional arguments for estimator constructor

    Returns:
            MetricResult with CI bounds in details dict
    """
    # Get config defaults
    config: OverlapMetricsConfig = get_config()
    if n_boot is None:
        n_boot = config.defaults.BOOTSTRAP_N_BOOT
    if ci is None:
        ci = config.defaults.BOOTSTRAP_CI
    if random_state is None:
        random_state = config.defaults.BOOTSTRAP_RANDOM_STATE
    if n_grid is None:
        n_grid = config.defaults.DEFAULT_N_GRID
    if grid is None:
        grid = config.defaults.DEFAULT_GRID_MODE

    rng: np.random.RandomState = np.random.RandomState(random_state)

    n_pos: int = len(samples.pos)
    n_neg: int = len(samples.neg)

    bootstrap_values: list[float] = []

    # Generate bootstrap replicates
    for _i in range(n_boot):
        # Resample with replacement
        pos_indices: npt.NDArray[np.int_] = rng.choice(n_pos, size=n_pos, replace=True)
        neg_indices: npt.NDArray[np.int_] = rng.choice(n_neg, size=n_neg, replace=True)

        boot_samples: ScoreSamples = ScoreSamples(
            pos=samples.pos[pos_indices],
            neg=samples.neg[neg_indices],
        )

        # Compute metric on bootstrap sample
        result: MetricResult = compute_metric(
            samples=boot_samples,
            estimator=estimator,
            metric=metric,
            n_grid=n_grid,
            grid=grid,
            random_state=None,  # Let each bootstrap use different randomness
            **est_kwargs,
        )

        bootstrap_values.append(result.value)

    # Compute original metric
    original_result: MetricResult = compute_metric(
        samples=samples,
        estimator=estimator,
        metric=metric,
        n_grid=n_grid,
        grid=grid,
        random_state=random_state,
        **est_kwargs,
    )

    # Compute percentile CI
    alpha: float = 1.0 - ci
    ci_low: float = float(np.percentile(bootstrap_values, 100 * alpha / 2))
    ci_high: float = float(np.percentile(bootstrap_values, 100 * (1 - alpha / 2)))

    # Add CI to details
    updated_details: dict[str, float] = {
        **original_result.details,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_level": ci,
    }

    return MetricResult(
        name=original_result.name,
        value=original_result.value,
        lower_is_better=original_result.lower_is_better,
        bounds=original_result.bounds,
        estimator_name=original_result.estimator_name,
        details=updated_details,
        meta=original_result.meta,
    )


# Export public API
__all__ = [
    "DEFAULT_SUITE",
    # Core types
    "ArrayLike1D",
    "EstimatorName",
    "MetricName",
    "MetricResult",
    "ScoreSamples",
    "__author__",
    "__description__",
    # Version info
    "__version__",
    "bootstrap_metric",
    # High-level API
    "compute_metric",
    "compute_suite",
    # Configuration
    "configure",
    # Factories (for advanced usage)
    "create_estimator",
    "create_metric",
]
