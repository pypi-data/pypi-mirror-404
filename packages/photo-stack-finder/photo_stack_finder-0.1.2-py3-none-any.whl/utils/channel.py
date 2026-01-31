"""Typed data channels connecting pipeline stages.

A Channel connects an OutputPort to an InputPort, establishing a typed
dependency edge in the pipeline graph. The Generic[T] type parameter
ensures compile-time type safety - the output and input must have
matching types.

Architecture:
- Auto-registration: Channels register themselves with the active graph
- Type safety: Generic[T] enforces matching port types
- Binding: Constructor automatically binds input port to output port

Analogous to: Channels in SystemC, wires connecting modules in Verilog
"""

from __future__ import annotations

from typing import TypeVar

from .base_ports import BaseChannel
from .graph_context import get_active_graph
from .ports import InputPort, OutputPort

T = TypeVar("T")


class Channel[T](BaseChannel):
    """Typed data connection between pipeline stages.

    Creates a dependency edge from producer (output port) to consumer
    (input port). The Generic[T] type parameter ensures type safety:
    both ports must handle the same data type.

    The channel automatically:
    1. Binds the input port to the output port
    2. Registers itself with the active PipelineGraph (if within PipelineBuilder context)

    Type parameter T specifies the data type flowing through this channel.

    Example:
        # Connect stages with type safety
        sha_bins_o: OutputPort[dict[str, list[str]]] = stage1.sha_bins_o
        sha_bins_input: InputPort[dict[str, list[str]]] = stage2.sha_bins_i

        # This will type-check correctly
        channel = Channel(sha_bins_o, sha_bins_input)

        # This would fail mypy type checking if types don't match
        # channel = Channel(different_type_output, sha_bins_input)  # Error!
    """

    def __init__(self, port_o: OutputPort[T], port_i: InputPort[T]) -> None:
        """Create a typed channel connecting two ports.

        Args:
            port_o: The producer port (where data comes from)
            port_i: The consumer port (where data goes to)

        Note:
            If called within a PipelineBuilder context (i.e., when
            PipelineStage._graph is set), this channel will auto-register
            with the graph.
        """
        self.output = port_o
        self.input = port_i

        # Bind the input port to the output port
        # This establishes the data flow connection
        port_i.bind(port_o)

        # Auto-register this edge if we're within a PipelineBuilder context
        active_graph = get_active_graph()
        if active_graph is not None:
            active_graph.add_edge(self)
