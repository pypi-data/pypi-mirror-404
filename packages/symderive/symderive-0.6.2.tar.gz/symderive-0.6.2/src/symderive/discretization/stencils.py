"""
discretization.py - Convert Symbolic Derivatives to Finite Difference Stencils.

Provides tools for converting variational derivatives and other symbolic
expressions into finite difference approximations, with code generation
for multiple programming languages.

Args:
    expr: Symbolic expression containing derivatives.
    step_map: Dictionary mapping variables to (grid_points, step_size).

Returns:
    Discretized expression or generated code string.

Internal Refs:
    Uses derive.core.math_api for SymPy operations.
    Uses derive.calculus.differentiation.D for derivative detection.
"""

from typing import Dict, List, Optional, Tuple, Union

from symderive.core.math_api import (
    Symbol, symbols, Function, Expr, Derivative, Rational,
    latex, sympify, sp, finite_diff_weights,
)


class Discretizer:
    """
    Converts symbolic derivatives to finite difference approximations.

    Uses SymPy's as_finite_difference method to generate stencil weights
    automatically based on Taylor series matching.

    Args:
        step_map: Dictionary mapping variables to (grid_points, step_size).
                  Example: {x: ([x-h, x, x+h], h)} for central difference.

    Internal Refs:
        Uses derive.core.math_api.Derivative for derivative detection.
    """

    def __init__(self, step_map: Dict[Symbol, Tuple[List[Expr], Symbol]]):
        """
        Initialize the discretizer with a step map.

        Args:
            step_map: Maps variables to (grid_points, step_size) tuples.
        """
        self.step_map = step_map

    def __call__(self, expr: Expr) -> Expr:
        """
        Apply discretization to an expression.

        Args:
            expr: Symbolic expression to discretize.

        Returns:
            Expression with derivatives replaced by finite differences.
        """
        return self._recurse(expr)

    def _recurse(self, expr: Expr) -> Expr:
        """
        Recursively traverse and discretize the expression tree.

        Args:
            expr: Expression node to process.

        Returns:
            Discretized expression.
        """
        if isinstance(expr, Derivative):
            return self._discretize_derivative(expr)

        if hasattr(expr, 'args') and expr.args:
            new_args = [self._recurse(arg) for arg in expr.args]
            return expr.func(*new_args)

        return expr

    def _discretize_derivative(self, deriv: Derivative) -> Expr:
        """
        Convert a derivative (including mixed partials) to finite difference.

        For mixed partial derivatives like d^2f/dxdy, this decomposes them into
        nested single-variable derivatives and processes each one sequentially.

        Args:
            deriv: SymPy Derivative object.

        Returns:
            Finite difference approximation or original if variable not in step_map.
        """
        if not deriv.variables:
            return deriv

        # Get unique variables
        unique_vars = []
        for var in deriv.variables:
            if var not in unique_vars:
                unique_vars.append(var)

        # Check if this is a mixed partial (multiple unique variables)
        if len(unique_vars) > 1:
            # Decompose into nested derivatives and process sequentially
            # For Derivative(f, x, y), create Derivative(Derivative(f, x), y)
            inner_expr = deriv.expr
            result = inner_expr

            # Process each variable's derivatives in sequence
            for var in unique_vars:
                if var not in self.step_map:
                    # Keep as symbolic derivative for this variable
                    count = deriv.variables.count(var)
                    result = Derivative(result, *([var] * count))
                else:
                    # Count how many times this variable appears
                    count = deriv.variables.count(var)
                    # Create derivative for just this variable
                    var_deriv = Derivative(result, *([var] * count))
                    # Apply finite difference
                    points, step = self.step_map[var]
                    result = var_deriv.as_finite_difference(points, var)
                    # Recursively process the result
                    result = self._recurse(result)

            return result

        # Single variable derivative - use original logic
        wrt = deriv.variables[0]

        if wrt in self.step_map:
            points, step = self.step_map[wrt]
            return deriv.as_finite_difference(points, wrt)

        return deriv


