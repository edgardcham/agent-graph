from collections import defaultdict
from dataclasses import fields
from typing import Any, Dict, Generator, List, Optional, Union

from .node import Node, RouterFunc, StateType, get_node
from .state import State


class Graph:
    """Graph executor with state management"""

    def __init__(self, checkpoint_every: Optional[int] = None):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[Union[str, RouterFunc]]] = defaultdict(list)
        self.entry_point: Optional[str] = None
        self.checkpoints: defaultdict[str, list[Any]] = defaultdict(list)
        self.checkpoint_every = checkpoint_every
        self._execution_count = 0

    def add_node(self, node_or_func: Union[str, Node, Any], node: Optional[Node] = None) -> "Graph":
        """Add node to graph
        
        Args:
            node_or_func: Can be:
                - Node instance (uses node.name)
                - Function decorated with @node (uses decorator name)
                - Function (uses function.__name__)
                - String name (for backward compatibility)
            node: Node instance (optional, for backward compatibility)
        """
        final_node: Node
        name: str
        
        if isinstance(node_or_func, str):
            # Backward compatibility: string name
            name = node_or_func
            if node is None:
                # Try to get from registry
                registry_node = get_node(name)
                if registry_node is None:
                    raise ValueError(f"Node '{name}' not found in registry. Either provide the node instance or use @node('{name}') decorator.")
                final_node = registry_node
            else:
                final_node = node
        elif isinstance(node_or_func, Node):
            # Node instance passed directly
            final_node = node_or_func
            name = final_node.name
        else:
            # Function passed (decorated or plain)
            func = node_or_func
            if hasattr(func, 'name') and hasattr(func, 'func'):
                # It's a decorated Node
                final_node = func
                name = final_node.name
            else:
                # Plain function - create Node
                name = func.__name__
                final_node = Node(func, name)
        
        self.nodes[name] = final_node
        if self.entry_point is None:
            self.entry_point = name
        return self

    def add_edge(self, source: Union[str, RouterFunc, Any], target: Union[str, RouterFunc, Any]) -> "Graph":
        """Add edge from source to target(s)
        
        Args:
            source: Source node name, START_NODE, or router function
            target: Target node name, END_NODE, or router function
        """
        # Handle START_NODE as source
        if hasattr(source, 'name') and str(getattr(source, 'name', '')) == "START":
            # START_NODE -> target means target becomes entry point
            if isinstance(target, str):
                if target not in self.nodes:
                    raise ValueError(f"Target node '{target}' not found in graph")
                self.entry_point = target
            elif hasattr(target, 'name'):
                # Target is a node object, use its name
                target_name = str(getattr(target, 'name', ''))
                if target_name and target_name in self.nodes:
                    self.entry_point = target_name
            return self
        
        # Handle normal edges
        if isinstance(source, str):
            source_name = source
        elif hasattr(source, 'name'):
            source_name = str(getattr(source, 'name', ''))
        else:
            source_name = str(source)  # fallback
            
        if isinstance(target, str):
            target_name = target
        elif hasattr(target, 'name'):
            target_name = str(getattr(target, 'name', ''))
        else:
            target_name = target  # Could be a router function
        
        if source_name not in self.nodes and source_name != "START":
            raise ValueError(f"Source node '{source_name}' not found in graph")
        
        self.edges[source_name].append(target_name)
        return self

    def add_conditional_edges(
        self, source: str, router: RouterFunc, path_map: Optional[Dict[str, str]] = None
    ) -> "Graph":
        """Add conditional edges based on router function

        Args:
            source: Source node name
            router: Function that returns next node name(s) based on state
            path_map: Optional mapping of router outputs to node names
        """
        if path_map:
            # Wrap router to apply path mapping
            def mapped_router(state: StateType) -> Union[str, List[str], None]:
                result = router(state)
                if isinstance(result, str):
                    return path_map.get(result, result)
                elif isinstance(result, list):
                    return [path_map.get(r, r) for r in result]
                return result

            self.edges[source].append(mapped_router)
        else:
            self.edges[source].append(router)
        return self

    def set_entry_point(self, name: str) -> "Graph":
        """Explicitly set entry point"""
        if name not in self.nodes:
            raise ValueError(f"Node '{name}' not found in graph")
        self.entry_point = name
        return self

    def run(self, initial_state: Any, max_steps: int = 100) -> Any:
        """Execute graph from entry point"""
        if not self.entry_point:
            raise ValueError("No entry point defined")

        if self.entry_point not in self.nodes:
            raise ValueError(f"Entry point '{self.entry_point}' not found in nodes")

        current_name = self.entry_point
        state = initial_state
        visited: list[str] = []
        step = 0

        while current_name and step < max_steps:
            visited.append(current_name)

            # Handle END node
            if current_name == "END":
                break

            # Get current node
            current_node = self.nodes.get(current_name)
            if not current_node:
                raise ValueError(f"Node '{current_name}' not found")

            # Track state before execution
            old_state = state

            # Execute node
            try:
                state = current_node(state)

                # Record changes if state supports it
                if hasattr(state, "_record_snapshot"):
                    # Calculate changes based on state type
                    changes: Dict[str, tuple[Any, Any]] = {}

                    if isinstance(state, State) and isinstance(old_state, State):
                        # For State objects, compare the dict representations
                        old_dict = old_state.dict
                        new_dict = state.dict
                        for key in new_dict:
                            old_val = old_dict.get(key)
                            new_val = new_dict.get(key)
                            if old_val != new_val:
                                changes[key] = (old_val, new_val)
                    else:
                        # For BaseState, compare field by field using dataclass fields
                        from dataclasses import is_dataclass

                        if is_dataclass(state) and is_dataclass(old_state):
                            try:
                                # Only call fields() on confirmed dataclass instances
                                old_fields = fields(old_state)
                                new_fields = fields(state)

                                old_dict = {
                                    f.name: getattr(old_state, f.name)
                                    for f in old_fields
                                    if not f.name.startswith("_")
                                }
                                new_dict = {
                                    f.name: getattr(state, f.name)
                                    for f in new_fields
                                    if not f.name.startswith("_")
                                }
                                for key in new_dict:
                                    if old_dict.get(key) != new_dict.get(key):
                                        changes[key] = (
                                            old_dict.get(key),
                                            new_dict.get(key),
                                        )
                            except Exception:
                                pass

                    # Record the snapshot - accessing protected method by design
                    state._record_snapshot(current_name, changes)  # type: ignore

            except Exception as e:
                # Add error to state
                if isinstance(state, State):
                    state = state.update(_error=str(e), _failed_node=current_name)
                else:
                    # For BaseState, we can't add arbitrary fields
                    raise RuntimeError(f"Node '{current_name}' failed: {str(e)}")
                break

            # Checkpoint if needed
            self._maybe_checkpoint(current_name, state)

            # Find next node
            next_node_name = self._get_next_node(current_name, state)
            current_name = next_node_name
            step += 1

        # Add execution metadata for State objects
        if isinstance(state, State):
            state = state.update(
                _execution_path=visited,
                _total_steps=step,
                _completed=current_name is None or current_name == "END",
            )

        return state

    def _get_next_node(self, current_name: str, state: Any) -> Optional[str]:
        """Determine next node based on edges"""
        edges = self.edges.get(current_name, [])

        for edge in edges:
            if isinstance(edge, str):
                # Direct edge
                return edge if edge in self.nodes or edge == "END" else None
            elif callable(edge):
                # Router function
                result = edge(state)
                if isinstance(result, str):
                    return result if result in self.nodes or result == "END" else None
                elif isinstance(result, list) and result:
                    # Return first valid node from list
                    for node_name in result:
                        if node_name in self.nodes or node_name == "END":
                            return node_name

        return None

    def _maybe_checkpoint(self, node_name: str, state: Any) -> None:
        """Save checkpoint if configured"""
        self._execution_count += 1
        self.checkpoints[node_name].append(state)

        if self.checkpoint_every and self._execution_count % self.checkpoint_every == 0:
            pass

    def visualize(self) -> str:
        """Generate Mermaid diagram"""
        lines = ["graph TD"]

        # Add nodes
        for name in self.nodes:
            lines.append(f"    {name}[{name}]")

        # Add END node if referenced
        if any("END" in str(edges) for edges in self.edges.values()):
            lines.append("    END((END))")

        # Add edges
        for source, edges in self.edges.items():
            for edge in edges:
                if isinstance(edge, str):
                    lines.append(f"    {source} --> {edge}")
                else:
                    # Router function
                    lines.append(f"    {source} -->|router| ?")

        return "\n".join(lines)

    def stream(self, initial_state: Any) -> Generator[Any, None, None]:
        """Yield state after each node execution"""
        if not self.entry_point:
            raise ValueError("No entry point defined")

        current_name = self.entry_point
        state = initial_state

        while current_name and current_name != "END":
            current_node = self.nodes.get(current_name)
            if not current_node:
                break

            state = current_node(state)
            yield state

            next_node_name = self._get_next_node(current_name, state)
            current_name = next_node_name
