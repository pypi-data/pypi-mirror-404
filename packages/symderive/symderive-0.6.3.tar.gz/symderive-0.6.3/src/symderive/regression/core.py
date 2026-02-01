"""
core.py - Symbolic Regression via PySR

Provides FindFormula for discovering symbolic expressions that fit data.

Args:
    data: Input data as list of [x, y] pairs, or (X, y) tuple of arrays.
    x: Symbol for the independent variable.
    n: Number of candidate formulas to return.

Returns:
    A SymPy expression (if n=1), list of expressions (if n>1).

Internal Refs:
    Uses derive.core.math_api for NumPy/SymPy operations.
    Uses derive.core.math_api.GetPySRRegressor for PySR symbolic regression.
"""

from typing import Any, Dict, List, Optional, Union, Literal

from symderive.core.math_api import (
    np,
    sp,
    np_asarray,
    np_arange,
    Symbol,
    nan,
    GetPySRRegressor,
    IsPySRAvailable,
)


# Map symbolic function names to PySR operators
_TARGET_FUNCTION_MAP = {
    'Plus': '+',
    'Times': '*',
    'Subtract': '-',
    'Divide': '/',
    'Power': '^',
    'Sin': 'sin',
    'Cos': 'cos',
    'Tan': 'tan',
    'Exp': 'exp',
    'Log': 'log',
    'Sqrt': 'sqrt',
    'Abs': 'abs',
    'Sinh': 'sinh',
    'Cosh': 'cosh',
    'Tanh': 'tanh',
    'ArcSin': 'asin',
    'ArcCos': 'acos',
    'ArcTan': 'atan',
}

# Default binary and unary operators
_DEFAULT_BINARY_OPS = ['+', '-', '*', '/']
_DEFAULT_UNARY_OPS = ['sin', 'cos', 'exp', 'log', 'sqrt', 'abs']


def _convert_target_functions(
    target_functions: Optional[List[str]]
) -> tuple[List[str], List[str]]:
    """Convert symbolic TargetFunctions to PySR operators."""
    if target_functions is None:
        return _DEFAULT_BINARY_OPS.copy(), _DEFAULT_UNARY_OPS.copy()

    binary_ops = []
    unary_ops = []

    for func in target_functions:
        mapped = _TARGET_FUNCTION_MAP.get(func, func.lower())
        if mapped in ['+', '-', '*', '/', '^']:
            binary_ops.append(mapped)
        else:
            unary_ops.append(mapped)

    # Ensure we have basic arithmetic if any binary ops specified
    if not binary_ops:
        binary_ops = ['+', '*']

    return binary_ops, unary_ops


def _data_to_arrays(
    data: Any,
    target_variable: Optional[Symbol] = None
) -> tuple[Any, Any, List[Symbol]]:
    """
    Convert input data to numpy arrays.

    Supports:
    - List of [x, y] pairs for 1D regression
    - List of [x1, x2, ..., y] for multivariate
    - Tuple of (X, y) arrays
    - numpy arrays directly
    """
    if isinstance(data, tuple) and len(data) == 2:
        X, y = data
        X = np_asarray(X)
        y = np_asarray(y)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        n_features = X.shape[1]
        if target_variable is not None:
            feature_names = [target_variable]
        else:
            feature_names = [Symbol(f'x{i}') for i in range(n_features)]
        return X, y, feature_names

    data = np_asarray(data)
    if data.ndim == 1:
        # Assume it's just y values, create x as indices
        y = data
        X = np_arange(len(y)).reshape(-1, 1)
        feature_names = [target_variable if target_variable else Symbol('x')]
        return X, y, feature_names

    # data is 2D: rows are observations, last column is y
    X = data[:, :-1]
    y = data[:, -1]

    if X.shape[1] == 1 and target_variable is not None:
        feature_names = [target_variable]
    else:
        feature_names = [Symbol(f'x{i}') for i in range(X.shape[1])]

    return X, y, feature_names


def _pysr_to_sympy(
    model: Any,
    feature_names: List[Symbol],
    n: int = 1
) -> Union[Any, List[Any]]:
    """
    Convert PySR model results to SymPy expressions.

    Internal Refs:
        Uses derive.core.math_api.Symbol for expression substitution.
    """
    equations = model.equations_

    if equations is None or len(equations) == 0:
        return nan if n == 1 else [nan]

    # Sort by score (higher is better) to get best equations
    sorted_eqs = equations.sort_values('score', ascending=False)

    results = []
    for i, (_, row) in enumerate(sorted_eqs.iterrows()):
        if i >= n:
            break
        sympy_expr = row['sympy_format']
        # Replace feature variable names with our symbols
        for j, sym_var in enumerate(feature_names):
            var_name = f'x{j}'
            if var_name in str(sympy_expr):
                sympy_expr = sympy_expr.subs(Symbol(var_name), sym_var)
        results.append(sympy_expr)

    if n == 1:
        return results[0] if results else nan
    return results