def Discretize(expr: Expr,
               step_map: Dict[Symbol, Tuple[List[Expr], Symbol]]) -> Expr:
    """
    Convert derivatives in an expression to finite difference approximations.

    This function replaces symbolic derivatives with their finite difference
    equivalents using SymPy's as_finite_difference method, which computes
    optimal stencil weights via Taylor series matching.

    Args:
        expr: Symbolic expression containing derivatives.
        step_map: Dictionary mapping variables to (grid_points, step_size).
                  The grid_points list determines the stencil pattern:
                  - [x-h, x, x+h] for central difference
                  - [x, x+h] for forward difference
                  - [x-h, x] for backward difference
                  - [x-2h, x-h, x, x+h, x+2h] for 5-point stencil

    Returns:
        Expression with derivatives replaced by finite differences.

    Examples:
        >>> x, h = symbols('x h')
        >>> f = Function('f')(x)
        >>> # Central difference for first derivative
        >>> Discretize(D(f, x), {x: ([x-h, x, x+h], h)})
        (f(x + h) - f(x - h))/(2*h)

        >>> # Second derivative with central difference
        >>> Discretize(D(f, x, 2), {x: ([x-h, x, x+h], h)})
        (f(x - h) - 2*f(x) + f(x + h))/h**2

    Internal Refs:
        Uses derive.core.math_api.Derivative for derivative detection.
        Uses SymPy's Derivative.as_finite_difference for stencil computation.
    """
    return Discretizer(step_map)(expr)


def FiniteDiffWeights(deriv_order: int, accuracy: int = 2,
                       point: Expr = 0) -> Tuple[List[int], List[Rational]]:
    """
    Compute finite difference stencil weights using Taylor series expansion.

    Automatically determines the optimal stencil points and weights for
    approximating a derivative of given order to specified accuracy.

    Args:
        deriv_order: Order of derivative (1 for first, 2 for second, etc.)
        accuracy: Order of accuracy (2, 4, 6, ...). Higher = more points.
        point: Point at which to evaluate (0 for centered, use offset for one-sided)

    Returns:
        Tuple of (offsets, weights) where offsets are integer grid offsets
        and weights are the coefficients.

    Examples:
        >>> # Second derivative, 2nd order accuracy (standard 3-point stencil)
        >>> offsets, weights = FiniteDiffWeights(2, accuracy=2)
        >>> offsets
        [-1, 0, 1]
        >>> weights
        [1, -2, 1]

        >>> # First derivative, 4th order accuracy (5-point stencil)
        >>> offsets, weights = FiniteDiffWeights(1, accuracy=4)
        >>> offsets
        [-2, -1, 0, 1, 2]
        >>> weights
        [1/12, -2/3, 0, 2/3, -1/12]

    Internal Refs:
        Uses sympy.finite_diff_weights for Taylor series computation.
    """
    # Number of points needed for given accuracy
    n_points = deriv_order + accuracy - 1 + (deriv_order % 2)
    if n_points % 2 == 0:
        n_points += 1  # Ensure odd for symmetric stencil

    half = n_points // 2
    offsets = list(range(-half, half + 1))

    # Get weights from SymPy's finite_diff_weights
    # Returns nested list: weights[deriv_order][-1] gives final weights for that order
    weights_table = finite_diff_weights(deriv_order, offsets, point)

    # Extract weights for the requested derivative order (last row has full weights)
    raw_weights = weights_table[deriv_order][-1]

    # Convert to Rationals
    weights = [Rational(w) for w in raw_weights]

    return offsets, weights


def Stencil(deriv_order: int, accuracy: int = 2) -> Dict[int, Rational]:
    """
    Generate a finite difference stencil as a dictionary.

    Convenience function that returns stencil as {offset: weight} dict.

    Args:
        deriv_order: Order of derivative
        accuracy: Order of accuracy (default 2)

    Returns:
        Dictionary mapping grid offsets to weights.

    Examples:
        >>> Stencil(2)  # Second derivative, 2nd order
        {-1: 1, 0: -2, 1: 1}

        >>> Stencil(1, accuracy=4)  # First derivative, 4th order
        {-2: 1/12, -1: -2/3, 0: 0, 1: 2/3, 2: -1/12}

    Internal Refs:
        Uses FiniteDiffWeights for computation.
    """
    offsets, weights = FiniteDiffWeights(deriv_order, accuracy)
    return dict(zip(offsets, weights))


