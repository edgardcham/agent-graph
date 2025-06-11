# AgentGraph v0.2.0

> **Dead simple agent graphs for Python** - Build AI workflows without the bloat

A lightweight, **fully type-safe** library for creating agent workflows as executable graphs. AgentGraph provides the minimal primitives needed to create complex agent interactions with full transparency and zero magic.

## 🚀 **Why AgentGraph?**

LangGraph got the concepts right but buried them under layers of abstraction. Developers need:

- **🎯 Clarity over features** - Understand the entire system in one sitting
- **⚡ Explicit over magic** - See exactly how state flows through the system
- **🪶 Lightweight over comprehensive** - 500 lines of code, not 50,000
- **🎨 Patterns over frameworks** - Learn once, apply everywhere
- **🔒 Type safety first** - Full generic support with IDE autocomplete

## 📦 **Installation**

```bash
# Using uv (recommended)
uv add agentgraph

# Using pip
pip install agentgraph
```

## ⚡ **Quick Start**

```python
from agentgraph import Graph, node, State, START_NODE, END_NODE

# NEW v0.2.0: Clean node creation
def greet_user(state: State) -> State:
    return state.update(message=f"Hello, {state.name}!")

def process_greeting(state: State) -> State:
    return state.update(processed=True, result=state.message.upper())

# Create nodes with simple syntax
greet = node(greet_user, "greet")
process = node(process_greeting, "process")

# Build the graph (with type safety)
g = Graph[State]()
g.add_node(greet)
g.add_node(process)

# Define the flow (now with add_path helper!)
g.add_path(START_NODE, greet, process, END_NODE)

# Execute
initial = State({"name": "World"})
result = g.run(initial)

print(result.result)  # "HELLO, WORLD!"
```

## ✨ **What's New in v0.2.0**

### **🔒 Full Type Safety**

```python
# Generic graphs with IDE autocomplete
g = Graph[State]()           # For flexible dict-based state
g = Graph[MyDataClass]()     # For typed dataclass state

# Type-safe node functions
@node("process")
def my_node(state: MyState) -> MyState:  # Full type inference
    return state.update(processed=True)
```

### **🎨 Clean Node Creation API**

```python
# NEW: Simple node creation - no more double calls!
process = node(process_func)  # Clean and simple
custom = node(process_func, "custom_name")  # With custom name

# OLD: Awkward decorator pattern (still supported)
@node("process")
def process_func(state): ...
```

### **🛤️ Semantic Routing**

```python
# NEW: Routes with semantic keys
def router(state: State) -> str:
    return "high" if state.priority > 5 else "low"  # Semantic keys!

g.add_conditional_edges(
    source=validate,
    router=router,
    routes={
        "high": process_high,    # Map semantic keys to nodes
        "low": process_low,
    }
)

# Supports enums for type safety
class Priority(Enum):
    HIGH = "high"
    LOW = "low"

def enum_router(state: State) -> Priority:
    return Priority.HIGH if state.priority > 5 else Priority.LOW
```

### **📊 Enhanced Visualization**

```python
# Generate Mermaid diagrams
print(g.visualize())  # Default: returns mermaid text

# NEW: Generate images directly
g.visualize("png", "workflow.png")  # Save as PNG
g.visualize("svg", view=True)       # Generate SVG and open it
g.visualize("pdf", "report.pdf")    # Export as PDF
```

### **🛤️ Linear Path Helper**

```python
# Before: Verbose edge definitions
g.add_edge(START_NODE, "fetch")
g.add_edge("fetch", "validate") 
g.add_edge("validate", "transform")
g.add_edge("transform", "report")
g.add_edge("report", END_NODE)

# After: Clean linear paths
g.add_path(START_NODE, "fetch", "validate", "transform", "report", END_NODE)
```

### **🚀 Loop Detection**

```python
# NEW: Better error handling for infinite loops
try:
    result = g.run(state, max_steps=50)
except LoopDetected as e:
    print(f"Loop detected after {e.max_steps} steps")
    print(f"Recent path: {' → '.join(e.visited_nodes[-10:])}")
```

