# Derive: Symbolic Mathematics for Physics

Derive is a Python symbolic mathematics library built on SymPy with a Mathematica-style API, designed for theoretical physics and applied mathematics.

## Quick Start

```python
from derive import *

# Symbols
x, y, t = symbols('x y t')
m = Symbol('m', positive=True)

# Calculus
D(Sin(x), x)                    # cos(x)
Integrate(x**2, (x, 0, 1))      # 1/3
Limit(Sin(x)/x, x, 0)           # 1
Series(Exp(x), (x, 0, 5))       # 1 + x + x²/2 + ...

# Algebra
Solve(x**2 - 4, x)              # [-2, 2]
Simplify(Sin(x)**2 + Cos(x)**2) # 1

# Linear Algebra
A = Matrix([[1, 2], [3, 4]])
Eigenvalues(A)
Det(A)
```

## Skill Files

| File | Topics |
|------|--------|
| [derive-basics.md](derive-basics.md) | Symbols, calculus, algebra, linear algebra, functional programming |
| [differential-geometry.md](differential-geometry.md) | Metrics, curvature tensors, Einsum, GR computations |
| [ode-solving.md](ode-solving.md) | Symbolic & numerical ODE solving, physics examples |
| [optimization.md](optimization.md) | Convex optimization, constraints, portfolio problems |
| [plotting.md](plotting.md) | 2D/3D plots, parametric, contour, vector fields |
| [special-functions.md](special-functions.md) | Bessel, Legendre, Hermite, spherical harmonics, etc. |

## Core Modules

```python
from derive import *                    # Main API
from derive.diffgeo import *            # Differential geometry
from derive.ode import DSolve, NDSolve  # ODE solvers
from derive.optimize import *           # Optimization
from derive.plotting import *           # Visualization
from derive.calculus import *           # Advanced calculus
```

## Physics Workflows

### Quantum Mechanics
```python
# Harmonic oscillator
x = Symbol('x')
n = Symbol('n', integer=True, nonnegative=True)
psi_n = HermiteH(n, x) * Exp(-x**2/2)

# Hydrogen atom radial part
r = Symbol('r', positive=True)
R_nl = AssociatedLaguerreL(n-l-1, 2*l+1, 2*r) * Exp(-r)

# Angular momentum
theta, phi = symbols('theta phi')
Y_lm = SphericalHarmonicY(l, m, theta, phi)
```

### General Relativity
```python
from derive.diffgeo import schwarzschild_metric, Metric

# Schwarzschild black hole
g = schwarzschild_metric()
ricci = g.ricci_tensor()      # Should vanish (vacuum)
R = g.ricci_scalar()          # 0

# Custom metric
theta, phi = symbols('theta phi')
sphere = Metric(
    coords=[theta, phi],
    components=[[1, 0], [0, Sin(theta)**2]]
)
christoffel = sphere.christoffel_second_kind()
riemann = sphere.riemann_tensor()
```

### Classical Mechanics
```python
# Lagrangian mechanics
t = Symbol('t')
q = Function('q')(t)
L = R(1,2)*m*D(q,t)**2 - R(1,2)*k*q**2

from derive.calculus import EulerLagrangeEquation
eq = EulerLagrangeEquation(L, q, [t])  # m*q'' + k*q = 0

# Solve ODE
from derive.ode import DSolve
sol = DSolve(Eq(eq, 0), q, t)
```

### Electromagnetism
```python
from derive.diffgeo import IndexSpace, AbstractTensor

spacetime = IndexSpace('spacetime', dim=4)
mu, nu, rho = spacetime.indices('mu nu rho')

# Field strength tensor F^μν (antisymmetric)
F = AbstractTensor('F', spacetime, spacetime, antisymmetric=True)

# Metric
g = AbstractTensor('g', spacetime, spacetime, symmetric=True)
```

## Key Patterns

### Exact Fractions (Avoid Floats)
```python
R(1, 2)          # 1/2 - exact
Half             # 1/2 - shortcut
Rational(3, 4)   # 3/4

# NOT: 0.5 (loses exactness in symbolic computation)
```

### Assumptions on Symbols
```python
x = Symbol('x', real=True)
t = Symbol('t', positive=True)
n = Symbol('n', integer=True, nonnegative=True)
m = Symbol('m', positive=True)  # Mass
```

### Simplification Pipeline
```python
expr = Sin(x)**2 + Cos(x)**2
Simplify(expr)           # General simplification
TrigSimplify(expr)       # Trig-specific
Expand((x+1)**3)         # Expand products
Factor(x**2 - 1)         # Factor polynomials
Collect(expr, x)         # Collect terms
```

### Numerical Evaluation
```python
N(Pi)                    # 3.14159...
N(Pi, 50)                # 50 digits
expr.evalf()             # SymPy method
float(expr.evalf())      # Python float
```

## Common Tasks

| Task | Code |
|------|------|
| Differentiate | `D(f, x)` or `D(f, (x, n))` for nth |
| Integrate | `Integrate(f, x)` or `Integrate(f, (x, a, b))` |
| Solve equation | `Solve(Eq(lhs, rhs), x)` or `Solve(expr, x)` |
| Taylor series | `Series(f, (x, x0, n))` |
| Limit | `Limit(f, x, x0)` or `Limit(f, x, x0, '+')` |
| Substitute | `expr.subs(x, value)` |
| Numerical ODE | `NDSolve(eq, y(x), x, ics, (t0, tf))` |
| Plot | `Plot(f, (x, a, b))` |
| Matrix ops | `Dot(A, B)`, `Inverse(A)`, `Eigenvalues(A)` |
| Christoffel | `metric.christoffel_second_kind()` |
| Riemann tensor | `metric.riemann_tensor()` |

## Project Structure

```
src/derive/
├── __init__.py          # Main exports
├── core/                # Symbols, constants, numbers
├── calculus/            # D, Integrate, Series, Limit, transforms
├── algebra/             # Solve, Simplify, linear algebra
├── diffgeo/             # Metrics, tensors, curvature
├── ode/                 # DSolve, NDSolve
├── optimize/            # Convex optimization
├── plotting/            # Visualization
├── functions/           # Trig, exponential, special
├── patterns/            # Pattern matching, replacement
├── probability/         # Distributions
├── discretization/      # PDE stencils
└── regression/          # Symbolic regression
```

## Tips

1. **Use exact rationals** (`R(1,2)`) instead of floats for symbolic work
2. **Add assumptions** to symbols (`positive=True`, `real=True`) for better simplification
3. **Simplify strategically** - not everything needs `Simplify()`
4. **Check dimensions** when working with tensors and metrics
5. **Use parallel tool calls** when plotting multiple independent figures
