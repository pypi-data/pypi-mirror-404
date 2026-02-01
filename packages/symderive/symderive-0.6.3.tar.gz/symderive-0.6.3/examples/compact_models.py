"""Compact Models: From FDTD Simulation Data to Circuit Models"""

import marimo

__generated_with = "0.19.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt

    from symderive import Symbol, Simplify, Exp, I, Pi
    from symderive.compact import (
        LoadSParameters, LoadSpectrum, LoadTouchstone,
        FitRationalModel, FitCompactModel,
        KramersKronig, CheckCausality, HilbertTransform,
        CompactModel, RationalModel, PoleResidueModel,
    )
    return (
        CheckCausality,
        CompactModel,
        Exp,
        FitCompactModel,
        FitRationalModel,
        HilbertTransform,
        I,
        KramersKronig,
        LoadSParameters,
        LoadSpectrum,
        LoadTouchstone,
        Pi,
        PoleResidueModel,
        RationalModel,
        Simplify,
        Symbol,
        mo,
        np,
        plt,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Compact Models for Photonic Devices

        This notebook demonstrates the `derive.compact` module for converting
        FDTD simulation data and S-parameter measurements into compact symbolic
        models suitable for circuit simulation.

        ## The Pipeline

        ```
        Optical Device Data (S-parameters, spectra)
            |
            v
        [LoadSParameters / LoadSpectrum]  -- Data I/O
            |
            v
        [FitRationalModel / FitCompactModel]  -- Model Fitting
            |
            v
        [KramersKronig / CheckCausality]  -- Physical Constraints
            |
            v
        [RationalModel / PoleResidueModel]  -- Export to SPICE/Verilog-A
        ```
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 1. Synthetic Test Data: Ring Resonator Response

        Let's create synthetic data representing a photonic ring resonator.
        The response has a Lorentzian lineshape with a resonance.
        """
    )
    return


@app.cell
def _(np):
    # Ring resonator parameters
    omega0 = 10.0  # Resonance frequency (normalized)
    gamma = 0.5    # Linewidth (loss rate)
    kappa = 0.3    # Coupling rate

    # Frequency sweep
    omega = np.linspace(1, 20, 500)

    # Complex frequency for Laplace domain
    s = 1j * omega

    # Ring resonator transfer function (all-pass response)
    # H(s) = (s - s0*) / (s - s0) where s0 = -gamma + j*omega0
    s0 = -gamma + 1j * omega0
    H_ring = (s - np.conj(s0)) / (s - s0)

    # Add some noise to simulate measurement
    noise = 0.02 * (np.random.randn(len(omega)) + 1j * np.random.randn(len(omega)))
    H_measured = H_ring + noise
    return H_measured, H_ring, gamma, kappa, noise, omega, omega0, s, s0


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"### Visualize the Ring Resonator Response")
    return


@app.cell
def _(H_measured, H_ring, np, omega, plt):
    import io
    from IPython.display import display, Image

    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Magnitude response
    ax1.plot(omega, 20 * np.log10(np.abs(H_ring)), 'b-', label='Ideal', linewidth=2)
    ax1.plot(omega, 20 * np.log10(np.abs(H_measured)), 'r.', alpha=0.3, label='Measured')
    ax1.set_xlabel('Frequency (normalized)')
    ax1.set_ylabel('|H| (dB)')
    ax1.set_title('Magnitude Response')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Phase response
    ax2.plot(omega, np.angle(H_ring, deg=True), 'b-', label='Ideal', linewidth=2)
    ax2.plot(omega, np.angle(H_measured, deg=True), 'r.', alpha=0.3, label='Measured')
    ax2.set_xlabel('Frequency (normalized)')
    ax2.set_ylabel('Phase (degrees)')
    ax2.set_title('Phase Response')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    _buf1 = io.BytesIO()
    fig1.savefig(_buf1, format='png', dpi=100, bbox_inches='tight')
    _buf1.seek(0)
    display(Image(_buf1.read()))
    plt.close(fig1)
    return ax1, ax2, fig1


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 2. Model Fitting with Vector Fitting

        The `FitRationalModel` function uses the Gustavsen-Semlyen vector fitting
        algorithm to find a rational function approximation:

        $$H(s) = \frac{b_m s^m + \cdots + b_1 s + b_0}{a_n s^n + \cdots + a_1 s + a_0}$$

        This is equivalent to finding poles and residues for a partial fraction expansion.
        """
    )
    return