### **🎯 Enhanced Developer Experience**

- **IDE Autocomplete**: Full IntelliSense support for all state properties
- **Type Checking**: Catch errors at development time, not runtime (0 pyright errors!)
- **Generic Conditions**: All 25+ condition helpers now type-aware
- **Registry Isolation**: Each graph maintains its own node registry
- **Clean Visualizations**: No duplicate edges, proper conditional routing display

### **Summary: v0.2.0 Makes AgentGraph Even Simpler**

```python
# Clean node creation
process = node(process_func)

# Semantic routing
g.add_conditional_edges(
    source=validate,
    router=lambda s: "high" if s.score > 0.8 else "low",
    routes={"high": fast_track, "low": review}
)

# Better debugging
try:
    result = g.run(state, max_steps=50)
except LoopDetected as e:
    print(f"Loop at step {e.max_steps}: {e.visited_nodes[-5:]}")

# Rich visualization
g.visualize("png", "workflow.png")  # Generate images!
```

## 🏗️ **Core Components**

### **1. State Management**

AgentGraph provides two state options:

#### **Flexible State (Dictionary-based)**

```python
from agentgraph import State

# Create state with any data
state = State({"user_id": 123, "query": "search term"})

# Immutable updates
new_state = state.update(processed=True, results=["item1", "item2"])

# Access fields
print(state.user_id)  # 123
print(new_state.processed)  # True
```

#### **Typed State (Dataclass-based)**

```python
from agentgraph import BaseState
from dataclasses import dataclass

@dataclass
class UserState(BaseState):
    user_id: int
    query: str
    processed: bool = False
    results: list = None

# Type-safe state management
state = UserState(user_id=123, query="search term")
new_state = state.update(processed=True, results=["item1"])
```

### **2. Node System**

Nodes are simple functions that transform state:

#### **Basic Nodes**

```python
@node("fetch_data")
def fetch_data(state: State) -> State:
    # Simulate API call
    data = fetch_from_api(state.query)
    return state.update(raw_data=data, fetched=True)

# Plain functions work too
def validate_data(state: State) -> State:
    is_valid = len(state.raw_data) > 0
    return state.update(valid=is_valid)
```

#### **Multiple Registration Patterns**

```python
# Pattern 1: Decorator with custom name
@node("processor")
def process_data(state: State) -> State:
    return state.update(processed=True)

# Pattern 2: Plain function (uses function name)
def analyze_results(state: State) -> State:
    return state.update(analyzed=True)

# Pattern 3: Manual node creation
from agentgraph import Node
custom_node = Node(lambda state: state.update(custom=True), "custom")

# All patterns work with the same API
g = Graph[State]()
g.add_node(process_data)      # Uses "processor" name
g.add_node(analyze_results)   # Uses "analyze_results" name
g.add_node(custom_node)       # Uses "custom" name
```

### **3. Graph Construction**

#### **Linear Workflows (New v0.2.0 Way!)**

```python
g = Graph[State]()
g.add_node(fetch_data)
g.add_node(validate_data)
g.add_node(process_data)

# Clean linear path (v0.2.0)
g.add_path(START_NODE, "fetch_data", "validate_data", "process_data", END_NODE)

# Or traditional edges (still supported)
# g.add_edge(START_NODE, "fetch_data")
# g.add_edge("fetch_data", "validate_data")
# g.add_edge("validate_data", "process_data")
# g.add_edge("process_data", END_NODE)
```

#### **Conditional Routing**

```python
@node("classifier")
def classify_request(state: State) -> State:
    request_type = "premium" if state.user_tier == "gold" else "standard"
    return state.update(request_type=request_type)

@node("premium_handler")
def handle_premium(state: State) -> State:
    return state.update(handled_by="premium_service")

@node("standard_handler")
def handle_standard(state: State) -> State:
    return state.update(handled_by="standard_service")

# Router function determines next node
def route_by_type(state: State) -> str:
    return f"{state.request_type}_handler"

g = Graph[State]()
g.add_node(classify_request)
g.add_node(handle_premium)
g.add_node(handle_standard)

g.add_edge(START_NODE, "classifier")
g.add_conditional_edges("classifier", route_by_type)
g.add_edge("premium_handler", END_NODE)
g.add_edge("standard_handler", END_NODE)
```

