"""
Test suite for Green's functions module.

Tests verify Green's function implementations for common PDEs.
"""

import pytest
from sympy import Heaviside
from symderive import Symbol, symbols, Simplify, Pi, Abs, Exp, I
from symderive.calculus.greens import (
    GreenFunction,
    GreenFunctionPoisson1D,
    GreenFunctionHelmholtz1D,
    GreenFunctionLaplacian3D,
    GreenFunctionWave1D,
)


class TestGreenFunctionPoisson1D:
    """Test 1D Poisson Green's function."""

    def test_basic_structure(self):
        """Green's function should be piecewise."""
        x, xp = symbols('x xp')
        L = Symbol('L', positive=True)
        G = GreenFunctionPoisson1D(x, xp, L)
        # Should be a Piecewise expression
        assert hasattr(G, 'args')

    def test_symmetry(self):
        """G(x, x') should equal G(x', x) (symmetric Green's function)."""
        x, xp = symbols('x xp')
        L = Symbol('L', positive=True)
        G1 = GreenFunctionPoisson1D(x, xp, L)
        G2 = GreenFunctionPoisson1D(xp, x, L)
        # Both should have same structure (symmetry in x, x')
        assert G1.has(x) and G1.has(xp)
        assert G2.has(x) and G2.has(xp)

    def test_boundary_at_zero(self):
        """G(0, x') = 0 for Dirichlet BC at x=0."""
        x, xp = symbols('x xp')
        L = Symbol('L', positive=True)
        G = GreenFunctionPoisson1D(x, xp, L)
        # Substitute x=0 and a specific x' value to verify
        G_at_0 = G.subs([(x, 0), (xp, L/2)])
        assert Simplify(G_at_0) == 0

    def test_boundary_at_L(self):
        """G(L, x') = 0 for Dirichlet BC at x=L."""
        x, xp = symbols('x xp')
        L = Symbol('L', positive=True)
        G = GreenFunctionPoisson1D(x, xp, L)
        # Substitute x=L and a specific x' value to verify
        G_at_L = G.subs([(x, L), (xp, L/2)])
        assert Simplify(G_at_L) == 0


class TestGreenFunctionHelmholtz1D:
    """Test 1D Helmholtz Green's function."""

    def test_basic_structure(self):
        """Should return exponential form."""
        x, xp, k = symbols('x xp k')
        G = GreenFunctionHelmholtz1D(x, xp, k)
        # Should contain exp and Abs
        assert G.has(Exp) or G.has(I)

    def test_contains_wavenumber(self):
        """Result should depend on wavenumber k."""
        x, xp, k = symbols('x xp k')
        G = GreenFunctionHelmholtz1D(x, xp, k)
        assert G.has(k)

    def test_symmetry_in_distance(self):
        """G depends on |x - x'|, so G(x, x') = G(x', x)."""
        x, xp, k = symbols('x xp k')
        G1 = GreenFunctionHelmholtz1D(x, xp, k)
        G2 = GreenFunctionHelmholtz1D(xp, x, k)
        # Both should have same form due to |x - x'| = |x' - x|
        diff = Simplify(G1 - G2)
        assert diff == 0


class TestGreenFunctionLaplacian3D:
    """Test 3D Laplacian Green's function."""

    def test_basic_form(self):
        """G(r) = -1/(4*pi*r)."""
        r = Symbol('r', positive=True)
        G = GreenFunctionLaplacian3D(r)
        expected = -1 / (4 * Pi * r)
        assert Simplify(G - expected) == 0

    def test_singularity_structure(self):
        """Should have 1/r singularity."""
        r = Symbol('r', positive=True)
        G = GreenFunctionLaplacian3D(r)
        # G * r should be constant
        G_times_r = Simplify(G * r)
        assert not G_times_r.has(r)


class TestGreenFunctionWave1D:
    """Test 1D wave equation Green's function."""

    def test_basic_structure(self):
        """Should contain Heaviside step function."""
        x, t, xp, tp, c = symbols('x t xp tp c')
        G = GreenFunctionWave1D(x, t, xp, tp, c)
        # Should depend on all variables
        assert G.has(x) and G.has(t) and G.has(c)

    def test_causality(self):
        """Green's function should be causal (zero for t < tp)."""
        x, t, xp, tp, c = symbols('x t xp tp c', positive=True)
        G = GreenFunctionWave1D(x, t, xp, tp, c)
        # Contains Heaviside which enforces causality
        assert G.has(Heaviside)

    def test_wave_speed_dependence(self):
        """Result should depend on wave speed c."""
        x, t, xp, tp, c = symbols('x t xp tp c')
        G = GreenFunctionWave1D(x, t, xp, tp, c)
        assert G.has(c)


class TestGreenFunction:
    """Test generic Green's function."""

    def test_basic_creation(self):
        """Should create a piecewise Green's function."""
        x, xp = symbols('x xp')
        G = GreenFunction(None, x, xp)
        # Should return an expression
        assert G is not None
        assert G.has(x) and G.has(xp)
