"""FastAPI orchestration server for photo deduplication.

This provides a web-based interface for configuring and running the pipeline.

Usage:
    python orchestrate.py
    # Then open browser to http://localhost:8000

API Endpoints:

## Configuration & Discovery

    GET  /api/browse
        Browse filesystem directories for source selection
        Query params: path (string)
        Returns: BrowseResponse (current_path, parent_path, directories)

    GET  /api/config/defaults
        Get default configuration values
        Query params: source_dir (optional)
        Returns: ConfigDefaultsResponse (source_dir, work_dir, max_workers, etc.)

    GET  /api/stages
        Get pipeline stage definitions in execution order
        Returns: list[StageDetail] (stage_id, display_name, review_type, etc.)

## Pipeline Control

    POST /api/pipeline/start
        Start pipeline execution with given configuration
        Body: dict with source_dir, work_dir, max_workers, etc.
        Returns: PipelineStartResponse (status, message)

    GET  /api/status
        Get current pipeline execution status
        Returns: PipelineStatusResponse (state, progress, stages, current_progress)

    POST /api/pipeline/stop
        Stop currently running pipeline
        Returns: PipelineStopResponse (status, message)

    POST /api/quit
        Gracefully shutdown the server
        Returns: ServerQuitResponse (status, message)

## Review Data Management

    POST /api/review/load
        Load review data from all stages with reviewable output
        Returns: ReviewLoadResponse (loaded, identical_count, sequence_count, photos_count)

    GET  /api/review/availability
        Check which review types have data available
        Returns: ReviewAvailabilityResponse (identical, sequences[])

    GET  /api/review/status
        Get current review session status
        Returns: ReviewStatusResponse (loaded, identical_count, sequence_count)

    GET  /api/review/identical/groups
        Get identical photos review data as JSON with pagination
        Query params: page (int), page_size (int), stage_id (int, optional)
        Returns: IdenticalGroupsResponse (groups, page, page_size, total_groups, total_pages, has_more)

    GET  /api/review/sequences/groups
        Get sequence similarity review data as JSON
        Query params: stage_id (int, optional)
        Returns: SequenceGroupsResponse (groups)

    POST /api/review/sequences/save
        Save sequence review decisions
        Body: dict with decisions
        Returns: ReviewSaveResponse (status, message, saved_count)

    POST /api/review/save
        Save all review decisions (identical + sequences)
        Body: dict with decisions
        Returns: ReviewSaveResponse (status, message, saved_count)

    POST /api/review/shutdown
        Shutdown server from review interface
        Returns: ShutdownResponse (status, message)

## Photo Information

    GET  /api/review/thumbnail/{photo_id}
        Get thumbnail image for a photo
        Path params: photo_id (int)
        Returns: Image file (JPEG)

## WebSocket

    WS   /ws/progress
        WebSocket for real-time progress updates during pipeline execution
        Sends: Progress messages with stage status and completion percentage

## Static Files

    GET  /
        Serve main orchestrator UI page
        Returns: HTML

    GET  /review/identical
        Serve identical photos review interface
        Returns: HTML

    GET  /review/sequences
        Serve sequence similarity review interface
        Returns: HTML

    GET  /static/{path}
        Serve static assets (CSS, JavaScript)
        Path params: path (string)
        Returns: Static file

    GET  /review/review_common.js
        Serve common JavaScript utilities for review interfaces
        Returns: JavaScript file
"""

from __future__ import annotations

import asyncio
import os
import signal

# Import existing config (don't modify it)
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pillow_heif import register_heif_opener

from utils import (
    CONFIG,
    BrowseResponse,
    ConfigDefaultsResponse,
    DirectoryInfo,
    IdenticalGroup,
    IdenticalGroupsResponse,
    PipelineStartResponse,
    PipelineStatusResponse,
    PipelineStopResponse,
    ReviewAvailabilityInfo,
    ReviewAvailabilityResponse,
    ReviewLoadResponse,
    ReviewSaveResponse,
    ReviewSessionData,
    ReviewStatusResponse,
    SequenceGroup,
    SequenceGroupsResponse,
    SequenceRow,
    ShutdownResponse,
    StageDetail,
    get_logger,
)

