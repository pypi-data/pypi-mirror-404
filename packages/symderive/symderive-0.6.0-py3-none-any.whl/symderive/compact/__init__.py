"""
compact - FDTD Compact Model Generation

Converts optical device simulation data (spectra, S-parameters) into closed-form
symbolic compact models with physical constraint enforcement.

Workflow:
    1. Load simulation data (LoadSParameters, LoadSpectrum)
    2. Fit symbolic model (FitCompactModel)
    3. Enforce causality via Kramers-Kronig (EnforceKramersKronig)
    4. Export compact model (CompactModel)

Internal Refs:
    Uses derive.regression.FindFormula for symbolic regression.
    Uses derive.calculus for Kramers-Kronig integral transforms.
"""

from symderive.compact.io import LoadSParameters, LoadSpectrum, LoadTouchstone
from symderive.compact.regression import FitCompactModel, FitRationalModel
from symderive.compact.constraints import (
    KramersKronig,
    EnforceKramersKronig,
    CheckCausality,
    HilbertTransform,
)
from symderive.compact.models import CompactModel, RationalModel, PoleResidueModel

__all__ = [
    # Data I/O
    'LoadSParameters',
    'LoadSpectrum',
    'LoadTouchstone',
    # Fitting
    'FitCompactModel',
    'FitRationalModel',
    # Physical constraints
    'KramersKronig',
    'EnforceKramersKronig',
    'CheckCausality',
    'HilbertTransform',
    # Model classes
    'CompactModel',
    'RationalModel',
    'PoleResidueModel',
]
