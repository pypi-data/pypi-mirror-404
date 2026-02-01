"""
io.py - Data Ingestion for FDTD/Optical Simulation Results

Provides functions to load S-parameter data, optical spectra, and
Touchstone files commonly used in photonic device characterization.

Args (common):
    file_path: Path to data file
    format: File format ('csv', 'touchstone', 'json', etc.)

Returns:
    Structured data suitable for compact model fitting.

Internal Refs:
    Uses derive.core.math_api for NumPy operations.
    Uses derive.data.Import for generic file loading.
"""

import itertools
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from symderive.core.math_api import (
    np,
    np_array,
    np_asarray,
    np_linspace,
    np_zeros,
    np_concatenate,
    np_pi,
)


def LoadSParameters(
    file_path: str,
    *,
    format: Optional[str] = None,
    ports: Optional[List[int]] = None,
    frequency_unit: str = 'Hz',
    parameter_format: str = 'RI',
) -> Dict[str, Any]:
    """
    Load S-parameter data from simulation or measurement files.

    LoadSParameters[file] loads S-parameters from file.
    LoadSParameters[file, ports -> {1, 2}] loads only specified ports.

    Args:
        file_path: Path to S-parameter file (.s2p, .s4p, .csv, etc.)
        format: File format (auto-detected from extension if None)
        ports: List of port indices to load (default: all)
        frequency_unit: Unit for frequency data ('Hz', 'GHz', 'THz')
        parameter_format: S-parameter format ('RI' for real/imag, 'MA' for mag/angle, 'DB' for dB/angle)

    Returns:
        Dict with keys:
            'frequency': Array of frequency points
            'S': Dict of S-parameter arrays keyed by (i,j) tuples
            'n_ports': Number of ports
            'metadata': Additional file metadata

    Examples:
        >>> data = LoadSParameters('device.s2p')
        >>> data['S'][(1,1)]  # S11 complex array
        >>> data['frequency']  # Frequency array

    Internal Refs:
        Uses derive.compact.io.LoadTouchstone for .snp files.
    """
    # Auto-detect format from extension if not specified
    extension = file_path.lower().split('.')[-1]

    if format is None:
        if re.match(r's\d+p', extension):
            format = 'touchstone'
        elif extension == 'csv':
            format = 'csv'
        else:
            format = 'touchstone'  # Default to touchstone

    if format == 'touchstone':
        # Use LoadTouchstone for .snp files
        ts_data = LoadTouchstone(file_path)

        # Convert frequency to requested unit
        frequency = _convert_frequency_unit(ts_data['frequency'], 'Hz', frequency_unit)

        # Convert S matrix to dict format keyed by (i, j) tuples (1-indexed)
        n_ports = ts_data['n_ports']
        s_dict = {}
        port_indices = itertools.product(range(n_ports), range(n_ports))
        for row, col in port_indices:
            s_dict[(row + 1, col + 1)] = ts_data['S'][:, row, col]

        # Filter ports if specified
        if ports is not None:
            s_dict = {k: v for k, v in s_dict.items() if k[0] in ports and k[1] in ports}

        return {
            'frequency': frequency,
            'S': s_dict,
            'n_ports': n_ports,
            'metadata': {
                'Z0': ts_data['Z0'],
                'format': ts_data['format'],
                'comments': ts_data['comments'],
                'source_file': file_path,
            },
        }

    raise ValueError(
        f"Format '{format}' is not supported. "
        "Supported formats: touchstone (.s1p, .s2p, .s4p, etc.)"
    )


