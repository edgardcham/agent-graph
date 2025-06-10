#!/usr/bin/env python3
"""Demo showing both node registration patterns with the new function-passing API"""

from src.agentgraph import END_NODE, START_NODE, Graph, Node, State, node


# Pattern 1: Decorator with automatic registration
@node("start")
def start_node(state: State) -> State:
    print("Starting...")
    return state.update(step=1)


@node("middle")
def middle_node(state: State) -> State:
    print(f"Middle step {state.step}")
    return state.update(step=2, data="processed")


# Pattern 2: Plain function (uses function name)
def end_node(state: State) -> State:
    print(f"End step {state.step}, data: {state.data}")
    return state.update(step=3, done=True)


def main():
    print("=== Both Registration Patterns Demo ===")

    # Create graph
    g = Graph()

    # NEW: Pass functions directly (no more "unused function" warnings!)
    g.add_node(start_node)  # Uses decorator name "start"
    g.add_node(middle_node)  # Uses decorator name "middle"
    g.add_node(end_node)  # Uses function name "end_node"

    # Add edges using START_NODE and END_NODE
    g.add_edge(START_NODE, "start")  # Sets entry point
    g.add_edge("start", "middle")
    g.add_edge("middle", "end_node")
    g.add_edge("end_node", END_NODE)  # Clean termination

    print("Graph nodes:", list(g.nodes.keys()))

    # Run
    initial = State({"task": "test both patterns"})
    final = g.run(initial)

    print(f"\nFinal state: done={final.done}")
    print("\nState history:")
    final.print_history()


def demo_conditional_routing():
    print("\n\n=== Conditional Routing Demo ===")

    @node("classifier")
    def classify(state: State) -> State:
        category = "premium" if state.value > 100 else "standard"
        print(f"Classified as: {category}")
        return state.update(category=category)

    @node("premium")
    def handle_premium(state: State) -> State:
        print("Handling premium case")
        return state.update(handled_by="premium")

    @node("standard")
    def handle_standard(state: State) -> State:
        print("Handling standard case")
        return state.update(handled_by="standard")

    # Router function
    def route_by_category(state: State) -> str:
        return state.category

    # Build graph - pass functions directly!
    g = Graph()
    g.add_node(classify)  # All functions are used now - no warnings!
    g.add_node(handle_premium)
    g.add_node(handle_standard)

    g.add_edge(START_NODE, "classifier")
    g.add_conditional_edges("classifier", route_by_category)
    g.add_edge("premium", END_NODE)
    g.add_edge("standard", END_NODE)

    # Test both paths
    print("--- High value (premium) ---")
    result1 = g.run(State({"value": 200}))
    print(f"Handled by: {result1.handled_by}")

    print("\n--- Low value (standard) ---")
    result2 = g.run(State({"value": 50}))
    print(f"Handled by: {result2.handled_by}")


def demo_mixed_patterns():
    print("\n\n=== Mixed Patterns Demo ===")

    # Pattern 1: Decorated with custom name
    @node("analyzer")
    def analyze_data(state: State) -> State:
        print("Analyzing data...")
        return state.update(analyzed=True)

    # Pattern 2: Plain function (uses function name)
    def process_results(state: State) -> State:
        print("Processing results...")
        return state.update(processed=True)

    # Pattern 3: Manual node creation
    def final_step(state: State) -> State:
        print("Final step...")
        return state.update(completed=True)

    manual_node = Node(final_step, "finale")

    g = Graph()
    g.add_node(analyze_data)  # Uses "analyzer" name from decorator
    g.add_node(process_results)  # Uses "process_results" function name
    g.add_node(manual_node)  # Uses "finale" name from Node constructor

    g.add_edge(START_NODE, "analyzer")
    g.add_edge("analyzer", "process_results")
    g.add_edge("process_results", "finale")
    g.add_edge("finale", END_NODE)

    print("Graph nodes:", list(g.nodes.keys()))

    result = g.run(State({"input": "test"}))
    print(
        f"Final: analyzed={result.analyzed}, processed={result.processed}, completed={result.completed}"
    )


def demo_backward_compatibility():
    print("\n\n=== Backward Compatibility Demo ===")

    @node("compat_test")
    def test_function(state: State) -> State:
        return state.update(tested=True)

    g = Graph()

    # Still works: string-based lookup from registry
    g.add_node(test_function)  # Finds test_function from registry

    # Also works: function-based (new way)
    def another_func(state: State) -> State:
        return state.update(done=True)

    g.add_node(another_func)

    g.add_edge(START_NODE, "compat_test")
    g.add_edge("compat_test", "another_func")
    g.add_edge("another_func", END_NODE)

    result = g.run(State({"mode": "compatibility"}))
    print(f"Tested: {result.tested}, Done: {result.done}")


if __name__ == "__main__":
    main()
    demo_conditional_routing()
    demo_mixed_patterns()
    demo_backward_compatibility()
