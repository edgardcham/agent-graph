#!/usr/bin/env python3
"""Demo showcasing the improved visualization with AgentGraph v0.2.0"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.agentgraph import END_NODE, START_NODE, BaseState, Graph, node


@dataclass
class ProcessState(BaseState):
    data: Optional[str] = None
    validation_result: Optional[str] = None
    processing_type: Optional[str] = None
    result: Optional[str] = None


# Define processing types with enum
class ProcessingType(Enum):
    CRITICAL = "critical"
    NORMAL = "normal"
    LOW = "low"


def main():
    g = Graph[ProcessState]()

    # Create nodes using clean API
    def fetch_func(state: ProcessState) -> ProcessState:
        print("Fetching data...")
        return state.update(data="Important business data")

    def validate_func(state: ProcessState) -> ProcessState:
        print("Validating data...")
        if state.data and "business" in state.data:
            return state.update(validation_result="valid", processing_type="critical")
        elif state.data:
            return state.update(validation_result="valid", processing_type="normal")
        else:
            return state.update(validation_result="invalid", processing_type="low")

    def process_critical_func(state: ProcessState) -> ProcessState:
        print("CRITICAL processing...")
        return state.update(result=f"[URGENT] {state.data}")

    def process_normal_func(state: ProcessState) -> ProcessState:
        print("Normal processing...")
        return state.update(result=f"[PROCESSED] {state.data}")

    def process_low_func(state: ProcessState) -> ProcessState:
        print("Low priority processing...")
        return state.update(result=f"[ARCHIVED] {state.data or 'No data'}")

    def report_func(state: ProcessState) -> ProcessState:
        print(f"Final report: {state.result}")
        return state

    # Create nodes
    fetch = node(fetch_func, "fetch")
    validate = node(validate_func, "validate")
    process_critical = node(process_critical_func, "critical")
    process_normal = node(process_normal_func, "normal")
    process_low = node(process_low_func, "low")
    report = node(report_func, "report")

    # Add all nodes
    g.add_node(fetch)
    g.add_node(validate)
    g.add_node(process_critical)
    g.add_node(process_normal)
    g.add_node(process_low)
    g.add_node(report)

    # Build graph with clear flow
    g.add_edge(START_NODE, fetch)
    g.add_edge(fetch, validate)

    # Semantic routing with clear route mapping
    def priority_router(state: ProcessState) -> str:
        if state.processing_type == "critical":
            return ProcessingType.CRITICAL.value
        elif state.processing_type == "normal":
            return ProcessingType.NORMAL.value
        else:
            return ProcessingType.LOW.value

    g.add_conditional_edges(
        source=validate,
        router=priority_router,
        routes={
            ProcessingType.CRITICAL.value: process_critical,
            ProcessingType.NORMAL.value: process_normal,
            ProcessingType.LOW.value: process_low,
        },
    )

    # All processing paths lead to report
    g.add_path(process_critical, report, END_NODE)
    g.add_path(process_normal, report, END_NODE)
    g.add_path(process_low, report, END_NODE)

    # Run the graph
    print("=== Running Graph ===")
    result = g.run(ProcessState())
    print(f"\nFinal state: {result}")

    # Show Mermaid visualization
    print("\n=== Mermaid Visualization ===")
    mermaid = g.visualize()
    print(mermaid)

    # Generate and show image path
    print("\n=== Image Generation ===")
    png_path = g.visualize(format="png", filename="process_flow.png")
    print(f"PNG generated at: {png_path}")

    svg_path = g.visualize(format="svg", filename="process_flow.svg")
    print(f"SVG generated at: {svg_path}")


if __name__ == "__main__":
    main()