def LoadSpectrum(
    file_path: str,
    *,
    format: Optional[str] = None,
    wavelength_unit: str = 'nm',
    data_type: str = 'transmission',
) -> Dict[str, Any]:
    """
    Load optical spectrum data from simulation or measurement.

    LoadSpectrum[file] loads transmission/reflection spectrum.
    LoadSpectrum[file, data_type -> 'reflection'] loads reflection data.

    Args:
        file_path: Path to spectrum file (.csv, .txt, .json)
        format: File format (auto-detected from extension if None)
        wavelength_unit: Unit for wavelength ('nm', 'um', 'm')
        data_type: Type of spectrum ('transmission', 'reflection', 'absorption', 'phase')

    Returns:
        Dict with keys:
            'wavelength': Array of wavelength points
            'frequency': Array of frequency points (computed from wavelength)
            'data': Complex spectrum data (or real if phase not available)
            'data_type': Type of loaded data
            'metadata': Additional file metadata

    Examples:
        >>> spec = LoadSpectrum('ring_resonator.csv')
        >>> spec['wavelength']  # Wavelength array in nm
        >>> spec['data']  # Transmission values

    Internal Refs:
        Uses standard Python file I/O for CSV loading.
    """
    # Auto-detect format from extension if not specified
    extension = file_path.lower().split('.')[-1]

    if format is None:
        if extension in ('csv', 'txt', 'dat'):
            format = 'csv'
        elif extension == 'json':
            format = 'json'
        else:
            format = 'csv'  # Default to CSV

    if format == 'csv':
        # Parse CSV file
        # Expected format: wavelength, magnitude [, phase]
        # First line may be header (if non-numeric)
        wavelengths = []
        magnitudes = []
        phases = []
        has_phase = False
        metadata = {'header': None, 'source_file': file_path}

        with open(file_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Try comma, then whitespace as delimiter
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
            else:
                parts = line.split()

            # Check if this is a header line (non-numeric first column)
            try:
                wl = float(parts[0])
            except ValueError:
                # This is a header line
                metadata['header'] = parts
                continue

            wavelengths.append(wl)
            magnitudes.append(float(parts[1]))
            if len(parts) > 2:
                phases.append(float(parts[2]))
                has_phase = True

        wavelength_arr = np_array(wavelengths)
        magnitude_arr = np_array(magnitudes)

        # Convert to complex if phase data available
        if has_phase:
            phase_arr = np_array(phases)
            # Assume phase is in degrees
            data = magnitude_arr * np.exp(1j * phase_arr * np_pi / 180.0)
        else:
            data = magnitude_arr

        # Compute frequency from wavelength
        frequency = _wavelength_to_frequency(wavelength_arr, wavelength_unit)

        return {
            'wavelength': wavelength_arr,
            'frequency': frequency,
            'data': data,
            'data_type': data_type,
            'metadata': metadata,
        }

    raise ValueError(
        f"Format '{format}' is not supported. "
        "Supported formats: csv, txt"
    )


def LoadTouchstone(
    file_path: str,
    *,
    version: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Load Touchstone format S-parameter files (.s1p, .s2p, .s4p, etc.).

    Touchstone is the industry-standard format for S-parameter data.
    Supports both Touchstone 1.0 and 2.0 formats.

    Args:
        file_path: Path to Touchstone file
        version: Touchstone version (1 or 2, auto-detected if None)

    Returns:
        Dict with keys:
            'frequency': Array of frequency points (Hz)
            'S': Complex S-parameter matrix [n_freq, n_ports, n_ports]
            'Z0': Reference impedance (default 50 ohms)
            'n_ports': Number of ports
            'comments': List of comment lines from file
            'format': Original data format ('RI', 'MA', 'DB')

    Examples:
        >>> data = LoadTouchstone('filter.s2p')
        >>> S21 = data['S'][:, 1, 0]  # S21 vs frequency

    Internal Refs:
        Called by LoadSParameters for .snp files.
    """
    # Determine number of ports from file extension
    extension = file_path.lower().split('.')[-1]
    match = re.match(r's(\d+)p', extension)
    if match:
        n_ports = int(match.group(1))
    else:
        raise ValueError(f"Cannot determine port count from extension: {extension}")

    comments = []
    data_lines = []
    option_line = None

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('!'):
                comments.append(line[1:].strip())
            elif line.startswith('#'):
                option_line = line
            else:
                data_lines.append(line)

    # Parse option line: # [freq_unit] [param_type] [format] [R ref_impedance]
    # Default: # GHz S MA R 50
    freq_unit = 'GHz'
    param_format = 'MA'
    z0 = 50.0

    if option_line:
        header = _parse_touchstone_header([option_line])
        freq_unit = header.get('freq_unit', freq_unit)
        param_format = header.get('format', param_format)
        z0 = header.get('Z0', z0)

    # Parse data lines
    # Each frequency point has n_ports^2 S-parameters
    # Format: freq S11_r S11_i S21_r S21_i ... for RI format
    # For 2+ ports, data may span multiple lines
    all_values = []
    for line in data_lines:
        values = [float(x) for x in line.split()]
        all_values.extend(values)

    # Calculate number of values per frequency point
    # Each S-parameter has 2 values (real/imag or mag/phase)
    n_sparams = n_ports * n_ports
    values_per_freq = 1 + n_sparams * 2  # freq + S-param data

    n_freq = len(all_values) // values_per_freq
    if n_freq * values_per_freq != len(all_values):
        raise ValueError(
            f"Data length {len(all_values)} not divisible by values per frequency "
            f"point {values_per_freq} for {n_ports}-port network"
        )

    # Reshape into frequency points
    all_values = np_array(all_values).reshape(n_freq, values_per_freq)

    frequency = all_values[:, 0]
    s_data = all_values[:, 1:]

    # Convert frequency to Hz
    frequency = _convert_frequency_unit(frequency, freq_unit, 'Hz')

    # Convert S-parameter format to complex
    s_complex = np_zeros((n_freq, n_ports, n_ports), dtype=complex)

    for i, (row, col) in itertools.product(range(n_freq), itertools.product(range(n_ports), range(n_ports))):
        idx = (row * n_ports + col) * 2
        val1 = s_data[i, idx]
        val2 = s_data[i, idx + 1]

        if param_format == 'RI':
            s_complex[i, row, col] = val1 + 1j * val2
        elif param_format == 'MA':
            # Magnitude and angle (degrees)
            mag = val1
            ang_rad = val2 * np_pi / 180.0
            s_complex[i, row, col] = mag * np.exp(1j * ang_rad)
        elif param_format == 'DB':
            # dB magnitude and angle (degrees)
            mag = 10 ** (val1 / 20.0)
            ang_rad = val2 * np_pi / 180.0
            s_complex[i, row, col] = mag * np.exp(1j * ang_rad)
        else:
            raise ValueError(f"Unknown S-parameter format: {param_format}")

    return {
        'frequency': frequency,
        'S': s_complex,
        'Z0': z0,
        'n_ports': n_ports,
        'comments': comments,
        'format': param_format,
    }


def _parse_touchstone_header(lines: List[str]) -> Dict[str, Any]:
    """
    Parse Touchstone file header to extract format information.

    Args:
        lines: List of lines containing option line(s)

    Returns:
        Dict with 'freq_unit', 'format', 'Z0' keys

    Internal Refs:
        Helper for LoadTouchstone.
    """
    result = {
        'freq_unit': 'GHz',
        'format': 'MA',
        'Z0': 50.0,
    }

    # Filter to only option lines and concatenate all tokens
    option_lines = [line.strip() for line in lines if line.strip().startswith('#')]
    if not option_lines:
        return result

    # Parse just the first option line (standard Touchstone has only one)
    tokens = option_lines[0][1:].upper().split()

    unit_map = {'HZ': 'Hz', 'KHZ': 'kHz', 'MHZ': 'MHz', 'GHZ': 'GHz', 'THZ': 'THz'}

    # Find frequency unit
    freq_units = [unit_map[t] for t in tokens if t in unit_map]
    if freq_units:
        result['freq_unit'] = freq_units[0]

    # Find parameter format
    formats = [t for t in tokens if t in ('RI', 'MA', 'DB')]
    if formats:
        result['format'] = formats[0]

    # Find reference impedance (token after 'R')
    r_indices = [i for i, t in enumerate(tokens) if t == 'R']
    if r_indices and r_indices[0] + 1 < len(tokens):
        try:
            result['Z0'] = float(tokens[r_indices[0] + 1])
        except ValueError:
            pass

    return result


def _convert_frequency_unit(
    frequency: Any,
    from_unit: str,
    to_unit: str = 'Hz',
) -> Any:
    """
    Convert frequency array between units.

    Args:
        frequency: Frequency array
        from_unit: Source unit ('Hz', 'kHz', 'MHz', 'GHz', 'THz')
        to_unit: Target unit (default 'Hz')

    Returns:
        Converted frequency array

    Internal Refs:
        Helper for LoadSParameters and LoadSpectrum.
    """
    unit_factors = {
        'Hz': 1.0,
        'kHz': 1e3,
        'MHz': 1e6,
        'GHz': 1e9,
        'THz': 1e12,
    }

    if from_unit not in unit_factors or to_unit not in unit_factors:
        raise ValueError(f"Unknown frequency unit: {from_unit} or {to_unit}")

    scale = unit_factors[from_unit] / unit_factors[to_unit]
    return np_asarray(frequency) * scale


def _wavelength_to_frequency(
    wavelength: Any,
    wavelength_unit: str = 'nm',
) -> Any:
    """
    Convert wavelength to frequency.

    Args:
        wavelength: Wavelength array
        wavelength_unit: Unit ('nm', 'um', 'm')

    Returns:
        Frequency array in Hz

    Internal Refs:
        Helper for LoadSpectrum.
        Uses c = 299792458 m/s.
    """
    c = 299792458.0  # speed of light in m/s

    unit_factors = {
        'nm': 1e-9,
        'um': 1e-6,
        'm': 1.0,
    }

    if wavelength_unit not in unit_factors:
        raise ValueError(f"Unknown wavelength unit: {wavelength_unit}")

    wavelength_m = np_asarray(wavelength) * unit_factors[wavelength_unit]
    return c / wavelength_m


__all__ = [
    'LoadSParameters',
    'LoadSpectrum',
    'LoadTouchstone',
]
