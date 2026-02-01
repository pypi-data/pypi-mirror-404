# symderive: Special Functions

## Overview
symderive provides extensive special function support for physics and mathematics. All functions support symbolic manipulation and numerical evaluation.

```python
from symderive import *
```

## Bessel Functions

### First Kind J_n(x)
```python
x = Symbol('x')

BesselJ(0, x)        # J_0(x)
BesselJ(1, x)        # J_1(x)
BesselJ(n, x)        # J_n(x) for symbolic n

# Numerical evaluation
float(BesselJ(0, 1).evalf())  # 0.7651976865579666
N(BesselJ(0, 2.5))            # 0.0483838...
```

### Second Kind Y_n(x) (Neumann)
```python
BesselY(0, x)        # Y_0(x)
BesselY(1, x)        # Y_1(x)
```

### Modified Bessel Functions
```python
BesselI(0, x)        # I_0(x) - modified first kind
BesselI(1, x)        # I_1(x)
BesselK(0, x)        # K_0(x) - modified second kind
BesselK(1, x)        # K_1(x)
```

### Hankel Functions
```python
HankelH1(0, x)       # H^(1)_0(x)
HankelH2(0, x)       # H^(2)_0(x)
```

### Spherical Bessel Functions
```python
SphericalBesselJ(0, x)   # j_0(x) = sin(x)/x
SphericalBesselJ(1, x)   # j_1(x)
SphericalBesselY(0, x)   # y_0(x) = -cos(x)/x
SphericalBesselY(1, x)   # y_1(x)
```

**Physics**: Bessel functions appear in cylindrical coordinates (wave guides, drums), spherical Bessel in 3D scattering problems.

## Orthogonal Polynomials

### Legendre Polynomials P_n(x)
```python
x = Symbol('x')

LegendreP(0, x)      # 1
LegendreP(1, x)      # x
LegendreP(2, x)      # (3x² - 1)/2
LegendreP(3, x)      # (5x³ - 3x)/2

# Associated Legendre P^m_n(x)
AssociatedLegendreP(1, 0, x)   # P^0_1 = x
AssociatedLegendreP(1, 1, x)   # P^1_1 = -√(1-x²)
AssociatedLegendreP(2, 1, x)   # P^1_2
```

**Physics**: Angular solutions in spherical coordinates, multipole expansions.

### Chebyshev Polynomials
```python
# First kind T_n(x)
ChebyshevT(0, x)     # 1
ChebyshevT(1, x)     # x
ChebyshevT(2, x)     # 2x² - 1
ChebyshevT(3, x)     # 4x³ - 3x

# Second kind U_n(x)
ChebyshevU(0, x)     # 1
ChebyshevU(1, x)     # 2x
ChebyshevU(2, x)     # 4x² - 1
```

**Physics**: Optimal polynomial approximations, spectral methods.

### Hermite Polynomials H_n(x)
```python
HermiteH(0, x)       # 1
HermiteH(1, x)       # 2x
HermiteH(2, x)       # 4x² - 2
HermiteH(3, x)       # 8x³ - 12x
```

**Physics**: Quantum harmonic oscillator eigenfunctions ψ_n(x) ∝ H_n(x)e^(-x²/2).

### Laguerre Polynomials L_n(x)
```python
LaguerreL(0, x)      # 1
LaguerreL(1, x)      # -x + 1
LaguerreL(2, x)      # x²/2 - 2x + 1

# Associated/Generalized Laguerre L^α_n(x)
AssociatedLaguerreL(1, 0, x)   # 1 - x
AssociatedLaguerreL(1, 1, x)   # 2 - x
AssociatedLaguerreL(2, 1, x)   # (x² - 4x + 2)/2
```

**Physics**: Radial hydrogen wavefunctions R_nl(r) ∝ L^(2l+1)_(n-l-1)(2r/na₀).

### Gegenbauer (Ultraspherical) Polynomials
```python
# C^α_n(x) - generalization of Legendre and Chebyshev
GegenbauerC(2, R(1,2), x)   # Reduces to Legendre when α=1/2
GegenbauerC(2, 1, x)        # Related to Chebyshev U
```

### Jacobi Polynomials
```python
# P^(α,β)_n(x) - most general classical orthogonal polynomials
JacobiP(2, 0, 0, x)              # Reduces to Legendre when α=β=0
JacobiP(2, R(1,2), R(1,2), x)    # Related to Chebyshev
```

## Spherical Harmonics Y^m_l(θ,φ)

```python
theta, phi = symbols('theta phi')

SphericalHarmonicY(0, 0, theta, phi)   # Y^0_0 = 1/(2√π)
SphericalHarmonicY(1, 0, theta, phi)   # Y^0_1 ∝ cos(θ)
SphericalHarmonicY(1, 1, theta, phi)   # Y^1_1 ∝ sin(θ)e^(iφ)
SphericalHarmonicY(2, 0, theta, phi)   # Y^0_2 ∝ 3cos²θ - 1
```

