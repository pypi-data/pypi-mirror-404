"""Self-contained configuration for overlap_metrics library.

This module provides internal configuration with frozen dataclasses.
Parent projects can customize settings via the configure() function.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumericsConfig:
    """Numerical computation constants."""

    # Floating point precision
    DTYPE_FLOAT: str = "float64"

    # Safe floors for logarithms and divisions
    LOG_FLOOR: float = 1e-300
    DIVISION_FLOOR: float = 1e-300

    # Integration tolerance for PDF normalization check
    INTEGRAL_TOLERANCE: float = 1e-3

    # Default clipping bounds for scores
    SCORE_MIN: float = 0.0
    SCORE_MAX: float = 1.0

    # Default epsilon for Beta/Logit transforms
    TRANSFORM_EPS: float = 1e-6


@dataclass(frozen=True)
class DefaultConfig:
    """Default parameters for estimators and metrics."""

    # Grid parameters
    DEFAULT_N_GRID: int = 2000
    DEFAULT_GRID_MODE: str = "uniform"

    # Histogram estimator
    HIST_N_BINS: int = 100
    HIST_SMOOTH: bool = True

    # Beta estimator
    BETA_EPS: float = 1e-6

    # Logit KDE estimator
    LOGIT_KDE_EPS: float = 1e-6

    # Bootstrap parameters
    BOOTSTRAP_N_BOOT: int = 500
    BOOTSTRAP_CI: float = 0.95
    BOOTSTRAP_RANDOM_STATE: int = 42


@dataclass(frozen=True)
class ValidationConfig:
    """Validation and error checking parameters."""

    # Minimum sample sizes
    MIN_SAMPLES: int = 2

    # Maximum allowed grid size (memory protection)
    MAX_GRID_SIZE: int = 100_000


@dataclass(frozen=True)
class OverlapMetricsConfig:
    """Complete configuration for overlap_metrics library."""

    numerics: NumericsConfig
    defaults: DefaultConfig
    validation: ValidationConfig


# Global configuration instance (can be replaced via configure())
_config = OverlapMetricsConfig(numerics=NumericsConfig(), defaults=DefaultConfig(), validation=ValidationConfig())


def get_config() -> OverlapMetricsConfig:
    """Get current configuration instance.

    Returns:
            Current OverlapMetricsConfig instance
    """
    return _config


def _update_convenience_accessors() -> None:
    """Update module-level convenience accessors after configure()."""
    global NUMERICS, DEFAULTS, VALIDATION  # noqa: PLW0603
    # Standard library config pattern (like logging.basicConfig)
    config = get_config()
    NUMERICS = config.numerics
    DEFAULTS = config.defaults
    VALIDATION = config.validation


def configure(
    numerics: NumericsConfig | None = None,
    defaults: DefaultConfig | None = None,
    validation: ValidationConfig | None = None,
) -> None:
    """Configure overlap_metrics library settings.

    Creates new frozen config instances and updates the global configuration.
    Pass None for any section to keep existing settings.

    Args:
            numerics: Numerical computation settings
            defaults: Default parameters for estimators/metrics
            validation: Validation parameters

    Example:
            >>> from overlap_metrics.config import configure, DefaultConfig
            >>> configure(defaults=DefaultConfig(DEFAULT_N_GRID=5000))
    """
    global _config  # noqa: PLW0603
    # Standard library config pattern (like logging.basicConfig)

    new_numerics = numerics if numerics is not None else _config.numerics
    new_defaults = defaults if defaults is not None else _config.defaults
    new_validation = validation if validation is not None else _config.validation

    _config = OverlapMetricsConfig(numerics=new_numerics, defaults=new_defaults, validation=new_validation)

    _update_convenience_accessors()


# Convenience accessors for backward compatibility
NUMERICS = get_config().numerics
DEFAULTS = get_config().defaults
VALIDATION = get_config().validation
