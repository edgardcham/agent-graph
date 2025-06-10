from typing import Any, Callable, List, Optional, Union, TypeVar

from .state import BaseState, State

StateType = Union[State, BaseState]
T = TypeVar('T', bound=StateType)

# Global registry for nodes created with decorators
_node_registry: dict[str, 'Node'] = {}


class Node:
    """Base node class"""

    def __init__(
        self,
        func: Callable[[Any], Any],
        name: Optional[str] = None,
    ):
        self.func = func
        self.name = name or func.__name__
        self._metadata: dict[str, Any] = {}
        
        # Register node if it has a name
        if self.name:
            _node_registry[self.name] = self

    def __call__(self, state: Any) -> Any:
        """Execute node function"""
        return self.func(state)

    def __repr__(self) -> str:
        return f"Node({self.name})"


def node(
    name: Optional[str] = None,
) -> Callable[[Callable[[Any], Any]], Node]:
    """Decorator for creating nodes"""

    def decorator(func: Callable[[Any], Any]) -> Node:
        return Node(func, name)

    return decorator


def get_node(name: str) -> Optional[Node]:
    """Get a node from the registry by name"""
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


# Type for conditional routing functions  
RouterFunc = Callable[[Any], Union[str, List[str], None]]