def FindFormula(
    data: Any,
    x: Optional[Symbol] = None,
    n: int = 1,
    prop: Optional[Union[str, List[str]]] = None,
    *,
    target_functions: Optional[List[str]] = None,
    specificity_goal: float = 0.8,
    time_constraint: Optional[float] = None,
    performance_goal: Literal['Speed', 'Quality'] = 'Speed',
    random_seeding: int = 1234,
    max_complexity: int = 20,
    niterations: int = 40,
    populations: int = 15,
    **kwargs
) -> Union[Any, List[Any], Dict[str, Any]]:
    """
    Find a symbolic formula that approximates data.

    FindFormula[data] finds a pure function that approximates data.
    FindFormula[data, x] finds a symbolic function of x that approximates data.
    FindFormula[data, x, n] finds up to n functions that approximate data.
    FindFormula[data, x, n, prop] returns functions with property prop.

    Args:
        data: Input data as list of [x, y] pairs, or (X, y) tuple of arrays.
        x: Symbol for the independent variable. If None, uses Symbol('x').
        n: Number of candidate formulas to return.
        prop: Property to return - 'Score', 'Error', 'Complexity', or 'All'.
            If a list, returns dict with those properties.

        Keyword options:
        target_functions: List of allowed functions (e.g., ['Sin', 'Cos', 'Plus']).
            Maps symbolic names to PySR operators.
        specificity_goal: Controls model complexity (0 to 1). Higher = more complex.
            Maps to PySR's parsimony coefficient.
        time_constraint: Maximum time in seconds for regression.
        performance_goal: 'Speed' for fast results, 'Quality' for better fit.
        random_seeding: Random seed for reproducibility.
        max_complexity: Maximum complexity of expressions.

        Additional PySR kwargs can be passed directly.

    Returns:
        A SymPy expression (if n=1), list of expressions (if n>1),
        or dict with requested properties.

    Examples:
        >>> data = [[x, 2*x + 1] for x in range(10)]
        >>> FindFormula(data, Symbol('x'))
        2*x + 1

        >>> data = [(x, np.sin(x)) for x in np.linspace(0, 2*np.pi, 100)]
        >>> FindFormula(data, Symbol('x'), target_functions=['Sin', 'Plus', 'Times'])
        sin(x)
    """
    if x is None:
        x = Symbol('x')

    # Convert data to arrays
    X, y, feature_names = _data_to_arrays(data, x)

    # Convert target functions to PySR operators
    binary_ops, unary_ops = _convert_target_functions(target_functions)

    # Map performance goal to PySR settings
    if performance_goal == 'Quality':
        niterations = max(niterations, 100)
        populations = max(populations, 30)

    # Map specificity_goal to parsimony (inverse relationship)
    # Higher specificity = more complex = lower parsimony penalty
    parsimony = 0.0032 * (1 - specificity_goal) + 0.001

    # Build PySR configuration
    model_kwargs = {
        'niterations': niterations,
        'populations': populations,
        'binary_operators': binary_ops,
        'unary_operators': unary_ops if unary_ops else None,
        'maxsize': max_complexity,
        'parsimony': parsimony,
        'random_state': random_seeding,
        'deterministic': True,
        'parallelism': 'serial',  # Required for determinism
        'progress': False,
        'verbosity': 0,
    }

    if time_constraint is not None:
        model_kwargs['timeout_in_seconds'] = time_constraint

    # Allow user overrides
    model_kwargs.update(kwargs)

    # Get PySR regressor from math_api (handles import error if not installed)
    _PySRRegressor = GetPySRRegressor()

    # Create and fit model
    model = _PySRRegressor(**model_kwargs)
    model.fit(X, y)

    # Get sympy expressions
    expressions = _pysr_to_sympy(model, feature_names, n)

    # Handle property requests
    if prop is None:
        return expressions

    # Build property dict
    equations = model.equations_
    if equations is None or len(equations) == 0:
        empty_result = {'Score': [], 'Error': [], 'Complexity': [], 'Expression': []}
        if isinstance(prop, list):
            return {p: empty_result.get(p, []) for p in prop}
        return empty_result.get(prop, [])

    sorted_eqs = equations.sort_values('score', ascending=False).head(n)

    result = {
        'Score': sorted_eqs['score'].tolist(),
        'Error': sorted_eqs['loss'].tolist(),
        'Complexity': sorted_eqs['complexity'].tolist(),
        'Expression': expressions if isinstance(expressions, list) else [expressions],
    }

    if prop == 'All':
        return result
    if isinstance(prop, list):
        return {p: result.get(p, []) for p in prop}
    return result.get(prop, expressions)


__all__ = ['FindFormula']
