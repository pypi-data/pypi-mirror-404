"""
Test suite for discretization module.

Tests for converting symbolic derivatives to finite difference stencils
and generating code in various languages.
"""

import pytest
from sympy import symbols, Function, Rational, simplify, expand

from symderive.core.math_api import Symbol
from symderive.calculus import D, VariationalDerivative
from symderive.discretization import Discretize, ToStencil, StencilCodeGen
from symderive.utils import Pipe


class TestDiscretize:
    """Tests for Discretize function."""

    def test_first_derivative_central(self):
        """Test central difference for first derivative."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # df/dx with central difference [x-h, x, x+h]
        expr = D(f, x)
        result = Discretize(expr, {x: ([x - h, x, x + h], h)})

        # Central difference: (f(x+h) - f(x-h)) / (2h)
        expected = (Function('f')(x + h) - Function('f')(x - h)) / (2 * h)
        assert simplify(result - expected) == 0

    def test_second_derivative_central(self):
        """Test central difference for second derivative."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # d^2f/dx^2 with central difference
        expr = D(f, (x, 2))
        result = Discretize(expr, {x: ([x - h, x, x + h], h)})

        # Central difference: (f(x+h) - 2f(x) + f(x-h)) / h^2
        expected = (Function('f')(x + h) - 2 * Function('f')(x) + Function('f')(x - h)) / h**2
        assert simplify(result - expected) == 0

    def test_forward_difference(self):
        """Test forward difference stencil."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # df/dx with forward difference [x, x+h]
        expr = D(f, x)
        result = Discretize(expr, {x: ([x, x + h], h)})

        # Forward difference: (f(x+h) - f(x)) / h
        expected = (Function('f')(x + h) - Function('f')(x)) / h
        assert simplify(result - expected) == 0

    def test_backward_difference(self):
        """Test backward difference stencil."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # df/dx with backward difference [x-h, x]
        expr = D(f, x)
        result = Discretize(expr, {x: ([x - h, x], h)})

        # Backward difference: (f(x) - f(x-h)) / h
        expected = (Function('f')(x) - Function('f')(x - h)) / h
        assert simplify(result - expected) == 0

    def test_higher_order_stencil(self):
        """Test higher-order stencil (5-point)."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # df/dx with 5-point stencil for higher accuracy
        expr = D(f, x)
        points = [x - 2*h, x - h, x, x + h, x + 2*h]
        result = Discretize(expr, {x: (points, h)})

        # Should give 4th-order accurate approximation
        # (-f(x+2h) + 8f(x+h) - 8f(x-h) + f(x-2h)) / (12h)
        assert result is not None
        # Verify it's a valid finite difference expression
        assert Function('f')(x + 2*h) in result.free_symbols or \
               result.has(Function('f')(x + 2*h))

    def test_mixed_derivatives(self):
        """Test expression with multiple derivatives."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # d^2f/dx^2 + f
        expr = D(f, (x, 2)) + f
        result = Discretize(expr, {x: ([x - h, x, x + h], h)})

        # Should discretize only the derivative term
        f_xph = Function('f')(x + h)
        f_x = Function('f')(x)
        f_xmh = Function('f')(x - h)
        expected = (f_xph - 2*f_x + f_xmh) / h**2 + f_x
        assert simplify(result - expected) == 0

    def test_multivariable_discretization(self):
        """Test discretization with multiple variables."""
        x, t = symbols('x t')
        hx, ht = symbols('h_x h_t')
        u = Function('u')(x, t)

        # Wave equation: d^2u/dt^2 - d^2u/dx^2
        expr = D(u, (t, 2)) - D(u, (x, 2))

        step_map = {
            x: ([x - hx, x, x + hx], hx),
            t: ([t - ht, t, t + ht], ht),
        }
        result = Discretize(expr, step_map)

        # Both derivatives should be discretized
        assert result is not None
        assert result.has(Function('u')(x + hx, t)) or \
               result.has(Function('u')(x, t + ht))

    def test_nested_expression(self):
        """Test discretization in nested expressions."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        from symderive.core.math_api import sin
        # sin(df/dx)
        expr = sin(D(f, x))
        result = Discretize(expr, {x: ([x - h, x, x + h], h)})

        # Should discretize the derivative inside sin
        expected_inner = (Function('f')(x + h) - Function('f')(x - h)) / (2 * h)
        expected = sin(expected_inner)
        assert simplify(result - expected) == 0


class TestVariationalToStencil:
    """Tests for variational derivative to stencil pipeline."""

    def test_wave_equation_stencil(self):
        """Test wave equation Lagrangian to stencil."""
        x = Symbol('x')
        h = Symbol('h')
        phi = Function('phi')(x)

        # Wave equation Lagrangian: L = (1/2)(dphi/dx)^2 - (1/2)phi^2
        L = Rational(1, 2) * D(phi, x)**2 - Rational(1, 2) * phi**2

        # Get Euler-Lagrange equation
        eq = VariationalDerivative(L, phi, [x])

        # Discretize
        result = Discretize(eq, {x: ([x - h, x, x + h], h)})

        # Should give discretized wave equation
        assert result is not None
        # The equation should involve phi at x-h, x, x+h
        assert result.has(Function('phi')(x + h)) or \
               result.has(Function('phi')(x - h))

    def test_pipe_integration(self):
        """Test Pipe API integration."""
        x = Symbol('x')
        h = Symbol('h')
        phi = Function('phi')(x)

        L = Rational(1, 2) * D(phi, x)**2

        # Use Pipe to chain operations
        result = (
            Pipe(L)
            .then(VariationalDerivative, phi, [x])
            .then(Discretize, {x: ([x - h, x, x + h], h)})
            .value
        )

        assert result is not None


class TestStencilCodeGen:
    """Tests for stencil code generation."""

    def test_python_codegen(self):
        """Test Python code generation."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # Second derivative central difference
        expr = D(f, (x, 2))
        stencil = Discretize(expr, {x: ([x - h, x, x + h], h)})

        code = StencilCodeGen(stencil, language='python',
                              array_name='u', index_var='i', spacing_name='dx')

        assert 'u[i+1]' in code or 'u[i + 1]' in code
        assert 'u[i-1]' in code or 'u[i - 1]' in code
        assert 'u[i]' in code
        assert 'dx' in code

    def test_c_codegen(self):
        """Test C code generation."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        expr = D(f, (x, 2))
        stencil = Discretize(expr, {x: ([x - h, x, x + h], h)})

        code = StencilCodeGen(stencil, language='c',
                              array_name='u', index_var='i', spacing_name='dx')

        assert 'u[i+1]' in code or 'u[i + 1]' in code
        assert 'u[i-1]' in code or 'u[i - 1]' in code
        assert 'dx' in code

    def test_fortran_codegen(self):
        """Test Fortran code generation."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        expr = D(f, (x, 2))
        stencil = Discretize(expr, {x: ([x - h, x, x + h], h)})

        code = StencilCodeGen(stencil, language='fortran',
                              array_name='u', index_var='i', spacing_name='dx')

        # Fortran uses 1-based indexing typically, but we test the general structure
        assert 'u(' in code or 'u[' in code
        assert 'dx' in code

    def test_latex_output(self):
        """Test LaTeX output for stencil."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        expr = D(f, (x, 2))
        stencil = Discretize(expr, {x: ([x - h, x, x + h], h)})

        code = StencilCodeGen(stencil, language='latex')

        # Should produce valid LaTeX
        assert '\\frac' in code or 'frac' in code


class TestToStencil:
    """Tests for ToStencil convenience function."""

    def test_to_stencil_basic(self):
        """Test ToStencil convenience function."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        expr = D(f, (x, 2))

        # ToStencil combines Discretize and optionally code generation
        result = ToStencil(expr, {x: h})

        # Should return discretized expression
        assert result is not None

    def test_to_stencil_with_width(self):
        """Test ToStencil with specified stencil width."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        expr = D(f, x)

        # 3-point stencil (default central)
        result3 = ToStencil(expr, {x: h}, width=3)

        # 5-point stencil (higher accuracy)
        result5 = ToStencil(expr, {x: h}, width=5)

        # 5-point should be different (higher order)
        # Both should be valid
        assert result3 is not None
        assert result5 is not None

    def test_to_stencil_codegen(self):
        """Test ToStencil with code generation."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        expr = D(f, (x, 2))

        # Get Python code directly - use 'spacing_name' to avoid conflict
        code = ToStencil(expr, {x: h}, language='python',
                         array_name='phi', index_var='j', spacing_name='h')

        assert 'phi[j' in code
        assert 'h' in code


