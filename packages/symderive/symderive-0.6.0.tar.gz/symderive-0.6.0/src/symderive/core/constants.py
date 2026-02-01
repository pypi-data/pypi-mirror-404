"""
constants.py - Mathematical Constants.

Provides constants: Pi, E, I, Infinity, etc.

Internal Refs:
    Uses math_api.pi, math_api.sym_E, math_api.sym_I, math_api.oo,
    math_api.zoo, math_api.nan
"""

from symderive.core.math_api import (
    pi,
    sym_E as sympy_E,
    sym_I as sympy_I,
    oo,
    zoo,
    nan,
)

# constants
Pi = pi
E = sympy_E
I = sympy_I
Infinity = oo
oo = oo  # Also export as oo for convenience
ComplexInfinity = zoo
Indeterminate = nan

__all__ = [
    'Pi',
    'E',
    'I',
    'Infinity',
    'oo',
    'ComplexInfinity',
    'Indeterminate',
]
