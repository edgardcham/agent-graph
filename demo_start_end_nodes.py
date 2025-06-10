#!/usr/bin/env python3
"""Demo showing START_NODE and END_NODE usage"""

from src.agentgraph import Graph, node, State, START_NODE, END_NODE


@node("first")
def first_node(state: State) -> State:
    print("First node executing...")
    return state.update(step=1)


@node("second")
def second_node(state: State) -> State:
    print("Second node executing...")
    return state.update(step=2)


def final_node(state: State) -> State:
    print("Final node executing...")
    return state.update(done=True)


def main():
    print("=== START_NODE and END_NODE Demo ===")
    
    # Create graph
    g = Graph()
    
    # Add nodes
    g.add_node(first_node)   # Uses "first" from decorator
    g.add_node(second_node)  # Uses "second" from decorator
    g.add_node(final_node)   # Uses "final_node" function name
    
    # Use START_NODE to set entry point
    g.add_edge(START_NODE, "first")        # Sets "first" as entry point
    g.add_edge("first", "second")
    g.add_edge("second", "final_node")
    g.add_edge("final_node", END_NODE)     # End execution
    
    print(f"Entry point: {g.entry_point}")
    print(f"Nodes: {list(g.nodes.keys())}")
    
    # Run
    initial = State({"task": "test start/end nodes"})
    final = g.run(initial)
    
    print(f"\nFinal state: step={final.step}, done={final.done}")


def demo_conditional_with_end():
    print("\n\n=== Conditional Routing with END_NODE ===")
    
    @node("router")
    def route_decision(state: State) -> State:
        decision = "skip" if state.value < 50 else "process"
        print(f"Router decision: {decision}")
        return state.update(decision=decision)
    
    @node("processor")
    def process_node(state: State) -> State:
        print("Processing...")
        return state.update(processed=True)
    
    def router_func(state: State) -> str:
        if state.decision == "skip":
            return END_NODE.name  # Go directly to END
        else:
            return "processor"
    
    g = Graph()
    g.add_node(route_decision)
    g.add_node(process_node)
    
    g.add_edge(START_NODE, "router")
    g.add_conditional_edges("router", router_func)
    g.add_edge("processor", END_NODE)
    
    # Test skip path
    print("--- Low value (skip processing) ---")
    result1 = g.run(State({"value": 25}))
    print(f"Processed: {getattr(result1, 'processed', False)}")
    
    # Test process path
    print("\n--- High value (process) ---")
    result2 = g.run(State({"value": 75}))
    print(f"Processed: {getattr(result2, 'processed', False)}")


if __name__ == "__main__":
    main()
    demo_conditional_with_end()