#### **Advanced Routing with Semantic Keys (v0.2.0)**

```python
from enum import Enum

# Define semantic routing keys
class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Create nodes with clean API
fast_process = node(fast_process_func, "fast")
careful_process = node(careful_process_func, "careful")
manual_review = node(manual_review_func, "manual")

# Router returns semantic keys
def confidence_router(state: State) -> str:
    if state.confidence > 0.8:
        return ConfidenceLevel.HIGH.value
    elif state.confidence > 0.5:
        return ConfidenceLevel.MEDIUM.value
    else:
        return ConfidenceLevel.LOW.value

# Map semantic keys to nodes (NEW!)
g.add_conditional_edges(
    source=classifier,
    router=confidence_router,
    routes={
        ConfidenceLevel.HIGH.value: fast_process,
        ConfidenceLevel.MEDIUM.value: careful_process,
        ConfidenceLevel.LOW.value: manual_review
    }
)
```

## 🎯 **Advanced Features**

### **State History & Debugging**

AgentGraph automatically tracks state evolution with full debugging capabilities:

```python
# Run your graph
result = g.run(initial_state)

# View complete execution history
result.print_history()
# Output:
# === State Evolution ===
#
# Step 0 - Node: __init__
# Timestamp: 14:23:45.123
#   (initial state)
#
# Step 1 - Node: fetch_data
# Timestamp: 14:23:45.200
# Changes:
#   raw_data: None → {"users": 150}
#   fetched: None → True
#
# Step 2 - Node: validate_data
# Timestamp: 14:23:45.250
# Changes:
#   valid: None → True

# Debug specific field evolution
result.debug_field("user_count")
# Output:
# === Evolution of 'user_count' ===
# Step 1 [fetch_data]: Initial value = 0
# Step 2 [process_data]: 0 → 150
```

### **Rich Condition System**

25+ built-in condition helpers for clean conditional logic:

```python
from agentgraph import field_gt, field_equals, field_in, all_conditions

# Numeric conditions
validate_data.add_edge(field_gt("user_count", 100), large_processor)
validate_data.add_edge(field_le("user_count", 100), small_processor)

# String conditions
router.add_edge(field_equals("status", "premium"), premium_handler)
router.add_edge(field_in("category", ["A", "B", "C"]), special_handler)

# Boolean logic
complex_condition = all_conditions(
    field_gt("score", 0.8),
    field_equals("verified", True),
    field_in("tier", ["gold", "platinum"])
)
router.add_edge(complex_condition, vip_handler)

# Custom conditions
from agentgraph import custom_condition

@custom_condition("is_business_hours")
def check_business_hours(state: State) -> bool:
    return 9 <= datetime.now().hour <= 17
```

### **Streaming Execution**

Monitor execution in real-time:

```python
for step_state in g.stream(initial_state):
    print(f"Completed node: {step_state._last_node}")
    print(f"Current data: {step_state.dict}")

    # Early termination based on conditions
    if step_state.should_stop:
        break
```

### **Graph Visualization**

Generate Mermaid diagrams for documentation:

```python
print(g.visualize())
# Output:
# graph TD
#     START_NODE[START]
#     fetch_data[fetch_data]
#     validate_data[validate_data]
#     process_data[process_data]
#     END_NODE((END))
#
#     START_NODE --> fetch_data
#     fetch_data --> validate_data
#     validate_data --> process_data
#     process_data --> END_NODE
```

## 📚 **Complete Examples**

### **Data Processing Pipeline**

