"""Type definitions and protocols for AgentGraph.

This module provides the type system foundation for v0.2.0,
enabling full type safety across the library.
"""

from typing import Any, Dict, Protocol, Tuple, TypeVar, runtime_checkable

from typing_extensions import Self


@runtime_checkable
class SupportsState(Protocol):
    """Protocol for state objects that can be used with AgentGraph.

    Both State and BaseState implement this protocol.
    """

    def update(self, **kwargs: Any) -> Self:
        """Return a new state with updated fields."""
        ...

    def _record_snapshot(
        self, node_name: str, changes: Dict[str, Tuple[Any, Any]]
    ) -> None:
        """Record a state snapshot (internal use)."""
        ...


# Generic type variable for state objects
TState = TypeVar("TState", bound=SupportsState)


# Type aliases for better readability
NodeName = str
Changes = Dict[str, Tuple[Any, Any]]
