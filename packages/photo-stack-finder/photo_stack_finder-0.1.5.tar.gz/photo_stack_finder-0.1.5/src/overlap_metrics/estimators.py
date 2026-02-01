"""Density estimator implementations for overlap_metrics library."""

from __future__ import annotations

from typing import cast

import numpy as np
import numpy.typing as npt
from scipy import stats

from .config import DEFAULTS, NUMERICS
from .core import DensityEstimatorBase
from .utils import validate_samples, validate_weights


class HistogramEstimator(DensityEstimatorBase):
    """Histogram-based density estimator with optional smoothing."""

    def __init__(self, n_bins: int = DEFAULTS.HIST_N_BINS, smooth: bool = DEFAULTS.HIST_SMOOTH):
        """Create histogram estimator.

        Args:
                n_bins: Number of histogram bins
                smooth: Apply Laplace smoothing if True
        """
        super().__init__(name="hist")
        self.n_bins: int = n_bins
        self.smooth: bool = smooth
        self._bin_edges: npt.NDArray[np.float64] | None = None
        self._bin_densities: npt.NDArray[np.float64] | None = None

    def fit(
        self,
        samples: npt.NDArray[np.float64],
        weights: npt.NDArray[np.float64] | None = None,
        random_state: int | None = None,
    ) -> None:
        """Fit histogram to samples."""
        validate_samples(samples, self.name)
        if weights is not None:
            validate_weights(weights, len(samples), self.name)

        # Create histogram
        counts: npt.NDArray[np.float64]
        bin_edges: npt.NDArray[np.float64]
        counts, bin_edges = np.histogram(
            samples,
            bins=self.n_bins,
            range=(NUMERICS.SCORE_MIN, NUMERICS.SCORE_MAX),
            weights=weights,
        )

        # Apply Laplace smoothing if requested
        if self.smooth:
            counts = counts + 1.0

        # Normalize to get density (integral = 1)
        bin_widths: npt.NDArray[np.float64] = np.diff(bin_edges)
        densities: npt.NDArray[np.float64] = counts / (counts.sum() * bin_widths)

        self._bin_edges = bin_edges
        self._bin_densities = densities
        self._mark_fitted()

    def pdf(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Evaluate PDF at points x using piecewise constant histogram."""
        self._check_fitted()
        assert self._bin_edges is not None  # Guaranteed by _check_fitted()
        assert self._bin_densities is not None  # Guaranteed by _check_fitted()

        # Find which bin each x falls into
        bin_indices: npt.NDArray[np.int_] = np.searchsorted(self._bin_edges[:-1], x, side="right") - 1

        # Clip to valid range
        bin_indices = np.clip(bin_indices, 0, len(self._bin_densities) - 1)

        # Return density for each bin
        return self._bin_densities[bin_indices]


class BetaEstimator(DensityEstimatorBase):
    """Beta distribution estimator using method of moments."""

    def __init__(self, eps: float = DEFAULTS.BETA_EPS):
        """Create Beta estimator.

        Args:
                eps: Small value to add/subtract from bounds to avoid numerical issues
        """
        super().__init__(name="beta")
        self.eps: float = eps
        self._alpha: float | None = None
        self._beta: float | None = None

    def fit(
        self,
        samples: npt.NDArray[np.float64],
        weights: npt.NDArray[np.float64] | None = None,
        random_state: int | None = None,
    ) -> None:
        """Fit Beta distribution using method of moments."""
        validate_samples(samples, self.name)
        w: npt.NDArray[np.float64] | None
        if weights is not None:
            validate_weights(weights, len(samples), self.name)
            # Normalize weights
            w = weights / weights.sum()
        else:
            w = None

        # Transform samples away from boundaries
        samples_trans: npt.NDArray[np.float64] = np.clip(
            samples, NUMERICS.SCORE_MIN + self.eps, NUMERICS.SCORE_MAX - self.eps
        )

        # Compute weighted moments
        mean: float
        var: float
        if w is None:
            mean = float(np.mean(samples_trans))
            var = float(np.var(samples_trans))
        else:
            mean = float(np.sum(w * samples_trans))
            var = float(np.sum(w * (samples_trans - mean) ** 2))

        # Method of moments: solve for alpha, beta
        if var <= 0 or var >= mean * (1 - mean):
            # Fallback to uniform-ish distribution
            self._alpha = 1.0
            self._beta = 1.0
        else:
            common: float = mean * (1 - mean) / var - 1
            self._alpha = mean * common
            self._beta = (1 - mean) * common

            # Ensure positive parameters
            self._alpha = max(0.1, self._alpha)
            self._beta = max(0.1, self._beta)

        self._mark_fitted()

    def pdf(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Evaluate Beta PDF at points x."""
        self._check_fitted()
        assert self._alpha is not None and self._beta is not None  # Guaranteed by _check_fitted()

        # Clip to valid range
        x_clipped: npt.NDArray[np.float64] = np.clip(x, NUMERICS.SCORE_MIN + self.eps, NUMERICS.SCORE_MAX - self.eps)

        # Use scipy's beta distribution
        return stats.beta.pdf(x_clipped, self._alpha, self._beta)


class LogitKDEEstimator(DensityEstimatorBase):
    """KDE on logit-transformed [0,1] samples."""

    def __init__(self, eps: float = DEFAULTS.LOGIT_KDE_EPS):
        """Create Logit-KDE estimator.

        Args:
                eps: Small value to add/subtract from bounds before logit transform
        """
        super().__init__(name="logit_kde")
        self.eps: float = eps
        self._kde: stats.gaussian_kde | None = None

    def fit(
        self,
        samples: npt.NDArray[np.float64],
        weights: npt.NDArray[np.float64] | None = None,
        random_state: int | None = None,
    ) -> None:
        """Fit KDE to logit-transformed samples."""
        validate_samples(samples, self.name)
        if weights is not None:
            validate_weights(weights, len(samples), self.name)

        # Transform samples to avoid boundaries
        samples_trans: npt.NDArray[np.float64] = np.clip(
            samples, NUMERICS.SCORE_MIN + self.eps, NUMERICS.SCORE_MAX - self.eps
        )

        # Apply logit transform: logit(p) = log(p / (1-p))
        logit_samples: npt.NDArray[np.float64] = np.log(samples_trans / (1 - samples_trans))

        # Fit Gaussian KDE in logit space
        self._kde = stats.gaussian_kde(logit_samples, weights=weights)
        self._mark_fitted()

    def pdf(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Evaluate PDF using change of variables from logit space."""
        self._check_fitted()
        assert self._kde is not None  # Guaranteed by _check_fitted()

        # Clip to valid range
        x_clipped: npt.NDArray[np.float64] = np.clip(x, NUMERICS.SCORE_MIN + self.eps, NUMERICS.SCORE_MAX - self.eps)

        # Transform to logit space
        logit_x: npt.NDArray[np.float64] = np.log(x_clipped / (1 - x_clipped))

        # Evaluate KDE in logit space
        pdf_logit: npt.NDArray[np.float64] = cast(npt.NDArray[np.float64], self._kde(logit_x))

        # Apply Jacobian for change of variables: |d(logit(x))/dx| = 1/(x*(1-x))
        jacobian: npt.NDArray[np.float64] = 1.0 / (x_clipped * (1 - x_clipped))

        return pdf_logit * jacobian


class BetaMixtureEstimator(DensityEstimatorBase):
    """Beta mixture model with EM algorithm (placeholder implementation)."""

    def __init__(self, n_components: int = 2, max_iter: int = 100, eps: float = DEFAULTS.BETA_EPS):
        """Create Beta mixture estimator.

        Args:
                n_components: Number of mixture components
                max_iter: Maximum EM iterations
                eps: Small value for numerical stability
        """
        super().__init__(name="beta_mix")
        self.n_components: int = n_components
        self.max_iter: int = max_iter
        self.eps: float = eps
        self._weights: npt.NDArray[np.float64] | None = None
        self._alphas: npt.NDArray[np.float64] | None = None
        self._betas: npt.NDArray[np.float64] | None = None

    def fit(
        self,
        samples: npt.NDArray[np.float64],
        weights: npt.NDArray[np.float64] | None = None,
        random_state: int | None = None,
    ) -> None:
        """Fit Beta mixture using simple initialization (full EM not implemented)."""
        validate_samples(samples, self.name)
        if weights is not None:
            validate_weights(weights, len(samples), self.name)

        # Placeholder: fit single Beta as fallback
        # Full EM implementation would go here
        # random_state parameter reserved for future EM implementation

        # Transform samples away from boundaries
        samples_trans: npt.NDArray[np.float64] = np.clip(
            samples, NUMERICS.SCORE_MIN + self.eps, NUMERICS.SCORE_MAX - self.eps
        )

        # Simple initialization: fit one component
        mean: float
        var: float
        if weights is None:
            mean = float(np.mean(samples_trans))
            var = float(np.var(samples_trans))
        else:
            w: npt.NDArray[np.float64] = weights / weights.sum()
            mean = float(np.sum(w * samples_trans))
            var = float(np.sum(w * (samples_trans - mean) ** 2))

        alpha: float
        beta: float
        if var <= 0 or var >= mean * (1 - mean):
            alpha, beta = 1.0, 1.0
        else:
            common: float = mean * (1 - mean) / var - 1
            alpha = max(0.1, mean * common)
            beta = max(0.1, (1 - mean) * common)

        # Store as single-component mixture
        self._weights = np.array([1.0])
        self._alphas = np.array([alpha])
        self._betas = np.array([beta])

        self._mark_fitted()

    def pdf(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Evaluate mixture PDF as weighted sum of component PDFs."""
        self._check_fitted()
        assert self._weights is not None  # Guaranteed by _check_fitted()
        assert self._alphas is not None  # Guaranteed by _check_fitted()
        assert self._betas is not None  # Guaranteed by _check_fitted()

        # Clip to valid range
        x_clipped: npt.NDArray[np.float64] = np.clip(x, NUMERICS.SCORE_MIN + self.eps, NUMERICS.SCORE_MAX - self.eps)

        # Compute mixture: sum_k w_k * Beta(x; alpha_k, beta_k)
        pdf_vals: npt.NDArray[np.float64] = np.zeros_like(x_clipped)
        k: int
        for k in range(len(self._weights)):
            pdf_vals += self._weights[k] * stats.beta.pdf(x_clipped, self._alphas[k], self._betas[k])

        return pdf_vals
