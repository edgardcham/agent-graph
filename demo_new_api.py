#!/usr/bin/env python3
"""Demo using the new AgentGraph v0.2.0 API improvements"""

import random
from dataclasses import dataclass
from typing import Optional

from src.agentgraph import END_NODE, START_NODE, BaseState, Graph, node


@dataclass
class AgentState(BaseState):
    name: Optional[str] = None
    power: Optional[int] = None


def main():
    g = Graph[AgentState]()

    # NEW: Clean node creation - no more double calls!
    def first_func(state: AgentState) -> AgentState:
        print("Executing first node")
        return state.update(power=0)
    
    def second_func(state: AgentState) -> AgentState:
        print("Executing second node")
        if random.random() < 0.5:
            return state.update(name="Goku")
        else:
            return state.update(name="Vegeta")

    def goku_func(state: AgentState) -> AgentState:
        print("Executing goku node")
        return state.update(power=9001)

    def vegeta_func(state: AgentState) -> AgentState:
        print("Executing vegeta node")
        return state.update(power=8999)

    def report_func(state: AgentState) -> AgentState:
        print(f"Report node: {state.name} has power {state.power}")
        if state.power is None:
            raise ValueError("Power is not set")
        if state.power > 9000:
            print("Power level is over 9000!")
        else:
            print("Power level is under 9000.")
        return state

    # Create nodes with clean syntax
    first = node(first_func, "first")
    second = node(second_func, "second")
    goku = node(goku_func, "goku")
    vegeta = node(vegeta_func, "vegeta")
    report = node(report_func, "report")

    # Add nodes to graph
    g.add_node(first)
    g.add_node(second)
    g.add_node(goku)
    g.add_node(vegeta)
    g.add_node(report)

    # Direct node references in edges
    g.add_edge(START_NODE, first)
    g.add_edge(first, second)
    
    # NEW: Semantic routing with routes mapping
    def router(state: AgentState) -> str:
        # Return semantic keys, not node names!
        return "saiyan" if state.name == "Goku" else "prince"

    g.add_conditional_edges(
        source=second,
        router=router,
        routes={
            "saiyan": goku,   # Semantic key -> node
            "prince": vegeta,
        }
    )
    
    # Or could use add_path for linear sections
    g.add_path(goku, report, END_NODE)
    g.add_path(vegeta, report, END_NODE)

    # Run the graph
    result = g.run(AgentState())
    print(f"\nFinal result: {result}")

    print("\nMermaid visualization:")
    print(g.visualize())
    
    # Generate image
    print("\nImage generated:", g.visualize(format="png"))


if __name__ == "__main__":
    main()