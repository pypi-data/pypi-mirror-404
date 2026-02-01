"""
symbols.py - Symbol and Function definitions.

Provides Symbol, symbols, and Function for creating symbolic variables.
Also exports common sympy types so users don't need to import sympy directly.

Internal Refs:
    Uses math_api.Symbol, math_api.symbols, math_api.Function, math_api.Rational,
    math_api.Integer, math_api.Float, math_api.Array, math_api.ImmutableDenseNDimArray,
    math_api.MutableDenseNDimArray, math_api.Heaviside, math_api.DiracDelta
"""

from symderive.core.math_api import (
    Symbol,
    symbols,
    Function,
    Rational,
    Integer,
    Float,
    Array,
    ImmutableDenseNDimArray,
    MutableDenseNDimArray,
    Heaviside,
    DiracDelta,
)

__all__ = [
    'Symbol',
    'symbols',
    'Function',
    'Rational',
    'Integer',
    'Float',
    # Common types
    'Array',
    'ImmutableDenseNDimArray',
    'MutableDenseNDimArray',
    'Heaviside',
    'DiracDelta',
]
