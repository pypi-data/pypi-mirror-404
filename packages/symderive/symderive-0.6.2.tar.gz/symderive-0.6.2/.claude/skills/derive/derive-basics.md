# symderive: Symbolic Mathematics Basics

## Overview
symderive is a Python symbolic mathematics library built on SymPy with a Mathematica-style API. Import everything via:

```python
from symderive import *
```

## Core Symbols and Constants

### Creating Symbols
```python
# Single symbol
x = Symbol('x')

# Multiple symbols
x, y, z = symbols('x y z')

# Symbols with assumptions
t = Symbol('t', real=True)
m = Symbol('m', positive=True)
n = Symbol('n', integer=True, nonnegative=True)
```

### Constants
```python
Pi          # π (3.14159...)
E           # Euler's number (2.71828...)
I           # Imaginary unit √(-1)
Infinity    # ∞
```

### Rational Numbers (avoid floating-point issues)
```python
# Use R() for exact fractions
R(1, 2)          # 1/2
R(3, 4)          # 3/4
Rational(1, 2)   # Same as R(1, 2)

# Common shortcuts
Half             # 1/2
Third            # 1/3
Quarter          # 1/4
```

## Basic Calculus

### Differentiation
```python
D(Sin(x), x)           # cos(x) - first derivative
D(x**3, x)             # 3*x**2
D(x**5, (x, 3))        # 60*x**2 - third derivative
D(x**2 * y**3, x)      # 2*x*y**3 - partial derivative
```

### Integration
```python
# Indefinite
Integrate(x**2, x)                    # x**3/3
Integrate(Sin(x), x)                  # -cos(x)

# Definite
Integrate(x**2, (x, 0, 1))           # 1/3
Integrate(x*y, (x, 0, 1), (y, 0, 1)) # 1/4 - multiple

# Numerical
NIntegrate(Sin(x**2), (x, 0, 10))    # 0.6460...
```

### Limits
```python
Limit(Sin(x)/x, x, 0)        # 1
Limit(1/x, x, 0, '+')        # Infinity (right limit)
Limit(1/x, x, 0, '-')        # -Infinity (left limit)
Limit((1 + 1/n)**n, n, Infinity)  # E
```

### Series Expansion
```python
Series(Exp(x), (x, 0, 5))    # 1 + x + x²/2 + x³/6 + ...
Series(Sin(x), (x, 0, 7))    # x - x³/6 + x⁵/120 - ...
```

### Summation and Products
```python
i = Symbol('i')
n = Symbol('n')

Sum(i, (i, 1, 10))           # 55
Sum(i**2, (i, 1, 10))        # 385
Sum(i, (i, 1, n))            # n*(n+1)/2 - symbolic
Product(i, (i, 1, 5))        # 120 (5!)
```

## Functions

### Trigonometric
```python
Sin(x), Cos(x), Tan(x), Cot(x), Sec(x), Csc(x)
Sinh(x), Cosh(x), Tanh(x)    # Hyperbolic
ArcSin(x), ArcCos(x), ArcTan(x)  # Inverse
```

### Exponential and Logarithmic
```python
Exp(x)      # e^x
Log(x)      # Natural log (ln)
Sqrt(x)     # √x
Power(x, n) # x^n
```

## Algebra

### Solving Equations
```python
Solve(x**2 - 4, x)           # [-2, 2]
Solve(x**2 + 2*x + 1, x)     # [-1]
NSolve(Cos(x) - x, x)        # Numerical solution
```

### Simplification
```python
Simplify(expr)
Expand((x + 1)**3)
Factor(x**2 - 1)
Collect(x**2 + 2*x*y + y**2, x)
TrigSimplify(Sin(x)**2 + Cos(x)**2)  # 1
```

## Linear Algebra

```python
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])

Dot(A, B)                    # Matrix multiplication
Transpose(A)
Inverse(A)
Det(A)                       # Determinant
Eigenvalues(A)
Eigenvectors(A)
Tr(A)                        # Trace
```

## Functional Operations

```python
# Nest applies function repeatedly
Nest(f, x, n)                # f(f(f(...f(x)...)))
NestList(f, x, n)            # [x, f(x), f(f(x)), ...]

# Fixed point iteration
FixedPoint(f, x)             # Iterate until convergence
FixedPointList(f, x)         # List all iterations

# Table generation
Table(i**2, (i, 1, 10))      # [1, 4, 9, 16, ...]
Map(Sin, [0, Pi/2, Pi])      # Apply to list
```

## Output

```python
Simplify(expr)
TeXForm(expr)                # LaTeX output
PrettyForm(expr)             # ASCII pretty print
N(expr)                      # Numerical evaluation
N(Pi, 50)                    # 50 decimal places
```
