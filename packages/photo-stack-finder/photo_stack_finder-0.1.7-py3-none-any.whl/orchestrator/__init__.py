"""Orchestration layer for photo deduplication workflow.

This module provides the web-based interface and pipeline orchestration for the
photo deduplication system. It includes:

- FastAPI web application (app)
- Pipeline orchestration and execution (PipelineOrchestrator)
- Pipeline configuration and building (PipelineBuilder, build_pipeline)
- Orchestrator runner and lifecycle management (OrchestratorRunner)
- Review data persistence (append_decision_to_log, build_review_index)
"""

from __future__ import annotations

# FastAPI application
from .app import app

# Pipeline building
from .build_pipeline import build_pipeline

# Orchestrator runner and status
from .orchestrator_runner import (
    OrchestratorRunner,
    OrchestratorStatus,
    PipelineStatusDict,
    get_runner,
)

# Pipeline orchestration
from .pipeline_builder import PipelineBuilder
from .pipeline_orchestrator import PipelineOrchestrator

# Review persistence
from .review_persistence import append_decision_to_log, build_review_index

__all__ = [
    "OrchestratorRunner",
    "OrchestratorStatus",
    "PipelineBuilder",
    "PipelineOrchestrator",
    "PipelineStatusDict",
    "app",
    "append_decision_to_log",
    "build_pipeline",
    "build_review_index",
    "get_runner",
]
