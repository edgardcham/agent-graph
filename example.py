#!/usr/bin/env python3
"""Example of AgentGraph usage - Data processing pipeline"""

from src.agentgraph import Graph, State, node


@node("fetch")
def fetch_data(state: State) -> State:
    """Simulate API fetch"""
    print(f"[FETCH] Fetching data for query: {state.query}")
    data = {"users": 150, "revenue": 50000}
    return state.update(raw_data=data, fetched=True)


@node("validate")
def validate_data(state: State) -> State:
    """Validate fetched data"""
    data = state.raw_data
    is_valid = data.get("users", 0) > 0
    print(f"[VALIDATE] Data valid: {is_valid}")
    return state.update(valid=is_valid, user_count=data.get("users", 0))


@node("process_small")
def process_small_dataset(state: State) -> State:
    """Process small datasets"""
    print(f"[PROCESS_SMALL] Processing {state.user_count} users")
    return state.update(
        result=f"Small dataset: {state.user_count} users", processing_type="small"
    )


@node("process_large")
def process_large_dataset(state: State) -> State:
    """Process large datasets"""
    print(f"[PROCESS_LARGE] Processing {state.user_count} users")
    return state.update(
        result=f"Large dataset: {state.user_count} users", processing_type="large"
    )


@node("generate_report")
def generate_report(state: State) -> State:
    """Generate final report"""
    report = f"Report: {state.result} (via {state.processing_type})"
    print(f"[REPORT] {report}")
    return state.update(report=report)


def main():
    print("=== AgentGraph Example: Data Processing Pipeline ===\n")

    # Build graph
    g = Graph()

    # Add nodes with explicit names
    g.add_node("fetch", fetch_data)
    g.add_node("validate", validate_data)
    g.add_node("process_small", process_small_dataset)
    g.add_node("process_large", process_large_dataset)
    g.add_node("report", generate_report)

    # Define routing function
    def route_by_size(state: State) -> str:
        return "process_small" if state.user_count < 100 else "process_large"

    # Build the graph flow
    g.add_edge("fetch", "validate")
    g.add_conditional_edges("validate", route_by_size)
    g.add_edge("process_small", "report")
    g.add_edge("process_large", "report")
    g.add_edge("report", "END")

    # Execute graph
    initial = State({"query": "get user metrics"})
    result = g.run(initial)

    print("\n=== Final Result ===")
    print(f"Report: {result.report}")
    print(f"Execution path: {' -> '.join(result._execution_path)}")
    print(f"Total steps: {result._total_steps}")
    print(f"Completed: {result._completed}")

    # Demonstrate visualization
    print("\n=== Graph Visualization (Mermaid) ===")
    print(g.visualize())

    # Demonstrate streaming execution
    print("\n=== Streaming Execution ===")
    for i, state in enumerate(g.stream(State({"query": "streaming test"}))):
        print(
            f"Step {i + 1}: Last processed = {state._execution_path[-1] if hasattr(state, '_execution_path') and state._execution_path else 'Initial'}"
        )


if __name__ == "__main__":
    main()
