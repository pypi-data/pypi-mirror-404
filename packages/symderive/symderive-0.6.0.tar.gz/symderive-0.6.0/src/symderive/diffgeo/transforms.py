"""
transforms.py - Coordinate Transformations

Provides coordinate transformation functionality for converting
between coordinate systems and transforming metric tensors.

Internal Refs:
    Uses math_api.Symbol, math_api.symbols, math_api.Matrix,
    math_api.sin, math_api.cos, math_api.Expr
"""

from itertools import product as iterproduct
from typing import List, Dict

from symderive.core.math_api import (
    Symbol,
    symbols,
    Matrix,
    sin,
    cos,
    Expr,
)

from symderive.diffgeo.metrics import Metric

# Use derive's own APIs for self-consistency
from symderive.calculus import D
from symderive.algebra import Simplify


class CoordinateTransformation:
    """
    Represents a coordinate transformation between two coordinate systems.
    """

    def __init__(self, old_coords: List[Symbol], new_coords: List[Symbol],
                 transform_eqs: Dict[Symbol, Expr]):
        """
        Initialize a coordinate transformation.

        Args:
            old_coords: Original coordinate symbols
            new_coords: New coordinate symbols
            transform_eqs: Dictionary mapping old coords to expressions in new coords
                          e.g., {x: r*cos(theta), y: r*sin(theta)}
        """
        self.old_coords = list(old_coords)
        self.new_coords = list(new_coords)
        self.transform = transform_eqs

        # Compute Jacobian
        self._jacobian = None
        self._inverse_jacobian = None

    @property
    def jacobian(self) -> Matrix:
        """
        Compute the Jacobian matrix ∂x^i/∂x'^j.
        """
        if self._jacobian is not None:
            return self._jacobian

        n = len(self.old_coords)
        J = Matrix.zeros(n, n)

        for i, j in iterproduct(range(n), range(n)):
            old = self.old_coords[i]
            new = self.new_coords[j]
            expr = self.transform.get(old, old)
            J[i, j] = D(expr, new)

        self._jacobian = J
        return self._jacobian

    @property
    def jacobian_determinant(self) -> Expr:
        """Get the Jacobian determinant."""
        return self.jacobian.det()

    def transform_metric(self, metric: Metric) -> Metric:
        """
        Transform a metric to new coordinates.

        g'_{mu nu} = (partial x^rho/partial x'^mu)(partial x^sigma/partial x'^nu) g_{rho sigma}
        """
        J = self.jacobian
        n = metric.dim

        # Pre-compute substituted metric components (dict-based substitution is more efficient)
        g_substituted = Matrix.zeros(n, n)
        for rho, sigma in iterproduct(range(n), range(n)):
            g_substituted[rho, sigma] = metric.g[rho, sigma].subs(self.transform)

        # New metric components using itertools.product
        g_new = Matrix.zeros(n, n)
        for mu, nu in iterproduct(range(n), range(n)):
            val = sum(
                J[rho, mu] * J[sigma, nu] * g_substituted[rho, sigma]
                for rho, sigma in iterproduct(range(n), range(n))
            )
            g_new[mu, nu] = Simplify(val)

        return Metric(self.new_coords, g_new)


def cartesian_to_spherical_3d() -> CoordinateTransformation:
    """
    Create transformation from Cartesian (x, y, z) to spherical (r, θ, φ).
    """
    x, y, z = symbols('x y z')
    r, theta, phi = symbols('r theta phi')

    transform = {
        x: r * sin(theta) * cos(phi),
        y: r * sin(theta) * sin(phi),
        z: r * cos(theta)
    }

    return CoordinateTransformation([x, y, z], [r, theta, phi], transform)


def cartesian_to_cylindrical() -> CoordinateTransformation:
    """
    Create transformation from Cartesian (x, y, z) to cylindrical (ρ, φ, z).
    """
    x, y, z_cart = symbols('x y z')
    rho, phi, z_cyl = symbols('rho phi z')

    transform = {
        x: rho * cos(phi),
        y: rho * sin(phi),
        z_cart: z_cyl
    }

    return CoordinateTransformation([x, y, z_cart], [rho, phi, z_cyl], transform)


__all__ = [
    'CoordinateTransformation',
    'cartesian_to_spherical_3d', 'cartesian_to_cylindrical',
]
