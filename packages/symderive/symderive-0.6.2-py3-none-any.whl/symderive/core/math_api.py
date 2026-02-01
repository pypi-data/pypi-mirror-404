"""
math_api.py - Centralized Math Library Adapter

This module serves as the single gateway for external math libraries (SymPy, NumPy, SciPy).
All other modules should import from here instead of directly importing these libraries.

The adapter provides:
- Consistent API across the codebase
- Easy library swapping if needed
- Clear documentation of external dependencies

Usage:
    from symderive.core.math_api import sp, np, sym, array, linspace, ...

Internal Refs:
    - SymPy: Symbolic mathematics
    - NumPy: Numerical arrays and vectorized operations
    - SciPy: Scientific computing (integration, optimization, statistics)
"""

# =============================================================================
# SymPy - Symbolic Mathematics
# =============================================================================
import sympy as sp

# Core symbolic types
from sympy import (
    Symbol,
    symbols,
    Function,
    Expr,
    Basic,
    Rational,
    Integer,
    Float,
)

# Symbolic operations
from sympy import (
    simplify as sym_simplify,
    expand as sym_expand,
    factor as sym_factor,
    collect as sym_collect,
    cancel as sym_cancel,
    apart as sym_apart,
    together as sym_together,
    trigsimp as sym_trigsimp,
    powsimp as sym_powsimp,
    logcombine as sym_logcombine,
    expand_trig as sym_expand_trig,
    nsimplify as sym_nsimplify,
)

# Calculus
from sympy import (
    diff as sym_diff,
    integrate as sym_integrate,
    limit as sym_limit,
    series as sym_series,
    summation as sym_summation,
    product as sym_product,
    Derivative,
    Integral,
)

# Solving
from sympy import (
    solve as sym_solve,
    dsolve as sym_dsolve,
    lambdify as sym_lambdify,
)
from sympy.solvers import solve as solvers_solve

# Linear algebra
from sympy import (
    Matrix,
    eye as sym_eye,
    zeros as sym_zeros,
    diag as sym_diag,
    tensorproduct,
    tensorcontraction,
    derive_by_array,
)

# Arrays
from sympy import (
    Array,
    ImmutableDenseNDimArray,
    MutableDenseNDimArray,
    permutedims,
)

# Functions
from sympy import (
    sin, cos, tan, cot, sec, csc,
    sinh, cosh, tanh, coth, sech, csch,
    asin, acos, atan, atan2, acot, asec, acsc,
    asinh, acosh, atanh, acoth, asech, acsch,
    exp, log, ln, sqrt,
    Abs, sign, floor, ceiling,
    re, im, conjugate, arg,
    Heaviside, DiracDelta,
    gamma, factorial, binomial, beta,
    legendre, assoc_legendre, hermite, chebyshevt, chebyshevu, laguerre, assoc_laguerre,
    gegenbauer, jacobi, Ynm, li,
    besselj, bessely, besseli, besselk, hankel1, hankel2,
    jn, yn,
    erf, erfc, erfi, erf2,
    Ei, expint, Si, Ci, Shi, Chi,
    fresnels, fresnelc,
    airyai, airybi, airyaiprime, airybiprime,
    elliptic_k, elliptic_f, elliptic_e, elliptic_pi,
    zeta, polylog, lerchphi, dirichlet_eta,
    hyper, meijerg,
)

# Constants
from sympy import (
    pi, E as sym_E, I as sym_I,
    oo, zoo, nan,
)

# Pattern matching
from sympy import Wild
from sympy.core.basic import Basic as sym_Basic
from sympy.core.function import UndefinedFunction

# Tensor support
from sympy.tensor.tensor import (
    TensorIndexType,
    TensorIndex,
    TensorHead,
    tensor_indices,
    TensorSymmetry,
    TensExpr,
)

# Printing
from sympy import latex, pretty, sympify
from sympy.printing.pretty.pretty import PrettyPrinter
from sympy.printing.str import StrPrinter

# Parsing
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

