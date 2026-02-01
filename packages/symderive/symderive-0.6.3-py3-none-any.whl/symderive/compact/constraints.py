"""
constraints.py - Physical Constraints for Compact Models

Implements Kramers-Kronig relations and other causality constraints
that optical response functions must satisfy.

The Kramers-Kronig relations connect the real and imaginary parts of
any causal linear response function:
    Re[chi(omega)] = (1/pi) * P.V. integral Im[chi(omega')] / (omega' - omega) d omega'
    Im[chi(omega)] = -(1/pi) * P.V. integral Re[chi(omega')] / (omega' - omega) d omega'

where P.V. denotes the Cauchy principal value.

Internal Refs:
    Uses derive.calculus for integral transforms.
    Uses derive.core.math_api for numerical operations.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from scipy.signal import hilbert as scipy_hilbert

from symderive.core.math_api import (
    np,
    np_array,
    np_asarray,
    np_zeros,
    np_ones,
    np_linspace,
    np_pi,
    Symbol,
    Integral,
    sp,
    integrate,
    oo,
    sym_lambdify,
)


def KramersKronig(
    chi: Any,
    omega: Any,
    *,
    component: str = 'imaginary',
    omega_vals: Optional[Any] = None,
    method: str = 'auto',
) -> Any:
    """
    Compute Kramers-Kronig transform of a response function.

    KramersKronig[chi, omega] computes the KK transform.
    KramersKronig[chi, omega, component -> 'real'] computes real part from imaginary.

    The Kramers-Kronig relations for a causal response chi(omega):
        Re[chi(omega)] = (1/pi) * P.V. integral_{-inf}^{inf} Im[chi(omega')] / (omega' - omega) d omega'
        Im[chi(omega)] = -(1/pi) * P.V. integral_{-inf}^{inf} Re[chi(omega')] / (omega' - omega) d omega'

    Args:
        chi: Response function (symbolic expression or numerical array)
        omega: Frequency variable (Symbol for symbolic, ignored for numerical)
        component: Which component to compute:
            - 'imaginary': Compute Im[chi] from Re[chi]
            - 'real': Compute Re[chi] from Im[chi]
        omega_vals: Frequency array (required for numerical, ignored for symbolic)
        method: Computation method ('auto', 'symbolic', 'fft', 'direct')

    Returns:
        Symbolic expression or numerical array for the transformed component.

    Examples:
        >>> omega = Symbol('omega', real=True)
        >>> chi_real = 1 / (1 + omega**2)  # Lorentzian
        >>> chi_imag = KramersKronig(chi_real, omega, component='imaginary')

    Internal Refs:
        Uses HilbertTransform internally.
    """
    # Numerical path
    if isinstance(chi, np.ndarray):
        if omega_vals is None:
            raise ValueError("omega_vals required for numerical KK transform")
        return _numerical_kramers_kronig(omega_vals, chi, component, method)

    # Symbolic path
    if not isinstance(omega, Symbol):
        raise ValueError("omega must be a Symbol for symbolic KK transform")

    return _symbolic_kramers_kronig(chi, omega, component)


def _symbolic_kramers_kronig(
    chi: Any,
    omega: Symbol,
    component: str,
) -> Any:
    """
    Symbolic Kramers-Kronig transform.

    Args:
        chi: Symbolic expression for chi (either real or imaginary part)
        omega: Frequency symbol
        component: 'real' or 'imaginary'

    Returns:
        Symbolic expression for the other component

    Internal Refs:
        Helper for KramersKronig.
    """
    omega_prime = Symbol('_omega_prime', real=True)

    # Substitute omega -> omega_prime in the expression
    integrand = chi.subs(omega, omega_prime) / (omega_prime - omega)

    # Compute principal value integral
    result = sp.integrate(integrand, (omega_prime, -oo, oo), principal_value=True)

    # Apply sign convention
    if component == 'imaginary':
        # chi''(omega) = -(1/pi) * P.V. integral chi'(omega') / (omega' - omega) domega'
        return -result / sp.pi
    else:
        # chi'(omega) = (1/pi) * P.V. integral chi''(omega') / (omega' - omega) domega'
        return result / sp.pi


def EnforceKramersKronig(
    model: Any,
    omega: Symbol,
    *,
    tolerance: float = 1e-6,
    method: str = 'project',
    keep_component: str = 'real',
    omega_range: Optional[Tuple[float, float]] = None,
    n_points: int = 1000,
) -> Dict[str, Any]:
    """
    Enforce Kramers-Kronig consistency on a model.

    Given a model that may not satisfy KK relations, project it onto
    the space of causal (KK-consistent) models.

    Args:
        model: Model expression or CompactModel instance
        omega: Frequency variable
        tolerance: Tolerance for KK consistency check
        method: Enforcement method:
            - 'project': Project onto causal subspace
            - 'average': Average measured and KK-derived components
        keep_component: Which component to keep ('real' or 'imaginary')
        omega_range: Frequency range for numerical projection
        n_points: Number of frequency points

    Returns:
        Dict with causal response data and metadata.

    Examples:
        >>> model = FitCompactModel(data, enforce_causality=False)
        >>> causal_model = EnforceKramersKronig(model, omega)

    Internal Refs:
        Uses KramersKronig for the transform.
    """
    # Get numerical values
    if hasattr(model, 'expression'):
        expr = model.expression
        freq_var = model.frequency_var
    else:
        expr = model
        freq_var = omega

    if omega_range is None:
        omega_range = (0.1, 100.0)

    omega_vals = np_linspace(omega_range[0], omega_range[1], n_points)

    f_numeric = sym_lambdify(freq_var, expr, modules=['numpy'])
    chi_complex = f_numeric(omega_vals)

    chi_real = np.real(chi_complex)
    chi_imag = np.imag(chi_complex)

    if method == 'project':
        if keep_component == 'real':
            chi_imag_new = _numerical_kramers_kronig(
                omega_vals, chi_real, component='imaginary'
            )
            chi_causal = chi_real + 1j * chi_imag_new
        else:
            chi_real_new = _numerical_kramers_kronig(
                omega_vals, chi_imag, component='real'
            )
            chi_causal = chi_real_new + 1j * chi_imag

    elif method == 'average':
        # Average original and KK-derived components
        chi_imag_from_real = _numerical_kramers_kronig(
            omega_vals, chi_real, component='imaginary'
        )
        chi_real_from_imag = _numerical_kramers_kronig(
            omega_vals, chi_imag, component='real'
        )

        chi_real_avg = (chi_real + chi_real_from_imag) / 2
        chi_imag_avg = (chi_imag + chi_imag_from_real) / 2
        chi_causal = chi_real_avg + 1j * chi_imag_avg

    else:
        raise ValueError(f"Unknown method: {method}. Supported: 'project', 'average'")

    return {
        'omega': omega_vals,
        'chi': chi_causal,
        'chi_real': np.real(chi_causal),
        'chi_imag': np.imag(chi_causal),
        'original_model': model,
        'method': method,
        'kept_component': keep_component if method == 'project' else 'both',
    }


def CheckCausality(
    model: Any,
    omega: Symbol,
    *,
    omega_range: Optional[Tuple[float, float]] = None,
    n_points: int = 1000,
    tolerance: float = 1e-3,
) -> Dict[str, Any]:
    """
    Check if a model satisfies Kramers-Kronig (causality) relations.

    A causal linear response function must satisfy:
        Im[chi(omega)] = -KK[Re[chi(omega)]]

    This function computes the KK transform and compares.

    Args:
        model: Model expression or CompactModel instance
        omega: Frequency variable
        omega_range: Frequency range (omega_min, omega_max) for numerical check
        n_points: Number of frequency points for numerical evaluation
        tolerance: Relative tolerance for causality check

    Returns:
        Dict with keys:
            'is_causal': Boolean indicating if model is causal
            'max_violation': Maximum relative violation of KK relations
            'violation_frequency': Frequency where max violation occurs
            'rms_violation': RMS violation over frequency range

    Examples:
        >>> result = CheckCausality(model, omega)
        >>> if not result['is_causal']:
        ...     print(f"Model violates causality by {result['max_violation']:.2%}")

    Internal Refs:
        Uses KramersKronig for the transform.
        Uses numerical integration for evaluation.
    """
    # Handle CompactModel objects
    if hasattr(model, 'expression'):
        expr = model.expression
        freq_var = model.frequency_var
    else:
        expr = model
        freq_var = omega

    # Set default frequency range
    if omega_range is None:
        omega_range = (0.1, 100.0)

    # Generate frequency points
    omega_vals = np_linspace(omega_range[0], omega_range[1], n_points)

    # Evaluate model numerically
    f_numeric = sym_lambdify(freq_var, expr, modules=['numpy'])
    chi_complex = f_numeric(omega_vals)

    # Extract real and imaginary parts
    chi_real = np.real(chi_complex)
    chi_imag = np.imag(chi_complex)

    # Compute KK transform: chi'' from chi'
    chi_imag_from_real = _numerical_kramers_kronig(
        omega_vals, chi_real, component='imaginary'
    )

    # Compute violation metrics
    diff = chi_imag - chi_imag_from_real

    # Handle potential zeros in denominator
    chi_imag_abs = np.abs(chi_imag)
    chi_imag_norm = np.where(chi_imag_abs > 1e-10, chi_imag_abs, 1e-10)

    relative_error = np.abs(diff) / chi_imag_norm

    max_violation = float(np.max(relative_error))
    max_violation_idx = int(np.argmax(relative_error))
    max_violation_freq = float(omega_vals[max_violation_idx])

    chi_imag_rms = np.sqrt(np.mean(chi_imag**2))
    if chi_imag_rms > 1e-20:
        rms_violation = float(np.sqrt(np.mean(diff**2)) / chi_imag_rms)
    else:
        rms_violation = 0.0

    # Reconstruction error (L2 norm)
    chi_imag_norm_l2 = np.linalg.norm(chi_imag)
    if chi_imag_norm_l2 > 1e-20:
        reconstruction_error = float(np.linalg.norm(diff) / chi_imag_norm_l2)
    else:
        reconstruction_error = 0.0

    # Determine if causal within tolerance
    is_causal = max_violation < tolerance

    return {
        'is_causal': is_causal,
        'max_violation': max_violation,
        'violation_frequency': max_violation_freq,
        'rms_violation': rms_violation,
        'reconstruction_error': reconstruction_error,
        'omega': omega_vals,
        'chi_imag_measured': chi_imag,
        'chi_imag_kk': chi_imag_from_real,
        'relative_error': relative_error,
    }


def HilbertTransform(
    signal: Any,
    t: Optional[Symbol] = None,
    *,
    method: str = 'auto',
) -> Any:
    """
    Compute the Hilbert transform of a signal.

    The Hilbert transform is related to Kramers-Kronig:
        H[f](t) = (1/pi) * P.V. integral f(tau) / (t - tau) d tau

    For a causal signal, the imaginary part of its Fourier transform
    is the Hilbert transform of the real part.

    Args:
        signal: Input signal (symbolic expression or numerical array)
        t: Time/frequency variable (Symbol)
        method: Computation method:
            - 'auto': Choose automatically based on input type
            - 'symbolic': Use symbolic integration
            - 'fft': Use FFT-based numerical computation

    Returns:
        Hilbert transform of the input signal.

    Examples:
        >>> t = Symbol('t', real=True)
        >>> f = Cos(t)
        >>> Hf = HilbertTransform(f, t)  # Returns Sin(t)

    Internal Refs:
        Used by KramersKronig internally.
        For numerical: uses FFT-based method.
    """
    # Check if numerical array
    if isinstance(signal, np.ndarray):
        return _hilbert_transform_fft(signal)

    # Symbolic path
    if method == 'fft':
        raise ValueError("FFT method requires numerical array input")

    if t is None:
        raise ValueError("Symbol t required for symbolic Hilbert transform")

    return _hilbert_transform_symbolic(signal, t)


def _hilbert_transform_fft(signal: Any) -> Any:
    """
    FFT-based Hilbert transform for numerical data.

    Uses scipy.signal.hilbert which computes the analytic signal,
    then extracts the imaginary part.

    Args:
        signal: Numerical array

    Returns:
        Hilbert transform array

    Internal Refs:
        Helper for HilbertTransform.
    """
    # scipy.signal.hilbert returns the analytic signal: f + i*H[f]
    # We extract the imaginary part to get H[f]
    analytic = scipy_hilbert(signal)
    return np.imag(analytic)


def _hilbert_transform_symbolic(expr: Any, t: Symbol) -> Any:
    """
    Symbolic Hilbert transform using principal value integral.

    H[f](t) = (1/pi) * P.V. integral_{-oo}^{oo} f(tau) / (t - tau) d tau

    Args:
        expr: Symbolic expression
        t: Variable symbol

    Returns:
        Symbolic Hilbert transform

    Internal Refs:
        Helper for HilbertTransform.
    """
    tau = Symbol('_tau', real=True)

    # Substitute t -> tau in the expression
    integrand = expr.subs(t, tau) / (t - tau)

    # Attempt symbolic integration with principal value
    result = sp.integrate(integrand, (tau, -oo, oo), principal_value=True)

    return result / sp.pi


def _numerical_kramers_kronig(
    omega: Any,
    chi_component: Any,
    component: str = 'imaginary',
    method: str = 'auto',
) -> Any:
    """
    Numerical Kramers-Kronig transform using Hilbert transform.

    The KK relations are equivalent to Hilbert transforms:
    - chi'(omega) = H[chi''](omega)  (real from imaginary)
    - chi''(omega) = -H[chi'](omega) (imaginary from real)

    Args:
        omega: Frequency array
        chi_component: Real or imaginary part of chi
        component: Which component to compute ('real' or 'imaginary')
        method: 'auto', 'fft', or 'direct'

    Returns:
        Transformed component array

    Internal Refs:
        Helper for KramersKronig when given numerical data.
        Uses scipy's Hilbert transform for numerical stability.
    """
    chi_component = np_asarray(chi_component)

    # Use Hilbert transform: the KK relations are Hilbert transforms
    hilbert_result = _hilbert_transform_fft(chi_component)

    # Apply sign convention for KK
    if component == 'imaginary':
        # chi''(omega) = -H[chi'](omega)
        return -hilbert_result
    else:
        # chi'(omega) = H[chi''](omega)
        return hilbert_result


def _kk_fft_method(
    omega: Any,
    chi_component: Any,
    component: str,
) -> Any:
    """
    FFT-based Kramers-Kronig transform using Hilbert transform.

    KK relations are essentially Hilbert transforms:
    - chi'(omega) = H[chi''](omega)
    - chi''(omega) = -H[chi'](omega)

    Args:
        omega: Frequency array (must be uniformly spaced)
        chi_component: Input component array
        component: 'real' or 'imaginary'

    Returns:
        Transformed component array

    Internal Refs:
        Helper for _numerical_kramers_kronig.
    """
    # Use scipy's Hilbert transform
    hilbert_result = _hilbert_transform_fft(chi_component)

    # Apply sign convention for KK
    if component == 'imaginary':
        # chi''(omega) = -H[chi'](omega)
        return -hilbert_result
    else:
        # chi'(omega) = H[chi''](omega)
        return hilbert_result


def _check_pole_stability(
    poles: Any,
    tolerance: float = 1e-10,
) -> Tuple[bool, List[Any]]:
    """
    Check if all poles are in the left half-plane (stable/causal).

    For a causal system, all poles must satisfy Re[pole] < 0.

    Args:
        poles: Array of pole locations (complex)
        tolerance: Tolerance for boundary (Re[pole] < tolerance)

    Returns:
        Tuple of (is_stable, unstable_poles)

    Internal Refs:
        Helper for CheckCausality.
        Used by FitRationalModel for stability enforcement.
    """
    poles = np_asarray(poles)
    real_parts = np.real(poles)
    unstable_mask = real_parts >= tolerance
    unstable_poles = poles[unstable_mask].tolist()
    is_stable = len(unstable_poles) == 0
    return is_stable, unstable_poles


__all__ = [
    'KramersKronig',
    'EnforceKramersKronig',
    'CheckCausality',
    'HilbertTransform',
]