def _generate_stencil_points(center: Symbol, step: Symbol,
                             width: int) -> List[Expr]:
    """
    Generate symmetric stencil points around a center.

    Args:
        center: Center point variable.
        step: Step size symbol.
        width: Number of points (must be odd for symmetric stencil).

    Returns:
        List of stencil points.

    Internal Refs:
        Uses derive.core.math_api.Symbol for symbolic arithmetic.
    """
    if width < 2:
        raise ValueError("Stencil width must be at least 2")

    half = (width - 1) // 2
    return [center + i * step for i in range(-half, half + 1)]


def ToStencil(expr: Expr,
              spacing: Dict[Symbol, Symbol],
              width: int = 3,
              language: Optional[str] = None,
              **codegen_kwargs) -> Union[Expr, str]:
    """
    Convenience function to discretize derivatives and optionally generate code.

    This combines Discretize with automatic stencil point generation and
    optional code generation for various programming languages.

    Args:
        expr: Symbolic expression containing derivatives.
        spacing: Dictionary mapping variables to their step sizes.
                 Example: {x: h, t: dt}
        width: Number of stencil points (default 3 for central difference).
        language: If specified, generate code in this language.
                  Options: 'python', 'c', 'fortran', 'latex', None.
        **codegen_kwargs: Additional arguments passed to StencilCodeGen.

    Returns:
        Discretized expression if language is None, otherwise code string.

    Examples:
        >>> x, h = symbols('x h')
        >>> f = Function('f')(x)
        >>> # Get discretized expression
        >>> ToStencil(D(f, x, 2), {x: h})
        (f(x - h) - 2*f(x) + f(x + h))/h**2

        >>> # Generate Python code
        >>> ToStencil(D(f, x, 2), {x: h}, language='python',
        ...           array_name='u', index_var='i', spacing='dx')
        '(u[i - 1] - 2*u[i] + u[i + 1])/dx**2'

    Internal Refs:
        Uses Discretize for finite difference conversion.
        Uses StencilCodeGen for code generation.
    """
    step_map = {}
    for var, step in spacing.items():
        points = _generate_stencil_points(var, step, width)
        step_map[var] = (points, step)

    result = Discretize(expr, step_map)

    if language is not None:
        return StencilCodeGen(result, language=language, **codegen_kwargs)

    return result


def StencilCodeGen(expr: Expr,
                   language: str = 'python',
                   array_name: str = 'u',
                   index_var: str = 'i',
                   spacing_name: str = 'h') -> str:
    """
    Generate code for a finite difference stencil expression.

    Converts a discretized symbolic expression into executable code
    for various programming languages.

    Args:
        expr: Discretized expression (output of Discretize or ToStencil).
        language: Target language ('python', 'c', 'fortran', 'latex').
        array_name: Name of the array variable in generated code.
        index_var: Name of the index variable.
        spacing_name: Name of the grid spacing variable in output code.

    Returns:
        Code string in the specified language.

    Examples:
        >>> x, h = symbols('x h')
        >>> f = Function('f')(x)
        >>> stencil = Discretize(D(f, (x, 2)), {x: ([x-h, x, x+h], h)})
        >>> StencilCodeGen(stencil, language='python',
        ...                array_name='phi', index_var='j', spacing_name='dx')
        '(phi[j - 1] - 2*phi[j] + phi[j + 1])/dx**2'

    Internal Refs:
        Uses derive.core.math_api.latex for LaTeX output.
    """
    if language == 'latex':
        return _codegen_latex(expr)

    return _codegen_array(expr, language, array_name, index_var, spacing_name)


def _codegen_latex(expr: Expr) -> str:
    """
    Generate LaTeX representation of a stencil expression.

    Args:
        expr: Symbolic expression.

    Returns:
        LaTeX string.

    Internal Refs:
        Uses derive.core.math_api.latex for conversion.
    """
    return latex(expr)