from .orchestrator_runner import OrchestratorRunner, PipelineStatusDict, get_runner

# Register HEIF opener so PIL can handle HEIC files (must be after all imports)
register_heif_opener()

# Initialize orchestrator paths in CONFIG (computed from package location)
CONFIG.orchestrator.STATIC_DIR = str(Path(__file__).parent / "static")
CONFIG.orchestrator.DOCS_DIR = str(Path(__file__).parent.parent.parent / "docs")


# Stage definitions are extracted from the actual running pipeline
# No need to build a dummy pipeline at module init - stages are populated
# when the user starts a pipeline with their chosen configuration


@asynccontextmanager
async def lifespan_manager(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for initializing and cleaning up resources.

    This is where application-wide state (app.state) should be set.
    """
    get_logger().info("Application Startup: Initializing application state.")

    # Stage instance cache (reuse across API calls to avoid repeated pickle loading)
    # 1. Initialize stage_cache here using app.state
    app.state.stage_cache = {}

    # Global photofiles dict (populated after Directory Walk completes)
    # Shared across all review sessions since it represents all photos from initial walk
    app.state.photofiles = None  # dict[int, PhotoFile] | None

    # Review session storage (populated after pipeline completion or per-stage)
    # 2. Initialize review_sessions dict mapping stage_id -> session_data
    # Mypy doesn't allow type annotations on non-self attributes
    app.state.review_sessions = {}  # dict[int, ReviewSessionData]
    # Legacy single session for backward compatibility (aggregates all stages)
    app.state.review_session = None  # ReviewSessionData | None

    yield

    # This runs on Application Shutdown
    get_logger().info("Application Shutdown: Cleaning up resources.")
    # No cleanup is strictly needed for simple dicts/Nones, but you would put
    # db connection closing or thread stopping here.


# Pass the new lifespan function to the FastAPI constructor
app = FastAPI(title="Photo Dedup Orchestrator", lifespan=lifespan_manager)


@app.get("/")
async def root() -> FileResponse:
    """Serve the main orchestrator UI."""
    static_dir = Path(__file__).parent / "static"
    return FileResponse(static_dir / "orchestrator.html")


@app.get("/api/browse", response_model=BrowseResponse)
async def browse_directories(path: str = "") -> BrowseResponse:
    """Browse filesystem directories.

    Args:
        path: Directory path to browse (empty for home/default)

    Returns:
        Dictionary with current path, parent path, and list of subdirectories
    """
    try:
        # Start from home directory if no path provided
        if not path:
            path = str(Path.home())

        current_path = Path(path).resolve()

        # Security check: ensure path exists and is a directory
        if not current_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        if not current_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        # Get parent directory (None if at root)
        parent_path = str(current_path.parent) if current_path.parent != current_path else None

        # List subdirectories (only directories, not files)
        directories = []
        try:
            for item in sorted(current_path.iterdir()):
                if item.is_dir():
                    try:
                        # Skip hidden directories and system directories
                        if not item.name.startswith(".") and not item.name.startswith("$"):
                            directories.append({"name": item.name, "path": str(item)})
                    except (PermissionError, OSError):
                        # Skip directories we can't access
                        continue
        except (PermissionError, OSError) as e:
            raise HTTPException(status_code=403, detail=f"Permission denied: {e!s}") from e

        return BrowseResponse(
            current_path=str(current_path),
            parent_path=parent_path,
            directories=[DirectoryInfo(name=d["name"], path=d["path"]) for d in directories],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error browsing directory: {e!s}") from e


@app.get("/api/config/defaults", response_model=ConfigDefaultsResponse)
async def get_default_config(source_dir: str | None = None) -> ConfigDefaultsResponse:
    """Get default configuration values.

    Args:
        source_dir: Optional source directory to auto-fill work_dir

    Returns:
        Dictionary of default configuration values
    """
    defaults: dict[str, Any] = {
        "source_dir": source_dir or "",
        "work_dir": "",
        # Processing defaults
        "max_workers": os.cpu_count() or 4,
        "batch_size": 256,
        "debug_mode": False,
        "log_level": "INFO",
        # Comparison defaults
        "comparison_method": "ssim",
        "comparison_gates": ["aspect_ratio", "dhash", "ssim"],
        "gate_thresholds": {
            "aspect_ratio": 0.85,
            "dhash": 0.80,
            "ssim": 0.95,
        },
        # Sequence defaults
        "min_association": 0.2,
        "max_mismatches": 2,
        "perceptual_method": "ahash",
        "perceptual_hamming_distance": 8,
        # Benchmark defaults
        "enable_benchmarks": False,
        "target_fpr": 0.00075,
        # Review server defaults
        "review_port": 8000,
        "review_host": "127.0.0.1",
    }

    # Auto-fill work_dir if source_dir provided
    if source_dir:
        source_path = Path(source_dir)
        work_dir = source_path.parent / CONFIG.orchestrator.DEFAULT_WORK_DIR_NAME
        defaults["work_dir"] = str(work_dir)

    return ConfigDefaultsResponse(
        source_dir=defaults.get("source_dir"),
        work_dir=defaults.get("work_dir"),
        max_workers=defaults.get("max_workers"),
        batch_size=defaults.get("batch_size"),
        debug_mode=defaults.get("debug_mode", False),
        comparison_method=defaults.get("comparison_method", "SSIM"),
        gate_thresholds=defaults.get("gate_thresholds", {}),
        enable_benchmarks=defaults.get("enable_benchmarks", False),
        target_fpr=defaults.get("target_fpr", 0.00075),
    )


@app.post("/api/pipeline/start", response_model=PipelineStartResponse)
async def start_pipeline(
    config: dict[str, Any],
    runner: OrchestratorRunner = Depends(get_runner),  # noqa: B008
) -> PipelineStartResponse:
    """Start the pipeline with given configuration.

    Args:
        config: Configuration dictionary from web form
        runner: Orchestrator runner (dependency injection)

    Returns:
        Status message
    """
    # Validate required fields
    if not config.get("source_dir"):  # FIXME: Can this be checked with a dependency?
        raise HTTPException(status_code=400, detail="source_dir is required")

    # Start pipeline in background thread
    started = runner.start(config)

    if not started:  # [gb] How can this ever happen?
        raise HTTPException(status_code=409, detail="Pipeline already running")

    return PipelineStartResponse(
        status="started",
        message=f"Pipeline started for {config['source_dir']}",
    )


@app.get("/api/status", response_model=PipelineStatusResponse)
async def get_status(
    runner: OrchestratorRunner = Depends(get_runner),  # noqa: B008
) -> PipelineStatusDict:
    """Get current pipeline status.

    Returns:
        Current status including stage, progress, etc.
    """
    return runner.get_status()


@app.get("/api/stages", response_model=list[StageDetail])
async def get_stages(
    runner: OrchestratorRunner = Depends(get_runner),  # noqa: B008
) -> list[StageDetail]:
    """Get pipeline stage definitions.

    Returns stages in execution order with metadata for UI rendering.
    Stage definitions are extracted from actual stage classes via topological sort.

    Returns stages from the actual running pipeline (which reflects the current
    config including benchmark enablement). Returns empty list if no pipeline
    has been started yet.

    Returns:
        List of StageDetail models with complete metadata, or empty list
    """
    # Return stages from actual pipeline if one has been built
    # This ensures benchmark stage presence reflects current config
    if runner.orchestrator is not None:
        stages = runner.orchestrator.graph.get_stages_in_order()
        return [
            StageDetail(
                stage_id=stage.stage_id if stage.stage_id is not None else i,
                stage_name=stage.stage_name,
                description=stage.description,
                required=True,
                produces_review=stage.needs_review() != "none",
                review_type=stage.needs_review(),
            )
            for i, stage in enumerate(stages)
        ]

    # No pipeline started yet - return empty list
    return []


@app.post("/api/pipeline/stop", response_model=PipelineStopResponse)
async def stop_pipeline(
    runner: OrchestratorRunner = Depends(get_runner),  # noqa: B008
) -> PipelineStopResponse:  # [gb] This is never called
    """Stop the currently running pipeline.

    Returns:
        Status message
    """
    stopped = runner.stop()

    if not stopped:
        raise HTTPException(status_code=409, detail="No pipeline running")

    return PipelineStopResponse(status="stopped", message="Pipeline stopped")


# =============================================================================
# Review Endpoints
# =============================================================================


@app.post("/api/review/load", response_model=ReviewLoadResponse)
async def load_review_data(
    stage_id: int | None = None,
    runner: OrchestratorRunner = Depends(get_runner),  # noqa: B008
) -> ReviewLoadResponse:
    """Load review data from all stages or a specific stage.

    Dynamically discovers review data by querying each stage's
    needs_review() and review_data properties. Works for any future
    review-producing stage without code changes.

    Args:
        stage_id: Optional stage ID to load data for only that stage.
                  If None, loads data from all stages (legacy behavior).
        runner: Orchestrator runner (dependency injection)

    Returns:
        ReviewLoadResponse with counts and status
    """
    get_logger().info(
        f"Loading review data from: {CONFIG.paths.WORK_DIR}"
        + (f" (stage_id={stage_id})" if stage_id is not None else " (all stages)")
    )

    if runner.orchestrator is None:  # FIXME: Can this be checked in the dependency?
        raise HTTPException(status_code=400, detail="Pipeline not initialized")
    stages = runner.orchestrator.graph.get_stages_in_order()

    # Filter to specific stage if requested
    if stage_id is not None:
        stages = [s for s in stages if s.stage_id == stage_id]
        if not stages:  # [gb] How does this ever happen?
            raise HTTPException(status_code=404, detail=f"Stage {stage_id} not found")

    identical_groups: list[IdenticalGroup] = []
    sequence_groups: list[SequenceGroup] = []

    # Populate global photofiles dict (shared across all review sessions)
    # Only load once - photofiles don't change after Directory Walk completes
    if app.state.photofiles is None:
        app.state.photofiles = runner.orchestrator.get_photofiles()
        get_logger().info(f"Loaded {len(app.state.photofiles)} photofiles from orchestrator")

    # Dynamically discover and load review data from requested stages
    for stage in stages:
        review_type = stage.needs_review()

        if review_type == "none":
            continue  # Skip stages without review data

        if not stage.has_review_data():  # [gb] How can this ever happen?
            get_logger().info(f"{stage.stage_name}: No review data available yet")
            continue

        # Load review data from stage using type-specific properties
        get_logger().info(f"Loading {review_type} review data from {stage.stage_name}")

        # Use match/case for automatic type narrowing with Literal types
        match review_type:
            case "photos":
                photo_groups = stage.identical_review_result
                identical_groups.extend(photo_groups)
                get_logger().info(f"Loaded {len(photo_groups)} identical groups from {stage.stage_name}")
            case "sequences":
                seq_groups = stage.sequence_review_result
                sequence_groups.extend(seq_groups)
                get_logger().info(f"Loaded {len(seq_groups)} sequence groups from {stage.stage_name}")

        # Store per-stage if loading single stage
        if stage_id is not None:
            app.state.review_sessions[stage_id] = ReviewSessionData(
                identical_groups=(identical_groups if review_type == "photos" else []),
                sequence_groups=(sequence_groups if review_type == "sequences" else []),
                decisions={"identical": {}, "sequences": {}},
                review_type=review_type,
                stage_name=stage.stage_name,
            )
            get_logger().info(f"Stored review session for stage {stage_id}")

    # Store aggregated data (legacy compatibility or when loading all)
    if stage_id is None:
        app.state.review_session = ReviewSessionData(
            identical_groups=identical_groups,
            sequence_groups=sequence_groups,
            decisions={"identical": {}, "sequences": {}},
        )

    get_logger().info(
        f"Review data loaded successfully: {len(identical_groups)} identical, "
        f"{len(sequence_groups)} sequence groups, {len(app.state.photofiles)} photos"
    )

    return ReviewLoadResponse(
        status="success",
        identical_count=len(identical_groups),
        sequence_count=len(sequence_groups),
        message=None,
    )


@app.get("/api/review/availability", response_model=ReviewAvailabilityResponse)
async def get_review_availability(
    runner: OrchestratorRunner = Depends(get_runner),  # noqa: B008
) -> ReviewAvailabilityResponse:
    """Check which stages have review data available (without loading).

    Dynamically discovers review capabilities by querying each stage's
    needs_review() and has_review_data() methods.

    Returns:
        ReviewAvailabilityResponse with map of stage_id to availability info
    """
    stages_info: dict[int, ReviewAvailabilityInfo] = {}

    # Get all stages from orchestrator
    if runner.orchestrator is None:  # [gb] How can this ever happen?
        raise HTTPException(status_code=400, detail="Pipeline not initialized")
    stages = runner.orchestrator.graph.get_stages_in_order()

    # Check each stage for review data
    for stage in stages:
        review_type = stage.needs_review()
        if review_type != "none":
            # Stage produces review data - check if available
            stage_id = stage.stage_id if stage.stage_id is not None else -1
            stages_info[stage_id] = ReviewAvailabilityInfo(
                available=stage.has_review_data(),
                review_type=review_type,
            )

    return ReviewAvailabilityResponse(stages=stages_info)


@app.get("/api/review/status", response_model=ReviewStatusResponse)
async def get_review_status() -> ReviewStatusResponse:
    """Get review session status."""
    if app.state.review_session is None:
        return ReviewStatusResponse(loaded=False, identical_count=0, sequence_count=0)

    # FIXME: More hard-coded stage names.
    return ReviewStatusResponse(
        loaded=True,
        identical_count=len(app.state.review_session.identical_groups),
        sequence_count=len(app.state.review_session.sequence_groups),
    )


@app.get("/api/review/identical/groups", response_model=IdenticalGroupsResponse)
async def get_identical_groups(
    page: int = 0,
    page_size: int = 100,
    stage_id: int | None = None,
) -> IdenticalGroupsResponse:
    """Get identical photos review data as JSON with pagination.

    Args:
        page: Page number (0-indexed)
        page_size: Number of groups per page (default: 100, max: 1000)
        stage_id: Optional stage ID to filter groups from specific stage only

    Returns:
        Paginated identical groups with metadata
    """
    # Get session data (per-stage or aggregated)
    if stage_id is not None:
        if stage_id not in app.state.review_sessions:  # [gb] How does this happen?
            raise HTTPException(
                status_code=400,
                detail=f"Review data for stage {stage_id} not loaded. Call /api/review/load?stage_id={stage_id} first.",
            )
        session = app.state.review_sessions[stage_id]
    else:  # [gb] How does this happen?
        if app.state.review_session is None:
            raise HTTPException(status_code=400, detail="Review data not loaded. Run pipeline first.")
        session = app.state.review_session

    # Limit page_size to prevent abuse
    page_size = min(page_size, 1000)

    all_groups = session.identical_groups
    total_groups = len(all_groups)

    # Calculate pagination
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, total_groups)

    # Return empty if page is out of range
    if start_idx >= total_groups:  # [gb] How does this happen?
        return IdenticalGroupsResponse(
            groups=[],
            page=page,
            page_size=page_size,
            total_groups=total_groups,
            total_pages=(total_groups + page_size - 1) // page_size,
            has_more=False,
        )

    return IdenticalGroupsResponse(
        groups=all_groups[start_idx:end_idx],
        page=page,
        page_size=page_size,
        total_groups=total_groups,
        total_pages=(total_groups + page_size - 1) // page_size,
        has_more=end_idx < total_groups,
    )


@app.get("/api/review/sequences/groups", response_model=SequenceGroupsResponse)
async def get_sequence_groups(stage_id: int | None = None) -> SequenceGroupsResponse:
    """Get sequence review groups for review interface.

    Groups are sorted to prioritize sequences with rotated photos (for easier review).
    Within each group, rows are sorted to put rotated photos first.

    Args:
        stage_id: Optional stage ID to filter groups from specific stage only

    Returns:
        Sequence similarity groups for review UI
    """
    # Get session data (per-stage or aggregated)
    if stage_id is not None:
        if stage_id not in app.state.review_sessions:  # [gb] How does this ever happend?
            raise HTTPException(
                status_code=400,
                detail=f"Review data for stage {stage_id} not loaded. Call /api/review/load?stage_id={stage_id} first.",
            )
        session = app.state.review_sessions[stage_id]
    else:  # [gb] How does this ever happen?
        if app.state.review_session is None:
            raise HTTPException(
                status_code=400,
                detail="Review data not loaded. Call /api/review/load first.",
            )
        session = app.state.review_session

    def get_row_sort_key(row: SequenceRow) -> float:
        """Calculate sort key for a row: minimum similarity score.

        Returns minimum similarity score in row (lower = more suspicious).
        Rows with lowest similarity appear first for review.
        """
        # Extract non-None photos
        photos = [p for p in row.photos if p is not None]

        if len(photos) <= 1:
            # Single photo or empty row: sim=1.0
            return 1.0

        # Get minimum similarity (excluding exemplar photos which have None similarity)
        similarities = [p.similarity_score for p in photos if p.similarity_score is not None]
        return min(similarities) if similarities else 1.0

    # Sort rows within each group by similarity (lowest first)
    for group in session.sequence_groups:
        group.rows = sorted(group.rows, key=get_row_sort_key)

    # Sort groups by the sort key of their first row
    sorted_groups = sorted(
        session.sequence_groups,
        key=lambda g: get_row_sort_key(g.rows[0]) if g.rows else (0, 1.0),
    )

    return SequenceGroupsResponse(groups=sorted_groups)


@app.post("/api/review/sequences/save", response_model=ReviewSaveResponse)
async def save_sequence_decisions(decisions: dict[str, Any]) -> ReviewSaveResponse:
    """Save sequence review decisions.

    Args:
        decisions: Decision data from review interface

    Returns:
        Status message
    """
    # Store decisions in session
    saved_count = 0
    if app.state.review_session is not None:
        app.state.review_session.decisions["sequences"].update(decisions)
        saved_count = len(decisions)

    # TODO: Persist to review_decisions.jsonl
    return ReviewSaveResponse(
        status="saved",
        message="Decisions saved (in-memory only)",
        saved_count=saved_count,
    )


@app.post("/api/review/save", response_model=ReviewSaveResponse)
async def save_all_decisions(decisions: dict[str, Any]) -> ReviewSaveResponse:
    """Save all review decisions.

    Args:
        decisions: Decision data from review interface

    Returns:
        Status message
    """
    # Store decisions in session
    saved_count = 0
    if app.state.review_session is not None:  # [gb] How does this ever happen?
        if "identical" in decisions:
            app.state.review_session.decisions["identical"].update(decisions["identical"])
            saved_count += len(decisions["identical"])
        if "sequences" in decisions:
            app.state.review_session.decisions["sequences"].update(decisions["sequences"])
            saved_count += len(decisions["sequences"])

    # TODO: Persist to review_decisions.jsonl
    return ReviewSaveResponse(
        status="saved",
        message="All decisions saved (in-memory only)",
        saved_count=saved_count,
    )


@app.post("/api/shutdown", response_model=ShutdownResponse)
async def shutdown_from_review() -> ShutdownResponse:
    """Shutdown the orchestrator server gracefully."""
    get_logger().info("Shutdown endpoint called: Initiating graceful shutdown via SIGINT.")

    # Signal uvicorn to initiate graceful shutdown
    # SIGINT (Ctrl+C signal) triggers uvicorn's shutdown sequence:
    # - Uvicorn stops accepting new connections
    # - Sends lifespan.shutdown event to the application
    # - FastAPI runs lifespan cleanup code (after yield)
    # - Process exits with code 0
    def shutdown() -> None:
        get_logger().info("Shutdown callback executing: raising SIGINT")
        signal.raise_signal(signal.SIGINT)

    # Schedule shutdown after a short delay (0.1s is usually enough)
    # This ensures the HTTP 200 OK response is sent back to the client first.
    asyncio.get_event_loop().call_later(0.1, shutdown)

    return ShutdownResponse(status="shutting_down")


@app.get("/api/review/thumbnail/{photo_id}", response_model=None)
async def get_thumbnail(photo_id: int) -> FileResponse | StreamingResponse:
    """Serve photo thumbnail with automatic HEIC-to-JPG conversion.

    Browsers don't natively support HEIC format, so this endpoint converts
    HEIC/HEIF files to JPG before serving. Other formats are served directly.

    Args:
        photo_id: Photo ID

    Returns:
        Image file response (direct file or converted stream)

    Raises:
        HTTPException: If review data not loaded or photo not found
    """
    # Access global photofiles dict (populated after Directory Walk completes)
    if app.state.photofiles is None:  # [gb] How does this ever happend?
        raise HTTPException(status_code=400, detail="Review data not loaded")
    if photo_id not in app.state.photofiles:  # [gb] How does this ever happen?
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")

    photo = app.state.photofiles[photo_id]

    # Check if file is HEIC/HEIF format (needs conversion for browser display)
    is_heic = photo.mime in ("heic", "heif") or photo.path.suffix.lower() in (
        ".heic",
        ".heif",
    )

    if is_heic:  # [gb] Can all thumbnails follow this route?
        # Convert HEIC to JPG for browser compatibility
        try:
            # Open HEIC file with PIL (pillow_heif handles the conversion)
            with Image.open(photo.path) as original_img:
                # Convert to RGB if necessary (removes alpha channel)
                if original_img.mode in ("RGBA", "LA", "P"):
                    rgb_img = Image.new("RGB", original_img.size, (255, 255, 255))
                    rgb_img.paste(
                        original_img,
                        mask=(original_img.split()[-1] if original_img.mode in ("RGBA", "LA") else None),
                    )
                    final_img = rgb_img
                elif original_img.mode != "RGB":
                    final_img = original_img.convert("RGB")
                else:
                    final_img = original_img

                # Save to BytesIO as JPG
                buffer = BytesIO()
                final_img.save(buffer, format="JPEG", quality=90, optimize=True)
                buffer.seek(0)

                return StreamingResponse(
                    buffer,
                    media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=3600"},
                )
        except Exception as e:
            get_logger().error(f"Failed to convert HEIC thumbnail for photo {photo_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to convert HEIC image: {e!s}") from e

    # Serve other formats directly
    return FileResponse(
        photo.path,
        media_type=f"image/{photo.mime}",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.websocket("/ws/progress")
async def websocket_progress(
    websocket: WebSocket,
    runner: OrchestratorRunner = Depends(get_runner),  # noqa: B008
) -> None:
    """WebSocket endpoint for real-time progress updates.

    Args:
        websocket: WebSocket connection
        runner: Orchestrator runner (dependency injection)
    """
    await websocket.accept()

    try:
        while True:
            # Send current status
            status = runner.get_status()
            await websocket.send_json(status)

            # Wait before next update
            await asyncio.sleep(0.5)

            # Stop if pipeline is no longer running
            if not status["running"] and (status["completed"] or status["error"]):
                break

    except WebSocketDisconnect:
        get_logger().info("WebSocket client disconnected")


# Serve review interface HTML files
@app.get("/review_identical.html")
async def serve_review_identical() -> FileResponse:
    """Serve identical files review interface."""
    static_path = (
        Path(CONFIG.orchestrator.STATIC_DIR)
        if CONFIG.orchestrator.STATIC_DIR
        else Path(__file__).parent / "static"
    )
    return FileResponse(static_path / "review_identical.html")


@app.get("/review_sequences.html")
async def serve_review_sequences() -> FileResponse:
    """Serve sequences review interface."""
    static_path = (
        Path(CONFIG.orchestrator.STATIC_DIR)
        if CONFIG.orchestrator.STATIC_DIR
        else Path(__file__).parent / "static"
    )
    return FileResponse(static_path / "review_sequences.html")


# Mount static files from CONFIG
static_dir = Path(CONFIG.orchestrator.STATIC_DIR) if CONFIG.orchestrator.STATIC_DIR else None
if static_dir and static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve review_common.js from static directory
@app.get("/review_common.js")
async def serve_review_common_js() -> FileResponse:
    """Serve review_common.js from static directory."""
    static_path = (
        Path(CONFIG.orchestrator.STATIC_DIR)
        if CONFIG.orchestrator.STATIC_DIR
        else Path(__file__).parent / "static"
    )
    return FileResponse(static_path / "review_common.js", media_type="application/javascript")
