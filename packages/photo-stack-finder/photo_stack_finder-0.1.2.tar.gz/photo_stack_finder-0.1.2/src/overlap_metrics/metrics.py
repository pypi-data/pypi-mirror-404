"""Concrete separation/overlap metrics for overlap_metrics library."""

from __future__ import annotations

import time

import numpy as np
import numpy.typing as npt
from scipy import stats

from .config import NUMERICS
from .core import (
    PDF,
    DensityEstimatorBase,
    MetricBase,
    MetricResult,
    SampleBasedMetric,
    ScoreSamples,
)
from .utils import kl_divergence, make_grid


class SeparationOVL(MetricBase):
    """1 - Overlap coefficient: higher values = better separation."""

    def __init__(self) -> None:
        super().__init__(name="separation_ovl", lower_is_better=False, bounds=(0.0, 1.0))

    def from_pdfs(
        self,
        p: PDF,
        q: PDF,
        n_grid: int,
        grid: str,
    ) -> MetricResult:
        """Compute 1 - OVL where OVL = ∫ min(p,q) dx."""
        xs: npt.NDArray[np.float64] = make_grid(n_grid=n_grid, mode=grid)
        p_vals: npt.NDArray[np.float64] = np.maximum(p(xs), 0.0)
        q_vals: npt.NDArray[np.float64] = np.maximum(q(xs), 0.0)

        # Compute overlap coefficient
        min_vals: npt.NDArray[np.float64] = np.minimum(p_vals, q_vals)
        ovl: float = float(np.trapezoid(min_vals, xs))

        # Separation is 1 - overlap
        separation: float = 1.0 - ovl

        return MetricResult(
            name=self.name,
            value=separation,
            lower_is_better=self.lower_is_better,
            bounds=self.bounds,
            estimator_name="pdf_based",
            details={"ovl": ovl},
            meta={},
        )


class BhattacharyyaDistance(MetricBase):
    """Bhattacharyya distance: -ln(BC) where BC = ∫ sqrt(p*q) dx."""

    def __init__(self) -> None:
        super().__init__(
            name="bhattacharyya_distance",
            lower_is_better=False,
            bounds=(0.0, float("inf")),
        )

    def from_pdfs(
        self,
        p: PDF,
        q: PDF,
        n_grid: int,
        grid: str,
    ) -> MetricResult:
        """Compute Bhattacharyya distance."""
        xs: npt.NDArray[np.float64] = make_grid(n_grid=n_grid, mode=grid)
        p_vals: npt.NDArray[np.float64] = np.maximum(p(xs), 0.0)
        q_vals: npt.NDArray[np.float64] = np.maximum(q(xs), 0.0)

        # Compute Bhattacharyya coefficient
        sqrt_product: npt.NDArray[np.float64] = np.sqrt(p_vals * q_vals)
        bc: float = float(np.trapezoid(sqrt_product, xs))

        # Distance is -ln(BC) with safe floor
        bc_safe: float = max(bc, NUMERICS.LOG_FLOOR)
        db: float = -np.log(bc_safe)

        return MetricResult(
            name=self.name,
            value=db,
            lower_is_better=self.lower_is_better,
            bounds=self.bounds,
            estimator_name="pdf_based",
            details={"bc": bc},
            meta={},
        )


class JensenShannon(MetricBase):
    """Jensen-Shannon divergence normalized by ln(2)."""

    def __init__(self) -> None:
        super().__init__(name="js_divergence", lower_is_better=False, bounds=(0.0, 1.0))

    def from_pdfs(
        self,
        p: PDF,
        q: PDF,
        n_grid: int,
        grid: str,
    ) -> MetricResult:
        """Compute Jensen-Shannon divergence."""
        xs: npt.NDArray[np.float64] = make_grid(n_grid=n_grid, mode=grid)
        p_vals: npt.NDArray[np.float64] = np.maximum(p(xs), NUMERICS.LOG_FLOOR)
        q_vals: npt.NDArray[np.float64] = np.maximum(q(xs), NUMERICS.LOG_FLOOR)

        # Midpoint distribution
        m_vals: npt.NDArray[np.float64] = 0.5 * (p_vals + q_vals)

        # Compute uniform dx for KL calculations
        dx: float = xs[1] - xs[0] if len(xs) > 1 else 1.0
        dx_array: npt.NDArray[np.float64] = np.full_like(xs, dx)

        # JS = 0.5 * KL(P||M) + 0.5 * KL(Q||M)
        kl_pm: float = kl_divergence(p_vals, m_vals, dx_array)
        kl_qm: float = kl_divergence(q_vals, m_vals, dx_array)
        js_raw: float = 0.5 * kl_pm + 0.5 * kl_qm

        # Normalize by ln(2) to get value in [0,1]
        js_normalized: float = js_raw / np.log(2.0)

        return MetricResult(
            name=self.name,
            value=js_normalized,
            lower_is_better=self.lower_is_better,
            bounds=self.bounds,
            estimator_name="pdf_based",
            details={"js_raw": js_raw},
            meta={},
        )


