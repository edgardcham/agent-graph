#!/usr/bin/env python3
"""Demo showing rich condition system with all available helpers"""

from typing import Dict, Any, List
from src.agentgraph import (
    Graph, node, State, START_NODE, END_NODE,
    field_gt, field_equals, field_in, field_len_gt, field_matches,
    field_is_true, all_conditions, any_conditions, custom_condition
)


@node("analyzer")
def analyze_user(state: State) -> State:
    """Analyze user data and add derived fields"""
    age = state.age
    score = state.score
    tags = state.get("tags", [])
    
    # Add derived fields for condition checking
    return state.update(
        age_group="adult" if age >= 18 else "minor",
        is_premium=score > 80,
        has_tags=len(tags) > 0,
        email_domain=state.email.split("@")[1] if "@" in state.email else "",
        status="active"
    )


@node("basic_processor")
def basic_process(state: State) -> State:
    print("→ Basic processing")
    return state.update(processed_by="basic")


@node("premium_processor") 
def premium_process(state: State) -> State:
    print("→ Premium processing")
    return state.update(processed_by="premium")


@node("vip_processor")
def vip_process(state: State) -> State:
    print("→ VIP processing")
    return state.update(processed_by="vip")


@node("minor_processor")
def minor_process(state: State) -> State:
    print("→ Minor processing")
    return state.update(processed_by="minor")


@node("enterprise_processor")
def enterprise_process(state: State) -> State:
    print("→ Enterprise processing")
    return state.update(processed_by="enterprise")


# Custom condition using decorator
@custom_condition("is_weekend_user")
def check_weekend_signup(state: State) -> bool:
    """Custom condition to check if user signed up on weekend"""
    signup_day = getattr(state, "signup_day", "")
    return signup_day in ["saturday", "sunday"]


def demo_numeric_conditions():
    """Demo numeric comparison conditions"""
    print("=== Numeric Conditions Demo ===")
    
    # Router using numeric conditions
    def age_router(state: State) -> str:
        if field_gt("age", 65)(state):
            return "vip_processor"
        elif field_gt("age", 18)(state):
            return "premium_processor" 
        else:
            return "minor_processor"
    
    g = Graph()
    g.add_node(analyze_user)
    g.add_node(premium_process)
    g.add_node(vip_process)
    g.add_node(minor_process)
    
    g.add_edge(START_NODE, "analyzer")
    g.add_conditional_edges("analyzer", age_router)
    g.add_edge("premium_processor", END_NODE)
    g.add_edge("vip_processor", END_NODE)
    g.add_edge("minor_processor", END_NODE)
    
    # Test different ages
    test_cases: List[Dict[str, Any]] = [
        {"age": 16, "score": 50, "email": "teen@gmail.com", "tags": []},
        {"age": 30, "score": 75, "email": "adult@company.com", "tags": ["user"]},
        {"age": 70, "score": 90, "email": "senior@retired.com", "tags": ["vip"]}
    ]
    
    for i, data in enumerate(test_cases):
        print(f"\n--- Test {i+1}: Age {data['age']} ---")
        result = g.run(State(data))
        print(f"Processed by: {getattr(result, 'processed_by', 'unknown')}")


def demo_string_conditions():
    """Demo string and containment conditions"""
    print("\n\n=== String & Containment Conditions Demo ===")
    
    def email_router(state: State) -> str:
        # Check email domain
        if field_equals("email_domain", "enterprise.com")(state):
            return "enterprise_processor"
        elif field_in("email_domain", ["gmail.com", "yahoo.com", "hotmail.com"])(state):
            return "basic_processor"
        else:
            return "premium_processor"
    
    g = Graph()
    g.add_node(analyze_user)
    g.add_node(basic_process)
    g.add_node(premium_process)
    g.add_node(enterprise_process)
    
    g.add_edge(START_NODE, "analyzer")
    g.add_conditional_edges("analyzer", email_router)
    g.add_edge("basic_processor", END_NODE)
    g.add_edge("premium_processor", END_NODE)
    g.add_edge("enterprise_processor", END_NODE)
    
    test_cases: List[Dict[str, Any]] = [
        {"age": 25, "score": 60, "email": "user@gmail.com", "tags": []},
        {"age": 35, "score": 85, "email": "admin@enterprise.com", "tags": ["admin"]},
        {"age": 28, "score": 70, "email": "dev@startup.io", "tags": ["developer"]}
    ]
    
    for i, data in enumerate(test_cases):
        print(f"\n--- Test {i+1}: Email {data['email']} ---")
        result = g.run(State(data))
        print(f"Processed by: {getattr(result, 'processed_by', 'unknown')}")


