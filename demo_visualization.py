#!/usr/bin/env python3
"""Demo showing graph visualization with conditional edges"""

from src.agentgraph import Graph, node, State, START_NODE, END_NODE


@node("analyzer")
def analyze_request(state: State) -> State:
    """Analyze incoming request and categorize it"""
    request_type = state.get("type", "unknown")
    priority = state.get("priority", 1)
    
    # Add analysis results
    if request_type == "premium":
        category = "high_value"
    elif priority >= 8:
        category = "urgent"
    elif priority >= 5:
        category = "normal"
    else:
        category = "low_priority"
    
    print(f"Analyzing {request_type} request → {category}")
    
    return state.update(
        category=category,
        analyzed=True
    )


@node("urgent_handler")
def handle_urgent(state: State) -> State:
    """Handle urgent requests with immediate processing"""
    print("🚨 Processing urgent request")
    return state.update(
        handled_by="urgent_team",
        response_time="immediate",
        escalated=True
    )


@node("premium_handler") 
def handle_premium(state: State) -> State:
    """Handle premium requests with special care"""
    print("⭐ Processing premium request")
    return state.update(
        handled_by="premium_team",
        response_time="within_1_hour",
        premium_features=True
    )


@node("standard_handler")
def handle_standard(state: State) -> State:
    """Handle standard requests normally"""
    print("📋 Processing standard request")
    return state.update(
        handled_by="standard_team",
        response_time="within_24_hours"
    )


@node("low_priority_handler")
def handle_low_priority(state: State) -> State:
    """Handle low priority requests in queue"""
    print("⏳ Queuing low priority request")
    return state.update(
        handled_by="queue_system",
        response_time="within_7_days",
        queued=True
    )


@node("quality_check")
def quality_assurance(state: State) -> State:
    """Perform quality check on processed requests"""
    handler = state.get("handled_by", "unknown")
    print(f"🔍 Quality check for {handler} processing")
    
    # Simulate quality score
    if handler == "urgent_team":
        quality_score = 95
    elif handler == "premium_team":
        quality_score = 90
    else:
        quality_score = 85
    
    return state.update(
        quality_checked=True,
        quality_score=quality_score
    )


@node("escalation")
def escalate_request(state: State) -> State:
    """Escalate failed requests"""
    print("⬆️ Escalating request to management")
    return state.update(
        escalated=True,
        escalation_reason="quality_failure",
        handled_by="management"
    )


def demo_simple_conditional_graph():
    """Demo a simple conditional routing graph"""
    print("=== Simple Conditional Graph Demo ===")
    
    def category_router(state: State) -> str:
        """Route based on request category"""
        category = state.get("category", "normal")
        
        if category == "urgent":
            return "urgent_handler"
        elif category == "high_value":
            return "premium_handler"
        elif category == "normal":
            return "standard_handler"
        else:
            return "low_priority_handler"
    
    # Build the graph
    g = Graph()
    g.add_node(analyze_request)
    g.add_node(handle_urgent)
    g.add_node(handle_premium)
    g.add_node(handle_standard)
    g.add_node(handle_low_priority)
    
    # Define the flow
    g.add_edge(START_NODE, "analyzer")
    g.add_conditional_edges("analyzer", category_router)
    g.add_edge("urgent_handler", END_NODE)
    g.add_edge("premium_handler", END_NODE)
    g.add_edge("standard_handler", END_NODE)
    g.add_edge("low_priority_handler", END_NODE)
    
    # Show the visualization
    print("\n📊 Graph Visualization:")
    print(g.visualize())
    
    # Test different request types
    test_cases = [
        {"type": "standard", "priority": 5, "user_id": 123},
        {"type": "premium", "priority": 3, "user_id": 456},
        {"type": "bug_report", "priority": 9, "user_id": 789},
        {"type": "feature_request", "priority": 2, "user_id": 101}
    ]
    
    print("\n📋 Execution Results:")
    for i, data in enumerate(test_cases):
        print(f"\n--- Test {i+1}: {data['type']} (Priority {data['priority']}) ---")
        result = g.run(State(data))
        print(f"Handled by: {result.handled_by}")
        print(f"Response time: {result.response_time}")
        print(f"Execution path: {' → '.join(result._execution_path)}")


