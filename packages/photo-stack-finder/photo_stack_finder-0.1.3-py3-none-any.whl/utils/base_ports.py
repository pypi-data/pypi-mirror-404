"""Base classes for port-based pipeline connectivity.

This module contains the non-generic base classes that define the port interface.
These classes have minimal dependencies to avoid circular imports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol


class StageProtocol(Protocol):
    """Protocol defining the minimal interface needed from a pipeline stage.

    This avoids circular dependency with pipeline_stage module.
    """

    stage_name: str

    def get_cache_timestamp(self) -> float:
        """Get timestamp when outputs were last computed.

        Returns:
            Modification time in seconds since epoch
        """
        ...

    def get_ref_photo_count(self) -> int | None:
        """Get count of reference photos after stage has run.

        Returns:
            Count of reference photos, or None if not available or stage hasn't run
        """
        ...

    def get_ref_sequence_count(self) -> int | None:
        """Get count of reference sequences after stage has run.

        Returns:
            Count of reference sequences, or None if not available or stage hasn't run
        """
        ...


class BaseOutputPort:
    """Non-generic base class for output ports.

    Enables type checking and collections that work with any output port
    regardless of data type. Useful for graph validation where we check
    port connectivity without reading data.
    """

    owner: StageProtocol  # Actual type is PipelineStage, but avoiding circular import

    def __init__(
        self,
        owner: StageProtocol,
    ):
        """Initialize output port.

        Args:
            owner: The stage that produces this output (used for timestamps)

        """
        self.owner = owner

    def timestamp(self) -> float:
        """Get when this output was last updated.

        All output ports from the same stage share the same timestamp
        (they are computed together).

        Returns:
            Modification time in seconds since epoch, or 0.0 if never computed
        """
        return self.owner.get_cache_timestamp()

    def get_ref_photo_count(self) -> int | None:
        """Get count of reference photos from owner stage.

        Returns:
            Count of reference photos in the owner, or None if not available
        """
        return self.owner.get_ref_photo_count()

    def get_ref_sequence_count(self) -> int | None:
        """Get count of reference sequences from owner stage.

        Returns:
            Count of reference sequences in the owner, or None if not available
        """
        return self.owner.get_ref_sequence_count()


class BaseInputPort(ABC):
    """Non-generic base class for input ports.

    Enables type checking and collections that work with any input port
    regardless of data type. Useful for graph validation where we check
    port connectivity without reading data.
    """

    _source: BaseOutputPort | None
    name: str

    def __init__(self, name: str):
        """Initialize input port.

        Args:
            name: Descriptive name for this input (e.g., "sha_bins", "forest")
        """
        self.name = name

    @abstractmethod
    def is_bound(self) -> bool:
        """Check if this input is connected to a source.

        Returns:
            True if bind() has been called, False otherwise
        """
        ...

    def timestamp(self) -> float:
        """Get timestamp from connected output.

        Returns:
            Timestamp from bound output port, or 0.0 if not bound

        Raises:
            RuntimeError: If port is not bound (should check is_bound() first)
        """
        if self._source is None:
            raise RuntimeError(f"Input port '{self.name}' is not bound to any source")
        ts = self._source.timestamp()
        if ts is None:
            raise RuntimeError(f"{self._source.owner.stage_name} is reporting None timestamp")
        return ts

    def get_ref_photo_count(self) -> int | None:
        """Get count of reference photos from connected source.

        Returns:
            Count of reference photos from source, or None if not available

        Raises:
            RuntimeError: If port is not bound to a source
        """
        if self._source is None:
            raise RuntimeError(f"Input port '{self.name}' is not bound to any source")
        return self._source.get_ref_photo_count()

    def get_ref_sequence_count(self) -> int | None:
        """Get count of reference sequences from connected source.

        Returns:
            Count of reference sequences from source, or None if not available

        Raises:
            RuntimeError: If port is not bound to a source
        """
        if self._source is None:
            raise RuntimeError(f"Input port '{self.name}' is not bound to any source")
        return self._source.get_ref_sequence_count()


class BaseChannel:
    """Non-generic base class for channels.

    Enables type checking and collections that work with any channel
    regardless of data type. Useful for graph storage where we track
    channels with different type parameters.
    """

    output: BaseOutputPort
    input: BaseInputPort
