"""Pydantic models for communicating across FastAPI.

Includes models for:
- pipeline configuration
- stage metadata
- review data
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Import PhotoFile for type annotations (no circular dependency)
# Import decision types for proper type annotations
from .review_types import IdenticalDecision, SequenceDecision

# Type alias for review types - used across pipeline stages and API models
# Defines what kind of review data a stage produces
ReviewType = Literal["none", "photos", "sequences"]


class PipelineConfig(BaseModel):
    """Model for the request body sent to /api/pipeline/start.

    Derived from the form inputs in orchestrator.html.
    """

    # Essential Parameters
    source_dir: str = Field(..., description="The directory containing source photos.")
    work_dir: str = Field(..., description="The directory to store intermediate and final results.")

    # Optimization Parameters (defaults are based on common practice)
    dry_run: bool = Field(False, description="If True, pipeline runs without making disk changes.")
    num_workers: int = Field(4, description="The number of worker processes to use for parallel tasks.")

    # You may need to add more configuration options here if they exist in CONFIG/utils
    # e.g., hash_algorithm: str = Field("perceptual", description="Hashing algorithm to use.")


class StageDetail(BaseModel):
    """Model for an individual stage returned by the /api/stages endpoint.

    Includes fields for dynamic review button generation.
    """

    stage_id: int = Field(..., description="The stable integer ID from topological sort (0-indexed)")
    stage_name: str = Field(
        ...,
        description="Stage name for both internal use and UI display",
    )
    description: str = Field(..., description="Description for UI tooltips")
    required: bool = Field(..., description="Whether this stage is required")

    # Critical fields for dynamic review interface
    produces_review: bool = Field(
        default=False,
        description="True if this stage generates results requiring user review",
    )
    review_type: ReviewType = Field(default="none", description="Type of review data produced")


class IdenticalGroupsResponse(BaseModel):
    """Response model for /api/review/identical/groups endpoint with pagination.

    Returns paginated identical photo groups with metadata for UI rendering.
    Each group contains photos that are byte-identical (same SHA256).
    """

    groups: list[IdenticalGroup] = Field(
        ...,
        description="Array of identical photo groups for current page",
    )
    page: int = Field(..., description="Current page number (0-indexed)")
    page_size: int = Field(..., description="Number of groups per page")
    total_groups: int = Field(..., description="Total number of groups across all pages")
    total_pages: int = Field(..., description="Total number of pages")
    has_more: bool = Field(..., description="Whether there are more pages available")


class SequenceGroupsResponse(BaseModel):
    """Response model for /api/review/sequences/groups endpoint.

    Returns sequence similarity groups for review UI. Each group represents
    a set of photo sequences that share similar template patterns or perceptual features.
    """

    groups: list[SequenceGroup] = Field(
        ...,
        description="Array of sequence groups with aligned photo sequences",
    )


# === Review API Endpoints ===


class ReviewAvailabilityInfo(BaseModel):
    """Info about review data availability for a single stage."""

    available: bool = Field(..., description="Whether review data is available")
    review_type: ReviewType = Field(..., description="Type of review data")


class ReviewAvailabilityResponse(BaseModel):
    """Response model for /api/review/availability endpoint."""

    stages: dict[int, ReviewAvailabilityInfo] = Field(..., description="Map of stage_id to availability info")


class ReviewLoadResponse(BaseModel):
    """Response model for /api/review/load endpoint."""

    status: Literal["success", "failed_but_continuing"] = Field(..., description="Load status")
    identical_count: int = Field(..., description="Number of identical photo groups")
    sequence_count: int = Field(..., description="Number of sequence groups")
    message: str | None = Field(None, description="Optional error message")


# === Directory Browser API ===


class DirectoryInfo(BaseModel):
    """Model for a directory entry in the browser."""

    name: str = Field(..., description="Directory name")
    path: str = Field(..., description="Full path to directory")


class BrowseResponse(BaseModel):
    """Response model for /api/browse endpoint."""

    current_path: str = Field(..., description="Current directory path")
    parent_path: str | None = Field(None, description="Parent directory path, None if at root")
    directories: list[DirectoryInfo] = Field(..., description="List of subdirectories")


# === Configuration API ===


class ConfigDefaultsResponse(BaseModel):
    """Response model for /api/config/defaults endpoint."""

    source_dir: str | None = Field(None, description="Source directory path")
    work_dir: str | None = Field(None, description="Work directory path")
    max_workers: int | None = Field(None, description="Maximum worker processes")
    batch_size: int | None = Field(None, description="Batch size for processing")
    debug_mode: bool = Field(False, description="Debug mode enabled")
    comparison_method: str = Field("SSIM", description="Comparison method to use")
    gate_thresholds: dict[str, float] = Field(default_factory=dict, description="Gate threshold values")
    enable_benchmarks: bool = Field(False, description="Enable benchmark stage")
    target_fpr: float = Field(0.00075, description="Target false positive rate")


# === Pipeline Control API ===


class PipelineStartResponse(BaseModel):
    """Response model for /api/pipeline/start endpoint."""

    status: str = Field(..., description="Status message")
    message: str = Field(..., description="Human-readable message")


class PipelineStatusResponse(BaseModel):
    """Response model for /api/status endpoint."""

    running: bool = Field(..., description="Whether pipeline is currently running")
    completed: bool = Field(False, description="Whether pipeline has completed")
    stage: str | None = Field(None, description="Current stage name")
    stage_number: int | None = Field(None, description="Current stage number")
    total_stages: int | None = Field(None, description="Total number of stages")
    message: str | None = Field(None, description="Status message")
    progress: float | None = Field(None, description="Progress percentage")
    error: str | None = Field(None, description="Error message if failed")


class PipelineStopResponse(BaseModel):
    """Response model for /api/pipeline/stop endpoint."""

    status: str = Field(..., description="Status of stop request")
    message: str = Field(..., description="Human-readable message")


class ServerQuitResponse(BaseModel):
    """Response model for /api/server/quit endpoint."""

    status: str = Field(..., description="Status of quit request")
    message: str = Field(..., description="Human-readable message")


class ShutdownResponse(BaseModel):
    """Response model for /api/shutdown endpoint."""

    status: str = Field(..., description="Status of shutdown request")


# === Review Status API ===


class ReviewStatusResponse(BaseModel):
    """Response model for /api/review/status endpoint."""

    loaded: bool = Field(..., description="Whether review data is loaded")
    identical_count: int = Field(0, description="Number of identical groups")
    sequence_count: int = Field(0, description="Number of sequence groups")


class ReviewSaveResponse(BaseModel):
    """Response model for /api/review/save and /api/review/sequences/save endpoints."""

    status: str = Field(..., description="Status of save operation")
    message: str = Field(..., description="Human-readable message")
    saved_count: int = Field(0, description="Number of items saved")


def _default_decisions() -> dict[str, dict[str, IdenticalDecision | SequenceDecision]]:
    """Default factory for review decisions dict."""
    return {"identical": {}, "sequences": {}}


class ReviewSessionData(BaseModel):
    """Internal model for review session storage.

    Stores review groups and metadata for a single stage or aggregated stages.
    Used in app.state.review_sessions dict.

    Note: photofiles dict is now stored in app.state.photofiles (shared globally)
    rather than per-session since it's identical for all stages.
    """

    identical_groups: list[IdenticalGroup] = Field(
        default_factory=list,
        description="Byte-identical photo groups (review_type='photos')",
    )
    sequence_groups: list[SequenceGroup] = Field(
        default_factory=list,
        description="Sequence similarity groups (review_type='sequences')",
    )
    decisions: dict[str, dict[str, IdenticalDecision | SequenceDecision]] = Field(
        default_factory=_default_decisions,
        description="User review decisions (identical and sequence decisions)",
    )
    review_type: str | None = Field(
        default=None,
        description="Type of review data in this session ('photos' or 'sequences')",
    )
    stage_name: str | None = Field(
        default=None,
        description="Name of stage this session belongs to (for per-stage sessions)",
    )


# === Photo Info API ===


class PhotoInfoResponse(BaseModel):
    """Response model for /api/review/photo_info/{photo_id} endpoint."""

    photo_id: int = Field(..., description="Photo ID")
    filename: str = Field(..., description="Filename")
    path: str = Field(..., description="Full path to photo")
    sha256: str | None = Field(None, description="SHA256 hash")
    width: int | None = Field(None, description="Image width in pixels")
    height: int | None = Field(None, description="Image height in pixels")
    file_size: int | None = Field(None, description="File size in bytes")
    created_date: str | None = Field(None, description="File creation date")


# =============================================================================
# Identical Group Models (for byte-identical photo review)
# =============================================================================


class IdenticalPhoto(BaseModel):
    """Model for a photo within an identical group.

    Represents a single photo that is byte-identical to other photos in the group.
    Includes all metadata needed for display (no lazy loading required).
    """

    id: int = Field(..., description="Photo ID")
    path: str = Field(..., description="Full path to photo file")
    filename: str = Field(..., description="Filename only")
    is_exemplar: bool = Field(..., description="Whether this photo is the chosen exemplar")
    file_size: int = Field(..., description="File size in bytes")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")


class IdenticalGroup(BaseModel):
    """Model for a group of byte-identical photos.

    Represents a set of photos that have identical SHA256 hashes and are verified
    to be byte-for-byte identical. Used in review UI for photo deduplication decisions.
    """

    group_id: str = Field(..., description="Stable group identifier (SHA256 hash of sorted photo SHA256s)")
    exemplar_id: int = Field(..., description="ID of the photo designated as exemplar")
    photos: list[IdenticalPhoto] = Field(..., description="List of all identical photos in group")
    is_identical: bool = Field(True, description="Always True for identical groups")
    confidence: str = Field("high", description="Confidence level (always 'high' for byte-identical)")


# =============================================================================
# Sequence Group Models (for sequence similarity review)
# =============================================================================


class SequenceInfo(BaseModel):
    """Metadata about a photo sequence within a group.

    Describes one of the sequences being compared in a sequence similarity group.
    """

    name: str = Field(..., description="Sequence name/path")
    parent_dir: str = Field(..., description="Parent directory of sequence")
    template_name: str = Field(..., description="Template pattern name")


class SequencePhoto(BaseModel):
    """Model for a photo within a sequence row.

    Represents a single photo at a specific position in a sequence,
    including its similarity score to the reference sequence and all
    metadata needed for display (no lazy loading required).
    """

    id: int = Field(..., description="Photo ID")
    filename: str = Field(..., description="Filename only")
    sequence_index: int = Field(..., description="Index of sequence this photo belongs to")
    is_exemplar: bool = Field(..., description="Whether this is from the reference sequence")
    similarity_score: float | None = Field(None, description="Similarity score to reference (0.0-1.0)")
    attention_test: bool = Field(False, description="Whether this is an attention test photo")
    file_size: int = Field(..., description="File size in bytes")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")


class SequenceRow(BaseModel):
    """Model for a row in a sequence comparison grid.

    Each row represents a position in the sequences being compared, with photos
    from each sequence at that position (or None if sequence doesn't have that position).
    """

    position_key: tuple[str, ...] = Field(..., description="Position identifier in sequence")
    row_index: int = Field(..., description="Row number for display ordering")
    photos: list[SequencePhoto | None] = Field(..., description="Photos at this position (None for missing)")


class SequenceGroup(BaseModel):
    """Model for a group of similar photo sequences.

    Represents multiple photo sequences that share similar template patterns or
    perceptual features. Used in review UI for sequence-level deduplication decisions.
    """

    group_id: str = Field(..., description="Stable group identifier")
    template_name: str = Field(..., description="Template pattern name")
    parent_dir: str = Field(..., description="Parent directory")
    created_by: str = Field(..., description="Stage that created this group")
    min_similarity: float = Field(..., description="Minimum similarity score in group")
    sequences: list[SequenceInfo] = Field(..., description="Sequences being compared")
    rows: list[SequenceRow] = Field(..., description="Rows of aligned photos across sequences")
