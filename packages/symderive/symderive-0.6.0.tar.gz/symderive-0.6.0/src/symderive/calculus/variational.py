"""
variational.py - Variational Calculus

Provides variational derivatives for deriving equations of motion
from Lagrangian densities.

Internal Refs:
    Uses math_api.Symbol, math_api.symbols, math_api.Function, math_api.Rational, math_api.Expr
"""

from typing import List

from symderive.core.math_api import (
    Symbol,
    symbols,
    Function,
    Rational,
    Expr,
)

# Use derive's own APIs for self-consistency
from symderive.calculus.differentiation import D
from symderive.algebra import Simplify


def VariationalDerivative(lagrangian: Expr, field: Function, coords: List[Symbol]) -> Expr:
    """
    Compute the variational (functional) derivative of a Lagrangian.

    This gives the Euler-Lagrange equations: δL/δφ = 0

    For L(φ, ∂_μ φ), the variational derivative is:
    δL/δφ = ∂L/∂φ - ∂_μ(∂L/∂(∂_μ φ))

    Args:
        lagrangian: The Lagrangian density expression
        field: The field function (e.g., phi(x, t))
        coords: Coordinate variables

    Returns:
        The Euler-Lagrange equation (set to 0 for equation of motion)

    Examples:
        >>> x, t = symbols('x t')
        >>> phi = Function('phi')(x, t)
        >>> # Klein-Gordon Lagrangian: L = (1/2)(partial_t phi)^2 - (1/2)(partial_x phi)^2 - (1/2)m^2 phi^2
        >>> m = Symbol('m')
        >>> L = Rational(1,2)*D(phi, t)**2 - Rational(1,2)*D(phi, x)**2 - Rational(1,2)*m**2*phi**2
        >>> eq = VariationalDerivative(L, phi, [x, t])
        >>> # Should give: partial_t^2 phi - partial_x^2 phi + m^2 phi = 0
    """
    # Get the field and its derivatives
    result = D(lagrangian, field)

    for coord in coords:
        # ∂L/∂(∂_μ φ)
        d_field = D(field, coord)
        partial_L = D(lagrangian, d_field)
        # ∂_μ(∂L/∂(∂_μ φ))
        result -= D(partial_L, coord)

    return Simplify(result)


def EulerLagrangeEquation(action_density: Expr, field: Function,
                          coords: List[Symbol]) -> Expr:
    """
    Derive the Euler-Lagrange equation from an action density.

    This is an alias for VariationalDerivative, named to match standard convention.

    Args:
        action_density: The Lagrangian density L
        field: The field to vary
        coords: Spacetime coordinates

    Returns:
        The Euler-Lagrange equation (= 0 for equations of motion)
    """
    return VariationalDerivative(action_density, field, coords)


__all__ = [
    'VariationalDerivative', 'EulerLagrangeEquation',
]