# Logic and assumptions
from sympy import (
    Q, ask, refine, Piecewise, And, Or, Not, Implies, Xor, Nand, Nor, Equivalent,
)
from sympy.assumptions.assume import global_assumptions, Predicate

# Comparison operators
from sympy import Eq, Ne, Lt, Le, Gt, Ge, Max, Min

# Number theory
from sympy import (
    gcd, lcm, isprime, prime, factorint, primefactors, totient, divisors,
    npartitions,
)

# Integral transforms
from sympy import (
    fourier_transform, inverse_fourier_transform,
    laplace_transform, inverse_laplace_transform,
)

# Finite differences
from sympy import finite_diff_weights

# =============================================================================
# NumPy - Numerical Arrays
# =============================================================================
import numpy as np

# Array creation
from numpy import (
    array as np_array,
    zeros as np_zeros,
    ones as np_ones,
    empty as np_empty,
    arange as np_arange,
    linspace as np_linspace,
    logspace as np_logspace,
    meshgrid as np_meshgrid,
    eye as np_eye,
    diag as np_diag,
    atleast_1d as np_atleast_1d,
    asarray as np_asarray,
)

# Array operations
from numpy import (
    dot as np_dot,
    matmul as np_matmul,
    transpose as np_transpose,
    reshape as np_reshape,
    concatenate as np_concatenate,
    stack as np_stack,
    vstack as np_vstack,
    hstack as np_hstack,
)

# Mathematical functions
from numpy import (
    sin as np_sin,
    cos as np_cos,
    tan as np_tan,
    exp as np_exp,
    log as np_log,
    sqrt as np_sqrt,
    abs as np_abs,
    power as np_power,
)

# Statistics
from numpy import (
    mean as np_mean,
    std as np_std,
    var as np_var,
    sum as np_sum,
    prod as np_prod,
    min as np_min,
    max as np_max,
)

# Constants
from numpy import (
    inf as np_inf,
    nan as np_nan,
    pi as np_pi,
    e as np_e,
)

# Type checking
from numpy import number as np_number

# =============================================================================
# SciPy - Scientific Computing
# =============================================================================
from scipy import integrate as scipy_integrate
from scipy import optimize as scipy_optimize
from scipy import stats as scipy_stats

# Specific functions
from scipy.integrate import solve_ivp, quad as scipy_quad
from scipy.optimize import fsolve as scipy_fsolve, minimize as scipy_minimize

# =============================================================================
# mpmath - Arbitrary Precision Arithmetic (Optional)
# =============================================================================
# NOTE: Deferred import - mpmath is an optional dependency
try:
    import mpmath as mpmath_module
    from mpmath import mpf as mpmath_mpf, mpi as mpmath_mpi, mp as mpmath_mp
    MPMATH_AVAILABLE = True
except ImportError:
    mpmath_module = None
    mpmath_mpf = None
    mpmath_mpi = None
    mpmath_mp = None
    MPMATH_AVAILABLE = False


def GetMpmath():
    """
    Get the mpmath module.

    Returns:
        mpmath module

    Raises:
        ImportError: If mpmath is not installed

    Internal Refs:
        Uses mpmath for arbitrary precision arithmetic.
    """
    if not MPMATH_AVAILABLE:
        raise ImportError(
            "mpmath is required for arbitrary precision arithmetic. "
            "Install with: pip install mpmath"
        )
    return mpmath_module


def IsMpmathAvailable():
    """
    Check if mpmath is available.

    Returns:
        True if mpmath is installed, False otherwise

    Internal Refs:
        Uses MPMATH_AVAILABLE constant.
    """
    return MPMATH_AVAILABLE


# =============================================================================
# PySR - Symbolic Regression (Optional)
# =============================================================================
# NOTE: Deferred import - pysr is an optional dependency that requires Julia
try:
    from pysr import PySRRegressor
    PYSR_AVAILABLE = True
except ImportError:
    PySRRegressor = None
    PYSR_AVAILABLE = False