@app.cell
def _(FitRationalModel, H_measured, omega):
    # Fit a rational model with 2 poles (matches our ring resonator)
    model_rational = FitRationalModel(omega, H_measured, n_poles=2)

    print(f"Fitted RationalModel:")
    print(f"  Number of poles: {model_rational.n_poles}")
    print(f"  Number of zeros: {model_rational.n_zeros}")
    print(f"  Poles: {model_rational.poles}")
    print(f"  Zeros: {model_rational.zeros}")
    print(f"  Stable: {model_rational.IsStable()}")
    return (model_rational,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"### Compare Fitted Model to Original Data")
    return


@app.cell
def _(H_measured, H_ring, model_rational, np, omega, plt):
    import io
    from IPython.display import display, Image

    # Evaluate the fitted model
    s_eval = 1j * omega
    H_fitted = model_rational.Evaluate(s_eval)

    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(12, 4))

    # Magnitude comparison
    ax3.plot(omega, 20 * np.log10(np.abs(H_ring)), 'b-', label='Ideal', linewidth=2)
    ax3.plot(omega, 20 * np.log10(np.abs(H_measured)), 'r.', alpha=0.2, label='Measured')
    ax3.plot(omega, 20 * np.log10(np.abs(H_fitted)), 'g--', label='Fitted', linewidth=2)
    ax3.set_xlabel('Frequency (normalized)')
    ax3.set_ylabel('|H| (dB)')
    ax3.set_title('Magnitude: Fitted vs Original')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Phase comparison
    ax4.plot(omega, np.angle(H_ring, deg=True), 'b-', label='Ideal', linewidth=2)
    ax4.plot(omega, np.angle(H_measured, deg=True), 'r.', alpha=0.2, label='Measured')
    ax4.plot(omega, np.angle(H_fitted, deg=True), 'g--', label='Fitted', linewidth=2)
    ax4.set_xlabel('Frequency (normalized)')
    ax4.set_ylabel('Phase (degrees)')
    ax4.set_title('Phase: Fitted vs Original')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    _buf2 = io.BytesIO()
    fig2.savefig(_buf2, format='png', dpi=100, bbox_inches='tight')
    _buf2.seek(0)
    display(Image(_buf2.read()))
    plt.close(fig2)
    return H_fitted, ax3, ax4, fig2, s_eval


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 3. Convert to Pole-Residue Form

        The pole-residue form is useful for physical interpretation and time-domain analysis:

        $$H(s) = d + \sum_k \frac{r_k}{s - p_k}$$

        Each pole $p_k$ represents a resonance mode, and the residue $r_k$ gives its strength.
        """
    )
    return


@app.cell
def _(model_rational):
    # Convert to pole-residue form
    model_pr = model_rational.ToPoleResidue()

    print(f"PoleResidueModel:")
    print(f"  Poles: {model_pr.poles}")
    print(f"  Residues: {model_pr.residues}")
    print(f"  Direct term: {model_pr.direct_term}")
    print(f"  Stable: {model_pr.IsStable()}")
    return (model_pr,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 4. Time-Domain Impulse Response

        The pole-residue form directly gives the time-domain impulse response:

        $$h(t) = d \cdot \delta(t) + \sum_k r_k \cdot e^{p_k t} \cdot u(t)$$

        where $u(t)$ is the Heaviside step function.
        """
    )
    return


@app.cell
def _(Simplify, model_pr):
    # Get symbolic time-domain expression
    h_t = model_pr.ToTimeDomain()
    print("Time-domain impulse response:")
    print(f"  h(t) = {Simplify(h_t)}")
    return (h_t,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 5. Export to SPICE

        The `ToSPICE` method generates a SPICE subcircuit using the Laplace transfer function:
        """
    )
    return


@app.cell
def _(model_rational):
    # Generate SPICE netlist
    spice_netlist = model_rational.ToSPICE('ring_resonator', format='hspice')
    print("HSPICE Netlist:")
    print("-" * 40)
    print(spice_netlist)
    print("-" * 40)

    # Also show Spectre format
    spectre_netlist = model_rational.ToSPICE('ring_resonator', format='spectre')
    print("\nSpectre Netlist:")
    print("-" * 40)
    print(spectre_netlist)
    return spectre_netlist, spice_netlist


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 6. Kramers-Kronig Relations and Causality

        Physical systems must satisfy the Kramers-Kronig relations, which connect
        the real and imaginary parts of a causal response function:

        $$\text{Re}[\chi(\omega)] = \frac{1}{\pi} \mathcal{P} \int_{-\infty}^{\infty} \frac{\text{Im}[\chi(\omega')]}{\omega' - \omega} d\omega'$$

        Let's verify causality for a Lorentzian susceptibility.
        """
    )
    return


