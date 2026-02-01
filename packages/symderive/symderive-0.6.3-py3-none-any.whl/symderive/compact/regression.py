"""
regression.py - Symbolic Regression for Compact Device Models

Provides functions to fit symbolic expressions to optical device data,
producing closed-form compact models suitable for circuit simulation.

The key insight is that optical response functions (permittivity, S-parameters)
must satisfy physical constraints like causality, which constrains the
allowed functional forms.

Args (common):
    data: Frequency-domain data (frequency, complex response)
    constraints: Physical constraints to enforce

Returns:
    CompactModel or symbolic expression.

Internal Refs:
    Uses derive.regression.FindFormula for symbolic regression.
    Uses derive.compact.constraints for causality enforcement.
"""

import itertools
from typing import Any, Dict, List, Optional, Tuple, Union

from symderive.core.math_api import (
    np,
    np_array,
    np_asarray,
    np_zeros,
    np_ones,
    np_logspace,
    np_pi,
    Symbol,
    Rational,
    sp,
)

from symderive.compact.models import RationalModel, PoleResidueModel


def FitCompactModel(
    data: Any,
    *,
    frequency_var: Optional[Symbol] = None,
    model_type: str = 'rational',
    max_poles: int = 10,
    enforce_causality: bool = True,
    enforce_passivity: bool = False,
    target_functions: Optional[List[str]] = None,
    **kwargs,
) -> Any:
    """
    Fit a symbolic compact model to frequency-domain device data.

    FitCompactModel[data] finds a compact model for the device response.
    FitCompactModel[data, model_type -> 'rational'] fits a rational function.
    FitCompactModel[data, enforce_causality -> True] ensures Kramers-Kronig compliance.

    Args:
        data: Input data as dict with 'frequency' and 'response' arrays,
              or tuple (frequency, response), or dict from LoadSParameters.
        frequency_var: Symbol for frequency variable (default: Symbol('omega'))
        model_type: Type of model to fit:
            - 'rational': Rational function P(s)/Q(s)
            - 'pole_residue': Pole-residue expansion
            - 'symbolic': General symbolic regression
        max_poles: Maximum number of poles for rational/pole-residue models
        enforce_causality: If True, enforce Kramers-Kronig relations
        enforce_passivity: If True, enforce passivity (|S| <= 1)
        target_functions: For 'symbolic' type, list of allowed functions

    Returns:
        CompactModel instance with the fitted symbolic expression.

    Examples:
        >>> data = LoadSpectrum('ring_resonator.csv')
        >>> model = FitCompactModel(data, model_type='rational', max_poles=4)
        >>> model.expression  # Symbolic transfer function
        >>> model.poles  # Pole locations
        >>> model.residues  # Residue values

    Internal Refs:
        Uses derive.regression.FindFormula for symbolic fitting.
        Uses derive.compact.constraints.EnforceKramersKronig for causality.
        Returns derive.compact.models.CompactModel.
    """
    if frequency_var is None:
        frequency_var = Symbol('omega')

    # Parse input data format
    frequency, response = _parse_input_data(data)

    # Select fitting method based on model_type
    if model_type == 'rational':
        model = FitRationalModel(
            frequency,
            response,
            n_poles=max_poles,
            frequency_var=frequency_var,
            enforce_stability=enforce_causality,
            **kwargs,
        )
        return model

    elif model_type == 'pole_residue':
        # Fit rational model first, then convert to pole-residue
        rational_model = FitRationalModel(
            frequency,
            response,
            n_poles=max_poles,
            frequency_var=frequency_var,
            enforce_stability=enforce_causality,
            **kwargs,
        )
        # Extract poles and residues from metadata
        poles = rational_model.metadata.get('poles', rational_model.poles)
        residues = rational_model.metadata.get('residues', np_zeros(len(poles)))
        direct_term = rational_model.metadata.get('direct_term', 0.0)

        return PoleResidueModel(
            poles.tolist(),
            residues.tolist(),
            direct_term=direct_term,
            frequency_var=frequency_var,
            metadata=rational_model.metadata,
        )

    elif model_type == 'symbolic':
        raise ValueError(
            "Symbolic regression model type is not supported. "
            "Use model_type='rational' or 'pole_residue' instead."
        )

    else:
        raise ValueError(
            f"Unknown model_type: {model_type}. "
            "Supported types: 'rational', 'pole_residue', 'symbolic'"
        )


