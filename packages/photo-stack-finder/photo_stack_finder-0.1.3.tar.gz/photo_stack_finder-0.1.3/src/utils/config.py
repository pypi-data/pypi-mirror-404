"""Global configuration for photo_dedup project."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from photo_compare import ComparisonMethodName


@dataclass
class ProcessingConfig:
    """Configuration for processing and parallelism."""

    # Worker pool settings
    MAX_WORKERS: int = os.cpu_count() or -1
    DEBUG_MODE: bool = False
    BATCH_SIZE: int = 256

    # Random seeds for reproducibility
    DEFAULT_RANDOM_SEED: int = 12345

    # Sequential gates configuration (order matters)
    # Gates are executed in order, short-circuiting on first failure
    # "aspect_ratio" is special gate, others are photo_compare methods
    COMPARISON_GATES: list[str] = field(default_factory=lambda: ["aspect_ratio", "dhash", "ssim"])

    # Gate thresholds (override defaults when specified)
    # Gates read from here first, fall back to DEFAULT_THRESHOLDS
    GATE_THRESHOLDS: dict[str, float] | None = None

    # Default thresholds for all gates (used when not in GATE_THRESHOLDS)
    DEFAULT_THRESHOLDS: dict[str, float] = field(
        default_factory=lambda: {
            # Hash methods
            "ahash": 0.95,
            "dhash": 0.75,
            "phash": 0.72,
            "whash": 0.97,
            # Feature methods
            "sift": 0.62,
            "akaze": 0.67,
            "orb": 0.56,
            "brisk": 1.52,
            # Structural methods
            "ssim": 0.90,
            "ms_ssim": 0.66,
            "hog": 0.83,
            # Histogram methods
            "colour_histogram": 0.75,
            "hsv_histogram": 0.75,
            # Pixel methods
            "mse": 0.85,
            "psnr": 0.85,
        }
    )

    # Aspect ratio threshold (special gate)
    ASPECT_RATIO_THRESHOLD: float = 0.98

    # Rotation matching configuration
    ROTATION_ANGLES: list[int] = field(default_factory=lambda: [90, 180, 270])

    def __post_init__(self) -> None:
        """Initialize GATE_THRESHOLDS after dataclass init."""
        if self.GATE_THRESHOLDS is None:
            self.GATE_THRESHOLDS = {
                "aspect_ratio": self.ASPECT_RATIO_THRESHOLD,
                "dhash": 0.80,
                "ssim": 0.95,
            }

    # Benchmark settings
    TARGET_FPR: float = 0.00075  # Target false positive rate for benchmark thresholds

    # Logging configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL  # DEBUG, INFO, WARNING, ERROR, CRITICAL  # DEBUG, INFO, WARNING, ERROR, CRITICAL  # DEBUG, INFO, WARNING, ERROR, CRITICAL  # DEBUG, INFO, WARNING, ERROR, CRITICAL  # DEBUG, INFO, WARNING, ERROR, CRITICAL


@dataclass
class SequenceConfig:
    """Configuration for sequence analysis and versioning."""

    # Cramér's V threshold for considering columns associated
    MIN_ASSOCIATION: float = 0.2

    # Maximum mismatches allowed when testing version dimensions
    MAX_MISMATCHES: int = 2

    # Sequence matching configuration
    MAX_COMPONENT_SIZE: int = 10  # Skip components larger than this
    MAX_SEQUENCE_MISMATCHES: int = 2  # Max mismatches to accept sequence match

    # Perceptual matching configuration
    PERCEPTUAL_METHOD: ComparisonMethodName = "ahash"  # Which method to use for binning
    PERCEPTUAL_HAMMING_DISTANCE: int = 8  # Max hamming distance for bin membership
    BURST_REDUCTION: bool = True  # Reduce connections in photo bursts


@dataclass
class PathsConfig:
    """File and directory paths configuration."""

    SOURCE_DIR: str = ""
    WORK_DIR: str = ""
    WORK_DIR_NAME: str = "photo_dedup"

    # ALL filenames are now consistently abstracted as configurable constants
    # Pipeline data files
    SHA_BINS: str = "sha_bins.pkl"
    IDENTICAL: str = "identical.pkl"
    NONIDENTICAL: str = "nonidentical.pkl"
    TEMPLATE_BINS: str = "template_bins.pkl"
    FOREST_VERSIONS: str = "forest_versions.pkl"
    FOREST_TEMPLATE_SIMILARITY: str = "forest_template_similarity.pkl"
    FOREST_SEQUENCE_MATCHES: str = "forest_sequence_matches.pkl"
    PERCEPTUAL_HASH_BINS: str = "perceptual_hash_bins.pkl"
    FOREST_FINAL: str = "forest_final.pkl"
    ARGS: str = "args.json"

    # Benchmarking output files
    BENCHMARK_SCORES: str = "benchmark_scores.pkl"  # Benchmark stage cache file
    BENCHMARK_RESULTS: str = "benchmark_results.csv"
    BENCHMARK_JSON: str = "benchmark_results.json"
    BENCHMARK_SUMMARY: str = "benchmark_summary.json"
    # Additional benchmark analysis files
    PAIR_SCORES: str = "pair_scores.csv"
    PAIR_GROUND_TRUTH: str = "pair_ground_truth.csv"
    CASCADE_COMPARISON: str = "cascade_comparison.csv"
    METHOD_METRICS: str = "method_metrics.csv"
    METHOD_CORRELATIONS: str = "method_correlations.csv"

    # Analysis output files
    ANALYSIS_REPORT: str = "analysis_report.txt"
    ANALYSIS_RECOMMENDATIONS: str = "analysis_recommendations.txt"
    PAIRS_SAMPLE: str = "pairs_sample.csv"

    # Review output files
    REVIEW_IDENTICAL: str = "review_identical.json"  # Fixed typo from REVIEW_IDENTIICAL
    REVIEW_SEQUENCES: str = "review_sequences.json"

    # Photo sidecar file extensions
    GOOGLE_SIDECAR_SUFFIX: str = ".json"
    XMP_SIDECAR_SUFFIX: str = ".xmp"
    SUPPLEMENTAL_SIDECAR_SUFFIX: str = ".supplemental-metadata.json"

    @property
    def source_dir(self) -> Path:
        """Source directory containing photos to process."""
        return Path(self.SOURCE_DIR)

    @property
    def work_dir(self) -> Path:
        """Work directory for intermediate and output files."""
        return Path(self.WORK_DIR)

    # Pipeline data file paths (using abstracted filenames)
    @property
    def sha_bins_pkl(self) -> Path:
        """Path to SHA256 bins pickle file."""
        return Path(self.WORK_DIR) / self.SHA_BINS

    @property
    def identical_pkl(self) -> Path:
        """Path to identical file classes pickle."""
        return Path(self.WORK_DIR) / self.IDENTICAL

    @property
    def nonidentical_pkl(self) -> Path:
        """Path to nonidentical exemplars pickle."""
        return Path(self.WORK_DIR) / self.NONIDENTICAL

    @property
    def template_bins_pkl(self) -> Path:
        """Path to template bins pickle file."""
        return Path(self.WORK_DIR) / self.TEMPLATE_BINS

    @property
    def forest_versions_pkl(self) -> Path:
        """Path to version detection results (forest after version grouping)."""
        return Path(self.WORK_DIR) / self.FOREST_VERSIONS

    @property
    def forest_template_similarity_pkl(self) -> Path:
        """Path to template similarity results (forest after template grouping)."""
        return Path(self.WORK_DIR) / self.FOREST_TEMPLATE_SIMILARITY

    @property
    def forest_sequence_matches_pkl(self) -> Path:
        """Path to sequence matching results (forest after index-based grouping)."""
        return Path(self.WORK_DIR) / self.FOREST_SEQUENCE_MATCHES

    @property
    def perceptual_hash_bins_pkl(self) -> Path:
        """Path to perceptual hash bins (intermediate data for perceptual matching)."""
        return Path(self.WORK_DIR) / self.PERCEPTUAL_HASH_BINS

    @property
    def forest_final_pkl(self) -> Path:
        """Path to final forest (complete pipeline output with all groupings applied)."""
        return Path(self.WORK_DIR) / self.FOREST_FINAL

    @property
    def args_json(self) -> Path:
        """Path to command-line arguments JSON file."""
        return Path(self.WORK_DIR) / self.ARGS

    # Benchmarking file paths (using abstracted filenames)
    @property
    def benchmark_scores_pkl(self) -> Path:
        """Path to benchmark scores pickle (stage cache file)."""
        return Path(self.WORK_DIR) / self.BENCHMARK_SCORES

    @property
    def benchmark_results_csv(self) -> Path:
        """Path to benchmark results CSV file."""
        return Path(self.WORK_DIR) / self.BENCHMARK_RESULTS

    @property
    def benchmark_results_json(self) -> Path:
        """Path to benchmark results JSON file."""
        return Path(self.WORK_DIR) / self.BENCHMARK_JSON

    @property
    def benchmark_summary_json(self) -> Path:
        """Path to benchmark summary JSON file."""
        return Path(self.WORK_DIR) / self.BENCHMARK_SUMMARY

    @property
    def pair_scores_csv(self) -> Path:
        """Path to pair-level scores CSV file."""
        return Path(self.WORK_DIR) / self.PAIR_SCORES

    @property
    def pair_ground_truth_csv(self) -> Path:
        """Path to pair ground truth CSV file."""
        return Path(self.WORK_DIR) / self.PAIR_GROUND_TRUTH

    @property
    def cascade_comparison_csv(self) -> Path:
        """Path to cascade comparison CSV file."""
        return Path(self.WORK_DIR) / self.CASCADE_COMPARISON

    @property
    def method_metrics_csv(self) -> Path:
        """Path to method metrics CSV file."""
        return Path(self.WORK_DIR) / self.METHOD_METRICS

    @property
    def method_correlations_csv(self) -> Path:
        """Path to method correlations CSV file."""
        return Path(self.WORK_DIR) / self.METHOD_CORRELATIONS

    # Analysis file paths (using abstracted filenames)
    @property
    def analysis_report_txt(self) -> Path:
        """Path to analysis report text file."""
        return Path(self.WORK_DIR) / self.ANALYSIS_REPORT

    @property
    def analysis_recommendations_txt(self) -> Path:
        """Path to analysis recommendations text file."""
        return Path(self.WORK_DIR) / self.ANALYSIS_RECOMMENDATIONS

    @property
    def pairs_sample_csv(self) -> Path:
        """Path to pairs sample CSV file."""
        return Path(self.WORK_DIR) / self.PAIRS_SAMPLE

    # Review file paths
    @property
    def review_identical_json(self) -> Path:
        """Path to review identical files JSON."""
        return Path(self.WORK_DIR) / self.REVIEW_IDENTICAL

    @property
    def review_sequences_json(self) -> Path:
        """Path to review sequences JSON file."""
        return Path(self.WORK_DIR) / self.REVIEW_SEQUENCES


# FIXME: Do we need this?  Should it be shared with the orchestrator?  Should the orchestrator have something similar?
@dataclass
class ReviewServerConfig:
    """Configuration for review server."""

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    BROWSER: bool = True
    PAGE: str = "review_identical.html"


# Declarative mapping for update_from_args() to reduce complexity.
# Each tuple: arg name, config path, transform function, truthiness check.
# Reduces 15 hasattr() conditionals to single data-driven loop.
@dataclass
class BenchmarkConfig:
    """Configuration for benchmark stage."""

    # Stage enablement
    ENABLED: bool = False  # Whether to include benchmarks stage in pipeline

    # Pair generation
    N_DIFFERENT_PAIRS: int = 100000  # Number of different (dissimilar) pairs to generate

    # Memory management
    MAX_PREP_SIZE_BYTES: int = 8 * 1024 * 1024  # 8MB max size for prepared data
    MEMORY_FRACTION: float = 0.8  # Fraction of available memory to use for clustering


@dataclass
class OrchestratorConfig:
    """Configuration for orchestrator server and UI."""

    # Directory naming
    DEFAULT_WORK_DIR_NAME: str = "photo_dedup"  # Default work directory name (relative to source parent)

    # Static asset paths (computed relative to package)
    # These are set dynamically and should not be overridden
    STATIC_DIR: str | None = None
    DOCS_DIR: str | None = None


ARG_CONFIG_MAP: list[tuple[str, str, Any, bool]] = [
    # Paths
    ("source_dir", "paths.SOURCE_DIR", str, True),
    # Processing (excluding special cases: debug, workers, work_dir)
    ("log_level", "processing.LOG_LEVEL", lambda x: x.upper(), True),
    ("batch_size", "processing.BATCH_SIZE", None, False),
    ("seed", "processing.DEFAULT_RANDOM_SEED", int, False),
    ("target_fpr", "processing.TARGET_FPR", float, False),
    # Sequences
    ("binning_method", "sequences.PERCEPTUAL_METHOD", None, True),
    # Review server
    ("host", "review_server.HOST", None, True),
    ("port", "review_server.PORT", None, False),
    ("browser", "review_server.BROWSER", None, False),
    ("page", "review_server.PAGE", None, True),
]


@dataclass
class Config:
    """Global configuration for photo_dedup."""

    processing: ProcessingConfig
    sequences: SequenceConfig
    paths: PathsConfig
    review_server: ReviewServerConfig

    def __init__(self) -> None:
        """Initialize global configuration with default values."""
        self.processing = ProcessingConfig()
        self.sequences = SequenceConfig()
        self.paths = PathsConfig()
        self.review_server = ReviewServerConfig()
        self.benchmark = BenchmarkConfig()
        self.orchestrator = OrchestratorConfig()

    def update_from_args(self, args: Any) -> None:
        """Update configuration from command line arguments.

        Uses declarative ARG_CONFIG_MAP to reduce branching complexity
        and improve testability. Special cases (work_dir, debug, workers)
        are handled separately.

        Args:
            args: Parsed command line arguments from argparse (argparse.Namespace)
        """
        # Apply standard mappings from ARG_CONFIG_MAP
        for arg_name, config_path, transform_func, requires_truthy in ARG_CONFIG_MAP:
            if not hasattr(args, arg_name):
                continue

            value = getattr(args, arg_name)

            # Check truthiness if required (for "and args.x" pattern)
            if requires_truthy and not value:
                continue

            # Check for None if not requires_truthy (for "is not None" pattern)
            if not requires_truthy and value is None:
                continue

            # Apply transformation if specified
            if transform_func is not None:
                value = transform_func(value)

            # Resolve config path (e.g., "paths.SOURCE_DIR" -> self.paths.SOURCE_DIR)
            parts = config_path.split(".")
            obj = self
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)

        # Special case: work_dir (has default fallback)
        if hasattr(args, "work_dir") and args.work_dir:
            self.paths.WORK_DIR = str(args.work_dir)
        else:
            # Default: work_dir is sibling to source_dir with WORK_DIR_NAME
            default_work_dir: Path = Path(self.paths.SOURCE_DIR).parent / self.paths.WORK_DIR_NAME
            self.paths.WORK_DIR = str(default_work_dir)

        # Special case: debug (affects both DEBUG_MODE and LOG_LEVEL)
        if hasattr(args, "debug"):
            self.processing.DEBUG_MODE = args.debug
            if args.debug:
                self.processing.LOG_LEVEL = "DEBUG"

        # Special case: workers (fallback to cpu_count())
        if hasattr(args, "workers") and args.workers is not None:
            workers_count: int = args.workers or os.cpu_count() or 8
            self.processing.MAX_WORKERS = workers_count


# Global configuration instance
CONFIG = Config()