```python
from agentgraph import Graph, node, State, START_NODE, END_NODE

@node("fetch")
def fetch_data(state: State) -> State:
    # Simulate API fetch
    data = {"users": 150, "revenue": 50000}
    return state.update(raw_data=data, fetched=True)

@node("validate")
def validate_data(state: State) -> State:
    data = state.raw_data
    is_valid = data.get("users", 0) > 0
    return state.update(
        valid=is_valid,
        user_count=data.get("users", 0)
    )

@node("process_small")
def process_small_dataset(state: State) -> State:
    return state.update(
        result=f"Small dataset: {state.user_count} users",
        processing_type="small"
    )

@node("process_large")
def process_large_dataset(state: State) -> State:
    return state.update(
        result=f"Large dataset: {state.user_count} users",
        processing_type="large"
    )

@node("generate_report")
def generate_report(state: State) -> State:
    report = f"Report: {state.result} (via {state.processing_type})"
    return state.update(report=report)

# Router function for conditional logic
def route_by_size(state: State) -> str:
    return "process_small" if state.user_count < 100 else "process_large"

# Build graph
g = Graph[State]()
g.add_node(fetch_data)
g.add_node(validate_data)
g.add_node(process_small_dataset)
g.add_node(process_large_dataset)
g.add_node(generate_report)

# Define flow
g.add_edge(START_NODE, "fetch")
g.add_edge("fetch", "validate")
g.add_conditional_edges("validate", route_by_size)
g.add_edge("process_small", "generate_report")
g.add_edge("process_large", "generate_report")
g.add_edge("generate_report", END_NODE)

# Execute
initial = State({"query": "get user metrics"})
result = g.run(initial)

print(result.report)
# Output: "Report: Large dataset: 150 users (via large)"

print(f"Execution path: {' -> '.join(result._execution_path)}")
# Output: "Execution path: fetch -> validate -> process_large -> generate_report"
```

### **Multi-Path Workflow with Typed State**

```python
from dataclasses import dataclass
from agentgraph import BaseState, Graph, node, START_NODE, END_NODE

@dataclass
class ProcessingState(BaseState):
    task: str
    priority: int = 1
    assigned_to: str = None
    completed: bool = False
    result: str = None

@node("triage")
def triage_task(state: ProcessingState) -> ProcessingState:
    # Assign based on priority
    if state.priority >= 8:
        assignee = "senior_team"
    elif state.priority >= 5:
        assignee = "regular_team"
    else:
        assignee = "junior_team"

    return state.update(assigned_to=assignee)

@node("senior_process")
def senior_process(state: ProcessingState) -> ProcessingState:
    return state.update(
        completed=True,
        result=f"Task '{state.task}' completed by senior team"
    )

@node("regular_process")
def regular_process(state: ProcessingState) -> ProcessingState:
    return state.update(
        completed=True,
        result=f"Task '{state.task}' completed by regular team"
    )

@node("junior_process")
def junior_process(state: ProcessingState) -> ProcessingState:
    return state.update(
        completed=True,
        result=f"Task '{state.task}' completed by junior team"
    )

def route_by_assignment(state: ProcessingState) -> str:
    return f"{state.assigned_to.replace('_team', '')}_process"

# Build graph
g = Graph[ProcessingState]()
g.add_node(triage_task)
g.add_node(senior_process)
g.add_node(regular_process)
g.add_node(junior_process)

g.add_edge(START_NODE, "triage")
g.add_conditional_edges("triage", route_by_assignment)
g.add_edge("senior_process", END_NODE)
g.add_edge("regular_process", END_NODE)
g.add_edge("junior_process", END_NODE)

# Test different priorities
high_priority = ProcessingState(task="Critical bug fix", priority=9)
result = g.run(high_priority)
print(result.result)
# Output: "Task 'Critical bug fix' completed by senior team"

# Debug the assignment logic
result.debug_field("assigned_to")
# Output:
# === Evolution of 'assigned_to' ===
# Step 1 [triage]: None → senior_team
```

## 🎨 **Design Principles**

### **Type Safety First**

- Full pyright/mypy compatibility
- Explicit type annotations throughout
- No runtime type surprises

### **Explicit Over Magic**

- Clear execution flow
- No hidden state mutations
- Traceable state evolution

### **Functional Design**

- Immutable state updates
- Pure node functions
- Predictable execution

### **Developer Experience**

- Rich debugging capabilities
- Comprehensive history tracking
- Visual graph representation

## 🔄 **Migration from LangGraph**