@app.cell
def _(KramersKronig, np):
    # Lorentzian absorption (imaginary part of susceptibility)
    omega_kk = np.linspace(0.1, 30, 500)
    omega0_kk = 10.0
    gamma_kk = 1.0

    # Imaginary part: Lorentzian peak
    chi_imag = gamma_kk / ((omega_kk - omega0_kk)**2 + gamma_kk**2)

    # Analytic real part (for comparison)
    chi_real_analytic = (omega_kk - omega0_kk) / ((omega_kk - omega0_kk)**2 + gamma_kk**2)

    # Compute real part from imaginary using Kramers-Kronig
    chi_real_kk = KramersKronig(chi_imag, None, component='real', omega_vals=omega_kk)

    print("Kramers-Kronig transform computed")
    print(f"  Input: Lorentzian absorption peak at omega = {omega0_kk}")
    print(f"  Output: Dispersion curve (real part of susceptibility)")
    return chi_imag, chi_real_analytic, chi_real_kk, gamma_kk, omega0_kk, omega_kk


@app.cell
def _(chi_imag, chi_real_analytic, chi_real_kk, omega0_kk, omega_kk, plt):
    import io
    from IPython.display import display, Image

    fig3, (ax5, ax6) = plt.subplots(1, 2, figsize=(12, 4))

    # Imaginary part (absorption)
    ax5.plot(omega_kk, chi_imag, 'b-', linewidth=2)
    ax5.axvline(omega0_kk, color='gray', linestyle='--', alpha=0.5)
    ax5.set_xlabel('Frequency')
    ax5.set_ylabel("Im[chi]")
    ax5.set_title('Lorentzian Absorption')
    ax5.grid(True, alpha=0.3)

    # Real part (dispersion) - compare KK to analytic
    ax6.plot(omega_kk, chi_real_analytic, 'b-', label='Analytic', linewidth=2)
    ax6.plot(omega_kk, chi_real_kk, 'r--', label='Kramers-Kronig', linewidth=2)
    ax6.axvline(omega0_kk, color='gray', linestyle='--', alpha=0.5)
    ax6.axhline(0, color='gray', linestyle='-', alpha=0.3)
    ax6.set_xlabel('Frequency')
    ax6.set_ylabel("Re[chi]")
    ax6.set_title('Dispersion: Analytic vs KK')
    ax6.legend()
    ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    _buf3 = io.BytesIO()
    fig3.savefig(_buf3, format='png', dpi=100, bbox_inches='tight')
    _buf3.seek(0)
    display(Image(_buf3.read()))
    plt.close(fig3)
    return ax5, ax6, fig3


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 7. Causality Check for Fitted Model

        We can verify that our fitted model satisfies causality constraints:
        """
    )
    return


@app.cell
def _(CheckCausality, CompactModel, I, Symbol, model_rational):
    # Create a CompactModel from our rational model's expression
    # The RationalModel uses s (complex Laplace frequency) as its variable.
    # To check causality, we need to transform to the omega domain: s = j*omega
    s_var = model_rational.frequency_var  # Symbol('s')
    omega_check = Symbol('omega', real=True)
    expression_omega = model_rational.expression.subs(s_var, I * omega_check)
    compact = CompactModel(expression_omega, omega_check)

    # Check causality
    causality_result = CheckCausality(
        compact,
        omega_check,
        omega_range=(1.0, 20.0),
        n_points=200
    )

    print("Causality Check Results:")
    print(f"  Is causal: {causality_result['is_causal']}")
    print(f"  Max violation: {causality_result['max_violation']:.4f}")
    print(f"  RMS violation: {causality_result['rms_violation']:.4f}")
    return causality_result, compact, omega_check


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 8. High-Level API: FitCompactModel

        For convenience, `FitCompactModel` provides a unified interface that accepts
        various data formats and returns the appropriate model type:
        """
    )
    return


@app.cell
def _(FitCompactModel, H_measured, omega):
    # Using dict format (like LoadSpectrum output)
    data_dict = {
        'frequency': omega,
        'response': H_measured
    }

    # Fit and get a PoleResidueModel directly
    model_auto = FitCompactModel(
        data_dict,
        model_type='pole_residue',
        max_poles=4
    )

    print(f"FitCompactModel result: {model_auto}")
    print(f"  Poles: {model_auto.poles}")
    print(f"  Stable: {model_auto.IsStable()}")
    return data_dict, model_auto


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Summary

        The `derive.compact` module provides a complete pipeline for:

        1. **Data I/O**: Load S-parameters (Touchstone) and optical spectra (CSV)
        2. **Model Fitting**: Vector fitting algorithm for rational function approximation
        3. **Physical Constraints**: Kramers-Kronig relations and causality verification
        4. **Model Export**: SPICE netlists, Verilog-A, time-domain expressions

        This enables seamless integration of FDTD simulation results into circuit-level
        photonic design workflows.
        """
    )
    return


if __name__ == "__main__":
    app.run()
