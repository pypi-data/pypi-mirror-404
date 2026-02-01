"""
Discretization module - Convert symbolic derivatives to finite difference stencils.

Provides tools for discretizing variational derivatives and generating
numerical simulation code in multiple programming languages.
"""

from symderive.discretization.stencils import (
    Discretize,
    Discretizer,
    ToStencil,
    StencilCodeGen,
    FiniteDiffWeights,
    Stencil,
)

__all__ = [
    'Discretize',
    'Discretizer',
    'ToStencil',
    'StencilCodeGen',
    'FiniteDiffWeights',
    'Stencil',
]
