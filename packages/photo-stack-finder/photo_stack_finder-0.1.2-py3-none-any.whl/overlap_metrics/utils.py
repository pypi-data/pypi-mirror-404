"""Utility functions for overlap_metrics library."""

from __future__ import annotations

from typing import cast

import numpy as np
from numpy.typing import NDArray

from .config import NUMERICS, VALIDATION


def make_grid(n_grid: int, mode: str) -> NDArray[np.float64]:
    """Create evaluation grid on [0,1] for numerical integration.

    Args:
            n_grid: Number of grid points
            mode: Grid type ('uniform' or 'edge_dense')

    Returns:
            Grid points as 1D array
    """
    if n_grid < 2:
        raise ValueError(f"Need at least 2 grid points, got {n_grid}")
    if n_grid > VALIDATION.MAX_GRID_SIZE:
        raise ValueError(f"Grid too large: {n_grid} > {VALIDATION.MAX_GRID_SIZE}")

    if mode == "uniform":
        return np.linspace(NUMERICS.SCORE_MIN, NUMERICS.SCORE_MAX, n_grid, dtype=NUMERICS.DTYPE_FLOAT)
    if mode == "edge_dense":
        # Dense grids near edges, coarser in middle
        quarter_size: int = n_grid // 4
        half_size: int = n_grid // 2
        remaining_size: int = n_grid - quarter_size - half_size

        left_edge: NDArray[np.float64] = np.linspace(0.0, 0.05, quarter_size, dtype=NUMERICS.DTYPE_FLOAT)
        middle: NDArray[np.float64] = np.linspace(0.05, 0.95, half_size, dtype=NUMERICS.DTYPE_FLOAT)
        right_edge: NDArray[np.float64] = np.linspace(0.95, 1.0, remaining_size, dtype=NUMERICS.DTYPE_FLOAT)

        return cast(NDArray[np.float64], np.unique(np.concatenate([left_edge, middle, right_edge])))
    raise ValueError(f"Unknown grid mode: {mode!r}")


def safe_log(x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Compute logarithm with safe floor to prevent -inf."""
    return cast(NDArray[np.float64], np.log(np.maximum(x, NUMERICS.LOG_FLOOR)))


def safe_divide(numerator: NDArray[np.float64], denominator: NDArray[np.float64]) -> NDArray[np.float64]:
    """Safe division with floor on denominator."""
    return cast(NDArray[np.float64], numerator / np.maximum(denominator, NUMERICS.DIVISION_FLOOR))


def kl_divergence(p: NDArray[np.float64], q: NDArray[np.float64], xs: NDArray[np.float64]) -> float:
    """Compute KL divergence KL(p||q) = ∫ p log(p/q) dx with safe handling."""
    # Only compute where p > 0 to avoid 0*log(0) issues
    mask: NDArray[np.bool_] = p > NUMERICS.LOG_FLOOR
    p_safe: NDArray[np.float64] = p[mask]
    q_safe: NDArray[np.float64] = np.maximum(q[mask], NUMERICS.LOG_FLOOR)
    xs_safe: NDArray[np.float64] = xs[mask]  # Actual x coordinates of remaining points

    if len(p_safe) == 0:
        return 0.0

    log_ratio: NDArray[np.float64] = safe_log(p_safe) - safe_log(q_safe)
    integrand: NDArray[np.float64] = p_safe * log_ratio

    # Use trapezoidal rule with actual x coordinates
    return float(np.trapezoid(integrand, xs_safe))


def validate_samples(samples: NDArray[np.float64], name: str) -> None:
    """Validate sample array properties."""
    if samples.ndim != 1:
        raise ValueError(f"{name} samples must be 1D, got shape {samples.shape}")
    if len(samples) < VALIDATION.MIN_SAMPLES:
        raise ValueError(f"{name} needs at least {VALIDATION.MIN_SAMPLES} samples, got {len(samples)}")
    if not np.all(np.isfinite(samples)):
        raise ValueError(f"{name} samples contain non-finite values")
    if not np.all((samples >= NUMERICS.SCORE_MIN) & (samples <= NUMERICS.SCORE_MAX)):
        raise ValueError(f"{name} samples must be in [{NUMERICS.SCORE_MIN}, {NUMERICS.SCORE_MAX}]")


def validate_weights(weights: NDArray[np.float64], n_samples: int, name: str) -> None:
    """Validate weight array properties."""
    if weights.ndim != 1:
        raise ValueError(f"{name} weights must be 1D, got shape {weights.shape}")
    if len(weights) != n_samples:
        raise ValueError(f"{name} weights length {len(weights)} != samples length {n_samples}")
    if not np.all(weights >= 0):
        raise ValueError(f"{name} weights must be non-negative")
    if not np.all(np.isfinite(weights)):
        raise ValueError(f"{name} weights contain non-finite values")
    if np.sum(weights) <= 0:
        raise ValueError(f"{name} weights must have positive sum")


def check_pdf_normalization(estimator_name: str, integral_value: float) -> None:
    """Check that PDF integrates to approximately 1."""
    if abs(integral_value - 1.0) > NUMERICS.INTEGRAL_TOLERANCE:
        raise RuntimeError(
            f"PDF for {estimator_name} integrates to {integral_value:.6f}, "
            f"expected ~1.0 (tolerance {NUMERICS.INTEGRAL_TOLERANCE})"
        )
