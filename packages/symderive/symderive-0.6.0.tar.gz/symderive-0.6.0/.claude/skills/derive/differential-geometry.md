# Derive: Differential Geometry & General Relativity

## Overview
Derive provides comprehensive tools for differential geometry, tensor calculus, and general relativity computations.

```python
from derive import *
from derive.diffgeo import (
    Metric, Tensor, CovariantDerivative,
    minkowski_metric, schwarzschild_metric, flrw_metric, spherical_metric_3d,
    CoordinateTransformation, cartesian_to_spherical_3d,
    Einsum, Contract, OuterProduct, InnerProduct,
    IndexSpace, AbstractTensor, LeviCivita,
)
```

## Metric Tensors

### Creating Metrics
```python
theta, phi = symbols('theta phi', real=True)

# 2-sphere metric: ds² = dθ² + sin²θ dφ²
sphere = Metric(
    coords=[theta, phi],
    components=[
        [1, 0],
        [0, Sin(theta)**2]
    ]
)

# Access metric components
sphere.g              # Metric matrix
sphere[0, 0]          # g_θθ = 1
sphere[1, 1]          # g_φφ = sin²θ
sphere.inverse        # Inverse metric g^μν
sphere.dim            # Dimension
```

### Built-in Metrics
```python
# Minkowski (flat spacetime)
eta = minkowski_metric(4)  # diag(-1, 1, 1, 1)

# Schwarzschild (black hole)
g_schw = schwarzschild_metric()  # ds² = -(1-2M/r)dt² + dr²/(1-2M/r) + r²dΩ²

# FLRW (cosmology)
g_flrw = flrw_metric()  # ds² = -dt² + a(t)²[dr² + r²dΩ²]

# 3D spherical coordinates
g_sph = spherical_metric_3d()  # ds² = dr² + r²dθ² + r²sin²θ dφ²
```

## Christoffel Symbols

Connection coefficients Γ^ρ_μν:
```python
gamma = sphere.christoffel_second_kind()

# Access components
Gamma_theta_phi_phi = gamma[0, 1, 1]  # Γ^θ_φφ = -sin(θ)cos(θ)
Gamma_phi_theta_phi = gamma[1, 0, 1]  # Γ^φ_θφ = cot(θ)

# First kind (lowered index)
gamma1 = sphere.christoffel_first_kind()  # Γ_ρμν
```

## Curvature Tensors

### Riemann Tensor
R^ρ_σμν measures curvature:
```python
riemann = sphere.riemann_tensor()
R_0101 = riemann[0, 1, 0, 1]  # R^θ_φθφ
```

### Ricci Tensor and Scalar
```python
ricci = sphere.ricci_tensor()      # R_μν = R^ρ_μρν
R_scalar = sphere.ricci_scalar()   # R = g^μν R_μν

# For unit 2-sphere: R = 2 (constant positive curvature)
```

### Einstein Tensor
G_μν = R_μν - (1/2)g_μν R
```python
einstein = sphere.einstein_tensor()
# Einstein's field equations: G_μν = 8πG T_μν
```

## Einstein Summation (Einsum)

Tensor contractions using Einstein notation:
```python
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])

# Matrix multiplication: C_ik = A_ij B_jk
C = Einsum("ij,jk->ik", A, B)

# Trace: tr(A) = A_ii
tr_A = Einsum("ii->", A)

# Transpose: A^T_ji = A_ij
A_T = Einsum("ij->ji", A)

# Outer product: (a⊗b)_ij = a_i b_j
a = Array([1, 2])
b = Array([3, 4])
outer = Einsum("i,j->ij", a, b)
```

### Tensor Operations
```python
# Contract indices
Contract(tensor, (0, 1))  # Contract indices 0 and 1

# Outer product
OuterProduct(a, b)

# Inner product (dot product)
InnerProduct(a, b)

# Trace
Trace(A)
```

## Abstract Index Notation

For symbolic tensor algebra (xAct-style):
```python
# Define index spaces
spacetime = IndexSpace('spacetime', dim=4)
gauge = IndexSpace('gauge', dim=3)

# Create indices
mu, nu, rho = spacetime.indices('mu nu rho')
a, b = gauge.indices('a b')

# Define tensors
g = AbstractTensor('g', spacetime, spacetime, symmetric=True)
F = AbstractTensor('F', spacetime, spacetime, antisymmetric=True)

# Index expressions
expr = g[mu, -nu]  # g^μ_ν (upper, lower)
trace = g[mu, -mu]  # Trace: g^μ_μ

# Tensor multiplication (auto-contracts repeated indices)
product = T[mu, nu] * S[-nu, rho]  # Contracts over ν
```

## Coordinate Transformations

```python
# Built-in transformations
trans = cartesian_to_spherical_3d()

# Jacobian matrix
J = trans.jacobian

# Jacobian determinant (volume element factor)
det_J = trans.jacobian_determinant  # r² sin(θ)
```

## Levi-Civita Symbol

Totally antisymmetric tensor:
```python
# Evaluate Levi-Civita symbol
LeviCivita(0, 1, 2)   # +1 (even permutation)
LeviCivita(0, 2, 1)   # -1 (odd permutation)
LeviCivita(0, 0, 1)   # 0 (repeated index)

# Full tensor
from derive.diffgeo import levi_civita_tensor
eps = levi_civita_tensor(3)  # ε_ijk
```

## Variational Calculus

Euler-Lagrange equations from Lagrangians:
```python
from derive.calculus import VariationalDerivative, EulerLagrangeEquation

x, t = symbols('x t')
phi = Function('phi')(x, t)

# Klein-Gordon Lagrangian
L = R(1,2)*D(phi,t)**2 - R(1,2)*D(phi,x)**2 - R(1,2)*m**2*phi**2

# Euler-Lagrange equation: δL/δφ = 0
eq = EulerLagrangeEquation(L, phi, [x, t])
# Returns: ∂²φ/∂x² - ∂²φ/∂t² - m²φ = 0
```

## Covariant Derivative

```python
# Covariant derivative of a tensor
nabla_T = CovariantDerivative(T, metric)
```

## Example: Schwarzschild Geometry

```python
g = schwarzschild_metric()

# Verify vacuum solution (R_μν = 0)
ricci = g.ricci_tensor()
Simplify(ricci)  # All components zero

# Ricci scalar
R = g.ricci_scalar()
Simplify(R)  # 0

# Kretschmann scalar K = R^μνρσ R_μνρσ
# (measures curvature strength, diverges at r=0)
```

## Example: Geodesic Equation

Particle motion in curved spacetime:
```python
import numpy as np

def geodesic_step_sphere(state, dlambda=0.05):
    """One step of geodesic on unit 2-sphere."""
    theta, phi, dtheta, dphi = state

    # Christoffel symbols
    sin_t, cos_t = np.sin(theta), np.cos(theta)

    # Geodesic acceleration
    d2theta = sin_t * cos_t * dphi**2
    d2phi = -2 * (cos_t / sin_t) * dtheta * dphi

    # Euler step
    return (
        theta + dtheta * dlambda,
        phi + dphi * dlambda,
        dtheta + d2theta * dlambda,
        dphi + d2phi * dlambda
    )

# Iterate geodesic
initial = (np.pi/2, 0.0, 0.0, 1.0)  # Start at equator
path = NestList(geodesic_step_sphere, initial, 100)
```
