"""AgentGraph - Dead simple agent graphs"""

from ._types import SupportsState, TState
from .conditions import (
    all_conditions,
    any_conditions,
    custom_condition,
    field_contains,
    field_equals,
    field_exists,
    field_ge,
    field_gt,
    field_in,
    field_is_false,
    field_is_none,
    field_is_not_none,
    field_is_true,
    field_le,
    field_len_equals,
    field_len_gt,
    field_lt,
    field_matches,
    field_not_equals,
    field_not_in,
    field_type_is,
    has_field,
    not_condition,
    when,
)
from .graph import Graph, LoopDetected
from .node import END_NODE, START_NODE, Node, RouterFunc, get_node, node, node_decorator
from .state import BaseState, State

__version__ = "0.2.0"
__all__ = [
    # Core types
    "TState",
    "SupportsState",
    "RouterFunc",
    # State management
    "State",
    "BaseState",
    # Node system
    "Node",
    "node",
    "node_decorator",
    "get_node",
    "START_NODE",
    "END_NODE",
    # Graph execution
    "Graph",
    "LoopDetected",
    # Conditions
    "when",
    "has_field",
    "field_exists",
    "field_equals",
    "field_not_equals",
    "field_gt",
    "field_ge",
    "field_lt",
    "field_le",
    "field_in",
    "field_not_in",
    "field_contains",
    "field_matches",
    "field_len_equals",
    "field_len_gt",
    "field_is_true",
    "field_is_false",
    "field_is_none",
    "field_is_not_none",
    "field_type_is",
    "all_conditions",
    "any_conditions",
    "not_condition",
    "custom_condition",
]