def demo_complex_conditional_graph():
    """Demo a more complex graph with multiple conditional branches"""
    print("\n\n=== Complex Conditional Graph Demo ===")
    
    def initial_router(state: State) -> str:
        """First routing decision"""
        category = state.get("category", "normal")
        return f"{category}_handler"
    
    def quality_router(state: State) -> str:
        """Route based on quality check results"""
        quality_score = state.get("quality_score", 0)
        
        if quality_score >= 90:
            return END_NODE.name  # High quality, we're done
        else:
            return "escalation"  # Low quality, escalate
    
    # Build complex graph
    g = Graph()
    g.add_node(analyze_request)
    g.add_node(handle_urgent)
    g.add_node(handle_premium) 
    g.add_node(handle_standard)
    g.add_node(handle_low_priority)
    g.add_node(quality_assurance)
    g.add_node(escalate_request)
    
    # Build the flow with multiple conditional points
    g.add_edge(START_NODE, "analyzer")
    g.add_conditional_edges("analyzer", initial_router)
    
    # All handlers go to quality check
    g.add_edge("urgent_handler", "quality_check")
    g.add_edge("premium_handler", "quality_check")
    g.add_edge("standard_handler", "quality_check")
    g.add_edge("low_priority_handler", "quality_check")
    
    # Quality check routes to either END or escalation
    g.add_conditional_edges("quality_check", quality_router)
    g.add_edge("escalation", END_NODE)
    
    # Show the visualization
    print("\n📊 Complex Graph Visualization:")
    print(g.visualize())
    
    # Test the complex flow
    test_cases = [
        {"type": "premium", "priority": 5, "user_id": 999},    # High quality
        {"type": "standard", "priority": 3, "user_id": 888}   # May need escalation
    ]
    
    print("\n📋 Complex Execution Results:")
    for i, data in enumerate(test_cases):
        print(f"\n--- Complex Test {i+1}: {data['type']} ---")
        result = g.run(State(data))
        print(f"Final handler: {result.handled_by}")
        print(f"Quality score: {result.quality_score}")
        print(f"Escalated: {result.get('escalated', False)}")
        print(f"Full path: {' → '.join(result._execution_path)}")
        
        # Show detailed state evolution
        print("\n🔍 State Evolution:")
        result.print_history()


def demo_path_mapping():
    """Demo conditional edges with path mapping"""
    print("\n\n=== Path Mapping Demo ===")
    
    def semantic_router(state: State) -> str:
        """Router that returns semantic names"""
        priority = state.get("priority", 1)
        
        if priority >= 9:
            return "critical"  # Semantic name
        elif priority >= 7:
            return "high"      # Semantic name
        elif priority >= 4:
            return "medium"    # Semantic name
        else:
            return "low"       # Semantic name
    
    # Build graph with path mapping
    g = Graph()
    g.add_node(analyze_request)
    g.add_node(handle_urgent)
    g.add_node(handle_premium)
    g.add_node(handle_standard)
    g.add_node(handle_low_priority)
    
    g.add_edge(START_NODE, "analyzer")
    
    # Use path mapping to translate semantic names to actual node names
    g.add_conditional_edges(
        "analyzer", 
        semantic_router,
        path_map={
            "critical": "urgent_handler",      # critical → urgent_handler
            "high": "premium_handler",         # high → premium_handler  
            "medium": "standard_handler",      # medium → standard_handler
            "low": "low_priority_handler"      # low → low_priority_handler
        }
    )
    
    g.add_edge("urgent_handler", END_NODE)
    g.add_edge("premium_handler", END_NODE)
    g.add_edge("standard_handler", END_NODE)
    g.add_edge("low_priority_handler", END_NODE)
    
    print("\n📊 Path Mapping Visualization:")
    print(g.visualize())
    
    # Test path mapping
    priorities = [10, 8, 5, 2]
    
    print("\n📋 Path Mapping Results:")
    for priority in priorities:
        print(f"\n--- Priority {priority} ---")
        result = g.run(State({"priority": priority, "type": "test"}))
        print(f"Routed to: {result.handled_by}")
        print(f"Path: {' → '.join(result._execution_path)}")


if __name__ == "__main__":
    demo_simple_conditional_graph()
    demo_complex_conditional_graph()
    demo_path_mapping()
    
    print("\n\n=== Visualization Features ===")
    print("• Mermaid diagram generation with g.visualize()")
    print("• Shows all nodes and edges clearly")
    print("• Indicates conditional routing with 'router' labels")
    print("• Compatible with Mermaid Live Editor and documentation")
    print("• Helps visualize complex workflow logic")
    print("• Great for documentation and debugging")