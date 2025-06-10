#!/usr/bin/env python3
"""Working example of the new AgentGraph API"""

from src.agentgraph import Graph, node, State


@node("start")
def start_node(state: State) -> State:
    print("Starting...")
    return state.update(step=1)


@node("middle") 
def middle_node(state: State) -> State:
    print(f"Middle step {state.step}")
    return state.update(step=2, data="processed")


@node("end")
def end_node(state: State) -> State:
    print(f"End step {state.step}, data: {state.data}")
    return state.update(step=3, done=True)


def main():
    print("=== AgentGraph Working Example ===")
    
    # Create graph
    g = Graph()
    
    # Add nodes
    g.add_node("start", start_node)
    g.add_node("middle", middle_node) 
    g.add_node("end", end_node)
    
    # Add edges
    g.add_edge("start", "middle")
    g.add_edge("middle", "end")
    g.add_edge("end", "END")
    
    # Run
    initial = State({"task": "test"})
    final = g.run(initial)
    
    print(f"Final state: done={final.done}")
    print("\nState history:")
    final.print_history()
    
    print("\nField evolution for 'step':")
    final.debug_field("step")


if __name__ == "__main__":
    main()