"""Port-based pipeline connectivity inspired by SystemC/Verilog.

This module provides typed input/output ports for pipeline stages, enabling:
- Type-safe connections between stages
- Dependency tracking through timestamps
- Decoupling stages from each other and from storage details

Architecture:
- InputPort: Typed input on a stage (like sc_in<T> in SystemC)
- OutputPort: Typed output on a stage (like sc_out<T> in SystemC)
- Ports connect stages without exposing cache paths or implementation
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .base_ports import BaseInputPort, BaseOutputPort, StageProtocol

T = TypeVar("T")


class OutputPort[T](BaseOutputPort):
    """Typed output port on a pipeline stage.

    An output port provides read access to a stage's output data.
    Multiple consumers can read from the same output port.

    The port uses a getter callback provided by the stage to access data.
    The port itself has no storage - it delegates to the stage's getter.

    Type parameter T specifies the data type this port produces,
    enabling compile-time type checking of connections.

    Analogous to: sc_out<T> in SystemC, output wire in Verilog
    """

    def __init__(
        self,
        owner: StageProtocol,
        getter: Callable[[], T],
    ):
        """Initialize output port.

        Args:
            owner: The stage that produces this output (used for timestamps)
            getter: Callable that returns the output data when called.
                    Typically a lambda like: lambda: self.result
                    or lambda: self.result['bins'] for partial data.
                    The getter is called each time read() is invoked.

        Example:
            # Simple case - return entire result
            self.output_o = OutputPort(self, lambda: self.result)

            # Multiple ports exposing different parts
            self.bins_o = OutputPort(self, lambda: self.sha_bins)
            self.forest_o = OutputPort(self, lambda: self.forest)
        """
        super().__init__(owner)
        self.getter = getter

    def read(self) -> T:
        """Read output data from owning stage.

        Calls the getter callback to retrieve the current output data.

        Returns:
            Output data of type T

        Raises:
            Exception: If getter fails (e.g., stage hasn't run yet)
        """
        return self.getter()


class InputPort[T](BaseInputPort):
    """Typed input port on a pipeline stage.

    An input port represents a dependency on another stage's output.
    It provides read access to upstream data without knowing which
    stage produces it or where it's stored.

    The port must be bound to an OutputPort before use. The binding
    enforces type compatibility through Generic[T].

    Type parameter T specifies the data type this port consumes,
    matching the OutputPort[T] it connects to.

    Analogous to: sc_in<T> in SystemC, input wire in Verilog
    """

    def __init__(self, name: str):
        """Initialize input port.

        Args:
            name: Descriptive name for this input (e.g., "sha_bins", "forest")
        """
        super().__init__(name)
        self._source: OutputPort[T] | None = None

    def bind(self, source: OutputPort[T]) -> None:
        """Bind this input to an output port.

        This connects the input to its data source. The Generic[T] type
        parameter ensures type compatibility at compile time.

        Args:
            source: The output port to read from

        Example:
            stage.forest_input.bind(prev_stage.forest_output)
        """
        self._source = source

    def read(self) -> T:
        """Read data from connected output port.

        Returns:
            Data of type T from the bound output port

        Raises:
            RuntimeError: If port is not bound to a source
        """
        if self._source is None:
            raise RuntimeError(f"Input port '{self.name}' is not bound to any source")
        return self._source.read()

    def is_bound(self) -> bool:
        """Check if this input is connected to a source.

        Returns:
            True if bind() has been called, False otherwise
        """
        return self._source is not None
