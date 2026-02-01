"""
Tests for derive.optimize module.

Tests the thin cvxpy wrapper for convex optimization.
"""

import pytest
import numpy as np

# Skip all tests if cvxpy is not installed
cvxpy = pytest.importorskip("cvxpy")

from symderive.optimize import (
    OptVar, Minimize, Maximize, OptimizationProblem,
    Norm, Sum, Quad, PositiveSemidefinite,
)


# =============================================================================
# OptVar Tests
# =============================================================================

class TestOptVar:
    """Tests for optimization variables."""

    def test_create_scalar(self):
        """Test creating a scalar variable."""
        x = OptVar('x')
        assert x.name == 'x'
        assert x.shape == ()
        assert x.domain == 'reals'

    def test_create_nonneg(self):
        """Test creating a nonnegative variable."""
        x = OptVar('x', domain='nonneg')
        assert x.domain == 'nonneg'

    def test_create_vector(self):
        """Test creating a vector variable."""
        x = OptVar('x', shape=(3,))
        assert x.shape == (3,)

    def test_create_with_bounds(self):
        """Test creating a variable with bounds."""
        x = OptVar('x', bounds=(0, 10))
        assert x.bounds == (0, 10)

    def test_get_bound_constraints(self):
        """Test that get_bound_constraints returns proper constraints."""
        x = OptVar('x', bounds=(0, 10))
        constraints = x.get_bound_constraints()
        assert len(constraints) == 2

    def test_get_bound_constraints_no_bounds(self):
        """Test that get_bound_constraints returns empty list when no bounds."""
        x = OptVar('x')
        constraints = x.get_bound_constraints()
        assert len(constraints) == 0

    def test_get_bound_constraints_partial_bounds(self):
        """Test partial bounds (only lower or upper)."""
        x = OptVar('x', bounds=(0, None))
        constraints = x.get_bound_constraints()
        assert len(constraints) == 1

        y = OptVar('y', bounds=(None, 10))
        constraints = y.get_bound_constraints()
        assert len(constraints) == 1

    def test_repr(self):
        """Test string representation."""
        x = OptVar('x', domain='nonneg')
        assert 'OptVar' in repr(x)
        assert 'x' in repr(x)


# =============================================================================
# Minimize Tests
# =============================================================================

class TestMinimize:
    """Tests for minimization problems."""

    def test_simple_minimize(self):
        """Test simple unconstrained minimization."""
        x = OptVar('x')
        prob = Minimize(x**2)
        result = prob.solve()
        assert abs(result) < 1e-6
        assert abs(x.value) < 1e-6

    def test_minimize_with_constraint(self):
        """Test minimization with constraint."""
        x = OptVar('x')
        prob = Minimize(x**2, [x >= 1])
        result = prob.solve()
        assert abs(result - 1.0) < 1e-6
        assert abs(x.value - 1.0) < 1e-6

    def test_minimize_two_vars(self):
        """Test minimization with two variables."""
        x = OptVar('x')
        y = OptVar('y')
        prob = Minimize(x**2 + y**2, [x + y >= 2])
        result = prob.solve()
        # Minimum is at x = y = 1, objective = 2
        assert abs(result - 2.0) < 1e-6
        assert abs(x.value - 1.0) < 1e-6
        assert abs(y.value - 1.0) < 1e-6

    def test_minimize_linear(self):
        """Test linear program."""
        x = OptVar('x', domain='nonneg')
        y = OptVar('y', domain='nonneg')
        prob = Minimize(
            2*x + 3*y,
            [x + y >= 1, x >= 0.2]
        )
        result = prob.solve()
        # Minimum is at x=1, y=0 (since 2<3), so obj=2
        assert abs(result - 2.0) < 1e-4

    def test_problem_status(self):
        """Test that problem status is set correctly."""
        x = OptVar('x')
        prob = Minimize(x**2, [x >= 0])
        prob.solve()
        assert prob.is_solved
        assert prob.status == 'optimal'


# =============================================================================
# Maximize Tests
# =============================================================================

class TestMaximize:
    """Tests for maximization problems."""

    def test_simple_maximize(self):
        """Test simple bounded maximization."""
        x = OptVar('x')
        prob = Maximize(x, [x <= 5, x >= 0])
        result = prob.solve()
        assert abs(result - 5.0) < 1e-6
        assert abs(x.value - 5.0) < 1e-6

    def test_maximize_with_multiple_constraints(self):
        """Test maximization with multiple constraints."""
        x = OptVar('x', domain='nonneg')
        y = OptVar('y', domain='nonneg')
        prob = Maximize(
            x + y,
            [x <= 3, y <= 4, x + y <= 5]
        )
        result = prob.solve()
        assert abs(result - 5.0) < 1e-6


# =============================================================================
# Norm Tests
# =============================================================================

class TestNorm:
    """Tests for norm functions."""

    def test_l2_norm_minimize(self):
        """Test minimizing L2 norm."""
        x = OptVar('x', shape=(2,))
        prob = Minimize(Norm(x, 2), [x[0] >= 1, x[1] >= 1])
        result = prob.solve()
        # Minimum L2 norm with x >= [1,1] is sqrt(2)
        assert abs(result - np.sqrt(2)) < 1e-4

    def test_l1_norm(self):
        """Test L1 norm constraint."""
        x = OptVar('x', shape=(3,))
        prob = Minimize(
            Sum(x),
            [Norm(x, 1) <= 1, x >= 0]
        )
        result = prob.solve()
        # All elements can be positive, L1 norm <= 1
        # Minimum sum with x >= 0 and ||x||_1 <= 1 is 0
        assert result >= -1e-6


