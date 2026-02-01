"""
Tests for derive.regression module.

Tests the PySR wrapper for symbolic regression (FindFormula).

Note: PySR tests are slow due to Julia JIT compilation and genetic algorithms.
Integration tests are marked as slow and skipped by default. Run with:
    pytest tests/test_symbolic.py -v --run-slow
"""

import pytest
import numpy as np
import sympy as sp

from symderive import Symbol
from symderive.regression import FindFormula
from symderive.regression.core import (
    _convert_target_functions,
    _data_to_arrays,
)


# =============================================================================
# Unit Tests (Fast - no PySR execution)
# =============================================================================

class TestHelperFunctions:
    """Unit tests for helper functions that don't run PySR."""

    def test_convert_target_functions_none(self):
        """Test default operators when target_functions is None."""
        binary, unary = _convert_target_functions(None)
        assert '+' in binary
        assert '*' in binary
        assert 'sin' in unary
        assert 'cos' in unary

    def test_convert_target_functions_mathematica_names(self):
        """Test converting Mathematica function names."""
        binary, unary = _convert_target_functions(['Plus', 'Times', 'Sin', 'Cos'])
        assert '+' in binary
        assert '*' in binary
        assert 'sin' in unary
        assert 'cos' in unary

    def test_convert_target_functions_power(self):
        """Test Power is mapped to ^ binary operator."""
        binary, unary = _convert_target_functions(['Plus', 'Power'])
        assert '^' in binary

    def test_data_to_arrays_list_of_pairs(self):
        """Test converting list of [x, y] pairs."""
        x = Symbol('x')
        data = [[0, 1], [1, 2], [2, 3]]
        X, y, names = _data_to_arrays(data, x)

        assert X.shape == (3, 1)
        assert y.shape == (3,)
        assert names[0] == x
        np.testing.assert_array_equal(X.flatten(), [0, 1, 2])
        np.testing.assert_array_equal(y, [1, 2, 3])

    def test_data_to_arrays_tuple(self):
        """Test converting (X, y) tuple."""
        x = Symbol('x')
        X_in = np.array([0, 1, 2, 3])
        y_in = np.array([1, 3, 5, 7])
        X, y, names = _data_to_arrays((X_in, y_in), x)

        assert X.shape == (4, 1)
        assert y.shape == (4,)
        assert names[0] == x

    def test_data_to_arrays_2d_array(self):
        """Test converting 2D numpy array."""
        x = Symbol('x')
        data = np.array([[0, 1], [1, 3], [2, 5]])
        X, y, names = _data_to_arrays(data, x)

        assert X.shape == (3, 1)
        assert y.shape == (3,)
        np.testing.assert_array_equal(X.flatten(), [0, 1, 2])
        np.testing.assert_array_equal(y, [1, 3, 5])

    def test_data_to_arrays_y_only(self):
        """Test converting y-only data (x becomes indices)."""
        x = Symbol('x')
        y_data = np.array([1, 4, 9, 16])
        X, y, names = _data_to_arrays(y_data, x)

        assert X.shape == (4, 1)
        np.testing.assert_array_equal(X.flatten(), [0, 1, 2, 3])
        np.testing.assert_array_equal(y, [1, 4, 9, 16])


# =============================================================================
# Import Tests (Fast)
# =============================================================================

class TestImport:
    """Tests for module import."""

    def test_import_from_derive(self):
        """Test that FindFormula can be imported from symderive."""
        from symderive import FindFormula as FF
        assert FF is not None
        assert callable(FF)

    def test_import_from_regression(self):
        """Test direct import from regression module."""
        from symderive.regression import FindFormula as FF
        assert FF is not None
        assert callable(FF)


# =============================================================================
# Integration Tests (Slow - actually run PySR)
# =============================================================================

@pytest.mark.slow
class TestFindFormulaIntegration:
    """Integration tests that actually run PySR. These are slow."""

    def test_simple_linear(self):
        """Test finding a simple linear formula y = 2x + 1."""
        x = Symbol('x')
        data = [[i, 2*i + 1] for i in range(20)]

        result = FindFormula(
            data, x,
            niterations=5,
            populations=5,
            max_complexity=8
        )

        assert isinstance(result, sp.Expr)
        # Evaluate at a test point - should be reasonably close
        test_val = float(result.subs(x, 5))
        expected = 11
        assert abs(test_val - expected) < 2.0

    def test_prop_all_returns_dict(self):
        """Test that prop='All' returns a dictionary."""
        x = Symbol('x')
        data = [[i, 2*i] for i in range(10)]

        result = FindFormula(
            data, x,
            prop='All',
            niterations=5,
            populations=5,
            max_complexity=5
        )

        assert isinstance(result, dict)
        assert 'Score' in result
        assert 'Error' in result
        assert 'Complexity' in result
        assert 'Expression' in result

    def test_multiple_results(self):
        """Test requesting n>1 formulas returns a list."""
        x = Symbol('x')
        data = [[i, i**2] for i in range(10)]

        results = FindFormula(
            data, x,
            n=3,
            niterations=5,
            populations=5,
            max_complexity=10
        )

        assert isinstance(results, list)
        assert len(results) >= 1
        for r in results:
            assert isinstance(r, sp.Expr)
