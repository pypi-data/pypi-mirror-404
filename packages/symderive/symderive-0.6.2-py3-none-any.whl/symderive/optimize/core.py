"""
optimize.py - Convex Optimization Interface

A thin wrapper around cvxpy for convex optimization problems.
Provides a simple interface while letting cvxpy handle solver backends.

Requires: uv sync --extra optimize

Internal Refs:
    Uses cvxpy for optimization (specialized library, not abstracted).
"""

from typing import Any, List, Optional, Union, Literal

# cvxpy is a specialized optimization library, not abstracted through math_api
# NOTE: Deferred import - cvxpy is an optional dependency
try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False
    cp = None


def _require_cvxpy():
    """Raise ImportError if cvxpy is not available."""
    if not CVXPY_AVAILABLE:
        raise ImportError(
            "cvxpy is required for optimization. "
            "Install with: uv sync --extra optimize"
        )

# Type alias for constraints
Constraint = Any


class OptVar:
    """
    Optimization variable.

    A thin wrapper that creates cvxpy variables with optional bounds and domain.

    Args:
        name: Variable name for display
        shape: Shape of variable (default scalar)
        domain: Domain constraint - 'reals', 'nonneg', 'pos', 'integers', 'boolean'
        bounds: Optional (lower, upper) bounds tuple

    Examples:
        >>> x = OptVar('x')
        >>> y = OptVar('y', domain='nonneg')
        >>> z = OptVar('z', shape=(3,))
        >>> w = OptVar('w', bounds=(0, 10))
    """

    # Registry mapping cvxpy Variable id -> OptVar for bound collection.
    # Uses strong references to ensure OptVars stay alive as long as they're registered.
    # Note: Can't use WeakKeyDictionary because cp.Variable overrides __eq__ to return
    # constraints, breaking dict equality checks.
    _registry: dict = {}

    def __init__(
        self,
        name: str,
        shape: tuple = (),
        domain: Literal['reals', 'nonneg', 'pos', 'integers', 'boolean'] = 'reals',
        bounds: Optional[tuple] = None,
    ):
        _require_cvxpy()
        self.name = name
        self.shape = shape
        self.domain = domain
        self.bounds = bounds
        self._cvx_var = None

    def _get_cvxpy_var(self):
        """Create or return the underlying cvxpy variable."""
        if self._cvx_var is None:
            # Map domain to cvxpy options
            kwargs = {'name': self.name}
            if self.shape:
                kwargs['shape'] = self.shape

            if self.domain == 'nonneg':
                kwargs['nonneg'] = True
            elif self.domain == 'pos':
                kwargs['pos'] = True
            elif self.domain == 'integers':
                kwargs['integer'] = True
            elif self.domain == 'boolean':
                kwargs['boolean'] = True

            self._cvx_var = cp.Variable(**kwargs)
            # Register for bound collection (strong reference keeps OptVar alive)
            OptVar._registry[id(self._cvx_var)] = self

        return self._cvx_var

    def get_bound_constraints(self):
        """
        Return constraint expressions for the bounds.

        Returns:
            List of cvxpy constraints (empty if no bounds specified)
        """
        if self.bounds is None:
            return []

        lower, upper = self.bounds
        cvx_var = self._get_cvxpy_var()
        constraints = []

        if lower is not None:
            constraints.append(cvx_var >= lower)
        if upper is not None:
            constraints.append(cvx_var <= upper)

        return constraints

    @property
    def value(self):
        """Get the optimal value after solving."""
        if self._cvx_var is None:
            return None
        return self._cvx_var.value

    def __repr__(self):
        return f"OptVar('{self.name}', shape={self.shape}, domain='{self.domain}')"

    # Arithmetic operations that return cvxpy expressions
    def __add__(self, other):
        return self._get_cvxpy_var() + _to_cvx(other)

    def __radd__(self, other):
        return _to_cvx(other) + self._get_cvxpy_var()

    def __sub__(self, other):
        return self._get_cvxpy_var() - _to_cvx(other)

    def __rsub__(self, other):
        return _to_cvx(other) - self._get_cvxpy_var()

    def __mul__(self, other):
        return self._get_cvxpy_var() * _to_cvx(other)

    def __rmul__(self, other):
        return _to_cvx(other) * self._get_cvxpy_var()

    def __truediv__(self, other):
        return self._get_cvxpy_var() / _to_cvx(other)

    def __pow__(self, other):

        return cp.power(self._get_cvxpy_var(), other)

    def __neg__(self):
        return -self._get_cvxpy_var()

    def __le__(self, other):
        return self._get_cvxpy_var() <= _to_cvx(other)

    def __ge__(self, other):
        return self._get_cvxpy_var() >= _to_cvx(other)

    def __eq__(self, other):
        return self._get_cvxpy_var() == _to_cvx(other)

    def __matmul__(self, other):
        return self._get_cvxpy_var() @ _to_cvx(other)

    def __rmatmul__(self, other):
        return _to_cvx(other) @ self._get_cvxpy_var()

    def __getitem__(self, key):
        return self._get_cvxpy_var()[key]


def _to_cvx(obj):
    """Convert object to cvxpy-compatible form."""
    if isinstance(obj, OptVar):
        return obj._get_cvxpy_var()
    return obj