def GetPySRRegressor():
    """
    Get the PySRRegressor class.

    Returns:
        PySRRegressor class

    Raises:
        ImportError: If pysr is not installed

    Internal Refs:
        Uses pysr for symbolic regression.
    """
    if not PYSR_AVAILABLE:
        raise ImportError(
            "PySR is required for FindFormula. Install with: uv sync --extra regression\n"
            "Note: PySR requires Julia to be installed."
        )
    return PySRRegressor


def IsPySRAvailable():
    """
    Check if PySR is available.

    Returns:
        True if pysr is installed, False otherwise

    Internal Refs:
        Uses PYSR_AVAILABLE constant.
    """
    return PYSR_AVAILABLE


# =============================================================================
# Convenience Aliases
# =============================================================================

# SymPy module reference
sym = sp

# Common operations with shorter names
simplify = sym_simplify
expand = sym_expand
factor = sym_factor
diff = sym_diff
integrate = sym_integrate
limit = sym_limit
solve = sym_solve
dsolve = sym_dsolve
lambdify = sym_lambdify

# Array creation shortcuts
array = np_array
zeros = np_zeros
ones = np_ones
linspace = np_linspace
arange = np_arange
meshgrid = np_meshgrid

# Statistics shortcuts
mean = np_mean
std = np_std
var = np_var


# =============================================================================
# Vectorized Operations
# =============================================================================

def vectorize_symbolic(expr, var, values):
    """
    Evaluate a symbolic expression over an array of values.

    Args:
        expr: SymPy expression to evaluate
        var: Symbol variable in expression
        values: Array of values to substitute

    Returns:
        NumPy array of evaluated results

    Examples:
        >>> x = Symbol('x')
        >>> vectorize_symbolic(x**2, x, [1, 2, 3, 4])
        array([1, 4, 9, 16])
    """
    f = sym_lambdify(var, expr, modules=['numpy'])
    return f(np_asarray(values))


