"""Test that the project is set up correctly."""

import sympy
import symderive


def test_import_symderive():
    """Test that symderive package can be imported."""
    assert hasattr(symderive, 'Symbol')


def test_sympy_available():
    """Test that sympy is available."""
    x = sympy.Symbol('x')
    assert sympy.diff(x**2, x) == 2*x