**Physics**: Angular momentum eigenstates, multipole expansions, atomic orbitals.

## Elliptic Integrals

### Complete Elliptic Integrals
```python
k = Symbol('k')

EllipticK(k)         # K(k) = ∫₀^(π/2) dθ/√(1-k²sin²θ) - first kind
EllipticE(k)         # E(k) = ∫₀^(π/2) √(1-k²sin²θ) dθ - second kind

# Special values
EllipticK(0)         # π/2
EllipticE(0)         # π/2
```

### Incomplete Elliptic Integrals
```python
EllipticF(phi, k)    # F(φ,k) - incomplete first kind
EllipticPi(n, phi, k)  # Π(n; φ, k) - third kind
```

**Physics**: Pendulum period, classical mechanics, string theory.

## Error Functions

```python
x = Symbol('x')

Erf(x)               # Error function: (2/√π) ∫₀^x e^(-t²) dt
Erfc(x)              # Complementary: 1 - Erf(x)
Erfi(x)              # Imaginary: -i·Erf(ix)

# Special values
Erf(0)               # 0
Erfc(0)              # 1
Erf(Infinity)        # 1
```

**Physics**: Probability distributions, diffusion, heat conduction.

## Airy Functions

Solutions to y'' - xy = 0:
```python
AiryAi(x)            # Ai(x) - decays for x > 0
AiryBi(x)            # Bi(x) - grows for x > 0

# Numerical
float(AiryAi(0).evalf())   # 0.35502805388781724
float(AiryBi(0).evalf())   # 0.61492662744600
```

**Physics**: WKB turning points, quantum tunneling, optics.

## Gamma and Related Functions

```python
Gamma(5)             # 24 (= 4!)
Gamma(R(1,2))        # √π
Gamma(R(3,2))        # √π/2

# Beta function: B(a,b) = Γ(a)Γ(b)/Γ(a+b)
Beta(2, 3)

# Factorial and Binomial
Factorial(5)         # 120
Binomial(10, 3)      # 120

# Digamma (logarithmic derivative of Gamma)
Digamma(x)           # ψ(x) = Γ'(x)/Γ(x)
```

## Zeta and Polylogarithms

```python
# Riemann zeta function
Zeta(2)              # π²/6
Zeta(4)              # π⁴/90
Zeta(3)              # Apéry's constant ≈ 1.202

# Polylogarithm Li_s(z)
PolyLog(2, x)        # Li_2(x) = dilogarithm
PolyLog(3, x)        # Li_3(x) = trilogarithm
```

**Physics**: Quantum field theory, statistical mechanics, string theory.

## Hypergeometric Functions

```python
a, b, c = symbols('a b c')

# Gauss hypergeometric ₂F₁
Hypergeometric2F1([a, b], [c], x)

# Generalized ₚFq
HypergeometricPFQ([a1, a2], [b1, b2], x)

# Meijer G-function (most general)
MeijerG([[a1], [a2]], [[b1], [b2]], x)
```

**Physics**: Many special functions are hypergeometric cases.

## Exponential Integrals

```python
ExpIntegralEi(x)     # Ei(x) = -∫_{-x}^∞ e^(-t)/t dt

# Sine and cosine integrals
SinIntegral(x)       # Si(x) = ∫₀^x sin(t)/t dt
CosIntegral(x)       # Ci(x) = -∫_x^∞ cos(t)/t dt

# Logarithmic integral
LogIntegral(x)       # li(x) = ∫₀^x dt/ln(t)
```

## Fresnel Integrals

Used in optics and wave propagation:
```python
FresnelS(x)          # S(x) = ∫₀^x sin(πt²/2) dt
FresnelC(x)          # C(x) = ∫₀^x cos(πt²/2) dt
```

## Numerical Evaluation

```python
# Single precision
N(BesselJ(0, 1))              # 0.765197686557966...

# High precision
N(BesselJ(0, 1), 50)          # 50 decimal places

# Using evalf()
BesselJ(0, 1).evalf()
BesselJ(0, 1).evalf(100)      # 100 digits
```

## Derivatives

All special functions support symbolic differentiation:
```python
D(BesselJ(0, x), x)           # -BesselJ(1, x)
D(BesselJ(n, x), x)           # (BesselJ(n-1,x) - BesselJ(n+1,x))/2

D(LegendreP(n, x), x)         # Uses Rodrigues formula
D(SphericalHarmonicY(l, m, theta, phi), theta)
```

## Series Expansions

```python
Series(BesselJ(0, x), (x, 0, 8))
# 1 - x²/4 + x⁴/64 - x⁶/2304 + ...

Series(Erf(x), (x, 0, 7))
# (2/√π)(x - x³/3 + x⁵/10 - x⁷/42 + ...)
```
