# Derive: Optimization

## Overview
Derive provides symbolic and numerical optimization through a cvxpy-based interface for convex optimization and analytical methods for unconstrained problems.

```python
from derive import *
from derive.optimize import OptVar, Minimize, Maximize, Constraint
```

## Optimization Variables

```python
# Scalar variable
x = OptVar('x')

# Variable with bounds
x = OptVar('x', lower=0)           # x >= 0
x = OptVar('x', lower=0, upper=10) # 0 <= x <= 10

# Vector variable
v = OptVar('v', shape=(3,))

# Matrix variable
M = OptVar('M', shape=(2, 2))

# Positive semidefinite matrix
P = OptVar('P', shape=(3, 3), PSD=True)

# Non-negative variable
y = OptVar('y', nonneg=True)
```

## Unconstrained Optimization

### Minimize
```python
x = OptVar('x')
y = OptVar('y')

# Minimize (x-1)² + (y-2)²
result = Minimize((x - 1)**2 + (y - 2)**2)

print(result.optimal_value)  # 0
print(result.variables)      # {'x': 1.0, 'y': 2.0}
```

### Maximize
```python
# Maximize -x² (equivalent to minimize x²)
result = Maximize(-x**2)
```

## Constrained Optimization

### Linear Constraints
```python
x = OptVar('x')
y = OptVar('y')

# Minimize x + y subject to:
#   x + 2y >= 4
#   x >= 0, y >= 0
result = Minimize(
    x + y,
    constraints=[
        x + 2*y >= 4,
        x >= 0,
        y >= 0
    ]
)
```

### Equality Constraints
```python
# Minimize x² + y² subject to x + y = 1
result = Minimize(
    x**2 + y**2,
    constraints=[x + y == 1]
)
# Optimal: x = y = 0.5
```

### Quadratic Programming
```python
# Minimize (1/2)x'Qx + c'x subject to Ax <= b
x = OptVar('x', shape=(2,))
Q = Matrix([[2, 0], [0, 2]])
c = Matrix([-1, -1])
A = Matrix([[1, 1], [-1, 0], [0, -1]])
b = Matrix([1, 0, 0])

# Using matrix operations
result = Minimize(
    R(1,2) * x.T @ Q @ x + c.T @ x,
    constraints=[A @ x <= b]
)
```

## Convex Functions

Derive supports standard convex functions:

```python
from derive.optimize import (
    norm, quad_form, sum_squares,
    log_sum_exp, geo_mean, lambda_max, lambda_min
)

x = OptVar('x', shape=(3,))

# L2 norm: ||x||_2
norm(x)
norm(x, 2)

# L1 norm: ||x||_1
norm(x, 1)

# Sum of squares: Σ x_i²
sum_squares(x)

# Quadratic form: x'Qx
Q = Matrix([[1, 0], [0, 2]])
x2 = OptVar('x', shape=(2,))
quad_form(x2, Q)

# Log-sum-exp (smooth max)
log_sum_exp(x)

# Geometric mean
geo_mean(x)
```

## Semidefinite Programming

```python
# Positive semidefinite constraint
X = OptVar('X', shape=(2, 2), PSD=True)

# Minimize trace(X) subject to X_11 >= 1
result = Minimize(
    Tr(X),
    constraints=[X[0, 0] >= 1]
)
```

## Second-Order Cone Programming

```python
x = OptVar('x', shape=(3,))
t = OptVar('t')

# ||x|| <= t (second-order cone constraint)
result = Minimize(
    t,
    constraints=[norm(x) <= t, x[0] + x[1] + x[2] == 1]
)
```

## Portfolio Optimization

```python
import numpy as np

n = 5  # Number of assets
returns = np.array([0.1, 0.12, 0.08, 0.15, 0.09])
cov_matrix = np.array([...])  # Covariance matrix

w = OptVar('w', shape=(n,), nonneg=True)  # Weights

# Maximize expected return - λ * variance
# Subject to: weights sum to 1
lambda_risk = 0.5

result = Maximize(
    returns @ w - lambda_risk * quad_form(w, cov_matrix),
    constraints=[sum(w) == 1]
)

optimal_weights = result.variables['w']
```

## Least Squares

```python
# ||Ax - b||² (linear least squares)
A = Matrix([[1, 2], [3, 4], [5, 6]])
b = Matrix([1, 2, 3])
x = OptVar('x', shape=(2,))

result = Minimize(sum_squares(A @ x - b))
```

### Regularized Least Squares
```python
# ||Ax - b||² + λ||x||² (Ridge/Tikhonov)
lambda_reg = 0.1
result = Minimize(sum_squares(A @ x - b) + lambda_reg * sum_squares(x))

# ||Ax - b||² + λ||x||₁ (Lasso)
result = Minimize(sum_squares(A @ x - b) + lambda_reg * norm(x, 1))
```

## Analytical Optimization

For symbolic/analytical optimization:

```python
x = Symbol('x')
f = x**2 - 4*x + 4

# Find critical points
critical = Solve(D(f, x), x)  # [2]

# Second derivative test
D(f, (x, 2))  # 2 > 0, so minimum

# Evaluate at critical point
f.subs(x, 2)  # 0
```

### Lagrange Multipliers
```python
x, y, lam = symbols('x y lambda')

# Minimize x² + y² subject to x + y = 1
L = x**2 + y**2 - lam*(x + y - 1)

# Solve gradient = 0
eqs = [D(L, x), D(L, y), D(L, lam)]
sol = Solve(eqs, [x, y, lam])
# x = y = 1/2, λ = 1
```

## Solver Options

```python
result = Minimize(
    objective,
    constraints=constraints,
    solver='ECOS',     # Default solver
    # solver='SCS',    # For large problems
    # solver='MOSEK',  # Commercial (if installed)
    verbose=True,      # Print solver output
    max_iters=1000,    # Maximum iterations
)

# Check solution status
print(result.status)  # 'optimal', 'infeasible', etc.
```

## Tips

1. **Convexity**: Only convex problems are guaranteed to find global optima
2. **Scaling**: Scale variables/constraints for numerical stability
3. **Feasibility**: Start with a feasible point if possible
4. **Bounds**: Add variable bounds to help the solver
5. **Warm start**: Use previous solutions as initial guesses
