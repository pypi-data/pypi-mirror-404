"""
Calculus module - Differentiation, Integration, Limits, Series, Variational Calculus.

Provides calculus operations.
"""

from symderive.calculus.differentiation import D
from symderive.calculus.integration import (
    Integrate, NIntegrate, ChangeVariables, IntegrateWithSubstitution
)
from symderive.calculus.limits import Limit
from symderive.calculus.series import Series, Sum, Product
from symderive.calculus.variational import VariationalDerivative, EulerLagrangeEquation
from symderive.calculus.greens import (
    GreenFunction, GreenFunctionPoisson1D, GreenFunctionHelmholtz1D,
    GreenFunctionLaplacian3D, GreenFunctionWave1D,
)
from symderive.calculus.transforms import (
    FourierTransform, InverseFourierTransform,
    LaplaceTransform, InverseLaplaceTransform,
    Convolve,
)

__all__ = [
    'D',
    'Integrate',
    'NIntegrate',
    'ChangeVariables',
    'IntegrateWithSubstitution',
    'Limit',
    'Series',
    'Sum',
    'Product',
    # Variational calculus
    'VariationalDerivative',
    'EulerLagrangeEquation',
    # Green's functions
    'GreenFunction',
    'GreenFunctionPoisson1D',
    'GreenFunctionHelmholtz1D',
    'GreenFunctionLaplacian3D',
    'GreenFunctionWave1D',
    # Integral transforms
    'FourierTransform',
    'InverseFourierTransform',
    'LaplaceTransform',
    'InverseLaplaceTransform',
    'Convolve',
]
