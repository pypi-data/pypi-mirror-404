"""
symbolic.py - Symbolic ODE Solver.

Provides DSolve for symbolic differential equation solving.

Args:
    eq: Differential equation to solve.
    func: Function to solve for (e.g., y(x)).
    var: Independent variable.

Returns:
    List of solutions.

Internal Refs:
    Uses derive.core.math_api for SymPy operations.
"""

from typing import Any, Dict, List, Optional

from symderive.core.math_api import sym_dsolve as dsolve


def DSolve(eq: Any, func: Any, var: Any = None,
           ics: Optional[Dict] = None, **kwargs) -> List:
    """
    ODE solver.

    DSolve[eqn, y[x], x] - solve ODE for y as function of x

    Args:
        eq: Differential equation to solve
        func: Function to solve for (e.g., y(x))
        var: Independent variable (optional, can be inferred)
        ics: Initial conditions as dict, e.g., {y(0): 1, y'(0): 0}
        **kwargs: Additional options passed to SymPy's dsolve

    Returns:
        List of solutions

    Examples:
        >>> x = Symbol('x')
        >>> y = Function('y')
        >>> DSolve(Eq(y(x).diff(x), y(x)), y(x), x)
        [Eq(y(x), C1*exp(x))]
        >>> DSolve(Eq(y(x).diff(x), y(x)), y(x), x, ics={y(0): 1})
        [Eq(y(x), exp(x))]
    """
    result = dsolve(eq, func, ics=ics, **kwargs)
    # dsolve returns a single Eq or list - normalize to list
    if isinstance(result, list):
        return result
    return [result]


__all__ = ['DSolve']
