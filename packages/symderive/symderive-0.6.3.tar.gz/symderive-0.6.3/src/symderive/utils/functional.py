"""
functional.py - Functional Programming Utilities

Provides higher-order functions, decorators, and functional patterns
for cleaner, more composable code.

Args:
    Various depending on function.

Returns:
    Various depending on function.

Internal Refs:
    Uses derive.core.math_api for SymPy operations.
"""

import inspect
from functools import wraps, reduce
from typing import Any, Callable, TypeVar, List, Tuple, Optional, Union

from symderive.core.math_api import sp, Matrix, lambdify

T = TypeVar('T')
R = TypeVar('R')


def matrix_method(method_name: str) -> Callable[[Any], Any]:
    """
    Create a function that applies a Matrix method.

    This is a factory function that generates matrix operation functions,
    reducing boilerplate for operations like det, inv, trace, etc.

    Args:
        method_name: Name of the Matrix method to call

    Returns:
        A function that applies the method to a matrix

    Examples:
        >>> Det = matrix_method('det')
        >>> Inv = matrix_method('inv')
        >>> Tr = matrix_method('trace')
        >>> Det([[1, 2], [3, 4]])
        -2
    """
    def operation(m: Any) -> Any:
        matrix = m if isinstance(m, Matrix) else sp.Matrix(m)
        return getattr(matrix, method_name)()
    operation.__name__ = method_name
    operation.__doc__ = f"Compute {method_name} of a matrix."
    return operation


def binary_matrix_method(method_name: str) -> Callable[[Any, Any], Any]:
    """
    Create a function that applies a binary Matrix method.

    Args:
        method_name: Name of the Matrix method to call

    Returns:
        A function that applies the method to two matrices

    Examples:
        >>> MatMul = binary_matrix_method('__matmul__')
    """
    def operation(m1: Any, m2: Any) -> Any:
        mat1 = m1 if isinstance(m1, Matrix) else sp.Matrix(m1)
        mat2 = m2 if isinstance(m2, Matrix) else sp.Matrix(m2)
        return getattr(mat1, method_name)(mat2)
    operation.__name__ = method_name
    return operation


def symbolic_to_callable(
    expr: Any,
    symbols: Union[Any, List[Any]],
    modules: List[str] = None
) -> Callable:
    """
    Convert a symbolic expression to a callable numerical function.

    This is a thin wrapper around sympy.lambdify with sensible defaults.

    Args:
        expr: Symbolic expression to convert
        symbols: Symbol(s) that become function parameters
        modules: Modules to use for numerical evaluation (default: ['numpy'])

    Returns:
        A callable function

    Examples:
        >>> x = Symbol('x')
        >>> f = symbolic_to_callable(x**2 + 1, x)
        >>> f(2)
        5.0
        >>> f = symbolic_to_callable(x*y, [x, y])
        >>> f(2, 3)
        6.0
    """
    if modules is None:
        modules = ['numpy']
    return lambdify(symbols, expr, modules=modules)


def apply_to_ranges(
    expr: Any,
    operation: Callable,
    *args: Any,
    tuple_length: int = 3,
    error_format: str = "Expected tuple of length {length}"
) -> Any:
    """
    Apply an operation over multiple range specifications.

    This abstracts the common pattern of iterating through variable ranges
    used in integration, summation, products, etc.

    Args:
        expr: Initial expression
        operation: Function to apply (takes expr and range tuple)
        *args: Range tuples like (var, start, end)
        tuple_length: Expected length of each tuple
        error_format: Error message format string

    Returns:
        Result after applying operation for each range

    Examples:
        >>> from sympy import integrate, Symbol
        >>> x, y = Symbol('x'), Symbol('y')
        >>> apply_to_ranges(x*y, lambda e, r: integrate(e, r), (x, 0, 1), (y, 0, 1))
        1/4
    """
    # NOTE: Deferred import to prevent circular dependency
    from symderive.utils.validation import validate_tuple

    result = expr
    for arg in args:
        validated = validate_tuple(arg, tuple_length, "range specification")
        result = operation(result, validated)
    return result


def curry(func: Callable) -> Callable:
    """
    Curry a function, allowing partial application.

    Args:
        func: Function to curry

    Returns:
        Curried version of the function

    Examples:
        >>> @curry
        ... def add(a, b, c):
        ...     return a + b + c
        >>> add(1)(2)(3)
        6
        >>> add(1, 2)(3)
        6
    """
    sig = inspect.signature(func)
    num_params = len([
        p for p in sig.parameters.values()
        if p.default == inspect.Parameter.empty
    ])

    @wraps(func)
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= num_params:
            return func(*args, **kwargs)
        return lambda *more_args, **more_kwargs: curried(
            *args, *more_args, **kwargs, **more_kwargs
        )
    return curried


