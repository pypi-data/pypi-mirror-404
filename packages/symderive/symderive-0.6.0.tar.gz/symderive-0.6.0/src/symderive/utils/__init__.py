"""
Utils module - Display, Logic, String operations, and Performance utilities.

Provides utility functions for output, control flow, lazy evaluation,
caching, and composable operations.
"""

from symderive.utils.display import (
    TeXForm, PrettyForm, Print, RichPrint, RichLatex, TableForm, Show, show,
)
from symderive.utils.logic import (
    Equal, Unequal, Less, LessEqual, Greater, GreaterEqual,
    And, Or, Not, Xor, Nand, Nor,
    If, Which, Switch, Piecewise, Max, Min,
)
from symderive.utils.strings import (
    StringJoin, StringLength, StringTake, StringDrop,
    StringReplace, ToString,
)
from symderive.utils.lazy import Lazy, LazyExpr, lazy, Force, force
from symderive.utils.cache import (
    ExpressionCache,
    Memoize, MemoizeMethod, CachedSimplify,
    GetChristoffelCache, GetRiemannCache, ClearAllCaches,
    memoize, memoize_method, cached_simplify,
    get_christoffel_cache, get_riemann_cache, clear_all_caches,
)
from symderive.utils.compose import (
    Pipe, pipe, Compose, ThreadFirst, ThreadLast,
    compose, thread_first, thread_last, Chainable,
    Nest, NestList, FixedPoint, FixedPointList,
)
from symderive.utils.assumptions import (
    Assuming, Refine, Ask, SimplifyWithAssumptions,
    GetAssumptions, AssumePositive, AssumeReal, AssumeInteger,
    get_assumptions, assume_positive, assume_real, assume_integer,
    AssumedSymbol,
    Positive, Negative, Real, Integer as IntegerPred, Rational as RationalPred,
    Complex as ComplexPred, Even, Odd, Prime as PrimePred,
    Nonzero, Nonnegative, Nonpositive, Finite, Infinite, Zero, Bounded,
)
from symderive.utils.validation import (
    ValidationError, validate_tuple, validate_range_tuple, validate_var_tuple,
    validate_positive_int, validate_nonnegative_int, is_tuple_like,
)
from symderive.utils.functional import (
    matrix_method, binary_matrix_method, symbolic_to_callable,
    apply_to_ranges, curry, flip, identity, const,
    foldl, foldr, scanl, take_while, drop_while, group_by,
)

__all__ = [
    # Display
    'TeXForm', 'PrettyForm', 'Print', 'RichPrint', 'RichLatex', 'TableForm', 'Show', 'show',
    # Logic
    'Equal', 'Unequal', 'Less', 'LessEqual', 'Greater', 'GreaterEqual',
    'And', 'Or', 'Not', 'Xor', 'Nand', 'Nor',
    'If', 'Which', 'Switch', 'Piecewise', 'Max', 'Min',
    # Strings
    'StringJoin', 'StringLength', 'StringTake', 'StringDrop',
    'StringReplace', 'ToString',
    # Lazy evaluation
    'Lazy', 'LazyExpr', 'lazy', 'Force', 'force',
    # Caching
    'ExpressionCache',
    'Memoize', 'MemoizeMethod', 'CachedSimplify',
    'GetChristoffelCache', 'GetRiemannCache', 'ClearAllCaches',
    'memoize', 'memoize_method', 'cached_simplify',
    'get_christoffel_cache', 'get_riemann_cache', 'clear_all_caches',
    # Composable API
    'Pipe', 'pipe', 'Compose', 'ThreadFirst', 'ThreadLast',
    'compose', 'thread_first', 'thread_last', 'Chainable',
    'Nest', 'NestList', 'FixedPoint', 'FixedPointList',
    # Assumptions
    'Assuming', 'Refine', 'Ask', 'SimplifyWithAssumptions',
    'GetAssumptions', 'AssumePositive', 'AssumeReal', 'AssumeInteger',
    'get_assumptions', 'assume_positive', 'assume_real', 'assume_integer',
    'AssumedSymbol',
    'Positive', 'Negative', 'Real', 'IntegerPred', 'RationalPred',
    'ComplexPred', 'Even', 'Odd', 'PrimePred',
    'Nonzero', 'Nonnegative', 'Nonpositive', 'Finite', 'Infinite', 'Zero', 'Bounded',
    # Validation
    'ValidationError', 'validate_tuple', 'validate_range_tuple', 'validate_var_tuple',
    'validate_positive_int', 'validate_nonnegative_int', 'is_tuple_like',
    # Functional utilities
    'matrix_method', 'binary_matrix_method', 'symbolic_to_callable',
    'apply_to_ranges', 'curry', 'flip', 'identity', 'const',
    'foldl', 'foldr', 'scanl', 'take_while', 'drop_while', 'group_by',
]