def _codegen_array(expr: Expr,
                   language: str,
                   array_name: str,
                   index_var: str,
                   spacing_name: str) -> str:
    """
    Generate array-based code for a stencil expression.

    Args:
        expr: Discretized expression.
        language: Target language.
        array_name: Array variable name.
        index_var: Index variable name.
        spacing_name: Spacing variable name.

    Returns:
        Code string.

    Internal Refs:
        Uses derive.core.math_api for expression manipulation.
    """
    expr_str = str(expr)

    free_syms = expr.free_symbols
    func_atoms = [a for a in expr.atoms(Function) if hasattr(a, 'args')]

    x_sym = None
    h_sym = None
    func_name = None

    for atom in func_atoms:
        if hasattr(atom, 'func') and hasattr(atom, 'args') and atom.args:
            func_name = str(atom.func)
            for arg in atom.args:
                if arg in free_syms:
                    for sym in free_syms:
                        if sym != arg and str(sym) not in func_name:
                            h_candidates = [s for s in free_syms
                                            if str(s) not in str(atom)]
                            if h_candidates:
                                h_sym = h_candidates[0]
                    x_sym = arg
            break

    if x_sym is None:
        for sym in free_syms:
            sym_str = str(sym)
            if sym_str in ['x', 't', 'r']:
                x_sym = sym
                break

    if h_sym is None:
        for sym in free_syms:
            sym_str = str(sym)
            if sym_str in ['h', 'dx', 'dt', 'dr', 'h_x', 'h_t']:
                h_sym = sym
                break

    if func_name is None:
        for atom in func_atoms:
            if hasattr(atom, 'func'):
                func_name = str(atom.func)
                break

    result = expr_str

    if func_name and x_sym and h_sym:
        result = _substitute_array_notation(
            expr, func_name, x_sym, h_sym,
            array_name, index_var, spacing_name, language
        )

    return result


def _substitute_array_notation(expr: Expr,
                               func_name: str,
                               x_sym: Symbol,
                               h_sym: Symbol,
                               array_name: str,
                               index_var: str,
                               spacing_name: str,
                               language: str) -> str:
    """
    Substitute function calls with array indexing notation.

    Args:
        expr: Expression to convert.
        func_name: Original function name.
        x_sym: Position variable.
        h_sym: Step size variable.
        array_name: Target array name.
        index_var: Index variable name.
        spacing_name: Spacing variable name in output.
        language: Target language.

    Returns:
        Code string with array notation.

    Internal Refs:
        Uses derive.core.math_api for expression analysis.
    """
    subs_dict = {}
    func_atoms = [a for a in expr.atoms(Function) if hasattr(a, 'func')]

    for atom in func_atoms:
        if str(atom.func) == func_name and atom.args:
            arg = atom.args[0]

            offset = arg - x_sym
            offset_simplified = offset.simplify() if hasattr(offset, 'simplify') else offset

            if offset_simplified == 0:
                idx_str = index_var
            else:
                coeff = offset_simplified / h_sym
                coeff_simplified = coeff.simplify() if hasattr(coeff, 'simplify') else coeff

                if coeff_simplified.is_Integer:
                    coeff_int = int(coeff_simplified)
                    if coeff_int > 0:
                        idx_str = f"{index_var} + {coeff_int}"
                    elif coeff_int < 0:
                        idx_str = f"{index_var} - {-coeff_int}"
                    else:
                        idx_str = index_var
                else:
                    idx_str = f"{index_var} + {coeff_simplified}"

            if language == 'fortran':
                replacement = f"{array_name}({idx_str})"
            else:
                replacement = f"{array_name}[{idx_str}]"

            placeholder = Symbol(f'__PLACEHOLDER_{id(atom)}__')
            subs_dict[atom] = placeholder
            subs_dict[placeholder] = replacement

    expr_substituted = expr.subs({k: v for k, v in subs_dict.items()
                                  if not isinstance(v, str)})

    result = str(expr_substituted)

    for placeholder, replacement in subs_dict.items():
        if isinstance(replacement, str):
            result = result.replace(str(placeholder), replacement)

    result = result.replace(str(h_sym), spacing_name)

    if '**' in result:
        if language == 'fortran':
            pass
        elif language == 'c':
            pass

    return result


__all__ = [
    'Discretize',
    'Discretizer',
    'ToStencil',
    'StencilCodeGen',
    'FiniteDiffWeights',
    'Stencil',
]
