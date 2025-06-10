#!/usr/bin/env python3
"""Test the new function-passing pattern"""

from src.agentgraph import Graph, node, State


# Pattern 1: Decorated functions (gets custom name)
@node("start")
def start_node(state: State) -> State:
    print("Starting...")
    return state.update(step=1)


# Pattern 2: Plain functions (uses function name)
def end_node(state: State) -> State:
    print(f"End step {state.step}")
    return state.update(done=True)


def main():
    print("=== Function Passing Pattern Test ===")
    
    # Create graph
    g = Graph()
    
    # Add nodes by passing the function directly!
    g.add_node(start_node)    # Uses decorator name "start"
    g.add_node(end_node)      # Uses function name "end_node"
    
    # Add edges using the actual names
    g.add_edge("start", "end_node")
    g.add_edge("end_node", "END")
    
    print("Graph nodes:", list(g.nodes.keys()))
    
    # Run
    initial = State({"task": "test"})
    final = g.run(initial)
    
    print(f"Final state: done={final.done}")


if __name__ == "__main__":
    main()