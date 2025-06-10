#!/usr/bin/env python3
"""Simple example of AgentGraph usage"""

from src.agentgraph import Graph, State, node


@node("fetch_data")
def fetch_data(state: State) -> State:
    """Fetch some data"""
    print(f"Fetching data for query: {state.query}")
    data = {"users": 150, "revenue": 50000}
    return state.update(raw_data=data, fetched=True)


@node("validate")
def validate_data(state: State) -> State:
    """Validate the data"""
    data = state.raw_data
    is_valid = data.get("users", 0) > 0
    print(f"Data valid: {is_valid}, user count: {data.get('users', 0)}")
    return state.update(valid=is_valid, user_count=data.get("users", 0))


@node("process_small")
def process_small(state: State) -> State:
    """Process small dataset"""
    print(f"Processing small dataset: {state.user_count} users")
    return state.update(
        result=f"Small dataset: {state.user_count} users", processing_type="small"
    )


@node("process_large")
def process_large(state: State) -> State:
    """Process large dataset"""
    print(f"Processing large dataset: {state.user_count} users")
    return state.update(
        result=f"Large dataset: {state.user_count} users", processing_type="large"
    )


@node("report")
def generate_report(state: State) -> State:
    """Generate report"""
    report_text = (
        f"Final report: {state.result} (processed via {state.processing_type})"
    )
    print(f"Generated: {report_text}")
    return state.update(report=report_text)


def main():
    # Create graph
    g = Graph()

    # Add nodes to graph with explicit names
    g.add_node("fetch_data", fetch_data)
    g.add_node("validate", validate_data)
    g.add_node("process_small", process_small)
    g.add_node("process_large", process_large)
    g.add_node("report", generate_report)

    # Define routing function
    def route_by_size(state: State) -> str:
        return "process_small" if state.user_count < 100 else "process_large"

    # Define flow using explicit edges
    g.add_edge("fetch_data", "validate")
    g.add_conditional_edges("validate", route_by_size)
    g.add_edge("process_small", "report")
    g.add_edge("process_large", "report")
    g.add_edge("report", "END")

    # Create initial state - this is where you define your starting data
    initial_state = State({"query": "get user metrics", "timestamp": "2024-01-10"})

    # Run the graph
    print("=== Running Graph ===")
    final_state = g.run(initial_state)

    # Access results
    print("\n=== Results ===")
    print(f"Final report: {final_state.report}")
    print(f"Execution path: {' -> '.join(final_state._execution_path)}")
    print(f"Completed: {final_state._completed}")

    # Show graph visualization
    print("\n=== Graph Structure (Mermaid) ===")
    print(g.visualize())


if __name__ == "__main__":
    main()
