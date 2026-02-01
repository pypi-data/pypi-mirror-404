"""Global graph context for pipeline auto-registration.

This module holds the active PipelineGraph instance during pipeline
construction. Stages and channels auto-register with this graph when
instantiated within a PipelineBuilder context.

Architecture:
- Breaks circular dependency between pipeline_stage, pipeline_graph, and channel
- Provides clean separation of concerns (graph context vs stage implementation)
- Enables auto-registration pattern without tight coupling
"""

# FIXME: Is this thread-safe?

from __future__ import annotations

from .pipeline_graph import PipelineGraph

# Circular dependency resolved by moving BaseChannel from channel.py to ports.py
# Previous cycle: channel → graph_context → pipeline_graph → channel (via BaseChannel)
# Now: pipeline_graph → ports (BaseChannel), channel → ports (BaseChannel), no cycle!

# Global graph context set by PipelineBuilder context manager
_active_graph: PipelineGraph | None = None


def get_active_graph() -> PipelineGraph | None:
    """Get the currently active pipeline graph for auto-registration.

    Returns:
        The active PipelineGraph if within a PipelineBuilder context, None otherwise
    """
    return _active_graph


def set_active_graph(graph: PipelineGraph | None) -> None:
    """Set the active pipeline graph for auto-registration.

    Args:
        graph: The PipelineGraph to set as active, or None to clear
    """
    global _active_graph  # noqa: PLW0603
    # Library configuration pattern - global state for graph context
    _active_graph = graph
