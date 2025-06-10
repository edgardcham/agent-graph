#!/usr/bin/env python3
"""Demo showing BaseState (typed dataclass-based state) usage"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from src.agentgraph import Graph, node, BaseState, START_NODE, END_NODE


@dataclass
class UserProcessingState(BaseState):
    """Typed state for user processing workflow"""
    user_id: int
    name: str
    email: str
    age: int = 0
    score: float = 0.0
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    processed: bool = False
    validated: bool = False
    final_status: Optional[str] = None


@dataclass
class OrderState(BaseState):
    """Typed state for order processing"""
    order_id: str
    customer_id: int
    amount: float
    currency: str = "USD"
    items: List[Dict[str, Any]] = field(default_factory=list)
    payment_verified: bool = False
    inventory_checked: bool = False
    shipped: bool = False
    tracking_number: Optional[str] = None


# User Processing Nodes
@node("validate_user")
def validate_user_data(state: UserProcessingState) -> UserProcessingState:
    """Validate user data and calculate derived fields"""
    print(f"Validating user: {state.name} ({state.email})")
    
    # Type-safe access to fields
    is_valid_email = "@" in state.email and "." in state.email
    category = "premium" if state.age >= 25 and state.score > 70 else "standard"
    
    return state.update(
        validated=is_valid_email,
        category=category,
        tags=state.tags + ["validated"] if is_valid_email else state.tags
    )


@node("process_premium")
def process_premium_user(state: UserProcessingState) -> UserProcessingState:
    """Handle premium user processing"""
    print(f"Processing premium user: {state.name}")
    
    return state.update(
        processed=True,
        final_status="premium_processed",
        tags=state.tags + ["premium", "processed"]
    )


@node("process_standard")
def process_standard_user(state: UserProcessingState) -> UserProcessingState:
    """Handle standard user processing"""
    print(f"Processing standard user: {state.name}")
    
    return state.update(
        processed=True,
        final_status="standard_processed",
        tags=state.tags + ["standard", "processed"]
    )


# Order Processing Nodes
@node("verify_payment")
def verify_payment(state: OrderState) -> OrderState:
    """Verify payment for order"""
    print(f"Verifying payment for order {state.order_id}: ${state.amount}")
    
    # Simulate payment verification
    payment_ok = state.amount > 0 and state.amount < 10000
    
    return state.update(payment_verified=payment_ok)


@node("check_inventory")
def check_inventory(state: OrderState) -> OrderState:
    """Check inventory availability"""
    print(f"Checking inventory for {len(state.items)} items")
    
    # Simulate inventory check
    inventory_ok = len(state.items) > 0 and len(state.items) <= 10
    
    return state.update(inventory_checked=inventory_ok)


@node("ship_order")
def ship_order(state: OrderState) -> OrderState:
    """Ship the order"""
    print(f"Shipping order {state.order_id}")
    
    tracking = f"TRK{state.order_id[-6:].upper()}"
    
    return state.update(
        shipped=True,
        tracking_number=tracking
    )


@node("cancel_order")
def cancel_order(state: OrderState) -> OrderState:
    """Cancel the order"""
    print(f"Canceling order {state.order_id}")
    
    return state.update(tracking_number="CANCELED")


def demo_user_processing():
    """Demo typed user processing workflow"""
    print("=== Typed User Processing Demo ===")
    
    def user_router(state: UserProcessingState) -> str:
        if state.validated and state.category == "premium":
            return "process_premium"
        elif state.validated:
            return "process_standard"
        else:
            return END_NODE.name  # Skip processing for invalid users
    
    g = Graph()
    g.add_node(validate_user_data)
    g.add_node(process_premium_user)
    g.add_node(process_standard_user)
    
    g.add_edge(START_NODE, "validate_user")
    g.add_conditional_edges("validate_user", user_router)
    g.add_edge("process_premium", END_NODE)
    g.add_edge("process_standard", END_NODE)
    
    # Test cases with typed state
    test_users = [
        UserProcessingState(
            user_id=1,
            name="Alice Premium",
            email="alice@company.com",
            age=30,
            score=85.0,
            tags=["new_user"]
        ),
        UserProcessingState(
            user_id=2,
            name="Bob Standard", 
            email="bob@gmail.com",
            age=22,
            score=65.0
        ),
        UserProcessingState(
            user_id=3,
            name="Invalid User",
            email="invalid-email",
            age=25,
            score=80.0
        )
    ]
    
    for user in test_users:
        print(f"\n--- Processing {user.name} ---")
        result = g.run(user)
        
        print(f"Final Status: {result.final_status}")
        print(f"Tags: {result.tags}")
        print(f"Validated: {result.validated}, Processed: {result.processed}")
        
        # Show state history with type information
        print("\nState Evolution:")
        result.print_history()


def demo_order_processing():
    """Demo typed order processing workflow"""
    print("\n\n=== Typed Order Processing Demo ===")
    
    def payment_router(state: OrderState) -> str:
        if state.payment_verified:
            return "check_inventory"
        else:
            return "cancel_order"
    
    def inventory_router(state: OrderState) -> str:
        if state.inventory_checked:
            return "ship_order"
        else:
            return "cancel_order"
    
    g = Graph()
    g.add_node(verify_payment)
    g.add_node(check_inventory)
    g.add_node(ship_order)
    g.add_node(cancel_order)
    
    g.add_edge(START_NODE, "verify_payment")
    g.add_conditional_edges("verify_payment", payment_router)
    g.add_conditional_edges("check_inventory", inventory_router)
    g.add_edge("ship_order", END_NODE)
    g.add_edge("cancel_order", END_NODE)
    
    # Test cases with typed state
    test_orders = [
        OrderState(
            order_id="ORD123456",
            customer_id=101,
            amount=99.99,
            items=[{"sku": "ITEM1", "qty": 2}, {"sku": "ITEM2", "qty": 1}]
        ),
        OrderState(
            order_id="ORD789012",
            customer_id=102,
            amount=15000.0,  # Too expensive, payment will fail
            items=[{"sku": "EXPENSIVE", "qty": 1}]
        ),
        OrderState(
            order_id="ORD345678",
            customer_id=103,
            amount=49.99,
            items=[]  # No items, inventory will fail
        )
    ]
    
    for order in test_orders:
        print(f"\n--- Processing Order {order.order_id} ---")
        result = g.run(order)
        
        print(f"Payment Verified: {result.payment_verified}")
        print(f"Inventory Checked: {result.inventory_checked}")
        print(f"Shipped: {result.shipped}")
        print(f"Tracking: {result.tracking_number}")


def demo_type_safety():
    """Demo type safety benefits of BaseState"""
    print("\n\n=== Type Safety Demo ===")
    
    # This demonstrates type-safe field access
    user = UserProcessingState(
        user_id=999,
        name="Type Safe User",
        email="typed@example.com",
        age=28,
        score=75.5
    )
    
    print("=== Type-Safe Field Access ===")
    print(f"User ID: {user.user_id}")  # int
    print(f"Name: {user.name}")        # str
    print(f"Score: {user.score}")      # float
    print(f"Tags: {user.tags}")        # List[str]
    
    # Update with type checking
    updated = user.update(
        score=88.0,        # Type-safe: float
        processed=True,    # Type-safe: bool
        tags=["updated"]   # Type-safe: List[str]
    )
    
    print("\nAfter update:")
    print(f"Score: {updated.score}")
    print(f"Processed: {updated.processed}")
    print(f"Tags: {updated.tags}")
    
    # Show field evolution with types
    print("\nField types:")
    print(f"user_id: {type(user.user_id).__name__}")
    print(f"score: {type(user.score).__name__}")
    print(f"processed: {type(user.processed).__name__}")
    print(f"tags: {type(user.tags).__name__}")


if __name__ == "__main__":
    demo_user_processing()
    demo_order_processing()
    demo_type_safety()
    
    print("\n\n=== BaseState Benefits ===")
    print("• Type safety: Field types are enforced")
    print("• IDE support: Auto-completion and type hints")
    print("• Validation: Dataclass validation at creation")
    print("• Documentation: Self-documenting field types")
    print("• Immutability: Same update() pattern as State")
    print("• History tracking: Full state evolution support")