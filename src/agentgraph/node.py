from typing import Any, Callable, Dict, Generic, List, Optional, Union

from ._types import TState

# Global registry for nodes created with decorators
_node_registry: Dict[str, "Node[Any]"] = {}


class Node(Generic[TState]):
    """Base node class with generic state type support."""

    def __init__(
        self,
        func: Callable[[TState], TState],
        name: Optional[str] = None,
    ):
        self.func = func
        self.name = name or func.__name__
        self._metadata: Dict[str, Any] = {}

        # Note: No automatic registration to avoid graph collisions
        # Registration is handled by the @node decorator or graph.add_node()

    def __call__(self, state: TState) -> TState:
        """Execute node function"""
        return self.func(state)

    def __repr__(self) -> str:
        return f"Node({self.name})"


def node(func: Callable[[TState], TState], name: Optional[str] = None) -> Node[TState]:
    """Create a node from a function.

    Args:
        func: Function that transforms state
        name: Optional node name (defaults to function name)

    Returns:
        Node instance

    Example:
        fetch = ag.node(fetch_func)
        process = ag.node(process_func, "processor")
    """
    return Node(func, name or func.__name__)


def node_decorator(
    name: Optional[str] = None, *, registry: Optional[Dict[str, Any]] = None
) -> Callable[[Callable[[TState], TState]], Node[TState]]:
    """Decorator for creating nodes.

    Example:
        @ag.node_decorator("processor")
        def process(state):
            return state.update(processed=True)
    """

    def decorator(func: Callable[[TState], TState]) -> Node[TState]:
        node_instance = Node(func, name)

        # Register in the specified registry, or global by default
        target_registry = registry if registry is not None else _node_registry
        target_registry[node_instance.name] = node_instance

        return node_instance

    return decorator


def get_node(
    name: str, registry: Optional[Dict[str, Any]] = None
) -> Optional[Node[Any]]:
    """Get a node from the registry by name"""
    if registry is not None:
        return registry.get(name)
    return _node_registry.get(name)


class SpecialNode:
    """Base class for special nodes"""

    def __init__(self, name: str):
        self.name = name

    def __call__(self, state: Any) -> Any:
        return state

    def __repr__(self) -> str:
        return self.name


class START(SpecialNode):
    """Special node to signal start of execution"""

    def __init__(self):
        super().__init__("START")


class END(SpecialNode):
    """Special node to signal end of execution"""

    def __init__(self):
        super().__init__("END")


# Singleton instances
START_NODE = START()
END_NODE = END()


# Type for conditional routing functions - now generic
RouterFunc = Callable[[TState], Union[str, List[str], None]]
