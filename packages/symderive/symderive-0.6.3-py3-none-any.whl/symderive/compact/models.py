"""
models.py - Compact Model Classes for Optical Devices

Provides classes representing compact models in various forms:
- CompactModel: Base class for all compact models
- RationalModel: Rational function P(s)/Q(s)
- PoleResidueModel: Pole-residue expansion

These models can be evaluated numerically, exported to circuit simulators,
and analyzed for physical properties (stability, passivity, causality).

Internal Refs:
    Uses derive.core.math_api for symbolic operations.
    Uses derive.algebra for polynomial operations.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from symderive.core.math_api import (
    np,
    np_array,
    np_asarray,
    np_zeros,
    Symbol,
    Rational,
    sp,
    sym_lambdify,
    latex,
)


class CompactModel:
    """
    Base class for compact device models.

    A CompactModel represents a closed-form expression for a device's
    frequency response, suitable for circuit simulation.

    Attributes:
        expression: Symbolic expression for the model
        frequency_var: Symbol for frequency variable
        parameters: Dict of model parameters
        metadata: Additional model information

    Examples:
        >>> model = CompactModel(expression, omega)
        >>> model.evaluate(1e9)  # Evaluate at 1 GHz
        >>> model.to_spice()  # Export to SPICE format

    Internal Refs:
        Extended by RationalModel and PoleResidueModel.
    """

    def __init__(
        self,
        expression: Any,
        frequency_var: Optional[Symbol] = None,
        *,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a CompactModel.

        Args:
            expression: Symbolic expression for the transfer function
            frequency_var: Symbol for frequency (default: Symbol('omega'))
            parameters: Dict of named parameters in the expression
            metadata: Additional information (source file, fit quality, etc.)
        """
        if frequency_var is None:
            frequency_var = Symbol('omega')

        self.expression = expression
        self.frequency_var = frequency_var
        self.parameters = parameters or {}
        self.metadata = metadata or {}
        self._numeric_func = None

    def Evaluate(
        self,
        frequency: Any,
        *,
        parameter_values: Optional[Dict[str, float]] = None,
    ) -> Any:
        """
        Evaluate the model at given frequency points.

        Args:
            frequency: Frequency value(s) to evaluate at
            parameter_values: Optional parameter substitutions

        Returns:
            Complex response value(s)

        Examples:
            >>> model.Evaluate(1e9)
            >>> model.Evaluate(np.linspace(1e9, 10e9, 100))
        """
        if self._numeric_func is None:
            self._numeric_func = sym_lambdify(
                self.frequency_var,
                self.expression,
                modules=['numpy'],
            )

        return self._numeric_func(np_asarray(frequency))

    def ToLaTeX(self) -> str:
        """
        Convert model expression to LaTeX string.

        Returns:
            LaTeX representation of the model expression.

        Examples:
            >>> print(model.ToLaTeX())
            \\frac{1}{1 + i \\omega \\tau}
        """
        return latex(self.expression)

    def ToSPICE(
        self,
        name: str = 'H',
        *,
        format: str = 'hspice',
    ) -> str:
        """
        Export model to SPICE subcircuit format.

        Args:
            name: Name for the subcircuit
            format: SPICE dialect ('hspice', 'spectre', 'ngspice')

        Returns:
            SPICE netlist string

        Internal Refs:
            Requires RationalModel or PoleResidueModel for proper export.
        """
        raise TypeError(
            "ToSPICE requires RationalModel or PoleResidueModel. "
            "Use FitCompactModel with model_type='rational' or 'pole_residue'."
        )

    def ToVerilogA(self, name: str = 'compact_model') -> str:
        """
        Export model to Verilog-A format.

        Args:
            name: Module name

        Returns:
            Verilog-A code string

        Internal Refs:
            Requires RationalModel or PoleResidueModel for proper export.
        """
        raise TypeError(
            "ToVerilogA requires RationalModel or PoleResidueModel."
        )

    def __repr__(self) -> str:
        return f"CompactModel({self.expression})"