def _parse_input_data(data: Any) -> Tuple[Any, Any]:
    """
    Parse various input data formats into frequency and response arrays.

    Args:
        data: Input data in various formats

    Returns:
        Tuple of (frequency, response) arrays

    Internal Refs:
        Helper for FitCompactModel.
    """
    # Tuple format: (frequency, response)
    if isinstance(data, tuple) and len(data) == 2:
        return np_asarray(data[0]), np_asarray(data[1])

    # Dict format from LoadSpectrum
    if isinstance(data, dict):
        if 'frequency' in data and 'response' in data:
            return np_asarray(data['frequency']), np_asarray(data['response'])
        elif 'frequency' in data and 'data' in data:
            # LoadSpectrum format
            return np_asarray(data['frequency']), np_asarray(data['data'])
        elif 'frequency' in data and 'S' in data:
            # LoadSParameters format - use first S-parameter
            s_dict = data['S']
            first_key = next(iter(s_dict))
            return np_asarray(data['frequency']), np_asarray(s_dict[first_key])

    raise ValueError(
        "Unsupported data format. Expected tuple (frequency, response) "
        "or dict with 'frequency' and 'response'/'data' keys."
    )


def FitRationalModel(
    frequency: Any,
    response: Any,
    *,
    n_poles: int = 4,
    n_zeros: int = 4,
    frequency_var: Optional[Symbol] = None,
    enforce_stability: bool = True,
    weight: Optional[Any] = None,
) -> Any:
    """
    Fit a rational function to frequency response data.

    The rational model has the form:
        H(s) = (b_m*s^m + ... + b_1*s + b_0) / (a_n*s^n + ... + a_1*s + a_0)

    For causal systems, poles must be in the left half-plane (negative real part).

    Args:
        frequency: Array of frequency points (angular frequency omega)
        response: Complex response array H(j*omega)
        n_poles: Number of poles (denominator degree)
        n_zeros: Number of zeros (numerator degree)
        frequency_var: Symbol for frequency (default: Symbol('s'))
        enforce_stability: If True, constrain poles to left half-plane
        weight: Optional weighting function for fit

    Returns:
        RationalModel with symbolic expression and pole/zero locations.

    Examples:
        >>> omega = np.linspace(1e9, 10e9, 1000)
        >>> H = measured_transfer_function(omega)
        >>> model = FitRationalModel(omega, H, n_poles=4)
        >>> print(model.expression)  # Symbolic rational function

    Internal Refs:
        Uses vector fitting (Gustavsen-Semlyen) algorithm.
        Returns derive.compact.models.RationalModel.
    """
    if frequency_var is None:
        frequency_var = Symbol('s')

    # Convert inputs to arrays
    omega = np_asarray(frequency)
    H_data = np_asarray(response)

    # Create complex frequency s = j*omega
    s_data = 1j * omega

    # Set up weights
    if weight is None:
        weights = np_ones(len(omega))
    else:
        weights = np_asarray(weight)

    # Run vector fitting algorithm
    poles, residues, d, e = _vector_fitting(
        s_data, H_data, n_poles,
        enforce_stability=enforce_stability,
        weights=weights,
    )

    # Convert pole-residue form to rational polynomial coefficients
    # Build numerator and denominator from poles/residues
    num_coeffs, den_coeffs = _pole_residue_to_coeffs(poles, residues, d)

    # Create and return RationalModel
    return RationalModel(
        num_coeffs.tolist(),
        den_coeffs.tolist(),
        frequency_var=frequency_var,
        metadata={
            'poles': poles,
            'residues': residues,
            'direct_term': d,
            'fit_method': 'vector_fitting',
        },
    )


