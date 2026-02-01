"""Pipeline builder with automatic stage and channel registration.

Provides a context manager that enables declarative pipeline construction:
- Stages created within the context auto-register with the graph
- Channels created within the context auto-register edges
- Graph validation happens automatically on context exit
- Execution order is computed automatically
- PipelineOrchestrator is created ready to execute

Usage:
    with PipelineBuilder() as builder:
        # Stages and channels auto-register during construction
        stage1 = MyStage(path1, "stage1")
        stage2 = MyStage(path2, "stage2")
        Channel(stage1.output_o, stage2.input_i)

    # After context exit, builder.orchestrator is ready
    builder.orchestrator.execute()

Architecture:
- Uses graph_context module for auto-registration
- Context manager pattern provides explicit scoping
- Validates graph structure on exit (fail-fast on errors)
- Cleans up registration state even on exceptions
"""

from __future__ import annotations

from typing import Any, Literal

from utils import graph_context
from utils.pipeline_graph import PipelineGraph

from .pipeline_orchestrator import PipelineOrchestrator


class PipelineBuilder:
    """Context manager for building pipeline graphs with auto-registration.

    Creates a scoped context where:
    - PipelineStage instances automatically register with the graph
    - Channel instances automatically register edges
    - Graph validation happens on context exit
    - Orchestrator is created and ready to execute

    The builder uses the graph_context module to enable auto-registration.
    This provides explicit scoping through the context manager while avoiding
    manual registration calls.

    Attributes:
        graph: The PipelineGraph being constructed
        orchestrator: The PipelineOrchestrator created on successful exit
                      (None until __exit__ completes successfully)
    """

    def __init__(self) -> None:
        """Initialize builder with empty graph.

        The orchestrator is not created until __exit__ succeeds.
        """
        self.graph = PipelineGraph()
        self.orchestrator: PipelineOrchestrator | None = None

    def __enter__(self) -> PipelineBuilder:
        """Enter context - enable auto-registration.

        Sets the active graph context to enable stages and channels to
        auto-register during construction.

        Returns:
            self for use in 'with' statement
        """
        graph_context.set_active_graph(self.graph)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> Literal[False]:
        """Exit context - validate graph and create orchestrator.

        Performs final graph validation and setup:
        1. If no exception occurred during construction:
           - Validates graph structure (cycles, connectivity, ports)
           - Computes execution order (topological sort)
           - Creates PipelineOrchestrator ready to execute

        2. Always clears the active graph context (stops registration)

        Args:
            exc_type: Exception type (if raised in context)
            exc_val: Exception value (if raised in context)
            exc_tb: Exception traceback (if raised in context)

        Returns:
            False (never suppresses exceptions)

        Raises:
            ValueError: If graph validation fails (cycles, disconnected components,
                       unbound ports, etc.)

        Note:
            The orchestrator is only created if no exception occurred during
            construction AND validation succeeds. Check if builder.orchestrator
            is not None before using.
        """
        try:
            # Only validate and create orchestrator if construction succeeded
            if exc_type is None:
                # Validate graph structure (raises ValueError on failure)
                self.graph.validate()

                # Compute execution order (topological sort)
                self.graph.compute_execution_order()

                # Create orchestrator ready to execute
                self.orchestrator = PipelineOrchestrator(self.graph)
        finally:
            # Always clear the active graph context to stop registration
            # This ensures clean state even if validation fails or exceptions occur
            graph_context.set_active_graph(None)

        # Never suppress exceptions
        return False