# =============================================================================
# Sum and Quad Tests
# =============================================================================

class TestSumQuad:
    """Tests for Sum and Quad functions."""

    def test_sum_constraint(self):
        """Test sum in constraints."""
        x = OptVar('x', shape=(3,), domain='nonneg')
        prob = Minimize(
            -Sum(x),  # Maximize sum
            [Sum(x) <= 10, x <= 5]
        )
        result = prob.solve()
        assert abs(result + 10.0) < 1e-4  # Sum should be 10

    def test_quad_form(self):
        """Test quadratic form."""
        x = OptVar('x', shape=(2,))
        prob = Minimize(Quad(x), [x[0] >= 1])
        result = prob.solve()
        # Minimum ||x||^2 with x[0] >= 1 is 1 (at x=[1,0])
        assert abs(result - 1.0) < 1e-4


# =============================================================================
# Edge Cases
# =============================================================================

class TestBoundsEnforcement:
    """Tests for bounds enforcement in optimization."""

    def test_inline_optvar_bounds_not_dropped(self):
        """Test that bounds work with inline OptVar (issue #15).

        Regression test: WeakValueDictionary caused OptVar to be GC'd before
        solve(), silently dropping bounds.
        """
        import gc

        # Create problem with inline OptVar - no variable stores the OptVar
        prob = Minimize(OptVar('x', bounds=(2, 10)))

        # Force garbage collection to trigger the bug if present
        gc.collect()

        result = prob.solve()
        assert prob.is_solved
        # If bounds were applied, minimum is at lower bound (2)
        # If bounds were dropped, this would be unbounded
        assert abs(result - 2.0) < 1e-4

    def test_bounds_enforced_in_minimize(self):
        """Test that bounds are actually enforced during minimization."""
        x = OptVar('x', bounds=(2, 10))
        prob = Minimize(x)  # Without bounds, min would be unbounded
        result = prob.solve()
        assert prob.is_solved
        assert abs(x.value - 2.0) < 1e-4  # Should find min at lower bound

    def test_bounds_enforced_in_maximize(self):
        """Test that bounds are enforced during maximization."""
        x = OptVar('x', bounds=(0, 5))
        prob = Maximize(x)
        result = prob.solve()
        assert prob.is_solved
        assert abs(x.value - 5.0) < 1e-4  # Should find max at upper bound

    def test_bounds_with_other_constraints(self):
        """Test bounds combined with explicit constraints."""
        x = OptVar('x', bounds=(0, 10))
        prob = Minimize(x**2, [x >= 3])  # Explicit constraint tighter than bound
        result = prob.solve()
        assert prob.is_solved
        assert abs(x.value - 3.0) < 1e-4  # Should respect the tighter constraint

    def test_bounds_make_problem_feasible(self):
        """Test that bounds properly constrain the solution space."""
        x = OptVar('x', bounds=(1, 5))
        y = OptVar('y', bounds=(1, 5))
        prob = Minimize(x + y)
        result = prob.solve()
        assert prob.is_solved
        assert abs(result - 2.0) < 1e-4  # Both at lower bounds


class TestEdgeCases:
    """Tests for edge cases."""

    def test_equality_constraint(self):
        """Test equality constraints."""
        x = OptVar('x')
        y = OptVar('y')
        prob = Minimize(x**2 + y**2, [x + y == 2])
        result = prob.solve()
        # Minimum when x = y = 1
        assert abs(result - 2.0) < 1e-4

    def test_infeasible_problem(self):
        """Test infeasible problem detection."""
        x = OptVar('x')
        prob = Minimize(x, [x >= 10, x <= 5])
        result = prob.solve()
        assert not prob.is_solved
        assert 'infeasible' in prob.status.lower()

    def test_unbounded_problem(self):
        """Test unbounded problem detection."""
        x = OptVar('x')
        prob = Minimize(-x)  # Unbounded below
        result = prob.solve()
        assert not prob.is_solved


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_portfolio_optimization(self):
        """Test a simple portfolio optimization problem."""
        import cvxpy as cp

        # Two assets with expected returns
        returns = np.array([0.1, 0.2])
        # Covariance matrix (for risk)
        cov = np.array([[0.04, 0.01], [0.01, 0.09]])

        w = OptVar('w', shape=(2,), domain='nonneg')
        w_cvx = w._get_cvxpy_var()

        # Maximize return - lambda * risk (simplified)
        # Use cvxpy directly for matrix operations
        prob = cp.Problem(
            cp.Maximize(returns @ w_cvx - 0.5 * cp.quad_form(w_cvx, cov)),
            [cp.sum(w_cvx) == 1]
        )
        result = prob.solve()

        # Should find optimal weights
        assert prob.status == 'optimal'
        weights = w.value
        assert abs(np.sum(weights) - 1.0) < 1e-4
        assert all(wi >= -1e-6 for wi in weights)

    def test_least_squares(self):
        """Test least squares problem."""
        import cvxpy as cp

        # min ||Ax - b||^2
        A = np.array([[1, 2], [3, 4], [5, 6]])
        b = np.array([1, 2, 3])

        x = OptVar('x', shape=(2,))
        x_cvx = x._get_cvxpy_var()

        prob = cp.Problem(cp.Minimize(cp.sum_squares(A @ x_cvx - b)))
        result = prob.solve()

        assert prob.status == 'optimal'
        # Check residual is reasonably small
        residual = np.linalg.norm(A @ x.value - b)
        assert residual < 0.5
