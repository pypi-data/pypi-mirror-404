# symderive: Differential Equations

## Overview
symderive provides both symbolic (DSolve) and numerical (NDSolve) solvers for ordinary differential equations.

```python
from symderive import *
from symderive.ode import DSolve, NDSolve, NDSolveSystem
```

## Symbolic ODE Solving (DSolve)

### First-Order ODEs
```python
x = Symbol('x')
y = Function('y')

# dy/dx = y → y = C*e^x
sol = DSolve(Eq(D(y(x), x), y(x)), y(x), x)

# dy/dx = x → y = x²/2 + C
sol = DSolve(Eq(D(y(x), x), x), y(x), x)

# dy/dx + y = sin(x)
sol = DSolve(Eq(D(y(x), x) + y(x), Sin(x)), y(x), x)
```

### Second-Order ODEs
```python
# y'' + y = 0 (harmonic oscillator)
sol = DSolve(Eq(D(y(x), (x, 2)) + y(x), 0), y(x), x)
# Result: C1*cos(x) + C2*sin(x)

# y'' - y = 0
sol = DSolve(Eq(D(y(x), (x, 2)) - y(x), 0), y(x), x)
# Result: C1*e^x + C2*e^(-x)

# y'' + 2y' + y = 0 (critically damped)
sol = DSolve(Eq(D(y(x), (x, 2)) + 2*D(y(x), x) + y(x), 0), y(x), x)
```

### Initial Value Problems
```python
# y' = y, y(0) = 1
sol = DSolve(
    Eq(D(y(x), x), y(x)),
    y(x), x,
    ics={y(0): 1}
)
# Result: e^x

# y'' + y = 0, y(0) = 0, y'(0) = 1
sol = DSolve(
    Eq(D(y(x), (x, 2)) + y(x), 0),
    y(x), x,
    ics={y(0): 0, D(y(x), x).subs(x, 0): 1}
)
# Result: sin(x)
```

## Numerical ODE Solving (NDSolve)

### Basic Usage
```python
# dy/dx = -y, y(0) = 1, solve from x=0 to x=5
result = NDSolve(
    Eq(D(y(x), x), -y(x)),
    y(x), x,
    {y(0): 1},
    (0, 5)
)

# Access solution
t_values = result['t']      # Time points
y_values = result['y']      # Solution values
interp = result['interp']   # Interpolation function
```

### Plotting Solutions
```python
from symderive.plotting import ListLinePlot

# Plot numerical solution
data = list(zip(result['t'], result['y']))
ListLinePlot(data, PlotLabel="Exponential Decay")
```

### Systems of ODEs
```python
# Coupled system: Lotka-Volterra (predator-prey)
x_f = Function('x')
y_f = Function('y')
t = Symbol('t')

alpha, beta, delta, gamma = 1.0, 0.1, 0.075, 1.5

eqs = [
    Eq(D(x_f(t), t), alpha*x_f(t) - beta*x_f(t)*y_f(t)),
    Eq(D(y_f(t), t), delta*x_f(t)*y_f(t) - gamma*y_f(t))
]

result = NDSolveSystem(
    eqs,
    [x_f(t), y_f(t)],
    t,
    {x_f(0): 10, y_f(0): 5},
    (0, 50)
)
```

### Solver Options
```python
result = NDSolve(
    eq, y(x), x, ics, (0, 10),
    method='RK45',      # Runge-Kutta 4(5), default
    # method='RK23',    # Runge-Kutta 2(3)
    # method='DOP853',  # High-order RK
    # method='BDF',     # For stiff problems
    # method='LSODA',   # Auto stiff/non-stiff
    max_step=0.1,       # Maximum step size
    rtol=1e-6,          # Relative tolerance
    atol=1e-9,          # Absolute tolerance
)
```

## Physics Examples

### Harmonic Oscillator
```python
x = Symbol('x')
t = Symbol('t')
omega = Symbol('omega', positive=True)
psi = Function('psi')

# ψ'' + ω²ψ = 0
eq = Eq(D(psi(t), (t, 2)) + omega**2 * psi(t), 0)
sol = DSolve(eq, psi(t), t)
# C1*cos(ωt) + C2*sin(ωt)
```

### Damped Oscillator
```python
gamma = Symbol('gamma', positive=True)  # Damping
omega0 = Symbol('omega_0', positive=True)  # Natural frequency

# ψ'' + 2γψ' + ω₀²ψ = 0
eq = Eq(
    D(psi(t), (t, 2)) + 2*gamma*D(psi(t), t) + omega0**2*psi(t),
    0
)
sol = DSolve(eq, psi(t), t)
```

### Driven Oscillator
```python
F0, omega_d = symbols('F_0 omega_d', positive=True)

# ψ'' + 2γψ' + ω₀²ψ = F₀ cos(ω_d t)
eq = Eq(
    D(psi(t), (t, 2)) + 2*gamma*D(psi(t), t) + omega0**2*psi(t),
    F0 * Cos(omega_d * t)
)
sol = DSolve(eq, psi(t), t)
```

### Pendulum (Nonlinear)
```python
# Numerical solution for nonlinear pendulum
# θ'' + (g/L) sin(θ) = 0

theta = Function('theta')
g_val, L_val = 9.8, 1.0

eq = Eq(D(theta(t), (t, 2)) + (g_val/L_val)*Sin(theta(t)), 0)

# Small angle: θ(0) = 0.1, θ'(0) = 0
result_small = NDSolve(eq, theta(t), t, {theta(0): 0.1, D(theta(t),t).subs(t,0): 0}, (0, 10))

# Large angle: θ(0) = 2.5, θ'(0) = 0
result_large = NDSolve(eq, theta(t), t, {theta(0): 2.5, D(theta(t),t).subs(t,0): 0}, (0, 10))
```

### Schrödinger Equation (Time-Independent)
```python
# -ℏ²/(2m) ψ'' + V(x)ψ = Eψ

hbar, m_e, E_n = symbols('hbar m E', positive=True)
V = Function('V')
psi = Function('psi')

# Rearranged: ψ'' = (2m/ℏ²)(V - E)ψ
schrodinger = Eq(
    D(psi(x), (x, 2)),
    (2*m_e/hbar**2) * (V(x) - E_n) * psi(x)
)
```

### Quantum Harmonic Oscillator
```python
# V(x) = (1/2)mω²x²
omega = Symbol('omega', positive=True)

eq = Eq(
    D(psi(x), (x, 2)),
    (2*m_e/hbar**2) * (R(1,2)*m_e*omega**2*x**2 - E_n) * psi(x)
)

# Analytic solution involves Hermite polynomials
# E_n = ℏω(n + 1/2)
```

## Boundary Value Problems

For boundary conditions at two points, use numerical shooting or relaxation:

```python
# Example: y'' = -y, y(0) = 0, y(π) = 0
# Eigenvalue problem - solutions are sin(nx)

from scipy.integrate import solve_bvp
import numpy as np

def ode(x, y):
    return [y[1], -y[0]]

def bc(ya, yb):
    return [ya[0], yb[0]]  # y(0) = 0, y(π) = 0

x = np.linspace(0, np.pi, 50)
y_init = np.zeros((2, x.size))
y_init[0] = np.sin(x)  # Initial guess

sol = solve_bvp(ode, bc, x, y_init)
```

## Green's Functions

For linear ODEs with point sources:
```python
from symderive.calculus import GreensFunction

# G'' + ω²G = δ(x - x')
# Returns the Green's function for the operator
```
