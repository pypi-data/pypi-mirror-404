"""
limits.py - Limit Operations.

Provides limit computation.

Args:
    expr: Expression to take the limit of.
    var: Variable approaching the point.
    point: Point to approach.

Returns:
    The limit value.

Internal Refs:
    Uses derive.core.math_api for SymPy operations.
"""

from typing import Any, Optional

from symderive.core.math_api import sym_limit as limit


def Limit(expr: Any, var: Any, point: Any, direction: Optional[str] = None) -> Any:
    """
    limits.

    Limit[f, x -> a] becomes Limit(f, x, a)
    Direction can be '+' (from right), '-' (from left), or None (both)

    Args:
        expr: Expression to take the limit of
        var: Variable approaching the point
        point: Point to approach
        direction: Optional direction ('+' for right, '-' for left)

    Returns:
        The limit value

    Examples:
        >>> x = Symbol('x')
        >>> Limit(Sin(x)/x, x, 0)
        1
        >>> Limit(1/x, x, 0, '+')
        oo
        >>> Limit(1/x, x, 0, '-')
        -oo
    """
    if direction == '+':
        return limit(expr, var, point, '+')
    elif direction == '-':
        return limit(expr, var, point, '-')
    else:
        return limit(expr, var, point)


__all__ = ['Limit']