class TestMixedPartialDerivatives:
    """Tests for mixed partial derivative discretization (Issue #10 fix)."""

    def test_mixed_partial_dxdy(self):
        """Test discretization of d^2f/dxdy."""
        x, y = symbols('x y')
        hx, hy = symbols('h_x h_y')
        f = Function('f')(x, y)

        # Mixed partial d^2f/dxdy
        expr = D(D(f, x), y)
        step_map = {
            x: ([x - hx, x, x + hx], hx),
            y: ([y - hy, y, y + hy], hy),
        }
        result = Discretize(expr, step_map)

        # Result should contain offsets in BOTH x and y
        result_str = str(result)
        assert 'h_x' in result_str
        assert 'h_y' in result_str
        # Should have terms with both x and hx offsets (SymPy may order as -h_x + x or h_x + x)
        assert 'h_x + x' in result_str or '-h_x + x' in result_str
        # Should have terms with both y and hy offsets
        assert 'h_y + y' in result_str or '-h_y + y' in result_str

    def test_mixed_partial_higher_order(self):
        """Test discretization of d^3f/dx^2dy."""
        x, y = symbols('x y')
        hx, hy = symbols('h_x h_y')
        f = Function('f')(x, y)

        # d^3f/dx^2 dy
        expr = D(D(f, (x, 2)), y)
        step_map = {
            x: ([x - hx, x, x + hx], hx),
            y: ([y - hy, y, y + hy], hy),
        }
        result = Discretize(expr, step_map)

        # Result should be non-trivial and contain both step sizes
        assert result is not None
        result_str = str(result)
        assert 'h_x' in result_str
        assert 'h_y' in result_str


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_no_derivatives(self):
        """Test expression with no derivatives passes through."""
        x = Symbol('x')
        h = Symbol('h')
        f = Function('f')(x)

        # Just f, no derivatives
        expr = f + x**2
        result = Discretize(expr, {x: ([x - h, x, x + h], h)})

        # Should return unchanged
        assert result == expr

    def test_empty_step_map(self):
        """Test with empty step map."""
        x = Symbol('x')
        f = Function('f')(x)

        expr = D(f, x)
        result = Discretize(expr, {})

        # Should return unchanged (no discretization possible)
        assert result == expr

    def test_unspecified_variable(self):
        """Test derivative w.r.t. variable not in step_map."""
        x, y = symbols('x y')
        h = Symbol('h')
        f = Function('f')(x, y)

        # Derivative w.r.t. y, but only x is in step_map
        expr = D(f, y)
        result = Discretize(expr, {x: ([x - h, x, x + h], h)})

        # Derivative w.r.t. y should remain symbolic
        assert result == expr