class HellingerDistance(MetricBase):
    """Hellinger distance: sqrt(1 - BC) where BC is Bhattacharyya coefficient."""

    def __init__(self) -> None:
        super().__init__(name="hellinger_distance", lower_is_better=False, bounds=(0.0, 1.0))

    def from_pdfs(
        self,
        p: PDF,
        q: PDF,
        n_grid: int,
        grid: str,
    ) -> MetricResult:
        """Compute Hellinger distance."""
        xs: npt.NDArray[np.float64] = make_grid(n_grid=n_grid, mode=grid)
        p_vals: npt.NDArray[np.float64] = np.maximum(p(xs), 0.0)
        q_vals: npt.NDArray[np.float64] = np.maximum(q(xs), 0.0)

        # Compute Bhattacharyya coefficient
        sqrt_product: npt.NDArray[np.float64] = np.sqrt(p_vals * q_vals)
        bc: float = float(np.trapezoid(sqrt_product, xs))

        # Hellinger distance
        hellinger: float = np.sqrt(max(0.0, 1.0 - bc))

        return MetricResult(
            name=self.name,
            value=hellinger,
            lower_is_better=self.lower_is_better,
            bounds=self.bounds,
            estimator_name="pdf_based",
            details={"bc": bc},
            meta={},
        )


class TotalVariation(MetricBase):
    """Total variation distance: 0.5 * ∫ |p - q| dx."""

    def __init__(self) -> None:
        super().__init__(name="total_variation", lower_is_better=False, bounds=(0.0, 1.0))

    def from_pdfs(
        self,
        p: PDF,
        q: PDF,
        n_grid: int,
        grid: str,
    ) -> MetricResult:
        """Compute total variation distance."""
        xs: npt.NDArray[np.float64] = make_grid(n_grid=n_grid, mode=grid)
        p_vals: npt.NDArray[np.float64] = np.maximum(p(xs), 0.0)
        q_vals: npt.NDArray[np.float64] = np.maximum(q(xs), 0.0)

        # TV = 0.5 * ∫ |p - q| dx
        abs_diff: npt.NDArray[np.float64] = np.abs(p_vals - q_vals)
        tv: float = 0.5 * float(np.trapezoid(abs_diff, xs))

        return MetricResult(
            name=self.name,
            value=tv,
            lower_is_better=self.lower_is_better,
            bounds=self.bounds,
            estimator_name="pdf_based",
            details={},
            meta={},
        )


class Wasserstein1D(SampleBasedMetric):
    """1D Wasserstein distance computed directly from samples."""

    def __init__(self) -> None:
        super().__init__(name="wasserstein_1d", lower_is_better=False, bounds=(0.0, float("inf")))

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
        """Compute Wasserstein distance directly from samples."""
        start_time: float = time.perf_counter()

        # Use scipy's implementation
        if weights_pos is not None or weights_neg is not None:
            # scipy 1.9+ supports weights
            try:
                wasserstein_dist: float = stats.wasserstein_distance(
                    samples.pos,
                    samples.neg,
                    u_weights=weights_pos,
                    v_weights=weights_neg,
                )
            except TypeError:
                # Fallback for older scipy versions
                wasserstein_dist = stats.wasserstein_distance(samples.pos, samples.neg)
        else:
            wasserstein_dist = stats.wasserstein_distance(samples.pos, samples.neg)

        runtime_ms: float = (time.perf_counter() - start_time) * 1000.0

        return MetricResult(
            name=self.name,
            value=wasserstein_dist,
            lower_is_better=self.lower_is_better,
            bounds=self.bounds,
            estimator_name=estimator.name,
            details={},
            meta={
                "n_pos": float(len(samples.pos)),
                "n_neg": float(len(samples.neg)),
                "runtime_ms": runtime_ms,
            },
        )


class KSStatistic(SampleBasedMetric):
    """Kolmogorov-Smirnov test statistic (two-sample)."""

    def __init__(self) -> None:
        super().__init__(name="ks_stat", lower_is_better=False, bounds=(0.0, 1.0))

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
        """Compute KS statistic directly from samples."""
        start_time: float = time.perf_counter()

        # Note: scipy's ks_2samp doesn't support weights
        if weights_pos is not None or weights_neg is not None:
            # Could implement weighted KS in future, for now ignore weights
            pass

        # Compute KS statistic
        ks_result = stats.ks_2samp(samples.pos, samples.neg)
        ks_stat: float = float(ks_result.statistic)

        runtime_ms: float = (time.perf_counter() - start_time) * 1000.0

        return MetricResult(
            name=self.name,
            value=ks_stat,
            lower_is_better=self.lower_is_better,
            bounds=self.bounds,
            estimator_name=estimator.name,
            details={"p_value": float(ks_result.pvalue)},
            meta={
                "n_pos": float(len(samples.pos)),
                "n_neg": float(len(samples.neg)),
                "runtime_ms": runtime_ms,
            },
        )
