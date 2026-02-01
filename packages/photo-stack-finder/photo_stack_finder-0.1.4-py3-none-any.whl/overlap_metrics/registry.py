"""Registry and factory pattern for overlap_metrics library."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from .core import DensityEstimatorBase, EstimatorName, MetricBase, MetricName
from .estimators import BetaEstimator, BetaMixtureEstimator, HistogramEstimator, LogitKDEEstimator
from .metrics import (
    BhattacharyyaDistance,
    HellingerDistance,
    JensenShannon,
    KSStatistic,
    SeparationOVL,
    TotalVariation,
    Wasserstein1D,
)

T = TypeVar("T")


@dataclass
class Registry[T]:
    """Generic registry for factory pattern."""

    _ctors: dict[str, Callable[..., T]] = field(default_factory=dict)

    def register(self, name: str, ctor: Callable[..., T]) -> None:
        """Register a constructor function."""
        if name in self._ctors:
            raise ValueError(f"Duplicate registration: {name!r}")
        self._ctors[name] = ctor

    def create(self, name: str, **kwargs: Any) -> T:
        """Create instance by name with keyword arguments."""
        if name not in self._ctors:
            known_names: list[str] = sorted(self._ctors.keys())
            raise ValueError(f"Unknown key: {name!r}. Known: {known_names}")
        return self._ctors[name](**kwargs)

    def list_available(self) -> list[str]:
        """List all available registered names."""
        return sorted(self._ctors.keys())


# Create registry instances
estimator_registry: Registry[DensityEstimatorBase] = Registry()
metric_registry: Registry[MetricBase] = Registry()


def _populate_estimator_registry() -> None:
    """Populate estimator registry with default implementations."""
    estimator_registry.register(EstimatorName.HIST.value, lambda **kwargs: HistogramEstimator(**kwargs))
    estimator_registry.register(EstimatorName.BETA.value, lambda **kwargs: BetaEstimator(**kwargs))
    estimator_registry.register(EstimatorName.LOGIT_KDE.value, lambda **kwargs: LogitKDEEstimator(**kwargs))
    estimator_registry.register(EstimatorName.BETA_MIX.value, lambda **kwargs: BetaMixtureEstimator(**kwargs))


def _populate_metric_registry() -> None:
    """Populate metric registry with default implementations."""
    metric_registry.register(MetricName.SEPARATION_OVL.value, lambda: SeparationOVL())
    metric_registry.register(MetricName.BHATTACHARYYA_DISTANCE.value, lambda: BhattacharyyaDistance())
    metric_registry.register(MetricName.JENSEN_SHANNON.value, lambda: JensenShannon())
    metric_registry.register(MetricName.HELLINGER.value, lambda: HellingerDistance())
    metric_registry.register(MetricName.TOTAL_VARIATION.value, lambda: TotalVariation())
    metric_registry.register(MetricName.WASSERSTEIN_1D.value, lambda: Wasserstein1D())
    metric_registry.register(MetricName.KS_STAT.value, lambda: KSStatistic())


def create_estimator(name: EstimatorName, **kwargs: Any) -> DensityEstimatorBase:
    """Create density estimator by enum name.

    Args:
            name: EstimatorName enum value
            **kwargs: Constructor arguments for the estimator

    Returns:
            Configured estimator instance
    """
    return estimator_registry.create(name.value, **kwargs)


def create_metric(name: MetricName) -> MetricBase:
    """Create metric by enum name.

    Args:
            name: MetricName enum value

    Returns:
            Metric instance
    """
    return metric_registry.create(name.value)


# Populate registries on import
_populate_estimator_registry()
_populate_metric_registry()
