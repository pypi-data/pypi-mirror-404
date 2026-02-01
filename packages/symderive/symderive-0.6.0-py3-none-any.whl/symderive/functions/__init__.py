"""
Functions module - Mathematical functions.

This module provides mathematical functions:
- Trigonometric (Sin, Cos, Tan, etc.)
- Exponential (Exp, Log, Sqrt)
- Special functions (Bessel, Legendre, etc.)
- Number theory functions (GCD, LCM, Prime, etc.)
"""

from symderive.functions.trig import (
    Sin, Cos, Tan, Cot, Sec, Csc,
    Sinh, Cosh, Tanh, Coth, Sech, Csch,
    ArcSin, ArcCos, ArcTan, ArcCot, ArcSec, ArcCsc,
    ArcSinh, ArcCosh, ArcTanh, ArcCoth, ArcSech, ArcCsch,
)
from symderive.functions.exponential import (
    Exp, Log, Ln, Sqrt, Power,
)
from symderive.functions.complex import (
    Re, Im, Conjugate, Arg, Abs,
)
from symderive.functions.special import (
    Factorial, Binomial, Gamma, Beta,
    BesselJ, BesselY, BesselI, BesselK,
    HankelH1, HankelH2,
    SphericalBesselJ, SphericalBesselY,
    LegendreP, AssociatedLegendreP,
    ChebyshevT, ChebyshevU,
    HermiteH, LaguerreL, AssociatedLaguerreL,
    GegenbauerC, JacobiP,
    SphericalHarmonicY,
    EllipticK, EllipticE, EllipticF, EllipticPi,
    Erf, Erfc, Erfi,
    ExpIntegralEi, SinIntegral, CosIntegral, LogIntegral,
    FresnelS, FresnelC,
    AiryAi, AiryBi,
    Zeta, PolyLog,
    Hypergeometric2F1, HypergeometricPFQ, MeijerG,
)
from symderive.functions.number import (
    Sign, Floor, Ceiling, N, Round, Mod,
    GCD, LCM, PrimeQ, Prime, FactorInteger,
)

__all__ = [
    # Trigonometric
    'Sin', 'Cos', 'Tan', 'Cot', 'Sec', 'Csc',
    'Sinh', 'Cosh', 'Tanh', 'Coth', 'Sech', 'Csch',
    'ArcSin', 'ArcCos', 'ArcTan', 'ArcCot', 'ArcSec', 'ArcCsc',
    'ArcSinh', 'ArcCosh', 'ArcTanh', 'ArcCoth', 'ArcSech', 'ArcCsch',
    # Exponential
    'Exp', 'Log', 'Ln', 'Sqrt', 'Power',
    # Complex
    'Re', 'Im', 'Conjugate', 'Arg', 'Abs',
    # Special functions
    'Factorial', 'Binomial', 'Gamma', 'Beta',
    'BesselJ', 'BesselY', 'BesselI', 'BesselK',
    'HankelH1', 'HankelH2',
    'SphericalBesselJ', 'SphericalBesselY',
    'LegendreP', 'AssociatedLegendreP',
    'ChebyshevT', 'ChebyshevU',
    'HermiteH', 'LaguerreL', 'AssociatedLaguerreL',
    'GegenbauerC', 'JacobiP',
    'SphericalHarmonicY',
    'EllipticK', 'EllipticE', 'EllipticF', 'EllipticPi',
    'Erf', 'Erfc', 'Erfi',
    'ExpIntegralEi', 'SinIntegral', 'CosIntegral', 'LogIntegral',
    'FresnelS', 'FresnelC',
    'AiryAi', 'AiryBi',
    'Zeta', 'PolyLog',
    'Hypergeometric2F1', 'HypergeometricPFQ', 'MeijerG',
    # Number functions
    'Sign', 'Floor', 'Ceiling', 'N', 'Round', 'Mod',
    'GCD', 'LCM', 'PrimeQ', 'Prime', 'FactorInteger',
]