def _collect_optvars(obj, collected=None):
    """Recursively collect all OptVar instances from an expression."""
    if collected is None:
        collected = []

    if isinstance(obj, OptVar):
        # Use identity check since OptVar.__eq__ is overridden for constraints
        if not any(v is obj for v in collected):
            collected.append(obj)
    elif CVXPY_AVAILABLE and isinstance(obj, cp.Variable):
        # Look up the OptVar from the registry (keyed by id)
        optvar = OptVar._registry.get(id(obj))
        if optvar is not None and not any(v is optvar for v in collected):
            collected.append(optvar)
    elif hasattr(obj, 'args'):
        # cvxpy expression - traverse arguments
        for arg in obj.args:
            _collect_optvars(arg, collected)

    return collected


class OptimizationProblem:
    """
    Base class for optimization problems.

    Attributes:
        objective: The objective expression
        constraints: List of constraint expressions
        sense: 'minimize' or 'maximize'
        _problem: The underlying cvxpy Problem
        _status: Solution status after solving
    """

    def __init__(
        self,
        objective,
        constraints: Optional[List[Constraint]] = None,
        sense: str = 'minimize'
    ):
        self.objective = objective
        self.constraints = constraints or []
        self.sense = sense
        self._problem = None
        self._status = None
        self._optvars = []  # Holds OptVars to prevent GC during solve

    def solve(
        self,
        solver: Optional[str] = None,
        verbose: bool = False,
        **kwargs
    ) -> float:
        """
        Solve the optimization problem.

        Args:
            solver: Specific solver to use (e.g., 'ECOS', 'SCS', 'OSQP')
            verbose: Print solver output
            **kwargs: Additional solver options

        Returns:
            Optimal objective value

        Examples:
            >>> x = OptVar('x', domain='nonneg')
            >>> prob = Minimize(x**2, [x >= 1])
            >>> prob.solve()
            1.0
        """
        _require_cvxpy()

        # Build objective
        if self.sense == 'minimize':
            obj = cp.Minimize(_to_cvx(self.objective))
        else:
            obj = cp.Maximize(_to_cvx(self.objective))

        # Convert constraints
        cvx_constraints = [_to_cvx(c) for c in self.constraints]

        # Collect all OptVar instances and add their bound constraints
        self._optvars = []
        _collect_optvars(self.objective, self._optvars)
        for c in self.constraints:
            _collect_optvars(c, self._optvars)

        for var in self._optvars:
            cvx_constraints.extend(var.get_bound_constraints())

        # Create and solve problem
        self._problem = cp.Problem(obj, cvx_constraints)

        solve_kwargs = {'verbose': verbose}
        if solver:
            solve_kwargs['solver'] = getattr(cp, solver.upper(), solver)
        solve_kwargs.update(kwargs)

        result = self._problem.solve(**solve_kwargs)
        self._status = self._problem.status

        # Clean up global registry - OptVars are now held by self._optvars
        for var in self._optvars:
            if var._cvx_var is not None:
                OptVar._registry.pop(id(var._cvx_var), None)

        return result

    @property
    def status(self) -> Optional[str]:
        """Get the solution status."""
        return self._status

    @property
    def is_solved(self) -> bool:
        """Check if problem was solved optimally."""
        _require_cvxpy()
        return self._status == cp.OPTIMAL

    @property
    def optimal_value(self) -> Optional[float]:
        """Get the optimal objective value."""
        if self._problem is None:
            return None
        return self._problem.value


def Minimize(
    objective,
    constraints: Optional[List[Constraint]] = None,
) -> OptimizationProblem:
    """
    Create a minimization problem.

    Args:
        objective: Expression to minimize
        constraints: List of constraints

    Returns:
        OptimizationProblem ready to solve

    Examples:
        >>> x = OptVar('x', domain='nonneg')
        >>> y = OptVar('y', domain='nonneg')
        >>> prob = Minimize(x**2 + y**2, [x + y >= 1])
        >>> prob.solve()
        0.5
    """
    return OptimizationProblem(objective, constraints, sense='minimize')


def Maximize(
    objective,
    constraints: Optional[List[Constraint]] = None,
) -> OptimizationProblem:
    """
    Create a maximization problem.

    Args:
        objective: Expression to maximize
        constraints: List of constraints

    Returns:
        OptimizationProblem ready to solve

    Examples:
        >>> x = OptVar('x', bounds=(0, 10))
        >>> prob = Maximize(x, [x <= 5])
        >>> prob.solve()
        5.0
    """
    return OptimizationProblem(objective, constraints, sense='maximize')


# =============================================================================
# Helper Functions for Common Optimization Constructs
# =============================================================================

def Norm(x, p: int = 2):
    """
    Create a norm expression.

    Args:
        x: Variable or expression
        p: Norm type (1, 2, or 'inf')

    Returns:
        cvxpy norm expression
    """
    _require_cvxpy()
    return cp.norm(_to_cvx(x), p)


def Sum(x):
    """
    Sum of elements.

    Args:
        x: Variable or expression

    Returns:
        cvxpy sum expression
    """
    _require_cvxpy()
    return cp.sum(_to_cvx(x))


def Quad(x, Q=None):
    """
    Quadratic form x^T Q x.

    Args:
        x: Variable vector
        Q: PSD matrix (defaults to identity)

    Returns:
        cvxpy quadratic expression
    """
    _require_cvxpy()
    cvx_x = _to_cvx(x)
    if Q is None:
        return cp.sum_squares(cvx_x)
    return cp.quad_form(cvx_x, Q)


def PositiveSemidefinite(X):
    """
    Constraint that matrix X is positive semidefinite.

    Args:
        X: Square matrix variable

    Returns:
        cvxpy PSD constraint
    """
    _require_cvxpy()
    return _to_cvx(X) >> 0


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'OptVar',
    'OptimizationProblem',
    'Minimize',
    'Maximize',
    'Norm',
    'Sum',
    'Quad',
    'PositiveSemidefinite',
]