AgentGraph provides a cleaner, more explicit API:

```python
# LangGraph style
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_edge(START, "agent")
graph.add_edge("agent", END)

# AgentGraph style
g = Graph[State]()
g.add_node(agent_node)  # Function passed directly
g.add_edge(START_NODE, "agent_node")  # Explicit node objects
g.add_edge("agent_node", END_NODE)
```

## 📋 **API Reference**

### **Core Classes**

- **`State(data: dict)`** - Flexible dictionary-based state
- **`BaseState`** - Type-safe dataclass-based state
- **`Node[TState](func, name)`** - Generic graph node wrapper
- **`Graph[TState]()`** - Type-safe graph executor
- **`START_NODE`** - Graph entry point marker
- **`END_NODE`** - Graph termination marker
- **`LoopDetected`** - Exception raised when execution loops

### **Node Creation** ✨ **NEW v0.2.0**

- **`node(func, name=None)`** - Create node from function (simple factory)
- **`node_decorator(name=None)`** - Decorator pattern for nodes
- **`get_node(name)`** - Retrieve node from registry

### **Type System** ✨ **NEW v0.2.0**

- **`TState`** - Generic type variable for state objects
- **`SupportsState`** - Protocol for state duck typing
- **`RouterFunc[TState]`** - Type alias for routing functions

### **Graph Methods**

- **`add_node(node)`** - Add node to graph
- **`add_edge(source, target)`** - Add direct edge
- **`add_path(*nodes)`** - Add linear path through nodes
- **`add_conditional_edges(source, router, routes=None)`** - Add conditional routing
- **`run(state, max_steps=100)`** - Execute graph
- **`stream(state)`** - Stream execution results
- **`visualize(format="mermaid", filename=None, view=False)`** - Generate visualization

### **Decorators**

- **`@node_decorator(name)`** - Convert function to named node
- **`@custom_condition(name)`** - Create named condition

### **Condition Helpers**

- **Existence**: `has_field()`, `field_exists()`, `field_is_none()`
- **Comparison**: `field_gt()`, `field_ge()`, `field_lt()`, `field_le()`, `field_equals()`
- **Containment**: `field_in()`, `field_contains()`, `field_matches()`
- **Boolean**: `field_is_true()`, `field_is_false()`, `all_conditions()`, `any_conditions()`

## 🚧 **Roadmap**

### **v0.2.0 - Type Safety & Developer Experience** ✅ **CURRENT**

- ✅ Full generic type system (`Graph[TState]`, `Node[TState]`)
- ✅ Clean node creation API (`node(func, name)`)
- ✅ Semantic routing with `routes` parameter
- ✅ Enhanced visualization (PNG/SVG/PDF support)
- ✅ Loop detection with helpful errors
- ✅ Registry isolation (graph-local registries)
- ✅ Linear path helper (`add_path()`)
- ✅ 0 type errors with full pyright/mypy compatibility

### **v0.3.0 - Intelligence & AI Integration**

- AI node integration with LLM support
- Dynamic routing with AI decision making
- Enhanced visualization tools
- Streaming execution improvements

### **v0.4.0 - Tools & Integration**

- Tool calling system
- MCP (Model Context Protocol) support
- External service integrations

### **v0.5.0 - Advanced Features**

- Parallel execution support
- Subgraph composition
- Advanced streaming capabilities
- Performance benchmarks and optimization

## 🤝 **Contributing**

We welcome contributions!

## 📄 **License**

MIT License - see [LICENSE](LICENSE) for details.

## ⭐ **Why Choose AgentGraph?**

- **🎯 Focused**: Core graph functionality without bloat
- **🔍 Transparent**: Full execution traceability
- **🧪 Testable**: Pure functions and immutable state
- **📈 Scalable**: From simple scripts to complex workflows
- **🎨 Pythonic**: Feels natural to Python developers
- **🔒 Type-Safe**: Full IDE support with generic type system ✨ **NEW**
- **🛤️ Ergonomic**: Clean linear workflows with `add_path()` ✨ **NEW**

---

**Built with ❤️ for developers who value clarity and simplicity.**