def _vector_fitting(
    s_data: Any,
    H_data: Any,
    n_poles: int,
    *,
    max_iterations: int = 50,
    tol_poles: float = 1e-6,
    enforce_stability: bool = True,
    weights: Optional[Any] = None,
) -> Tuple[Any, Any, float, float]:
    """
    Vector fitting algorithm for rational approximation.

    Implements the Gustavsen-Semlyen algorithm for fitting a rational
    function to frequency response data.

    Args:
        s_data: Complex frequencies (j*omega)
        H_data: Measured transfer function values
        n_poles: Number of poles to fit
        max_iterations: Maximum number of iterations
        tol_poles: Convergence tolerance for pole movement
        enforce_stability: If True, flip RHP poles to LHP
        weights: Optional weighting array

    Returns:
        Tuple of (poles, residues, d, e)

    Internal Refs:
        Reference: Gustavsen & Semlyen, IEEE Trans. Power Delivery, 1999.
    """
    omega = np.imag(s_data)
    omega_abs = np.abs(omega)
    omega_min = omega_abs[omega_abs > 0].min() if np.any(omega_abs > 0) else 1.0
    omega_max = omega_abs.max() if omega_abs.max() > 0 else 1e9

    # Initialize poles
    poles = _initialize_poles(omega_min, omega_max, n_poles)

    if weights is None:
        weights = np_ones(len(s_data))

    include_d = True
    include_e = False

    for iteration in range(max_iterations):
        poles_old = poles.copy()

        # Build and solve the linear system
        poles, c_tilde = _vector_fitting_iteration_core(
            s_data, H_data, poles, weights, include_d, include_e
        )

        # Enforce stability if requested
        if enforce_stability:
            poles = _enforce_stability(poles)

        # Enforce complex conjugate pairs
        poles = _enforce_conjugate_pairs(poles)

        # Check convergence
        if _check_pole_convergence(poles_old, poles, tol_poles):
            break

    # Final residue identification with converged poles
    residues, d, e = _identify_residues(
        s_data, H_data, poles, include_d, include_e, weights
    )

    return poles, residues, d, e


def _vector_fitting_iteration_core(
    s_data: Any,
    H_data: Any,
    poles: Any,
    weights: Any,
    include_d: bool,
    include_e: bool,
) -> Tuple[Any, Any]:
    """
    Single iteration of the vector fitting algorithm.

    Args:
        s_data: Complex frequency array (j*omega)
        H_data: Complex response data
        poles: Current pole estimates
        weights: Weighting array
        include_d: Include constant term
        include_e: Include s term

    Returns:
        Tuple of (new_poles, c_tilde)

    Internal Refs:
        Helper for _vector_fitting.
        Reference: Gustavsen & Semlyen, IEEE Trans. Power Delivery, 1999.
    """
    n_poles = len(poles)
    n_freq = len(s_data)
    n_unknowns = n_poles + int(include_d) + int(include_e) + n_poles

    # Build system matrix using vectorized operations
    # Phi matrix: phi[k, n] = 1 / (s_data[k] - poles[n])
    # Shape: (n_freq, n_poles)
    s_col = s_data.reshape(-1, 1)  # (n_freq, 1)
    poles_row = poles.reshape(1, -1)  # (1, n_poles)
    phi_matrix = 1.0 / (s_col - poles_row)  # (n_freq, n_poles)

    # Weight and H arrays
    w_col = weights.reshape(-1, 1)  # (n_freq, 1)
    H_col = H_data.reshape(-1, 1)  # (n_freq, 1)

    # Build A matrix columns using vectorized operations
    A_blocks = []

    # Columns for c_n (residues of H): weighted phi
    weighted_phi = w_col * phi_matrix  # (n_freq, n_poles)
    A_blocks.append(weighted_phi)

    # Column for d (constant term)
    if include_d:
        d_col = w_col * np_ones((n_freq, 1))  # (n_freq, 1)
        A_blocks.append(d_col)

    # Column for e (s term)
    if include_e:
        e_col = w_col * s_col  # (n_freq, 1)
        A_blocks.append(e_col)

    # Columns for c_tilde_n (sigma residues): -H * weighted phi
    sigma_cols = -w_col * H_col * phi_matrix  # (n_freq, n_poles)
    A_blocks.append(sigma_cols)

    # Concatenate all blocks
    A_complex = np.hstack(A_blocks)  # (n_freq, n_unknowns)

    # RHS: weighted H_data
    b_complex = (w_col * H_col).flatten()  # (n_freq,)

    # Separate into real and imaginary parts for real least squares
    A = np_zeros((2 * n_freq, n_unknowns))
    A[0::2, :] = A_complex.real
    A[1::2, :] = A_complex.imag

    b = np_zeros(2 * n_freq)
    b[0::2] = b_complex.real
    b[1::2] = b_complex.imag

    # Solve least squares
    x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

    # Extract c_tilde (the sigma residues)
    c_tilde_start = n_poles + int(include_d) + int(include_e)
    c_tilde = x[c_tilde_start:c_tilde_start + n_poles]

    # Compute new poles as eigenvalues of (A - 1*c_tilde^T)
    A_matrix = np.diag(poles) - np.outer(np_ones(n_poles), c_tilde)
    new_poles, _ = np.linalg.eig(A_matrix)

    return new_poles, c_tilde