def demo_complex_conditions():
    """Demo complex condition combinations"""
    print("\n\n=== Complex Conditions Demo ===")
    
    def complex_router(state: State) -> str:
        # VIP: High score AND premium email domain AND has tags
        vip_condition = all_conditions(
            field_gt("score", 80),
            field_in("email_domain", ["enterprise.com", "vip.com"]),
            field_len_gt("tags", 0)
        )
        
        # Premium: Either high score OR premium domain
        premium_condition = any_conditions(
            field_gt("score", 70),
            field_equals("email_domain", "premium.com")
        )
        
        # Check custom condition
        weekend_condition = check_weekend_signup
        
        if vip_condition(state):
            return "vip_processor"
        elif weekend_condition(state):
            return "premium_processor"  # Weekend users get premium
        elif premium_condition(state):
            return "premium_processor"
        else:
            return "basic_processor"
    
    g = Graph()
    g.add_node(analyze_user)
    g.add_node(basic_process)
    g.add_node(premium_process)
    g.add_node(vip_process)
    
    g.add_edge(START_NODE, "analyzer")
    g.add_conditional_edges("analyzer", complex_router)
    g.add_edge("basic_processor", END_NODE)
    g.add_edge("premium_processor", END_NODE)
    g.add_edge("vip_processor", END_NODE)
    
    test_cases: List[Dict[str, Any]] = [
        {
            "age": 30, "score": 85, "email": "admin@enterprise.com", 
            "tags": ["admin", "premium"], "signup_day": "monday"
        },
        {
            "age": 25, "score": 60, "email": "user@gmail.com", 
            "tags": [], "signup_day": "saturday"
        },
        {
            "age": 28, "score": 75, "email": "dev@startup.com", 
            "tags": ["dev"], "signup_day": "tuesday"
        },
        {
            "age": 22, "score": 45, "email": "student@university.edu", 
            "tags": [], "signup_day": "wednesday"
        }
    ]
    
    for i, data in enumerate(test_cases):
        print(f"\n--- Test {i+1}: Score {data['score']}, {data['email']}, Weekend: {data['signup_day'] in ['saturday', 'sunday']} ---")
        result = g.run(State(data))
        print(f"Processed by: {getattr(result, 'processed_by', 'unknown')}")


def demo_boolean_and_pattern_conditions():
    """Demo boolean, length and pattern matching conditions"""
    print("\n\n=== Boolean & Pattern Conditions Demo ===")
    
    def validation_router(state: State) -> str:
        # Check if user has valid premium email pattern
        premium_email_pattern = field_matches("email", r".*@(premium|vip|enterprise)\.com$")
        
        # Check boolean flags
        is_premium_user = field_is_true("is_premium")
        has_content = field_len_gt("tags", 0)
        
        if premium_email_pattern(state) and is_premium_user(state):
            return "vip_processor"
        elif is_premium_user(state) or has_content(state):
            return "premium_processor"
        else:
            return "basic_processor"
    
    g = Graph()
    g.add_node(analyze_user)
    g.add_node(basic_process)
    g.add_node(premium_process)
    g.add_node(vip_process)
    
    g.add_edge(START_NODE, "analyzer")
    g.add_conditional_edges("analyzer", validation_router)
    g.add_edge("basic_processor", END_NODE)
    g.add_edge("premium_processor", END_NODE)
    g.add_edge("vip_processor", END_NODE)
    
    test_cases: List[Dict[str, Any]] = [
        {"age": 30, "score": 85, "email": "user@premium.com", "tags": ["premium"]},
        {"age": 25, "score": 75, "email": "admin@company.com", "tags": ["admin", "user"]},
        {"age": 22, "score": 50, "email": "student@university.edu", "tags": []},
        {"age": 35, "score": 90, "email": "ceo@enterprise.com", "tags": ["executive"]}
    ]
    
    for i, data in enumerate(test_cases):
        print(f"\n--- Test {i+1}: {data['email']} (Score: {data['score']}) ---")
        result = g.run(State(data))
        print(f"Processed by: {getattr(result, 'processed_by', 'unknown')}")


if __name__ == "__main__":
    demo_numeric_conditions()
    demo_string_conditions()
    demo_complex_conditions()
    demo_boolean_and_pattern_conditions()
    
    print("\n\n=== Available Condition Helpers ===")
    print("• Numeric: field_gt, field_ge, field_lt, field_le, field_equals, field_not_equals")
    print("• Containment: field_in, field_not_in, field_contains")
    print("• Boolean: field_is_true, field_is_false, field_is_none, field_is_not_none")
    print("• Length: field_len_equals, field_len_gt")
    print("• Pattern: field_matches (regex)")
    print("• Type: field_type_is")
    print("• Existence: has_field, field_exists")
    print("• Logic: all_conditions, any_conditions, not_condition")
    print("• Custom: @custom_condition decorator")