class RationalModel(CompactModel):
    """
    Rational function model: H(s) = P(s) / Q(s).

    The rational model is a ratio of polynomials in the complex frequency s.
    This is the standard form for linear time-invariant systems.

    Attributes:
        numerator_coeffs: Coefficients [b_m, ..., b_1, b_0] of numerator
        denominator_coeffs: Coefficients [a_n, ..., a_1, a_0] of denominator
        poles: Array of pole locations
        zeros: Array of zero locations
        gain: DC gain or high-frequency gain

    Examples:
        >>> model = RationalModel(
        ...     numerator_coeffs=[1, 0],
        ...     denominator_coeffs=[1, 2, 1],
        ...     frequency_var=s
        ... )
        >>> model.expression  # s / (s^2 + 2*s + 1)

    Internal Refs:
        Created by FitRationalModel.
        Can be converted to PoleResidueModel via ToPoleResidue().
    """

    def __init__(
        self,
        numerator_coeffs: List[float],
        denominator_coeffs: List[float],
        frequency_var: Optional[Symbol] = None,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a RationalModel from polynomial coefficients.

        Args:
            numerator_coeffs: Numerator coefficients [b_m, ..., b_1, b_0]
                (highest degree first)
            denominator_coeffs: Denominator coefficients [a_n, ..., a_1, a_0]
                (highest degree first)
            frequency_var: Symbol for complex frequency (default: Symbol('s'))
            metadata: Additional model information
        """
        if frequency_var is None:
            frequency_var = Symbol('s')

        self.numerator_coeffs = np_array(numerator_coeffs)
        self.denominator_coeffs = np_array(denominator_coeffs)

        # Build symbolic expression
        s = frequency_var
        numerator = sum(
            c * s**i
            for i, c in enumerate(reversed(numerator_coeffs))
        )
        denominator = sum(
            c * s**i
            for i, c in enumerate(reversed(denominator_coeffs))
        )
        expression = numerator / denominator

        super().__init__(
            expression,
            frequency_var,
            metadata=metadata,
        )

        # Compute poles and zeros
        self._poles = None
        self._zeros = None

    @property
    def poles(self) -> Any:
        """Pole locations (roots of denominator)."""
        if self._poles is None:
            self._poles = np.roots(self.denominator_coeffs)
        return self._poles

    @property
    def zeros(self) -> Any:
        """Zero locations (roots of numerator)."""
        if self._zeros is None:
            self._zeros = np.roots(self.numerator_coeffs)
        return self._zeros

    @property
    def n_poles(self) -> int:
        """Number of poles."""
        return len(self.denominator_coeffs) - 1

    @property
    def n_zeros(self) -> int:
        """Number of zeros."""
        return len(self.numerator_coeffs) - 1

    def IsStable(self) -> bool:
        """
        Check if model is stable (all poles in left half-plane).

        Returns:
            True if all poles have negative real part.
        """
        return all(np.real(self.poles) < 0)

    def ToPoleResidue(self) -> 'PoleResidueModel':
        """
        Convert to pole-residue form.

        Returns:
            Equivalent PoleResidueModel.

        Internal Refs:
            Uses partial fraction decomposition via scipy.signal.residue.
        """
        from scipy.signal import residue

        # scipy.signal.residue computes partial fraction expansion
        # r, p, k = residue(b, a) where H(s) = sum(r_i / (s - p_i)) + k(s)
        residues, poles, direct = residue(
            self.numerator_coeffs, self.denominator_coeffs
        )

        # Direct term may be a polynomial, but for proper rational functions it's a scalar
        direct_term = direct[0] if len(direct) > 0 else 0.0

        return PoleResidueModel(
            poles=list(poles),
            residues=list(residues),
            direct_term=direct_term,
            frequency_var=self.frequency_var,
            metadata=self.metadata,
        )

    def ToSPICE(
        self,
        name: str = 'H',
        *,
        format: str = 'hspice',
    ) -> str:
        """
        Export to SPICE Laplace transfer function.

        Args:
            name: Subcircuit name
            format: SPICE dialect ('hspice', 'spectre', 'ngspice')

        Returns:
            SPICE netlist string

        Examples:
            >>> print(model.ToSPICE('filter'))
            .SUBCKT filter in out
            E1 out 0 LAPLACE {V(in)} = {...}
            .ENDS

        Internal Refs:
            Uses numerator_coeffs and denominator_coeffs for polynomial form.
        """
        # Build numerator polynomial string: b_m*s^m + b_{m-1}*s^{m-1} + ... + b_0
        num_terms = []
        for i, coeff in enumerate(self.numerator_coeffs):
            power = len(self.numerator_coeffs) - 1 - i
            if abs(coeff) < 1e-15:
                continue
            if power == 0:
                num_terms.append(f"{coeff:.6g}")
            elif power == 1:
                num_terms.append(f"{coeff:.6g}*s")
            else:
                num_terms.append(f"{coeff:.6g}*s**{power}")

        # Build denominator polynomial string
        den_terms = []
        for i, coeff in enumerate(self.denominator_coeffs):
            power = len(self.denominator_coeffs) - 1 - i
            if abs(coeff) < 1e-15:
                continue
            if power == 0:
                den_terms.append(f"{coeff:.6g}")
            elif power == 1:
                den_terms.append(f"{coeff:.6g}*s")
            else:
                den_terms.append(f"{coeff:.6g}*s**{power}")

        num_str = "+".join(num_terms) if num_terms else "0"
        den_str = "+".join(den_terms) if den_terms else "1"

        if format == 'hspice':
            lines = [
                f".SUBCKT {name} in out",
                f"E1 out 0 LAPLACE {{V(in)}} = {{({num_str})/({den_str})}}",
                ".ENDS",
            ]
        elif format == 'spectre':
            lines = [
                f"subckt {name} (in out)",
                f"E1 (out 0) laplace V(in) ({num_str})/({den_str})",
                "ends",
            ]
        else:  # ngspice or default
            lines = [
                f".SUBCKT {name} in out",
                f"E1 out 0 LAPLACE V(in) = {{({num_str})/({den_str})}}",
                ".ENDS",
            ]

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"RationalModel(n_poles={self.n_poles}, n_zeros={self.n_zeros})"


class PoleResidueModel(CompactModel):
    """
    Pole-residue expansion model.

    H(s) = d + sum_k residue_k / (s - pole_k)

    This form is useful for:
    - Physical interpretation (each pole is a resonance)
    - Stability analysis (poles must be in LHP)
    - Time-domain conversion (exponential terms)

    Attributes:
        poles: Array of pole locations
        residues: Array of residue values
        direct_term: Direct feedthrough term (d)

    Examples:
        >>> model = PoleResidueModel(
        ...     poles=[-1+1j, -1-1j],
        ...     residues=[0.5-0.5j, 0.5+0.5j],
        ...     frequency_var=s
        ... )

    Internal Refs:
        Created by FitCompactModel with model_type='pole_residue'.
        Can be converted from RationalModel via ToPoleResidue().
    """

    def __init__(
        self,
        poles: List[complex],
        residues: List[complex],
        *,
        direct_term: complex = 0.0,
        frequency_var: Optional[Symbol] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a PoleResidueModel.

        Args:
            poles: List of pole locations (complex)
            residues: List of residue values (complex)
            direct_term: Direct feedthrough term
            frequency_var: Symbol for complex frequency (default: Symbol('s'))
            metadata: Additional model information
        """
        if frequency_var is None:
            frequency_var = Symbol('s')

        self._poles = np_array(poles)
        self._residues = np_array(residues)
        self.direct_term = complex(direct_term)

        # Build symbolic expression
        s = frequency_var
        expression = self.direct_term
        for pole, residue in zip(poles, residues):
            expression = expression + residue / (s - pole)

        super().__init__(
            expression,
            frequency_var,
            metadata=metadata,
        )

    @property
    def poles(self) -> Any:
        """Pole locations."""
        return self._poles

    @property
    def residues(self) -> Any:
        """Residue values."""
        return self._residues

    @property
    def n_poles(self) -> int:
        """Number of poles."""
        return len(self._poles)

    def IsStable(self) -> bool:
        """
        Check if model is stable (all poles in left half-plane).

        Returns:
            True if all poles have negative real part.
        """
        return all(np.real(self.poles) < 0)

    def ToRational(self) -> RationalModel:
        """
        Convert to rational function form.

        Returns:
            Equivalent RationalModel.

        Internal Refs:
            Combines partial fractions into single rational function.
            Uses scipy.signal.invres for inverse partial fraction expansion.
        """
        from scipy.signal import invres

        # scipy.signal.invres converts pole-residue form back to polynomial coefficients
        # invres(r, p, k) -> (b, a) where H(s) = b(s) / a(s)
        direct = np_array([self.direct_term]) if self.direct_term != 0 else np_array([])

        num_coeffs, den_coeffs = invres(
            self._residues, self._poles, direct
        )

        return RationalModel(
            numerator_coeffs=list(np.real(num_coeffs)),
            denominator_coeffs=list(np.real(den_coeffs)),
            frequency_var=self.frequency_var,
            metadata=self.metadata,
        )

    def ToTimeDomain(self, t: Optional[Symbol] = None) -> Any:
        """
        Convert to time-domain impulse response.

        h(t) = d*delta(t) + sum_k residue_k * exp(pole_k * t) * u(t)

        where u(t) is the unit step function.

        Args:
            t: Time variable (default: Symbol('t'))

        Returns:
            Symbolic expression for h(t)

        Internal Refs:
            Uses inverse Laplace transform properties.
            Uses sympy.Heaviside for unit step function.
            Uses sympy.DiracDelta for impulse.
        """
        if t is None:
            t = Symbol('t', real=True, positive=True)

        # Build time-domain expression: h(t) = d*delta(t) + sum_k r_k * exp(p_k * t)
        # For causal systems (t >= 0), we use Heaviside step function
        h_t = sp.Integer(0)

        # Add direct term contribution (impulse)
        if abs(self.direct_term) > 1e-15:
            h_t = h_t + self.direct_term * sp.DiracDelta(t)

        # Add pole-residue contributions
        for pole, residue in zip(self._poles, self._residues):
            # Each pole contributes: residue * exp(pole * t) * Heaviside(t)
            h_t = h_t + residue * sp.exp(pole * t) * sp.Heaviside(t)

        return h_t

    def __repr__(self) -> str:
        return f"PoleResidueModel(n_poles={self.n_poles})"


__all__ = [
    'CompactModel',
    'RationalModel',
    'PoleResidueModel',
]
