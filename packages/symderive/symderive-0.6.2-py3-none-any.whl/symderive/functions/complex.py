"""
complex.py - Complex Number Functions.

Provides functions for working with complex numbers: Re, Im, Conjugate, Arg, Abs.

Internal Refs:
    Uses math_api.re, math_api.im, math_api.conjugate, math_api.arg, math_api.Abs
"""

from symderive.core.math_api import re, im, conjugate, arg, Abs as sympy_abs
from symderive.functions.utils import alias_function

# Complex number functions
Re = alias_function('Re', re)
Im = alias_function('Im', im)
Conjugate = alias_function('Conjugate', conjugate)
Arg = alias_function('Arg', arg)
Abs = alias_function('Abs', sympy_abs)

__all__ = [
    'Re',
    'Im',
    'Conjugate',
    'Arg',
    'Abs',
]
