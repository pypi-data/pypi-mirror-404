"""
assumptions.py - Assumptions System for Symbolic Computation

Provides context managers and utilities for working with mathematical assumptions.

Internal Refs:
    Uses math_api.Symbol, math_api.Q, math_api.ask, math_api.refine,
    math_api.sym_simplify, math_api.global_assumptions, math_api.Predicate,
    math_api.And
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional, List, Union

from symderive.core.math_api import (
    Symbol,
    Q,
    ask,
    refine,
    sym_simplify as simplify,
    global_assumptions,
    Predicate,
    And,
)


@contextmanager
def Assuming(*conditions):
    """
    Context manager for temporarily adding assumptions.

    Within the context, expressions will simplify according to the given
    assumptions. Assumptions are automatically removed when exiting the context.

    Pre-existing global assumptions are preserved after the context exits.

    Args:
        *conditions: One or more assumption conditions (e.g., Q.positive(x))

    Yields:
        None

    Examples:
        >>> x = Symbol('x')
        >>> with Assuming(Q.positive(x)):
        ...     result = refine(Abs(x))
        ...     print(result)  # x (not |x| since x is positive)

        >>> with Assuming(Q.real(x), Q.positive(x)):
        ...     result = simplify_with_assumptions(sqrt(x**2))
        ...     print(result)  # x
    """
    # Track which conditions are newly added (not pre-existing)
    newly_added = []

    for condition in conditions:
        if condition not in global_assumptions:
            newly_added.append(condition)
        global_assumptions.add(condition)

    try:
        yield
    finally:
        # Remove only the conditions we newly added
        for condition in newly_added:
            global_assumptions.remove(condition)


def Refine(expr: Any, *assumptions) -> Any:
    """
    Simplify an expression under given assumptions.

    This is a wrapper around SymPy's refine that accepts multiple assumptions
    directly without requiring a context manager.

    Args:
        expr: Expression to refine
        *assumptions: Assumption conditions (e.g., Q.positive(x))

    Returns:
        Refined expression

    Examples:
        >>> x = Symbol('x')
        >>> Refine(Abs(x), Q.positive(x))
        x
        >>> Refine(sqrt(x**2), Q.real(x), Q.positive(x))
        x
    """
    if not assumptions:
        return refine(expr)

    # Combine multiple assumptions with And
    if len(assumptions) == 1:
        combined = assumptions[0]
    else:
        combined = And(*assumptions)

    return refine(expr, combined)


def Ask(proposition: Any, assumptions: Optional[Any] = None) -> Optional[bool]:
    """
    Query whether a proposition is true given assumptions.

    Args:
        proposition: A predicate to query (e.g., Q.positive(x))
        assumptions: Optional assumptions context

    Returns:
        True, False, or None if undetermined

    Examples:
        >>> x = Symbol('x', positive=True)
        >>> Ask(Q.positive(x))
        True
        >>> y = Symbol('y')
        >>> Ask(Q.positive(y), Q.real(y) & Q.positive(y))
        True
    """
    if assumptions is None:
        return ask(proposition)
    return ask(proposition, assumptions)


def SimplifyWithAssumptions(expr: Any, *assumptions) -> Any:
    """
    Simplify an expression with temporary assumptions.

    Combines refine and simplify for best results.

    Args:
        expr: Expression to simplify
        *assumptions: Assumption conditions

    Returns:
        Simplified expression

    Examples:
        >>> x = Symbol('x')
        >>> SimplifyWithAssumptions(sqrt(x**2), Q.positive(x))
        x
    """
    if assumptions:
        refined = Refine(expr, *assumptions)
        return simplify(refined)
    return simplify(expr)


class AssumedSymbol:
    """
    Factory for creating symbols with built-in assumptions.

    Provides a cleaner API for creating assumed symbols.

    Examples:
        >>> x = AssumedSymbol.positive('x')
        >>> # equivalent to Symbol('x', positive=True)
    """

    @staticmethod
    def positive(name: str, **kwargs) -> Symbol:
        """Create a positive symbol."""
        return Symbol(name, positive=True, **kwargs)

    @staticmethod
    def negative(name: str, **kwargs) -> Symbol:
        """Create a negative symbol."""
        return Symbol(name, negative=True, **kwargs)

    @staticmethod
    def real(name: str, **kwargs) -> Symbol:
        """Create a real symbol."""
        return Symbol(name, real=True, **kwargs)

    @staticmethod
    def integer(name: str, **kwargs) -> Symbol:
        """Create an integer symbol."""
        return Symbol(name, integer=True, **kwargs)

    @staticmethod
    def nonzero(name: str, **kwargs) -> Symbol:
        """Create a nonzero symbol."""
        return Symbol(name, nonzero=True, **kwargs)

    @staticmethod
    def nonnegative(name: str, **kwargs) -> Symbol:
        """Create a nonnegative symbol."""
        return Symbol(name, nonnegative=True, **kwargs)

    @staticmethod
    def complex(name: str, **kwargs) -> Symbol:
        """Create a complex symbol (default, no real assumption)."""
        return Symbol(name, complex=True, **kwargs)

    @staticmethod
    def even(name: str, **kwargs) -> Symbol:
        """Create an even integer symbol."""
        return Symbol(name, even=True, **kwargs)

    @staticmethod
    def odd(name: str, **kwargs) -> Symbol:
        """Create an odd integer symbol."""
        return Symbol(name, odd=True, **kwargs)

    @staticmethod
    def prime(name: str, **kwargs) -> Symbol:
        """Create a prime symbol."""
        return Symbol(name, prime=True, **kwargs)


# Predicate shortcuts - expose SymPy's Q predicates with cleaner names
Positive = Q.positive
Negative = Q.negative
Real = Q.real
Integer = Q.integer
Rational = Q.rational
Complex = Q.complex
Even = Q.even
Odd = Q.odd
Prime = Q.prime
Nonzero = Q.nonzero
Nonnegative = Q.nonnegative
Nonpositive = Q.nonpositive
Finite = Q.finite
Infinite = Q.infinite
Zero = Q.zero
Bounded = Q.finite  # Alias


def GetAssumptions(symbol: Symbol) -> Dict[str, bool]:
    """
    Get all assumptions for a symbol.

    Args:
        symbol: A SymPy symbol

    Returns:
        Dictionary of assumption name -> value

    Examples:
        >>> x = Symbol('x', positive=True, real=True)
        >>> GetAssumptions(x)
        {'positive': True, 'real': True, ...}
    """
    assumptions = {}
    for key in symbol.assumptions0:
        val = getattr(symbol, f'is_{key}', None)
        if val is not None:
            assumptions[key] = val
    return assumptions


# Compatibility alias
get_assumptions = GetAssumptions


def AssumePositive(*names: str) -> List[Symbol]:
    """
    Create multiple positive symbols at once.

    Args:
        *names: Symbol names

    Returns:
        List of positive symbols

    Examples:
        >>> a, b, c = AssumePositive('a', 'b', 'c')
    """
    return [Symbol(name, positive=True) for name in names]


# Compatibility alias
assume_positive = AssumePositive


def AssumeReal(*names: str) -> List[Symbol]:
    """
    Create multiple real symbols at once.

    Args:
        *names: Symbol names

    Returns:
        List of real symbols
    """
    return [Symbol(name, real=True) for name in names]


# Compatibility alias
assume_real = AssumeReal


def AssumeInteger(*names: str) -> List[Symbol]:
    """
    Create multiple integer symbols at once.

    Args:
        *names: Symbol names

    Returns:
        List of integer symbols
    """
    return [Symbol(name, integer=True) for name in names]


# Compatibility alias
assume_integer = AssumeInteger


__all__ = [
    # Context manager
    'Assuming',
    # Functions
    'Refine',
    'Ask',
    'SimplifyWithAssumptions',
    # CamelCase (preferred)
    'GetAssumptions',
    'AssumePositive',
    'AssumeReal',
    'AssumeInteger',
    # lowercase (compatibility)
    'get_assumptions',
    'assume_positive',
    'assume_real',
    'assume_integer',
    # Symbol factory
    'AssumedSymbol',
    # Predicates (Q shortcuts)
    'Positive',
    'Negative',
    'Real',
    'Integer',
    'Rational',
    'Complex',
    'Even',
    'Odd',
    'Prime',
    'Nonzero',
    'Nonnegative',
    'Nonpositive',
    'Finite',
    'Infinite',
    'Zero',
    'Bounded',
]
