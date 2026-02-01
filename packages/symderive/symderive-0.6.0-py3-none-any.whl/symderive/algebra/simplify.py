"""
simplify.py - Expression Simplification and Transformation.

Provides functions for simplifying and transforming symbolic expressions.

Args:
    expr: Expression to simplify/transform.

Returns:
    Simplified or transformed expression.

Internal Refs:
    Uses derive.core.math_api for SymPy operations.
"""

from typing import Any

from symderive.core.math_api import (
    sp,
    sym_simplify as simplify,
    sym_expand as expand,
    sym_factor as factor,
    sym_collect as collect,
    sym_cancel as cancel,
    sym_apart as apart,
    sym_together as together,
    sym_trigsimp as trigsimp,
    sym_powsimp as powsimp,
    sym_logcombine as logcombine,
    sym_expand_trig,
)

# Direct aliases
Simplify = simplify
Expand = expand
Factor = factor
Collect = collect
Cancel = cancel
Apart = apart
Together = together
TrigSimplify = trigsimp
PowerSimplify = powsimp
LogSimplify = logcombine


def TrigExpand(expr: Any) -> Any:
    """
    Expand trigonometric expressions.

    Args:
        expr: Expression containing trigonometric functions

    Returns:
        Expanded expression

    Examples:
        >>> x = Symbol('x')
        >>> TrigExpand(Sin(2*x))
        2*sin(x)*cos(x)
    """
    return sym_expand_trig(expr)


def TrigReduce(expr: Any) -> Any:
    """
    Reduce trigonometric expressions.

    Args:
        expr: Expression containing trigonometric functions

    Returns:
        Reduced expression

    Examples:
        >>> x = Symbol('x')
        >>> TrigReduce(Sin(x)*Cos(x))
        sin(2*x)/2
    """
    return trigsimp(expr)


__all__ = [
    'Simplify',
    'Expand',
    'Factor',
    'Collect',
    'Cancel',
    'Apart',
    'Together',
    'TrigSimplify',
    'TrigExpand',
    'TrigReduce',
    'PowerSimplify',
    'LogSimplify',
]
