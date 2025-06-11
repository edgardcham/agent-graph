import re
from functools import wraps
from typing import Any, Callable, Container, Pattern, Union

from ._types import SupportsState


def when(condition: Callable[[SupportsState], bool]) -> Callable[[SupportsState], bool]:
    """Create named condition for readability"""
    return condition


def has_field(field: str) -> Callable[[SupportsState], bool]:
    """Check if state has field"""

    def check(state: SupportsState) -> bool:
        return hasattr(state, field) and getattr(state, field) is not None

    check.__name__ = f"has_{field}"
    return check


def field_exists(field: str) -> Callable[[SupportsState], bool]:
    """Check if field exists (even if None)"""

    def check(state: SupportsState) -> bool:
        return hasattr(state, field)

    check.__name__ = f"{field}_exists"
    return check


def field_equals(field: str, value: Any) -> Callable[[SupportsState], bool]:
    """Check if field equals value"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, None) == value

    check.__name__ = f"{field}_equals_{value}"
    return check


def field_not_equals(field: str, value: Any) -> Callable[[SupportsState], bool]:
    """Check if field does not equal value"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, None) != value

    check.__name__ = f"{field}_not_equals_{value}"
    return check


def field_gt(field: str, value: Union[int, float]) -> Callable[[SupportsState], bool]:
    """Check if field greater than value"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, 0) > value

    check.__name__ = f"{field}_gt_{value}"
    return check


def field_ge(field: str, value: Union[int, float]) -> Callable[[SupportsState], bool]:
    """Check if field greater than or equal to value"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, 0) >= value

    check.__name__ = f"{field}_ge_{value}"
    return check


def field_lt(field: str, value: Union[int, float]) -> Callable[[SupportsState], bool]:
    """Check if field less than value"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, 0) < value

    check.__name__ = f"{field}_lt_{value}"
    return check


def field_le(field: str, value: Union[int, float]) -> Callable[[SupportsState], bool]:
    """Check if field less than or equal to value"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, 0) <= value

    check.__name__ = f"{field}_le_{value}"
    return check


def field_in(field: str, values: Container[Any]) -> Callable[[SupportsState], bool]:
    """Check if field value is in container"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, None) in values

    check.__name__ = f"{field}_in_{values}"
    return check


def field_not_in(field: str, values: Container[Any]) -> Callable[[SupportsState], bool]:
    """Check if field value is not in container"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, None) not in values

    check.__name__ = f"{field}_not_in_{values}"
    return check


def field_contains(field: str, value: Any) -> Callable[[SupportsState], bool]:
    """Check if field (container) contains value"""

    def check(state: SupportsState) -> bool:
        field_value = getattr(state, field, None)
        if field_value is None:
            return False
        try:
            return value in field_value
        except TypeError:
            return False

    check.__name__ = f"{field}_contains_{value}"
    return check


def field_matches(
    field: str, pattern: Union[str, Pattern[str]]
) -> Callable[[SupportsState], bool]:
    """Check if field matches regex pattern"""
    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    def check(state: SupportsState) -> bool:
        field_value = getattr(state, field, None)
        if field_value is None:
            return False
        return bool(pattern.match(str(field_value)))

    check.__name__ = f"{field}_matches_pattern"
    return check


def field_len_equals(field: str, length: int) -> Callable[[SupportsState], bool]:
    """Check if field length equals value"""

    def check(state: SupportsState) -> bool:
        field_value = getattr(state, field, None)
        if field_value is None:
            return False
        try:
            return len(field_value) == length
        except TypeError:
            return False

    check.__name__ = f"{field}_len_equals_{length}"
    return check


def field_len_gt(field: str, length: int) -> Callable[[SupportsState], bool]:
    """Check if field length greater than value"""

    def check(state: SupportsState) -> bool:
        field_value = getattr(state, field, None)
        if field_value is None:
            return False
        try:
            return len(field_value) > length
        except TypeError:
            return False

    check.__name__ = f"{field}_len_gt_{length}"
    return check


def field_is_true(field: str) -> Callable[[SupportsState], bool]:
    """Check if field is truthy"""

    def check(state: SupportsState) -> bool:
        return bool(getattr(state, field, False))

    check.__name__ = f"{field}_is_true"
    return check


def field_is_false(field: str) -> Callable[[SupportsState], bool]:
    """Check if field is falsy"""

    def check(state: SupportsState) -> bool:
        return not bool(getattr(state, field, True))

    check.__name__ = f"{field}_is_false"
    return check


def field_is_none(field: str) -> Callable[[SupportsState], bool]:
    """Check if field is None"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, None) is None

    check.__name__ = f"{field}_is_none"
    return check


def field_is_not_none(field: str) -> Callable[[SupportsState], bool]:
    """Check if field is not None"""

    def check(state: SupportsState) -> bool:
        return getattr(state, field, None) is not None

    check.__name__ = f"{field}_is_not_none"
    return check


def field_type_is(field: str, expected_type: type) -> Callable[[SupportsState], bool]:
    """Check if field is of specific type"""

    def check(state: SupportsState) -> bool:
        field_value = getattr(state, field, None)
        return isinstance(field_value, expected_type)

    check.__name__ = f"{field}_type_is_{expected_type.__name__}"
    return check


def all_conditions(
    *conditions: Callable[[SupportsState], bool],
) -> Callable[[SupportsState], bool]:
    """All conditions must be true"""

    def check(state: SupportsState) -> bool:
        return all(cond(state) for cond in conditions)

    check.__name__ = "all_conditions"
    return check


def any_conditions(
    *conditions: Callable[[SupportsState], bool],
) -> Callable[[SupportsState], bool]:
    """Any condition must be true"""

    def check(state: SupportsState) -> bool:
        return any(cond(state) for cond in conditions)

    check.__name__ = "any_conditions"
    return check


def not_condition(
    condition: Callable[[SupportsState], bool],
) -> Callable[[SupportsState], bool]:
    """Negate a condition"""

    def check(state: SupportsState) -> bool:
        return not condition(state)

    check.__name__ = f"not_{condition.__name__}"
    return check


def custom_condition(
    name: str,
) -> Callable[[Callable[[SupportsState], bool]], Callable[[SupportsState], bool]]:
    """Create a custom named condition decorator"""

    def decorator(
        func: Callable[[SupportsState], bool],
    ) -> Callable[[SupportsState], bool]:
        @wraps(func)
        def wrapper(state: SupportsState) -> bool:
            return func(state)

        wrapper.__name__ = name
        return wrapper

    return decorator
