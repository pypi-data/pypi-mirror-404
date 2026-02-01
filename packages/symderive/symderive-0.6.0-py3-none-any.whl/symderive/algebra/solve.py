"""
solve.py - Equation Solving.

Provides equation solvers: Solve, NSolve, FindRoot.

Args:
    eqns: Equation(s) to solve.
    vars: Variable(s) to solve for.

Returns:
    List of solution dictionaries.

Internal Refs:
    Uses derive.core.math_api for SymPy/SciPy operations.
"""

from typing import Any, List, Dict, Tuple

from symderive.core.math_api import (
    sp,
    sym_solve as solve,
    scipy_optimize,
    sym_lambdify as lambdify,
)


def Solve(eqns: Any, vars: Any, **kwargs) -> List[Dict]:
    """
    equation solver.

    Solve[eqn, x] - solve equation for x
    Solve[{eqn1, eqn2}, {x, y}] - solve system of equations

    Args:
        eqns: Equation(s) to solve (can be single or list)
        vars: Variable(s) to solve for (can be single or list)
        **kwargs: Additional options passed to SymPy

    Returns:
        List of solution dictionaries

    Examples:
        >>> x = Symbol('x')
        >>> Solve(x**2 - 4, x)
        [{x: -2}, {x: 2}]
    """
    result = solve(eqns, vars, dict=True)
    return result


def _to_numerical(value: Any) -> complex:
    """Convert symbolic value to numerical, handling three-valued is_real logic."""
    # is_real can be True, False, or None - only return real if explicitly True
    if value.is_real is True:
        return complex(value).real
    return complex(value)


def NSolve(eqns: Any, vars: Any, **kwargs) -> List[Dict]:
    """
    Numerical equation solver.

    Converts symbolic solutions to numerical values. Note: This function
    first solves symbolically, then converts to floats. For equations that
    cannot be solved symbolically, use FindRoot instead.

    Args:
        eqns: Equation(s) to solve
        vars: Variable(s) to solve for
        **kwargs: Additional options

    Returns:
        List of numerical solution dictionaries

    Examples:
        >>> x = Symbol('x')
        >>> NSolve(x**2 - 2, x)
        [{x: -1.4142135623730951}, {x: 1.4142135623730951}]
    """
    solutions = solve(eqns, vars, dict=True)
    return [{k: _to_numerical(v) for k, v in sol.items()} for sol in solutions]


def FindRoot(expr: Any, var_guess: Tuple[Any, float]) -> Dict:
    """
    numerical root finding.

    FindRoot[f, {x, x0}] - find root starting from x0

    Args:
        expr: Expression to find root of (f(x) = 0)
        var_guess: Tuple (var, x0) specifying variable and initial guess

    Returns:
        Dictionary with the root

    Examples:
        >>> x = Symbol('x')
        >>> FindRoot(x**2 - 2, (x, 1))
        {x: 1.4142135623730951}
    """
    if isinstance(var_guess, (list, tuple)) and len(var_guess) == 2:
        var, x0 = var_guess
        f = lambdify(var, expr, modules=['numpy'])

        result = scipy_optimize.fsolve(f, float(x0))
        return {var: result[0]}

    raise ValueError("FindRoot requires format: FindRoot(expr, (var, x0))")


__all__ = ['Solve', 'NSolve', 'FindRoot']