def symbolic_to_numeric(expr, variables, modules='numpy'):
    """
    Convert a symbolic expression to a numerical function.

    Args:
        expr: SymPy expression
        variables: Variable(s) the expression depends on
        modules: Modules to use for numerical evaluation (default: 'numpy')

    Returns:
        Callable numerical function

    Examples:
        >>> x = Symbol('x')
        >>> f = symbolic_to_numeric(sin(x), x)
        >>> f(np_pi / 2)
        1.0
    """
    return sym_lambdify(variables, expr, modules=[modules, 'scipy'])


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    # Module references
    'sp', 'np', 'sym',
    'scipy_integrate', 'scipy_optimize', 'scipy_stats',

    # SymPy core types
    'Symbol', 'symbols', 'Function', 'Expr', 'Basic', 'Rational', 'Integer', 'Float',
    'Wild', 'sym_Basic', 'UndefinedFunction',

    # SymPy operations
    'simplify', 'expand', 'factor', 'sym_collect', 'sym_cancel', 'sym_apart',
    'sym_together', 'sym_trigsimp', 'sym_powsimp', 'sym_logcombine',
    'sym_expand_trig', 'sym_nsimplify',
    'sym_simplify', 'sym_expand', 'sym_factor',

    # Calculus
    'diff', 'integrate', 'limit', 'sym_series', 'sym_summation', 'sym_product',
    'sym_diff', 'sym_integrate', 'sym_limit',
    'Derivative', 'Integral',

    # Solving
    'solve', 'dsolve', 'lambdify', 'solvers_solve',
    'sym_solve', 'sym_dsolve', 'sym_lambdify',

    # Linear algebra
    'Matrix', 'sym_eye', 'sym_zeros', 'sym_diag',
    'tensorproduct', 'tensorcontraction', 'derive_by_array',
    'Array', 'ImmutableDenseNDimArray', 'MutableDenseNDimArray', 'permutedims',

    # Functions
    'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
    'sinh', 'cosh', 'tanh', 'coth', 'sech', 'csch',
    'asin', 'acos', 'atan', 'atan2', 'acot', 'asec', 'acsc',
    'asinh', 'acosh', 'atanh', 'acoth', 'asech', 'acsch',
    'exp', 'log', 'ln', 'sqrt', 'Abs', 'sign', 'floor', 'ceiling',
    're', 'im', 'conjugate', 'arg',
    'Heaviside', 'DiracDelta',
    'gamma', 'factorial', 'binomial',
    'legendre', 'assoc_legendre', 'hermite', 'chebyshevt', 'chebyshevu',
    'laguerre', 'assoc_laguerre',
    'besselj', 'bessely', 'besseli', 'besselk', 'hankel1', 'hankel2', 'jn', 'yn',
    'gegenbauer', 'jacobi', 'Ynm', 'beta', 'li',
    'erf', 'erfc', 'erfi', 'erf2', 'Ei', 'expint', 'Si', 'Ci', 'Shi', 'Chi',
    'fresnels', 'fresnelc',
    'airyai', 'airybi', 'airyaiprime', 'airybiprime',
    'elliptic_k', 'elliptic_f', 'elliptic_e', 'elliptic_pi',
    'zeta', 'polylog', 'lerchphi', 'dirichlet_eta',
    'hyper', 'meijerg',

    # Constants
    'pi', 'sym_E', 'sym_I', 'oo', 'zoo', 'nan',

    # Tensor support
    'TensorIndexType', 'TensorIndex', 'TensorHead', 'tensor_indices',
    'TensorSymmetry', 'TensExpr',

    # Printing
    'latex', 'pretty', 'sympify', 'PrettyPrinter', 'StrPrinter',

    # Parsing
    'parse_expr', 'standard_transformations', 'implicit_multiplication_application', 'convert_xor',

    # Logic
    'Q', 'ask', 'refine', 'Piecewise', 'And', 'Or', 'Not', 'Implies', 'Xor', 'Nand', 'Nor', 'Equivalent',
    'global_assumptions', 'Predicate',

    # Comparison operators
    'Eq', 'Ne', 'Lt', 'Le', 'Gt', 'Ge', 'Max', 'Min',

    # Number theory
    'gcd', 'lcm', 'isprime', 'prime', 'factorint', 'primefactors', 'totient', 'divisors', 'npartitions',

    # Integral transforms
    'fourier_transform', 'inverse_fourier_transform',
    'laplace_transform', 'inverse_laplace_transform',

    # Finite differences
    'finite_diff_weights',

    # NumPy array creation
    'array', 'zeros', 'ones', 'linspace', 'arange', 'meshgrid',
    'np_array', 'np_zeros', 'np_ones', 'np_empty', 'np_arange',
    'np_linspace', 'np_logspace', 'np_meshgrid', 'np_eye', 'np_diag',
    'np_atleast_1d', 'np_asarray',

    # NumPy operations
    'np_dot', 'np_matmul', 'np_transpose', 'np_reshape',
    'np_concatenate', 'np_stack', 'np_vstack', 'np_hstack',

    # NumPy math
    'np_sin', 'np_cos', 'np_tan', 'np_exp', 'np_log', 'np_sqrt', 'np_abs', 'np_power',

    # NumPy statistics
    'mean', 'std', 'var', 'np_mean', 'np_std', 'np_var',
    'np_sum', 'np_prod', 'np_min', 'np_max',

    # NumPy constants
    'np_inf', 'np_nan', 'np_pi', 'np_e',

    # NumPy types
    'np_number',

    # SciPy
    'solve_ivp', 'scipy_quad', 'scipy_fsolve', 'scipy_minimize',

    # mpmath (optional)
    'mpmath_module', 'mpmath_mpf', 'mpmath_mpi', 'mpmath_mp',
    'MPMATH_AVAILABLE', 'GetMpmath', 'IsMpmathAvailable',

    # PySR (optional)
    'PySRRegressor', 'PYSR_AVAILABLE', 'GetPySRRegressor', 'IsPySRAvailable',

    # Utilities
    'vectorize_symbolic', 'symbolic_to_numeric',
]
