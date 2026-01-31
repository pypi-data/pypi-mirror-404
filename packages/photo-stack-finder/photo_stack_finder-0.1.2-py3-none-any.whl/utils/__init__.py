"""Utilities for photo deduplication."""

from __future__ import annotations

from .base_pipeline_stage import BasePipelineStage

# Port-based connectivity exports (Phase 1: Infrastructure)
from .base_ports import BaseInputPort, BaseOutputPort
from .channel import Channel

# Comparison gates exports
from .comparison_gates import (
    AspectRatioGate,
    BaseGate,
    ComparisonGate,
    GateName,
    GateSequence,
    MethodGate,
)

# Pipeline stage implementations
from .compute_benchmarks import ComputeBenchmarks
from .compute_identical import ComputeIdentical
from .compute_indices import ComputeIndices
from .compute_perceptual_hash import ComputePerceptualHash
from .compute_perceptual_match import ComputePerceptualMatch
from .compute_sha_bins import ComputeShaBins
from .compute_template_similarity import ComputeTemplateSimilarity
from .compute_templates import ComputeTemplates
from .compute_versions import ComputeVersions

# Config module exports
from .config import (
    CONFIG,
    Config,
    PathsConfig,
    ProcessingConfig,
    SequenceConfig,
)

# Data I/O utilities
from .data_io import load_required_csv, save_dataframe_with_logging

# Logger module exports
from .logger import LOGGER_T, get_logger

# Pipeline stage and progress tracker exports
from .models import (
    BrowseResponse,
    ConfigDefaultsResponse,
    DirectoryInfo,
    IdenticalGroup,
    IdenticalGroupsResponse,
    IdenticalPhoto,
    PipelineStartResponse,
    PipelineStatusResponse,
    PipelineStopResponse,
    ReviewAvailabilityInfo,
    ReviewAvailabilityResponse,
    ReviewLoadResponse,
    ReviewSaveResponse,
    ReviewSessionData,
    ReviewStatusResponse,
    ReviewType,
    SequenceGroup,
    SequenceGroupsResponse,
    SequenceInfo,
    SequencePhoto,
    SequenceRow,
    ServerQuitResponse,
    ShutdownResponse,
    StageDetail,
)

# PhotoFile module exports
from .photo_file import (
    PhotoFile,
    PreferenceTuple,
    load_json_sidecar,
    pick_exemplar_from_class,
)

# Pipeline building
from .pipeline_graph import PipelineGraph
from .pipeline_stage import PipelineStage, atomic_pickle_dump, atomic_pickle_load

# Plotting utilities
from .plot_helpers import (
    save_correlation_heatmap,
    save_histogram_comparison,
    save_pca_scatter,
)
from .ports import InputPort, OutputPort
from .progress import ProgressInfo, ProgressTracker, format_seconds_weighted

# Report generation
from .report_builder import ReportBuilder

# Sequence exports
from .sequence import (
    INDEX_T,
    PhotoFileSeries,
    PhotoSequence,
)

# Template module exports
from .template import (
    DefaultDict,
    partial_format,
)

__all__ = [
    # Config
    "CONFIG",
    # PhotoFile
    "INDEX_T",
    # Logger
    "LOGGER_T",
    # Pipeline Stage & Progress
    "AspectRatioGate",
    # Comparison Gates
    "BaseGate",
    # Ports (Base classes)
    "BaseInputPort",
    "BaseOutputPort",
    # Pipeline Stage Classes
    "BasePipelineStage",
    # Models - Response Types
    "BrowseResponse",
    "Channel",
    "ComparisonGate",
    "ComputeBenchmarks",
    "ComputeIdentical",
    "ComputeIndices",
    "ComputePerceptualHash",
    "ComputePerceptualMatch",
    "ComputeShaBins",
    "ComputeTemplateSimilarity",
    "ComputeTemplates",
    "ComputeVersions",
    # Configuration
    "Config",
    "ConfigDefaultsResponse",
    # Template
    "DefaultDict",
    "DirectoryInfo",
    "GateName",
    "GateSequence",
    # Models - Review Data
    "IdenticalGroup",
    "IdenticalGroupsResponse",
    "IdenticalPhoto",
    # Ports (Phase 1)
    "InputPort",
    "MethodGate",
    "OutputPort",
    "PathsConfig",
    "PhotoFile",
    "PhotoFileSeries",
    # Sequence
    "PhotoSequence",
    # Models - Pipeline Types
    "PipelineGraph",
    "PipelineStage",
    "PipelineStartResponse",
    "PipelineStatusResponse",
    "PipelineStopResponse",
    "PreferenceTuple",
    "ProcessingConfig",
    "ProgressInfo",
    "ProgressTracker",
    # Report utilities
    "ReportBuilder",
    # Models - Review Types
    "ReviewAvailabilityInfo",
    "ReviewAvailabilityResponse",
    "ReviewLoadResponse",
    "ReviewSaveResponse",
    "ReviewSessionData",
    "ReviewStatusResponse",
    "ReviewType",
    "SequenceConfig",
    "SequenceGroup",
    "SequenceGroupsResponse",
    "SequenceInfo",
    "SequencePhoto",
    "SequenceRow",
    # Models - Server Types
    "ServerQuitResponse",
    "ShutdownResponse",
    "StageDetail",
    "atomic_pickle_dump",
    # Pipeline building
    "atomic_pickle_load",
    # Parallel
    "compute_sha_bins",
    "compute_template_similarity",
    "format_seconds_weighted",
    "get_logger",
    "load_json_sidecar",
    # Data I/O utilities
    "load_required_csv",
    "partial_format",
    "pick_exemplar_from_class",
    # Plotting utilities
    "save_correlation_heatmap",
    "save_dataframe_with_logging",
    "save_histogram_comparison",
    "save_pca_scatter",
]