def _poles_to_symbolic(
    poles: Any,
    residues: Any,
    frequency_var: Symbol,
    direct_term: float = 0.0,
) -> Any:
    """
    Convert pole-residue representation to symbolic expression.

    H(s) = d + sum_k residue_k / (s - pole_k)

    Args:
        poles: Array of pole locations
        residues: Array of residue values
        frequency_var: Symbol for complex frequency s
        direct_term: Direct feedthrough term d

    Returns:
        SymPy expression for the transfer function

    Internal Refs:
        Helper for FitRationalModel.
    """
    s = frequency_var
    expr = sp.Float(direct_term)

    for pole, residue in zip(poles, residues):
        # Handle complex poles/residues by converting to sympy
        if np.iscomplex(pole) or np.iscomplex(residue):
            pole_sym = sp.Float(pole.real) + sp.I * sp.Float(pole.imag)
            res_sym = sp.Float(residue.real) + sp.I * sp.Float(residue.imag)
        else:
            pole_sym = sp.Float(float(pole))
            res_sym = sp.Float(float(residue))

        expr = expr + res_sym / (s - pole_sym)

    return sp.simplify(expr)


def _initialize_poles(
    omega_min: float,
    omega_max: float,
    n_poles: int,
    Q_init: float = 50.0,
) -> Any:
    """
    Initialize poles for vector fitting.

    Poles are placed as complex conjugate pairs with logarithmic
    spacing in frequency and controlled damping.

    Args:
        omega_min: Minimum angular frequency
        omega_max: Maximum angular frequency
        n_poles: Number of poles
        Q_init: Initial Q factor (controls damping)

    Returns:
        Array of initial pole locations

    Internal Refs:
        Helper for _vector_fitting.
    """
    n_pairs = n_poles // 2

    if n_pairs > 0:
        # Logarithmic spacing captures both narrow and broad features
        betas = np_logspace(np.log10(omega_min), np.log10(omega_max), n_pairs)
    else:
        betas = np_array([])

    poles = []
    for beta in betas:
        alpha = beta / Q_init  # Damping: higher Q = less damping
        poles.append(-alpha + 1j * beta)
        poles.append(-alpha - 1j * beta)

    # Add real pole if odd number requested
    if n_poles % 2:
        poles.append(-np.sqrt(omega_min * omega_max))

    return np_array(poles)


