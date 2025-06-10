from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar


@dataclass
class StateSnapshot:
    """A snapshot of state at a point in time"""

    step: int
    node_name: str
    timestamp: datetime
    data: Dict[str, Any]
    changes: Dict[str, tuple[Any, Any]]  # field -> (old_value, new_value)


T = TypeVar("T", bound="BaseState")


@dataclass
class BaseState:
    """Base state class that all states should inherit from

    Tracks history of all field changes with node attribution.
    """

    # Metadata fields (not part of user data)
    _history: List[StateSnapshot] = field(
        default_factory=lambda: [], init=False, repr=False
    )
    _current_step: int = field(default=0, init=False, repr=False)
    _last_node: Optional[str] = field(default=None, init=False, repr=False)

    def update(self: T, **kwargs: Any) -> T:
        """Create new state with updates, tracking changes"""
        # Get current data
        current_data = self._get_user_fields()

        # Calculate what changed
        changes = {}
        for key, new_value in kwargs.items():
            if key in current_data:
                old_value = current_data[key]
                if old_value != new_value:
                    changes[key] = (old_value, new_value)
            else:
                # Field doesn't exist in schema
                raise ValueError(
                    f"Field '{key}' not defined in {self.__class__.__name__}"
                )

        # Apply updates
        updated_data = {**current_data, **kwargs}

        # Create new instance
        new_state = self.__class__(**updated_data)
        new_state._history = self._history.copy()
        new_state._current_step = self._current_step
        new_state._last_node = self._last_node

        return new_state

    def _record_snapshot(
        self, node_name: str, changes: Dict[str, tuple[Any, Any]]
    ) -> None:
        """Record a snapshot of the current state (called by Graph)"""
        snapshot = StateSnapshot(
            step=self._current_step,
            node_name=node_name,
            timestamp=datetime.now(),
            data=self._get_user_fields(),
            changes=changes,
        )
        self._history.append(snapshot)
        self._current_step += 1
        self._last_node = node_name

    def _get_user_fields(self) -> Dict[str, Any]:
        """Get only user-defined fields (not metadata)"""
        data: Dict[str, Any] = {}
        for f in fields(self):
            if not f.name.startswith("_"):
                data[f.name] = getattr(self, f.name)
        return data

    def get_history(self) -> List[StateSnapshot]:
        """Get full history of state changes"""
        return self._history.copy()

    def get_changes_at_step(self, step: int) -> Optional[StateSnapshot]:
        """Get state snapshot at specific step"""
        for snapshot in self._history:
            if snapshot.step == step:
                return snapshot
        return None

    def get_changes_by_node(self, node_name: str) -> List[StateSnapshot]:
        """Get all changes made by a specific node"""
        return [s for s in self._history if s.node_name == node_name]

    def print_history(self) -> None:
        """Pretty print the state evolution"""
        print("=== State Evolution ===")
        for snapshot in self._history:
            print(f"\nStep {snapshot.step} - Node: {snapshot.node_name}")
            print(f"Timestamp: {snapshot.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
            if snapshot.changes:
                print("Changes:")
                for field_name, (old, new) in snapshot.changes.items():
                    print(f"  {field_name}: {old} → {new}")
            else:
                print("  (no changes)")

    def debug_field(self, field_name: str) -> None:
        """Show evolution of a specific field"""
        print(f"\n=== Evolution of '{field_name}' ===")
        current_value = None

        for snapshot in self._history:
            if field_name in snapshot.changes:
                old, new = snapshot.changes[field_name]
                print(f"Step {snapshot.step} [{snapshot.node_name}]: {old} → {new}")
                current_value = new
            elif field_name in snapshot.data:
                if current_value is None:
                    current_value = snapshot.data[field_name]
                    print(
                        f"Step {snapshot.step} [{snapshot.node_name}]: Initial value = {current_value}"
                    )


# For backwards compatibility and flexibility
class State:
    """Flexible dictionary-based state with history tracking"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._history: List[StateSnapshot] = []
        self._current_step = 0
        self._last_node: Optional[str] = None

        # Record initial state
        self._record_snapshot("__init__", {})

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            if key in self._data:
                return self._data[key]
            return super().__getattribute__(key)
        return self._data.get(key)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, **kwargs: Any) -> "State":
        """Create new state with updates"""
        # Calculate changes
        changes = {}
        for key, new_value in kwargs.items():
            old_value = self._data.get(key)
            if old_value != new_value:
                changes[key] = (old_value, new_value)

        # Create new state
        new_data = {**self._data, **kwargs}
        new_state = State(new_data)
        new_state._history = self._history.copy()
        new_state._current_step = self._current_step
        new_state._last_node = self._last_node

        return new_state

    def _record_snapshot(
        self, node_name: str, changes: Dict[str, tuple[Any, Any]]
    ) -> None:
        """Record a snapshot (called by Graph)"""
        snapshot = StateSnapshot(
            step=self._current_step,
            node_name=node_name,
            timestamp=datetime.now(),
            data=deepcopy(self._data),
            changes=changes,
        )
        self._history.append(snapshot)
        self._current_step += 1
        self._last_node = node_name

    @property
    def dict(self) -> Dict[str, Any]:
        return deepcopy(self._data)

    def get_history(self) -> List[StateSnapshot]:
        """Get full history"""
        return self._history.copy()

    def print_history(self) -> None:
        """Pretty print the state evolution"""
        print("=== State Evolution ===")
        for snapshot in self._history:
            print(f"\nStep {snapshot.step} - Node: {snapshot.node_name}")
            print(f"Timestamp: {snapshot.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
            if snapshot.changes:
                print("Changes:")
                for field_name, (old, new) in snapshot.changes.items():
                    print(f"  {field_name}: {old} → {new}")
            else:
                print("  (initial state)" if snapshot.step == 0 else "  (no changes)")

    def debug_field(self, field_name: str) -> None:
        """Show evolution of a specific field"""
        print(f"\n=== Evolution of '{field_name}' ===")

        for snapshot in self._history:
            if field_name in snapshot.changes:
                old, new = snapshot.changes[field_name]
                print(f"Step {snapshot.step} [{snapshot.node_name}]: {old} → {new}")
            elif snapshot.step == 0 and field_name in snapshot.data:
                print(
                    f"Step {snapshot.step} [{snapshot.node_name}]: Initial value = {snapshot.data[field_name]}"
                )