def flip(func: Callable[[Any, Any], R]) -> Callable[[Any, Any], R]:
    """
    Flip the argument order of a binary function.

    Args:
        func: Binary function to flip

    Returns:
        Function with flipped argument order

    Examples:
        >>> div = lambda a, b: a / b
        >>> flip(div)(2, 10)  # 10 / 2
        5.0
    """
    @wraps(func)
    def flipped(a: Any, b: Any) -> R:
        return func(b, a)
    return flipped


def identity(x: T) -> T:
    """
    Identity function - returns its argument unchanged.

    Args:
        x: Any value

    Returns:
        The same value

    Examples:
        >>> identity(42)
        42
    """
    return x


def const(x: T) -> Callable[[Any], T]:
    """
    Create a constant function that always returns x.

    Args:
        x: Value to return

    Returns:
        Function that ignores its argument and returns x

    Examples:
        >>> always_five = const(5)
        >>> always_five("ignored")
        5
    """
    def constant(_: Any) -> T:
        return x
    return constant


def foldl(func: Callable[[T, Any], T], initial: T, xs: List[Any]) -> T:
    """
    Left fold (reduce) over a list.

    Args:
        func: Binary function (accumulator, element) -> new_accumulator
        initial: Initial accumulator value
        xs: List to fold over

    Returns:
        Final accumulated value

    Examples:
        >>> foldl(lambda acc, x: acc + x, 0, [1, 2, 3, 4])
        10
    """
    return reduce(func, xs, initial)


def foldr(func: Callable[[Any, T], T], initial: T, xs: List[Any]) -> T:
    """
    Right fold over a list.

    Args:
        func: Binary function (element, accumulator) -> new_accumulator
        initial: Initial accumulator value
        xs: List to fold over

    Returns:
        Final accumulated value

    Examples:
        >>> foldr(lambda x, acc: [x] + acc, [], [1, 2, 3])
        [1, 2, 3]
    """
    result = initial
    for x in reversed(xs):
        result = func(x, result)
    return result


def scanl(func: Callable[[T, Any], T], initial: T, xs: List[Any]) -> List[T]:
    """
    Left scan - like foldl but returns all intermediate values.

    Args:
        func: Binary function (accumulator, element) -> new_accumulator
        initial: Initial accumulator value
        xs: List to scan over

    Returns:
        List of all intermediate accumulator values

    Examples:
        >>> scanl(lambda acc, x: acc + x, 0, [1, 2, 3, 4])
        [0, 1, 3, 6, 10]
    """
    result = [initial]
    acc = initial
    for x in xs:
        acc = func(acc, x)
        result.append(acc)
    return result


def take_while(pred: Callable[[T], bool], xs: List[T]) -> List[T]:
    """
    Take elements from the start of a list while predicate is true.

    Args:
        pred: Predicate function
        xs: List to take from

    Returns:
        Prefix of xs where pred holds

    Examples:
        >>> take_while(lambda x: x < 5, [1, 2, 3, 5, 4, 3])
        [1, 2, 3]
    """
    result = []
    for x in xs:
        if pred(x):
            result.append(x)
        else:
            break
    return result


def drop_while(pred: Callable[[T], bool], xs: List[T]) -> List[T]:
    """
    Drop elements from the start of a list while predicate is true.

    Args:
        pred: Predicate function
        xs: List to drop from

    Returns:
        Suffix of xs starting where pred first fails

    Examples:
        >>> drop_while(lambda x: x < 5, [1, 2, 3, 5, 4, 3])
        [5, 4, 3]
    """
    for i, x in enumerate(xs):
        if not pred(x):
            return xs[i:]
    return []


def group_by(key: Callable[[T], Any], xs: List[T]) -> dict:
    """
    Group elements by a key function.

    Args:
        key: Function to extract grouping key
        xs: List to group

    Returns:
        Dict mapping keys to lists of elements

    Examples:
        >>> group_by(lambda x: x % 2, [1, 2, 3, 4, 5])
        {1: [1, 3, 5], 0: [2, 4]}
    """
    result = {}
    for x in xs:
        k = key(x)
        if k not in result:
            result[k] = []
        result[k].append(x)
    return result


__all__ = [
    # Matrix utilities
    'matrix_method',
    'binary_matrix_method',
    # Symbolic/numeric conversion
    'symbolic_to_callable',
    # Range application
    'apply_to_ranges',
    # Function combinators
    'curry',
    'flip',
    'identity',
    'const',
    # Folds and scans
    'foldl',
    'foldr',
    'scanl',
    # List utilities
    'take_while',
    'drop_while',
    'group_by',
]