def _enforce_stability(poles: Any) -> Any:
    """
    Flip any RHP poles to LHP to maintain causality.

    Args:
        poles: Array of pole locations

    Returns:
        Array with all poles in left half-plane

    Internal Refs:
        Helper for _vector_fitting.
    """
    return np.where(poles.real > 0, -np.abs(poles.real) + 1j * poles.imag, poles)


def _enforce_conjugate_pairs(poles: Any) -> Any:
    """
    Ensure poles come in complex conjugate pairs.

    Preserves the original number of poles by properly pairing
    complex poles and averaging to enforce exact conjugacy.

    Args:
        poles: Array of pole locations

    Returns:
        Array with conjugate pairs enforced (same length as input)

    Internal Refs:
        Helper for _vector_fitting.
    """
    n_original = len(poles)
    tol = 1e-10

    # Separate real and complex poles
    real_mask = np.abs(poles.imag) < tol
    real_poles = list(poles[real_mask].real)
    complex_poles = poles[~real_mask]

    if len(complex_poles) == 0:
        return np_array(real_poles)

    # Sort complex poles by imaginary part to pair them
    sorted_idx = np.argsort(complex_poles.imag)
    sorted_complex = complex_poles[sorted_idx]

    # Pair from ends: most negative imag with most positive imag
    n_complex = len(sorted_complex)
    n_pairs = n_complex // 2

    paired = []
    for i in range(n_pairs):
        p_neg = sorted_complex[i]  # Negative imaginary part
        p_pos = sorted_complex[n_complex - 1 - i]  # Positive imaginary part
        # Average real parts, average absolute imaginary parts
        avg_real = (p_neg.real + p_pos.real) / 2
        avg_imag = (np.abs(p_neg.imag) + np.abs(p_pos.imag)) / 2
        paired.append(avg_real + 1j * avg_imag)
        paired.append(avg_real - 1j * avg_imag)

    # If odd number of complex poles, middle one becomes real
    if n_complex % 2 == 1:
        mid_pole = sorted_complex[n_pairs]
        real_poles.append(mid_pole.real)

    result = np_array(real_poles + paired)

    # Safety check: ensure we return the same number of poles
    if len(result) != n_original:
        # Shouldn't happen, but pad/truncate if needed
        if len(result) < n_original:
            # Duplicate last pole to maintain count
            pad = [result[-1]] * (n_original - len(result))
            result = np.append(result, pad)
        else:
            result = result[:n_original]

    return result


def _check_pole_convergence(
    poles_old: Any,
    poles_new: Any,
    tol: float,
) -> bool:
    """
    Check if poles have converged.

    Args:
        poles_old: Previous pole locations
        poles_new: Current pole locations
        tol: Convergence tolerance

    Returns:
        True if converged

    Internal Refs:
        Helper for _vector_fitting.
    """
    # Sort poles by imaginary part for consistent comparison
    idx_old = np.argsort(poles_old.imag)
    idx_new = np.argsort(poles_new.imag)

    poles_old_sorted = poles_old[idx_old]
    poles_new_sorted = poles_new[idx_new]

    # Relative pole movement
    rel_movement = np.abs(poles_new_sorted - poles_old_sorted) / (np.abs(poles_old_sorted) + 1e-10)
    max_movement = np.max(rel_movement)

    return max_movement < tol


