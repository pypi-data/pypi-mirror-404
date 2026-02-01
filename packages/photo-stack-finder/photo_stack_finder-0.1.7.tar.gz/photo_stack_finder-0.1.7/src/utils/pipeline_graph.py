"""Pipeline dependency graph with validation and topological sorting.

Provides graph computation methods for pipeline orchestration:
- Cycle detection to enforce DAG property (using NetworkX)
- Connected component checking (using NetworkX)
- Topological sorting for execution order (using NetworkX)
- Port connectivity validation
"""

from __future__ import annotations

import networkx as nx

from .base_pipeline_stage import BasePipelineStage
from .base_ports import BaseChannel, BaseInputPort, BaseOutputPort


class PipelineGraph:
    """Dependency graph of pipeline stages.

    Manages registration, validation, and analysis of stage dependencies.
    Stages and channels auto-register during construction within a
    PipelineBuilder context.
    """

    def __init__(self) -> None:
        """Initialize empty pipeline graph."""
        self.nodes: dict[str, BasePipelineStage] = {}
        self.channels: list[BaseChannel] = []
        self._execution_order: list[str] | None = None

    # === Registration (called by stage/channel constructors) ===

    def add_node(self, stage: BasePipelineStage) -> None:
        """Register a stage in the graph.

        Called automatically by BasePipelineStage.__init__() during
        auto-registration.

        Args:
            stage: The pipeline stage to register

        Raises:
            ValueError: If a stage with this name already exists
        """
        if stage.stage_name in self.nodes:
            raise ValueError(f"Stage '{stage.stage_name}' already registered in graph")
        self.nodes[stage.stage_name] = stage

    def add_edge(self, channel: BaseChannel) -> None:
        """Register a channel (dependency edge with port information).

        Called automatically by Channel.__init__() during auto-registration.

        Args:
            channel: The Channel instance containing output/input port references
        """
        self.channels.append(channel)

    # === Validation (called by PipelineBuilder.__exit__) ===

    def validate(self) -> None:
        """Validate graph structure.

        Performs comprehensive validation:
        - No cycles (DAG property)
        - Single connected component (no isolated subgraphs)
        - All input ports are bound (have a source)
        - All output ports that exist are connected (at least one consumer)
        - All referenced stages exist

        Raises:
            ValueError: If validation fails with descriptive error message

        Note:
            Source stages (no input ports) and sink stages (no output ports)
            are valid. Validation only checks ports that actually exist.
        """
        if not self.nodes:
            raise ValueError("Cannot validate empty pipeline graph")

        # Check 1: All channels reference valid stages
        self._check_valid_stage_references()

        # Check 2: No cycles (DAG property)
        self._check_no_cycles()

        # Check 3: Single connected component
        self._check_single_component()

        # Check 4: All ports are properly connected
        self._check_all_ports_connected()

    def _check_valid_stage_references(self) -> None:
        """Verify all channels reference stages that exist in the graph.

        Raises:
            ValueError: If a channel references an unknown stage
        """
        for channel in self.channels:
            producer_name = channel.output.owner.stage_name
            # FIXME: Provide a base class method for this instead of using a private attribute.
            consumer_name = channel.input._source.owner.stage_name if channel.input._source else None

            if producer_name not in self.nodes:
                raise ValueError(f"Channel references unknown producer stage: '{producer_name}'")

            if consumer_name and consumer_name not in self.nodes:
                raise ValueError(f"Channel references unknown consumer stage: '{consumer_name}'")

    # FIXME: Why not do this as self.nodes and self.channels are populated?  Having those structures separate seems pointless.
    def _build_networkx_graph(self) -> nx.DiGraph[str]:
        """Build NetworkX directed graph from pipeline stages and channels.

        Returns:
            NetworkX DiGraph with stage names as nodes and channels as edges
        """
        graph: nx.DiGraph[str] = nx.DiGraph()

        # Add all stage nodes
        graph.add_nodes_from(self.nodes.keys())

        # Build reverse mapping: InputPort → Stage (owner)
        # Needed because InputPort doesn't have an owner attribute
        input_port_owners: dict[int, str] = {}
        for stage_name, stage in self.nodes.items():
            # Use __dict__ to avoid triggering properties
            for attr_name, attr in stage.__dict__.items():
                if attr_name.startswith("_"):
                    continue
                if isinstance(attr, BaseInputPort):
                    input_port_owners[id(attr)] = stage_name

        # Add edges from channels (producer → consumer)
        for channel in self.channels:
            producer = channel.output.owner.stage_name
            consumer = input_port_owners.get(id(channel.input))
            if consumer:
                graph.add_edge(producer, consumer)

        return graph

    def _check_no_cycles(self) -> None:
        """Detect cycles using NetworkX DAG checking.

        Raises:
            ValueError: If a cycle is detected, with the cycle path
        """
        graph = self._build_networkx_graph()

        if not nx.is_directed_acyclic_graph(graph):
            # Find a cycle to report in error message
            try:
                cycle = nx.find_cycle(graph, orientation="original")
                # cycle is a list of (source, target, key) tuples
                cycle_nodes = [edge[0] for edge in cycle] + [cycle[0][0]]
                cycle_path = " → ".join(cycle_nodes)
                raise ValueError(f"Cycle detected in pipeline: {cycle_path}")
            except nx.NetworkXNoCycle:
                # Shouldn't happen but provide fallback
                raise ValueError("Cycle detected in pipeline (details unavailable)") from None

    def _check_single_component(self) -> None:
        """Verify graph is a single connected component.

        Treats edges as undirected for connectivity check.
        This prevents isolated subgraphs that would indicate
        configuration errors.

        Raises:
            ValueError: If graph has multiple connected components
        """
        if not self.nodes:
            return

        graph = self._build_networkx_graph()

        # Check weak connectivity (treat directed edges as undirected)
        num_components = nx.number_weakly_connected_components(graph)

        if num_components > 1:
            # Find the components to report in error
            components = list(nx.weakly_connected_components(graph))
            # Sort components by size for consistent error messages
            components_sorted = sorted(components, key=len, reverse=True)
            component_sizes = [len(comp) for comp in components_sorted]

            # Show which stages are unreachable from the largest component
            largest_component = components_sorted[0]
            unreached = set(self.nodes.keys()) - largest_component

            raise ValueError(
                f"Pipeline has {len(components_sorted)} disconnected components "
                f"with sizes {component_sizes}. "
                f"Unreached stages from main component: {sorted(unreached)}"
            )

    def _check_all_ports_connected(self) -> None:
        """Verify all ports on all stages are properly connected.

        - All input ports must be bound to a source
        - All output ports must have at least one consumer

        Source stages (no inputs) and sink stages (no outputs) are valid.

        Raises:
            ValueError: If any port is unconnected
        """
        # Build set of connected ports from channels
        # Use base classes since we check identity regardless of data type
        connected_inputs: set[BaseInputPort] = set()
        connected_outputs: set[BaseOutputPort] = set()

        for channel in self.channels:
            connected_outputs.add(channel.output)
            connected_inputs.add(channel.input)

        # Check all ports on all stages
        for stage_name, stage in self.nodes.items():
            # Use __dict__ to avoid triggering properties
            for attr_name, attr in stage.__dict__.items():
                if attr_name.startswith("_"):
                    continue

                # Check input ports are bound
                if isinstance(attr, BaseInputPort):
                    if not attr.is_bound():
                        raise ValueError(f"Unbound input port: {stage_name}.{attr_name}")
                    if attr not in connected_inputs:
                        raise ValueError(f"Input port {stage_name}.{attr_name} bound but not connected by channel")

                # Check output ports are connected
                # Exceptions: Optional ports that don't need to be connected:
                # - Review ports (for web UI, not pipeline flow)
                # - Full tuple output ports (backward compatibility, use specific ports instead)
                # - Final output ports (sink nodes - consumed by orchestrator after execution)
                # - photofiles_o (only consumed by optional benchmarks stage)
                if isinstance(attr, BaseOutputPort) and attr not in connected_outputs:
                    is_optional = "review" in attr_name.lower() or (
                        # Full tuple outputs (return complete result, not subset)
                        "forest_template_bins" in attr_name  # ComputeVersions
                        or "forest_bins" in attr_name  # ComputeTemplateSimilarity, ComputeIndices
                        or "final_forest" in attr_name  # Final pipeline output (sink node)
                        or "photofiles" in attr_name  # Only consumed by optional benchmarks stage
                    )
                    if not is_optional:
                        raise ValueError(
                            f"Unconnected output port: {stage_name}.{attr_name} (no channels consume this output)"
                        )

    # === Graph Analysis (called by orchestrator) ===

    def compute_execution_order(self) -> list[str]:
        """Compute topological sort of stages using NetworkX.

        Must be called after validate() succeeds.

        Returns:
            List of stage names in valid execution order (dependency order)

        Raises:
            ValueError: If cycle detected during sort (shouldn't happen after validate)
        """
        graph = self._build_networkx_graph()

        try:
            result = list(nx.topological_sort(graph))
            self._execution_order = result

            # Annotate stages with their execution order position (stable ID)
            # Use 1-based indexing (0 means "not started" in orchestrator)
            for i, stage_name in enumerate(result, start=1):
                self.nodes[stage_name].stage_id = i

            return result
        except nx.NetworkXError as e:
            raise ValueError(f"Cannot compute topological sort (cycle may be present): {e}") from e

    def get_execution_order(self) -> list[str]:
        """Get previously computed execution order.

        Returns:
            Cached execution order from compute_execution_order()

        Raises:
            RuntimeError: If compute_execution_order() not called yet
        """
        if self._execution_order is None:
            raise RuntimeError("Execution order not computed. Call compute_execution_order() first.")
        return self._execution_order

    def get_stages_in_order(self) -> list[BasePipelineStage]:
        """Get stage instances in execution order.

        Returns:
            List of BasePipelineStage instances in topological order

        Raises:
            RuntimeError: If compute_execution_order() not called yet
        """
        order = self.get_execution_order()
        return [self.nodes[name] for name in order]

    def get_dependencies(self, stage_name: str) -> list[str]:
        """Get names of stages that a given stage depends on.

        Args:
            stage_name: Name of the stage to query

        Returns:
            List of upstream stage names (producers that this stage consumes from)

        Raises:
            KeyError: If stage_name not in graph
        """
        if stage_name not in self.nodes:
            raise KeyError(f"Stage '{stage_name}' not found in graph")

        dependencies: list[str] = []
        for channel in self.channels:
            consumer_port = channel.input._source
            if consumer_port and consumer_port.owner.stage_name == stage_name:
                producer = channel.output.owner.stage_name
                dependencies.append(producer)

        return dependencies

    def get_all_stages(self) -> dict[str, BasePipelineStage]:
        """Get all registered stages.

        Returns:
            Dictionary mapping stage names to stage instances
        """
        return self.nodes.copy()
