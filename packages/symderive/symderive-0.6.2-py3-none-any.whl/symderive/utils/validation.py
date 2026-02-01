"""
validation.py - Input Validation Utilities

Provides reusable validation functions for common parameter patterns
used throughout the derive library.
"""

from typing import Any, Tuple, Union, Sequence, Optional


class ValidationError(ValueError):
    """Custom validation error with helpful messages."""
    pass


def validate_tuple(
    arg: Any,
    expected_length: int,
    name: str = "argument"
) -> tuple:
    """
    Validate that an argument is a tuple/list of expected length.

    Args:
        arg: The argument to validate
        expected_length: Required length
        name: Name for error messages

    Returns:
        The argument as a tuple

    Raises:
        ValidationError: If validation fails

    Examples:
        >>> validate_tuple((x, 0, 1), 3, "bounds")
        (x, 0, 1)
        >>> validate_tuple([a, b], 2, "range")
        (a, b)
    """
    if not isinstance(arg, (list, tuple)):
        raise ValidationError(
            f"{name} must be a tuple or list, got {type(arg).__name__}"
        )
    if len(arg) != expected_length:
        raise ValidationError(
            f"{name} must have {expected_length} elements, got {len(arg)}"
        )
    return tuple(arg)


def validate_range_tuple(
    arg: Any,
    name: str = "range"
) -> Tuple[Any, Any, Any]:
    """
    Validate a (var, start, end) range tuple.

    Args:
        arg: The argument to validate
        name: Name for error messages

    Returns:
        Tuple of (var, start, end)

    Examples:
        >>> x = Symbol('x')
        >>> validate_range_tuple((x, 0, 1), "integration bounds")
        (x, 0, 1)
    """
    return validate_tuple(arg, 3, name)


def validate_var_tuple(
    arg: Any,
    name: str = "variable specification"
) -> Tuple[Any, int]:
    """
    Validate a (var, n) tuple for differentiation order etc.

    Args:
        arg: The argument to validate
        name: Name for error messages

    Returns:
        Tuple of (var, n)

    Examples:
        >>> x = Symbol('x')
        >>> validate_var_tuple((x, 2), "derivative order")
        (x, 2)
    """
    return validate_tuple(arg, 2, name)


def validate_positive_int(
    n: Any,
    name: str = "argument"
) -> int:
    """
    Validate that an argument is a positive integer.

    Args:
        n: The argument to validate
        name: Name for error messages

    Returns:
        The validated integer

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(n, int) or n <= 0:
        raise ValidationError(f"{name} must be a positive integer, got {n}")
    return n


def validate_nonnegative_int(
    n: Any,
    name: str = "argument"
) -> int:
    """
    Validate that an argument is a non-negative integer.

    Args:
        n: The argument to validate
        name: Name for error messages

    Returns:
        The validated integer

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(n, int) or n < 0:
        raise ValidationError(f"{name} must be a non-negative integer, got {n}")
    return n


def is_tuple_like(arg: Any, length: Optional[int] = None) -> bool:
    """
    Check if an argument is tuple-like (list or tuple) with optional length check.

    Args:
        arg: The argument to check
        length: Optional required length

    Returns:
        True if arg is tuple-like (and has correct length if specified)

    Examples:
        >>> is_tuple_like((1, 2, 3))
        True
        >>> is_tuple_like([1, 2], 2)
        True
        >>> is_tuple_like([1, 2], 3)
        False
    """
    if not isinstance(arg, (list, tuple)):
        return False
    if length is not None and len(arg) != length:
        return False
    return True


__all__ = [
    'ValidationError',
    'validate_tuple',
    'validate_range_tuple',
    'validate_var_tuple',
    'validate_positive_int',
    'validate_nonnegative_int',
    'is_tuple_like',
]
