import os
from collections import defaultdict
from dataclasses import fields
from itertools import pairwise
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    List,
    Literal,
    Optional,
    Union,
    cast,
)

from ._types import TState
from .node import END, START, Node, RouterFunc, get_node
from .state import State


class LoopDetected(RuntimeError):
    """Raised when the graph execution exceeds max_steps, indicating a potential infinite loop."""

    def __init__(self, visited_nodes: List[str], max_steps: int):
        self.visited_nodes = visited_nodes
        self.max_steps = max_steps

        # Show last 10 nodes to help debug the loop
        recent_path = (
            " → ".join(visited_nodes[-10:])
            if len(visited_nodes) > 10
            else " → ".join(visited_nodes)
        )

        super().__init__(
            f"Graph execution exceeded {max_steps} steps, indicating a potential infinite loop. "
            f"Recent path: {recent_path}"
        )


class Graph(Generic[TState]):
    """Graph executor with state management and full type safety."""

    def __init__(
        self,
        checkpoint_every: Optional[int] = None,
        registry: Optional[Dict[str, Node[TState]]] = None,
    ):
        self.nodes: Dict[str, Node[TState]] = {}
        self.edges: Dict[str, List[Union[str, RouterFunc[TState]]]] = defaultdict(list)
        self.entry_point: Optional[str] = None
        self.checkpoints: defaultdict[str, list[TState]] = defaultdict(list)
        self.checkpoint_every = checkpoint_every
        self._execution_count = 0
        # Graph-local registry - each graph has its own isolated registry
        self._registry: Dict[str, Node[TState]] = registry or {}
        # NEW: Store conditional routing information for visualization
        self._conditional_routes: Dict[str, List[str]] = {}  # source -> list of targets

    def add_node(
        self,
        node_or_func: Union[str, Node[TState], Callable[[TState], TState]],
        node: Optional[Node[TState]] = None,
    ) -> "Graph[TState]":
        """Add node to graph

        Args:
            node_or_func: Can be:
                - Node instance (uses node.name)
                - Function decorated with @node (uses decorator name)
                - Function (uses function.__name__)
                - String name (for backward compatibility)
            node: Node instance (optional, for backward compatibility)
        """
        final_node: Node[TState]
        name: str

        if isinstance(node_or_func, str):
            # Backward compatibility: string name
            name = node_or_func
            if node is None:
                # Try to get from graph's local registry first, then global
                registry_node = self._registry.get(name) or get_node(name, None)
                if registry_node is None:
                    raise ValueError(
                        f"Node '{name}' not found in registry. Either provide the node instance or use @node('{name}') decorator."
                    )
                final_node = registry_node  # type: ignore
            else:
                final_node = node
        elif isinstance(node_or_func, Node):
            # Node instance passed directly
            final_node = node_or_func  # type: ignore
            name = final_node.name
        else:
            # Check if it's callable (function or Node instance)
            if hasattr(node_or_func, "func") and hasattr(node_or_func, "name"):
                # It's a Node instance (from decorator or manual creation)
                final_node = node_or_func  # type: ignore
                name = getattr(node_or_func, "name")
            elif callable(node_or_func):
                # Plain function - create Node
                name = getattr(node_or_func, "__name__", "unknown")
                final_node = Node(node_or_func, name)
            else:
                raise ValueError(f"Invalid node type: {type(node_or_func)}")

        self.nodes[name] = final_node

        # Also register in graph's local registry for future lookups
        self._registry[name] = final_node

        if self.entry_point is None:
            self.entry_point = name
        return self

    def node(
        self, name: Optional[str] = None
    ) -> Callable[[Callable[[TState], TState]], Node[TState]]:
        """Create a node decorator that registers to this graph's local registry.

        This ensures the node is isolated to this graph instance.

        Example:
            g = Graph[State]()

            @g.node("process")
            def process_data(state: State) -> State:
                return state.update(processed=True)
        """
        from .node import node_decorator

        return node_decorator(name, registry=self._registry)

    def add_edge(
        self,
        source: Union[str, RouterFunc[TState], Any],
        target: Union[str, RouterFunc[TState], Any],
    ) -> "Graph[TState]":
        """Add edge from source to target(s)

        Args:
            source: Source node name, START_NODE, or router function
            target: Target node name, END_NODE, or router function
        """
        # Handle START_NODE as source
        if hasattr(source, "name") and str(getattr(source, "name", "")) == "START":
            # START_NODE -> target means target becomes entry point
            if isinstance(target, str):
                if target not in self.nodes:
                    raise ValueError(f"Target node '{target}' not found in graph")
                self.entry_point = target
            elif hasattr(target, "name"):
                # Target is a node object, use its name
                target_name = str(getattr(target, "name", ""))
                if target_name and target_name in self.nodes:
                    self.entry_point = target_name
            return self

        # Handle normal edges
        if isinstance(source, str):
            source_name = source
        elif hasattr(source, "name"):
            source_name = str(getattr(source, "name", ""))
        else:
            source_name = str(source)  # fallback

        if isinstance(target, str):
            target_name = target
        elif hasattr(target, "name"):
            target_name = str(getattr(target, "name", ""))
        else:
            target_name = target  # Could be a router function

        if source_name not in self.nodes and source_name != "START":
            raise ValueError(f"Source node '{source_name}' not found in graph")

        self.edges[source_name].append(target_name)
        return self

    def add_path(self, *nodes: Any) -> "Graph[TState]":
        """Add a linear path of edges through multiple nodes.

        Args:
            *nodes: Sequence of node names, Node instances, START_NODE, or END_NODE

        Example:
            g.add_path(START_NODE, "fetch", "validate", "report", END_NODE)
        """
        if len(nodes) < 2:
            raise ValueError("add_path requires at least 2 nodes")

        # Normalize node references to names/special nodes
        normalized: List[Any] = []
        for n in nodes:
            if isinstance(n, str):
                normalized.append(n)
            elif isinstance(n, (START, END)):
                normalized.append(n)
            elif isinstance(n, Node):
                normalized.append(n.name)
            elif hasattr(n, "name"):
                normalized.append(n)
            else:
                raise ValueError(f"Invalid node type in path: {type(n)}")

        # Add edges between consecutive nodes
        for source, target in pairwise(normalized):
            self.add_edge(source, target)

        return self

    def add_conditional_edges(
        self,
        source: Union[str, Node[TState]],
        router: Callable[[TState], Any],
        routes: Optional[Dict[Any, Union[str, Node[TState]]]] = None,
        path_map: Optional[Dict[str, str]] = None,
    ) -> "Graph[TState]":
        """Add conditional edges based on router function.

        Args:
            source: Source node
            router: Function that returns a routing key
            routes: Mapping of router outputs to target nodes (NEW!)
            path_map: Legacy string mapping (backward compatibility)

        Example:
            # New way - semantic routing
            g.add_conditional_edges(
                source=validate,
                router=lambda s: "high" if s.score > 0.8 else "low",
                routes={"high": process_high, "low": process_low}
            )

            # Old way still works
            g.add_conditional_edges(
                source="validate",
                router=lambda s: "process_high" if s.score > 0.8 else "process_low"
            )
        """
        source_name = source.name if isinstance(source, Node) else source

        if routes:
            # NEW: Store the route targets for visualization
            route_targets: List[str] = []
            for target in routes.values():
                if isinstance(target, Node):
                    route_targets.append(target.name)
                else:
                    route_targets.append(str(target))
            self._conditional_routes[source_name] = route_targets

            # NEW: Route mapping provided
            def mapped_router(state: TState) -> Union[str, List[str], None]:
                result = router(state)

                # Handle single result
                if not isinstance(result, list):
                    target = routes.get(result)
                    if target is None:
                        return None
                    return target.name if isinstance(target, Node) else target

                # Handle multiple results with proper typing
                targets: List[str] = []
                result_list = cast(List[Any], result)  # Type assertion
                for key in result_list:
                    target = routes.get(key)
                    if target:
                        targets.append(
                            target.name if isinstance(target, Node) else target
                        )
                return targets if targets else None

            self.edges[source_name].append(mapped_router)

        elif path_map:
            # Store mapped targets for visualization
            self._conditional_routes[source_name] = list(path_map.values())

            # OLD: Backward compatibility with path_map
            def mapped_router(state: TState) -> Union[str, List[str], None]:
                result = router(state)
                if isinstance(result, str):
                    return path_map.get(result, result)
                elif isinstance(result, list):
                    mapped: List[str] = []
                    result_list = cast(List[str], result)  # Type assertion
                    for r in result_list:
                        mapped_value = path_map.get(r, r)
                        mapped.append(mapped_value)
                    return mapped if mapped else None
                return None  # Explicit None for other cases

            self.edges[source_name].append(mapped_router)

        else:
            # OLD: Raw router for backward compatibility
            self.edges[source_name].append(router)  # type: ignore[arg-type]

        return self

    def set_entry_point(self, name: str) -> "Graph[TState]":
        """Explicitly set entry point"""
        if name not in self.nodes:
            raise ValueError(f"Node '{name}' not found in graph")
        self.entry_point = name
        return self

    def run(self, initial_state: TState, *, max_steps: int = 100) -> TState:
        """Execute graph from entry point with full type safety"""
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

        # Check if we exceeded max_steps (potential infinite loop)
        if step >= max_steps and current_name and current_name != "END":
            raise LoopDetected(visited, max_steps)

        # Add execution metadata for State objects
        if isinstance(state, State):
            state = state.update(
                _execution_path=visited,
                _total_steps=step,
                _completed=current_name is None or current_name == "END",
            )  # type: ignore

        return state  # type: ignore[return-value]

    def _get_next_node(self, current_name: str, state: TState) -> Optional[str]:
        """Determine next node based on edges"""
        edges = self.edges.get(current_name, [])

        for edge in edges:
            if isinstance(edge, str):
                # Direct edge
                return edge if edge in self.nodes or edge == "END" else None
            elif callable(edge):
                # Router function
                result = edge(state)

                # NEW: Handle Node instances returned from router
                if hasattr(result, "name"):  # It's a Node!
                    node_name: str = getattr(result, "name")
                    return node_name if node_name in self.nodes else None
                elif isinstance(result, str):
                    return result if result in self.nodes or result == "END" else None
                elif isinstance(result, list) and result:
                    # Return first valid node from list
                    for item in result:
                        if hasattr(item, "name"):  # Node instance
                            node_name = getattr(item, "name")
                        else:  # String
                            node_name = str(item)

                        if node_name in self.nodes or node_name == "END":
                            return node_name

        return None

    def _maybe_checkpoint(self, node_name: str, state: TState) -> None:
        """Save checkpoint if configured"""
        self._execution_count += 1
        self.checkpoints[node_name].append(state)

        if self.checkpoint_every and self._execution_count % self.checkpoint_every == 0:
            pass

    def visualize(
        self,
        format: Literal["mermaid", "png", "svg", "pdf"] = "mermaid",
        filename: Optional[str] = None,
        view: bool = False,
    ) -> str:
        """Generate graph visualization in multiple formats

        Args:
            format: Output format - "mermaid" for text, "png"/"svg"/"pdf" for images
            filename: Optional filename to save image (only for image formats)
            view: Whether to open the generated image (only for image formats)

        Returns:
            For "mermaid": Returns the mermaid diagram text
            For image formats: Returns the path to the generated file

        Examples:
            # Get mermaid text
            mermaid_text = graph.visualize()

            # Generate PNG image
            image_path = graph.visualize("png", "my_graph.png")

            # Generate and open SVG
            svg_path = graph.visualize("svg", view=True)
        """
        if format == "mermaid":
            return self._generate_mermaid()
        else:
            return self._generate_image(format, filename, view)

    def _generate_mermaid(self) -> str:
        """Generate Mermaid diagram text"""
        lines = ["graph TD"]

        # Add START node if there's an entry point
        if self.entry_point:
            lines.append("    START_NODE[START]")

        # Add regular nodes with better styling
        for name in self.nodes:
            lines.append(f"    {name}[{name}]")

        # Add END node if referenced
        if any("END" in str(edges) for edges in self.edges.values()):
            lines.append("    END_NODE((END))")

        # Add entry point connection FIRST (before other edges)
        if self.entry_point:
            lines.append(f"    START_NODE --> {self.entry_point}")

        # Track edges we've already added to avoid duplicates
        added_edges: set[Union[tuple[str, str], str]] = set()

        # Add edges
        for source, edges in self.edges.items():
            for edge in edges:
                if isinstance(edge, str):
                    edge_key = (source, edge)
                    if edge_key not in added_edges:
                        added_edges.add(edge_key)
                        if edge == "END":
                            lines.append(f"    {source} --> END_NODE")
                        else:
                            lines.append(f"    {source} --> {edge}")
                else:
                    # Router function - show conditional routing
                    router_id = f"{source}_router"
                    if router_id not in added_edges:  # Only add router once
                        added_edges.add(router_id)
                        lines.append(f"    {router_id}{{router}}")
                        lines.append(f"    {source} --> {router_id}")

                        # Use stored conditional routes if available
                        if source in self._conditional_routes:
                            # We know the exact targets from the routes mapping
                            for dest in self._conditional_routes[source]:
                                lines.append(f"    {router_id} -.-> {dest}")
                        else:
                            # Fallback: try to guess conditional destinations
                            # (This is the old logic, kept for backward compatibility)
                            conditional_destinations: List[str] = []

                            # Find all nodes that are targets of direct edges
                            all_direct_targets: set[str] = set()
                            for _, edge_list in self.edges.items():
                                for e in edge_list:
                                    if isinstance(e, str):
                                        all_direct_targets.add(e)

                            # Conditional destinations are nodes that exist but aren't direct targets
                            # AND have outgoing edges (meaning they're part of the flow)
                            for node_name in self.nodes:
                                if (
                                    node_name != source
                                    and node_name not in all_direct_targets
                                    and node_name in self.edges
                                ):  # Has outgoing edges
                                    conditional_destinations.append(node_name)

                            # Add conditional routing connections
                            for dest in conditional_destinations:
                                lines.append(f"    {router_id} -.-> {dest}")

        return "\n".join(lines)

    def _generate_image(
        self,
        format: Literal["png", "svg", "pdf"],
        filename: Optional[str] = None,
        view: bool = False,
    ) -> str:
        """Generate image using graphviz"""
        try:
            import graphviz  # type: ignore
        except ImportError:
            raise ImportError(
                "graphviz is required for image generation. Install with: "
                "pip install graphviz (and ensure graphviz system package is installed)"
            )

        # Create graphviz Digraph
        dot = graphviz.Digraph(comment="AgentGraph Visualization")  # type: ignore
        dot.attr(rankdir="TB", size="8,6")  # type: ignore
        dot.attr("node", shape="box", style="rounded,filled", fillcolor="lightblue")  # type: ignore

        # Add START node
        if self.entry_point:
            dot.node("START", "START", shape="ellipse", fillcolor="lightgreen")  # type: ignore

        # Add regular nodes
        for name in self.nodes:
            dot.node(name, name)  # type: ignore

        # Add END node if needed
        has_end = any("END" in str(edges) for edges in self.edges.values())
        if has_end:
            dot.node("END", "END", shape="ellipse", fillcolor="lightcoral")  # type: ignore

        # Track which routers and edges we've already created
        created_routers: set[str] = set()
        created_edges: set[tuple[str, str]] = (
            set()
        )  # NEW: Track all edges to avoid duplicates

        # Add edges
        for source, edges in self.edges.items():
            for edge in edges:
                if isinstance(edge, str):
                    # Create edge key to track duplicates
                    if edge == "END":
                        edge_key = (source, "END")
                    else:
                        edge_key = (source, edge)

                    # Only add if not already created
                    if edge_key not in created_edges:
                        created_edges.add(edge_key)
                        if edge == "END":
                            dot.edge(source, "END")  # type: ignore
                        else:
                            dot.edge(source, edge)  # type: ignore
                else:
                    # Router function - create a diamond decision node
                    router_id = f"{source}_router"

                    # Only create router once
                    if router_id not in created_routers:
                        created_routers.add(router_id)
                        dot.node(  # type: ignore
                            router_id, "router", shape="diamond", fillcolor="yellow"
                        )
                        dot.edge(source, router_id)  # type: ignore  # No label

                        # Connect router to its destinations
                        if source in self._conditional_routes:
                            # We know the exact targets from the routes mapping
                            for dest in self._conditional_routes[source]:
                                router_edge_key = (router_id, dest)
                                if router_edge_key not in created_edges:
                                    created_edges.add(router_edge_key)
                                    dot.edge(router_id, dest, style="dashed")  # type: ignore
                        else:
                            # Fallback: try to find conditional destinations
                            all_direct_edges: set[str] = set()
                            for _, edge_list in self.edges.items():
                                for e in edge_list:
                                    if isinstance(e, str):
                                        all_direct_edges.add(e)

                            # Find nodes that have edges but aren't direct targets
                            for node_name in self.nodes:
                                if (
                                    node_name != source
                                    and node_name not in all_direct_edges
                                    and node_name in self.edges
                                ):
                                    router_edge_key = (router_id, node_name)
                                    if router_edge_key not in created_edges:
                                        created_edges.add(router_edge_key)
                                        dot.edge(router_id, node_name, style="dashed")  # type: ignore

        # Add entry point connection
        if self.entry_point:
            dot.edge("START", self.entry_point)  # type: ignore

        # Determine output filename
        if filename is None:
            filename = f"agentgraph_visualization.{format}"
        elif not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"

        # Remove extension for graphviz (it adds it automatically)
        base_filename = filename.rsplit(".", 1)[0]

        # Render the graph
        try:
            output_path = dot.render(base_filename, format=format, cleanup=True)  # type: ignore

            if view:
                try:
                    import webbrowser

                    webbrowser.open(f"file://{os.path.abspath(output_path)}")  # type: ignore
                except Exception:
                    print(f"Could not open {output_path} automatically")

            return output_path

        except Exception as e:
            raise RuntimeError(f"Failed to generate {format} image: {str(e)}")

    def stream(self, initial_state: TState) -> Generator[TState, None, None]:
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