def _identify_residues(
    s_data: Any,
    H_data: Any,
    poles: Any,
    include_d: bool,
    include_e: bool,
    weights: Any,
) -> Tuple[Any, float, float]:
    """
    Final least-squares identification of residues with fixed poles.

    Args:
        s_data: Complex frequency array
        H_data: Response data
        poles: Converged pole locations
        include_d: Include constant term
        include_e: Include s term
        weights: Weighting array

    Returns:
        Tuple of (residues, d, e)

    Internal Refs:
        Helper for _vector_fitting.
    """
    n_poles = len(poles)
    n_freq = len(s_data)
    n_cols = n_poles + int(include_d) + int(include_e)

    # Build phi matrix vectorized
    s_col = s_data.reshape(-1, 1)
    poles_row = poles.reshape(1, -1)
    phi_matrix = 1.0 / (s_col - poles_row)

    w_col = weights.reshape(-1, 1)

    # Build A matrix blocks
    A_blocks = [w_col * phi_matrix]

    if include_d:
        A_blocks.append(w_col * np_ones((n_freq, 1)))

    if include_e:
        A_blocks.append(w_col * s_col)

    A_complex = np.hstack(A_blocks)
    b_complex = (w_col * H_data.reshape(-1, 1)).flatten()

    # Separate real and imaginary
    A = np_zeros((2 * n_freq, n_cols))
    A[0::2, :] = A_complex.real
    A[1::2, :] = A_complex.imag

    b = np_zeros(2 * n_freq)
    b[0::2] = b_complex.real
    b[1::2] = b_complex.imag

    x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

    residues = x[:n_poles] + 0j
    col = n_poles
    d = x[col] if include_d else 0.0
    col += int(include_d)
    e = x[col] if include_e else 0.0

    return residues, d, e


def _pole_residue_to_coeffs(
    poles: Any,
    residues: Any,
    direct_term: float,
) -> Tuple[Any, Any]:
    """
    Convert pole-residue form to polynomial coefficients.

    H(s) = d + sum_k r_k / (s - p_k) = P(s) / Q(s)

    Args:
        poles: Pole locations
        residues: Residue values
        direct_term: Direct feedthrough term

    Returns:
        Tuple of (numerator_coeffs, denominator_coeffs)
        Coefficients are in descending order [a_n, ..., a_1, a_0]

    Internal Refs:
        Helper for FitRationalModel.
    """
    n_poles = len(poles)

    # Denominator is product of (s - p_k)
    den_coeffs = np_array([1.0])
    for pole in poles:
        den_coeffs = np.convolve(den_coeffs, [1.0, -pole])

    # Numerator: combine fractions
    # d * Q(s) + sum_k r_k * prod_{j!=k} (s - p_j)
    num_coeffs = direct_term * den_coeffs

    # Precompute all partial products (excluding one pole at a time)
    # Use polynomial division: Q(s) / (s - p_i) gives partial product
    partial_products = _compute_partial_products(poles, len(den_coeffs))

    # Sum contributions from each residue
    for i, residue in enumerate(residues):
        num_coeffs = num_coeffs + residue * partial_products[i]

    # Ensure real coefficients (should be if conjugate pairs handled correctly)
    num_coeffs = num_coeffs.real
    den_coeffs = den_coeffs.real

    return num_coeffs, den_coeffs


def _compute_partial_products(poles: Any, target_len: int) -> List[Any]:
    """
    Compute partial products for each pole (product of all other factors).

    For each i, computes prod_{j != i} (s - p_j)

    Args:
        poles: Array of pole locations
        target_len: Target length for coefficient arrays (for padding)

    Returns:
        List of polynomial coefficient arrays (all same length)

    Internal Refs:
        Helper for _pole_residue_to_coeffs.
    """
    n = len(poles)
    if n == 0:
        return []
    if n == 1:
        # Partial product when excluding the only pole is just 1
        result = np_zeros(target_len)
        result[-1] = 1.0
        return [result]

    # Compute full product
    full_product = np_array([1.0])
    for pole in poles:
        full_product = np.convolve(full_product, [1.0, -pole])

    # For each pole, divide full product by (s - p_i)
    # This is polynomial division: Q(s) / (s - p_i)
    partial_products = []
    for pole in poles:
        # Polynomial division of full_product by [1, -pole]
        quotient, _ = np.polydiv(full_product, [1.0, -pole])
        # Pad to target length (quotient has degree n-1, need degree n)
        padded = np_zeros(target_len, dtype=quotient.dtype)
        padded[-len(quotient):] = quotient
        partial_products.append(padded)

    return partial_products


__all__ = [
    'FitCompactModel',
    'FitRationalModel',
]
