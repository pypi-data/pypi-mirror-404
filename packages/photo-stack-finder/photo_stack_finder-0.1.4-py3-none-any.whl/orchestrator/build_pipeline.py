"""Pipeline construction using PipelineBuilder pattern.

This module constructs the complete photo deduplication pipeline using the
new port-based orchestration system.  All 8 stages are wired together via
Channel connections based on their InputPort/OutputPort declarations.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from utils import (
    CONFIG,
    Channel,
    ComputeBenchmarks,
    ComputeIdentical,
    ComputeIndices,
    ComputePerceptualHash,
    ComputePerceptualMatch,
    ComputeShaBins,
    ComputeTemplates,
    ComputeTemplateSimilarity,
    ComputeVersions,
    InputPort,
    PhotoFile,
)

from .pipeline_builder import PipelineBuilder
from .pipeline_orchestrator import PipelineOrchestrator


def build_pipeline(source_dir: Path) -> PipelineOrchestrator:
    """Build the complete photo deduplication pipeline.

    Constructs a pipeline graph with 8-9 stages connected via ports:
    1. ComputeShaBins - Hash files and bin by SHA256
    2. ComputeIdentical - Find byte-identical duplicates
    3. ComputeTemplates - Bin photos by filename template
    4. ComputeVersions - Detect version patterns in filenames
    5. ComputeTemplateSimilarity - Match photos with similar templates
    6. ComputeIndices - Find sequences with overlapping indices
    7. ComputePerceptualHash - Compute perceptual hashes and bin
    8. ComputePerceptualMatch - Match photos by perceptual hash similarity
    9. ComputeBenchmarks - (Optional, controlled by CONFIG.benchmark.ENABLED)

    Args:
        source_dir: Root directory containing photos to process

    Returns:
        PipelineOrchestrator ready for execution

    Raises:
        ValueError: If graph validation fails (unbound ports, cycles, etc.)
    """
    builder = PipelineBuilder()

    # FIXME: expected_photo_count=None everywhere.  Should this argument be removed?
    with builder:
        # SHA256 Hashing and Binning
        sha_bins_stage = ComputeShaBins(source_path=source_dir)

        # Identical Files Detection
        identical_stage = ComputeIdentical()
        Channel(sha_bins_stage.sha_bins_o, identical_stage.sha_bins_i)

        # Template Binning
        templates_stage = ComputeTemplates()
        Channel(identical_stage.nonidentical_o, templates_stage.nonidentical_photos_i)

        # Version Detection
        versions_stage = ComputeVersions()
        Channel(templates_stage.template_bins_o, versions_stage.template_bins_i)

        # Template Similarity
        template_similarity_stage = ComputeTemplateSimilarity()
        # Use the dedicated template_remainder_bins_o port
        Channel(
            versions_stage.template_remainder_bins_o,
            template_similarity_stage.template_bins_i,
        )

        # Index Overlap
        indices_stage = ComputeIndices()
        # Use the dedicated index_bins_o port
        Channel(template_similarity_stage.index_bins_o, indices_stage.index_bins_i)

        # Perceptual Hash Binning
        perceptual_hash_stage = ComputePerceptualHash()
        # Use the dedicated forest_o port from indices stage
        Channel(indices_stage.forest_o, perceptual_hash_stage.forest_i)

        # Perceptual Matching
        perceptual_match_stage = ComputePerceptualMatch()
        # ComputePerceptualMatch needs forest from indices and bins from perceptual_hash
        Channel(indices_stage.forest_o, perceptual_match_stage.forest_i)
        Channel(
            perceptual_hash_stage.perceptual_bins_o,
            perceptual_match_stage.perceptual_bins_i,
        )

        # Benchmark Comparison Methods (optional, controlled by CONFIG)
        if CONFIG.benchmark.ENABLED:
            benchmarks_stage = ComputeBenchmarks()
            Channel(perceptual_match_stage.final_forest_o, benchmarks_stage.forest_i)
            Channel[dict[int, PhotoFile]](
                sha_bins_stage.photofiles_o,
                cast(InputPort[dict[int, PhotoFile]], benchmarks_stage.photofiles_i),
            )

    # Builder __exit__ validates graph and creates orchestrator

    assert builder.orchestrator is not None, "Pipeline builder failed to create orchestrator"
    builder.orchestrator.get_photofiles = lambda: sha_bins_stage.photofiles
    return builder.orchestrator
