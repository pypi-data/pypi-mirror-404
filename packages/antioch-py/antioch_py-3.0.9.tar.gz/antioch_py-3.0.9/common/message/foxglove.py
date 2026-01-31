from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FoxgloveConvertible(Protocol):
    """
    Protocol for messages that can be converted to Foxglove format.

    Implement this protocol for any message type that has a corresponding Foxglove
    schema. The protocol provides a conversion method that returns the Foxglove type.
    """

    def to_foxglove(self) -> Any | None:
        """
        Convert this message to its Foxglove representation.

        :return: The Foxglove schema object, or None if this message should not be published.
        """

        ...
