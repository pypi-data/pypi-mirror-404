"""Variational Derivatives to Numerical Stencils: Inflation Simulations

Based on arXiv:1608.04408 - "Robustness of Inflation to Inhomogeneous Initial Conditions"
by Clough, Lim, DiNunno, Fischler, Flauger, and Paban.

This notebook demonstrates how to:
1. Derive equations of motion from Lagrangians using variational calculus
2. Convert symbolic PDEs to finite difference stencils
3. Generate code for numerical simulations in multiple languages
"""

import marimo

__generated_with = "0.19.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from symderive import (
        Symbol, symbols, Function, Rational, R,
        D, Simplify, Expand,
        Exp, Sin, Cos, Sqrt, Pi,
        TeXForm, Pipe,
    )
    from symderive.calculus import VariationalDerivative, EulerLagrangeEquation
    from symderive.discretization import Discretize, ToStencil, StencilCodeGen
    from symderive.diffgeo import Metric, minkowski_metric
    return (
        D,
        Discretize,
        EulerLagrangeEquation,
        Expand,
        Function,
        Metric,
        Pipe,
        R,
        Rational,
        Simplify,
        StencilCodeGen,
        Sqrt,
        Symbol,
        TeXForm,
        ToStencil,
        VariationalDerivative,
        minkowski_metric,
        mo,
        symbols,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # From Lagrangians to Numerical Stencils

    This notebook demonstrates the complete pipeline from theoretical physics to
    numerical simulation code, based on the scalar field dynamics in
    [arXiv:1608.04408](https://arxiv.org/abs/1608.04408).

    ## The Physics

    Single-field inflation uses a scalar field with canonical kinetic term:

    $$\mathcal{L}_\phi = -\frac{1}{2}g^{\mu\nu}\partial_\mu \phi \partial_\nu\phi - V(\phi)$$

    The Klein-Gordon equation governing the field dynamics is:

    $$\partial_t^2 \phi - \gamma^{ij}\partial_i\partial_j\phi + \frac{dV}{d\phi} = 0$$

    We will derive this equation using variational calculus, then convert it to
    finite difference form suitable for numerical simulation.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Deriving the Klein-Gordon Equation

    Starting from the scalar field Lagrangian density in flat spacetime:

    $$\mathcal{L} = \frac{1}{2}(\partial_t\phi)^2 - \frac{1}{2}(\partial_x\phi)^2 - V(\phi)$$

    The Euler-Lagrange equation gives us the equation of motion.
    """)
    return


@app.cell
def _(D, Function, R, Simplify, Symbol, VariationalDerivative, mo, symbols):
    # Define coordinates and field
    x, t = symbols('x t')
    phi = Function('phi')(x, t)
    m = Symbol('m', positive=True)  # mass parameter

    # Klein-Gordon Lagrangian: L = (1/2)(d_t phi)^2 - (1/2)(d_x phi)^2 - (1/2)m^2 phi^2
    L_KG = R(1, 2) * D(phi, t)**2 - R(1, 2) * D(phi, x)**2 - R(1, 2) * m**2 * phi**2

    # Derive the equation of motion
    eom_KG = VariationalDerivative(L_KG, phi, [x, t])

    mo.md(f"""
    **Klein-Gordon Lagrangian:**

    $\\mathcal{{L}} = {L_KG}$

    **Equation of Motion** ($\\delta\\mathcal{{L}}/\\delta\\phi = 0$):

    ${Simplify(eom_KG)} = 0$

    This is the Klein-Gordon equation: $\\partial_t^2\\phi - \\partial_x^2\\phi + m^2\\phi = 0$
    """)
    return L_KG, eom_KG, m, phi, t, x


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. The Wave Equation (Massless Limit)

    Setting $m = 0$ gives the wave equation, which appears in the gradient energy
    dominated regime of inflation simulations.
    """)
    return


@app.cell
def _(D, Function, R, Simplify, VariationalDerivative, mo, symbols):
    # Wave equation (massless Klein-Gordon)
    x_w, t_w = symbols('x t')
    phi_w = Function('phi')(x_w, t_w)

    L_wave = R(1, 2) * D(phi_w, t_w)**2 - R(1, 2) * D(phi_w, x_w)**2

    eom_wave = VariationalDerivative(L_wave, phi_w, [x_w, t_w])

    mo.md(f"""
    **Wave Equation Lagrangian:**

    $\\mathcal{{L}} = {L_wave}$

    **Equation of Motion:**

    ${Simplify(eom_wave)} = 0$

    This gives: $\\partial_t^2\\phi = \\partial_x^2\\phi$ (the wave equation)
    """)
    return L_wave, eom_wave, phi_w, t_w, x_w


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Converting to Finite Differences

    For numerical simulation, we need to discretize the spatial derivatives.
    The `Discretize` function converts symbolic derivatives to finite difference
    approximations using Taylor series matching.

    ### Central Difference Stencils

    For a 3-point central difference:
    - First derivative: $\frac{\partial f}{\partial x} \approx \frac{f(x+h) - f(x-h)}{2h}$
    - Second derivative: $\frac{\partial^2 f}{\partial x^2} \approx \frac{f(x+h) - 2f(x) + f(x-h)}{h^2}$
    """)
    return


@app.cell
def _(D, Discretize, Function, Simplify, Symbol, mo):
    # Discretization example
    x_d = Symbol('x')
    h = Symbol('h')  # grid spacing
    f = Function('f')(x_d)

    # Second derivative
    d2f_dx2 = D(f, (x_d, 2))

    # Central difference discretization
    stencil_3pt = Discretize(d2f_dx2, {x_d: ([x_d - h, x_d, x_d + h], h)})

    mo.md(f"""
    **Second Derivative Discretization (3-point central):**

    Symbolic: $\\frac{{\\partial^2 f}}{{\\partial x^2}}$

    Discretized: ${Simplify(stencil_3pt)}$

    This is the standard 3-point stencil: $\\frac{{f_{{i+1}} - 2f_i + f_{{i-1}}}}{{h^2}}$
    """)
    return d2f_dx2, f, h, stencil_3pt, x_d


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Discretizing the Wave Equation

    Now let's discretize the full wave equation for numerical simulation.
    """)
    return


@app.cell
def _(D, Discretize, Function, Simplify, mo, symbols):
    # Full wave equation discretization
    x_full, t_full = symbols('x t')
    hx, ht = symbols('h_x h_t')  # spatial and temporal grid spacing
    u = Function('u')(x_full, t_full)

    # Wave equation: d^2u/dt^2 - d^2u/dx^2 = 0
    wave_eq = D(u, (t_full, 2)) - D(u, (x_full, 2))

    # Discretize both derivatives
    step_map = {
        x_full: ([x_full - hx, x_full, x_full + hx], hx),
        t_full: ([t_full - ht, t_full, t_full + ht], ht),
    }
    wave_discrete = Discretize(wave_eq, step_map)

    mo.md(f"""
    **Wave Equation:**

    $\\frac{{\\partial^2 u}}{{\\partial t^2}} - \\frac{{\\partial^2 u}}{{\\partial x^2}} = 0$

    **Discretized Form:**

    ${Simplify(wave_discrete)} = 0$

    Rearranging for time-stepping: $u(x, t+h_t) = 2u(x,t) - u(x, t-h_t) + \\frac{{h_t^2}}{{h_x^2}}[u(x+h_x,t) - 2u(x,t) + u(x-h_x,t)]$
    """)
    return ht, hx, step_map, t_full, u, wave_discrete, wave_eq, x_full


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Higher-Order Stencils

    For better accuracy, we can use wider stencils. The `ToStencil` function
    automatically generates symmetric stencil points.
    """)
    return


@app.cell
def _(D, Function, Simplify, Symbol, ToStencil, mo):
    # Higher-order stencils
    x_ho = Symbol('x')
    h_ho = Symbol('h')
    f_ho = Function('f')(x_ho)

    # Compare 3-point and 5-point stencils for first derivative
    df_dx = D(f_ho, x_ho)

    stencil_3 = ToStencil(df_dx, {x_ho: h_ho}, width=3)
    stencil_5 = ToStencil(df_dx, {x_ho: h_ho}, width=5)

    mo.md(f"""
    **First Derivative Stencils:**

    3-point: ${Simplify(stencil_3)}$

    5-point: ${Simplify(stencil_5)}$

    The 5-point stencil provides 4th-order accuracy vs 2nd-order for 3-point.
    """)
    return df_dx, f_ho, h_ho, stencil_3, stencil_5, x_ho


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Code Generation

    The `StencilCodeGen` function converts discretized expressions to code
    in multiple programming languages - useful for generating numerical
    relativity simulation code.
    """)
    return


@app.cell
def _(D, Discretize, Function, StencilCodeGen, Symbol, mo):
    # Code generation example
    x_cg = Symbol('x')
    h_cg = Symbol('h')
    phi_cg = Function('phi')(x_cg)

    # Second derivative stencil
    d2phi = D(phi_cg, (x_cg, 2))
    stencil_cg = Discretize(d2phi, {x_cg: ([x_cg - h_cg, x_cg, x_cg + h_cg], h_cg)})

    # Generate code in different languages
    python_code = StencilCodeGen(stencil_cg, language='python',
                                  array_name='phi', index_var='i', spacing_name='dx')
    c_code = StencilCodeGen(stencil_cg, language='c',
                            array_name='phi', index_var='i', spacing_name='dx')
    fortran_code = StencilCodeGen(stencil_cg, language='fortran',
                                   array_name='phi', index_var='i', spacing_name='dx')
    latex_code = StencilCodeGen(stencil_cg, language='latex')

    mo.md(f"""
    **Code Generation for** $\\partial^2\\phi/\\partial x^2$:

    **Python:**
    ```python
    d2phi_dx2 = {python_code}
    ```

    **C:**
    ```c
    double d2phi_dx2 = {c_code};
    ```

    **Fortran:**
    ```fortran
    d2phi_dx2 = {fortran_code}
    ```

    **LaTeX:**
    ${latex_code}$
    """)
    return (
        c_code,
        d2phi,
        fortran_code,
        h_cg,
        latex_code,
        phi_cg,
        python_code,
        stencil_cg,
        x_cg,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7. Complete Pipeline: Lagrangian to Simulation Code

    Using symderive's `Pipe` API, we can chain the entire workflow.
    """)
    return


@app.cell
def _(
    D,
    Discretize,
    Function,
    Pipe,
    R,
    StencilCodeGen,
    Symbol,
    VariationalDerivative,
    mo,
    symbols,
):
    # Complete pipeline example
    x_pipe, t_pipe = symbols('x t')
    h_pipe = Symbol('h')
    psi = Function('psi')(x_pipe, t_pipe)

    # Lagrangian for massless scalar field (1D)
    L_pipe = R(1, 2) * D(psi, t_pipe)**2 - R(1, 2) * D(psi, x_pipe)**2

    # Pipeline: Lagrangian -> EoM -> Discretize spatial part
    eom_spatial = (
        Pipe(L_pipe)
        .then(VariationalDerivative, psi, [x_pipe, t_pipe])
        .then(Discretize, {x_pipe: ([x_pipe - h_pipe, x_pipe, x_pipe + h_pipe], h_pipe)})
        .value
    )

    # Generate simulation code
    sim_code = StencilCodeGen(eom_spatial, language='python',
                               array_name='psi', index_var='i', spacing_name='dx')

    mo.md(f"""
    **Complete Pipeline:**

    1. Start with Lagrangian: $\\mathcal{{L}} = {L_pipe}$

    2. Derive equation of motion via variational derivative

    3. Discretize spatial derivatives

    4. Generate Python code:

    ```python
    # Equation of motion (set to zero and solve for time evolution)
    eom = {sim_code}
    ```

    This can be directly used in a time-stepping numerical scheme!
    """)
    return L_pipe, eom_spatial, h_pipe, psi, sim_code, t_pipe, x_pipe


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8. Application: Initial Conditions from arXiv:1608.04408

    The paper uses inhomogeneous initial conditions for the scalar field:

    $$\phi(t=0, \mathbf{x}) = \phi_0 + \frac{\Delta\phi}{N}\sum_{n=1}^{N}\left(\cos\frac{2\pi nx}{L} + \cos\frac{2\pi ny}{L} + \cos\frac{2\pi nz}{L}\right)$$

    With initial velocity:
    $$\frac{\partial\phi(t=0, \mathbf{x})}{\partial t} = 0$$

    The gradient energy density is:
    $$\rho_{\mathrm{grad}} = \frac{1}{2}\gamma^{ij}\partial_i\phi\partial_j\phi$$

    Let's compute the discretized gradient energy.
    """)
    return


@app.cell
def _(D, Discretize, Function, R, Simplify, Symbol, mo):
    # Gradient energy density discretization
    x_grad = Symbol('x')
    h_grad = Symbol('h')
    phi_grad = Function('phi')(x_grad)

    # Gradient energy: (1/2)(d phi/dx)^2
    rho_grad = R(1, 2) * D(phi_grad, x_grad)**2

    # Discretize
    rho_grad_discrete = Discretize(rho_grad, {x_grad: ([x_grad - h_grad, x_grad, x_grad + h_grad], h_grad)})

    mo.md(f"""
    **Gradient Energy Density (1D):**

    Continuous: $\\rho_{{\\mathrm{{grad}}}} = \\frac{{1}}{{2}}\\left(\\frac{{\\partial\\phi}}{{\\partial x}}\\right)^2$

    Discretized: $\\rho_{{\\mathrm{{grad}}}} = {Simplify(rho_grad_discrete)}$

    This uses the central difference approximation for the first derivative.
    """)
    return h_grad, phi_grad, rho_grad, rho_grad_discrete, x_grad


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 9. Multi-Dimensional Stencils: The 3D Laplacian

    Numerical relativity simulations operate in 3D. The spatial Laplacian
    appears in the Hamiltonian constraint and evolution equations:

    $$\nabla^2 \phi = \frac{\partial^2\phi}{\partial x^2} + \frac{\partial^2\phi}{\partial y^2} + \frac{\partial^2\phi}{\partial z^2}$$

    Each term uses the standard second derivative stencil.
    """)
    return


@app.cell
def _(D, Discretize, Function, Simplify, StencilCodeGen, mo, symbols):
    # 3D Laplacian
    x_3d, y_3d, z_3d = symbols('x y z')
    hx_3d, hy_3d, hz_3d = symbols('h_x h_y h_z')
    phi_3d = Function('phi')(x_3d, y_3d, z_3d)

    # Laplacian in 3D
    laplacian_3d = D(phi_3d, (x_3d, 2)) + D(phi_3d, (y_3d, 2)) + D(phi_3d, (z_3d, 2))

    # Discretize with uniform spacing h
    h_uniform = symbols('h')
    step_map_3d = {
        x_3d: ([x_3d - h_uniform, x_3d, x_3d + h_uniform], h_uniform),
        y_3d: ([y_3d - h_uniform, y_3d, y_3d + h_uniform], h_uniform),
        z_3d: ([z_3d - h_uniform, z_3d, z_3d + h_uniform], h_uniform),
    }
    laplacian_discrete = Discretize(laplacian_3d, step_map_3d)

    # Generate C code for the stencil
    c_laplacian = StencilCodeGen(
        Discretize(D(phi_3d, (x_3d, 2)), {x_3d: ([x_3d - h_uniform, x_3d, x_3d + h_uniform], h_uniform)}),
        language='c', array_name='phi', index_var='i', spacing_name='dx'
    )

    mo.md(f"""
    **3D Laplacian Stencil:**

    Continuous: $\\nabla^2\\phi = {laplacian_3d}$

    Discretized (uniform grid $h$): ${Simplify(laplacian_discrete)}$

    This is the classic 7-point stencil used in numerical relativity codes.

    **C code for one dimension** (repeat for j, k indices):
    ```c
    d2phi_dx2 = {c_laplacian};
    ```
    """)
    return (
        c_laplacian, h_uniform, hx_3d, hy_3d, hz_3d,
        laplacian_3d, laplacian_discrete, phi_3d,
        step_map_3d, x_3d, y_3d, z_3d,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 10. Stencil Accuracy: 2nd vs 4th vs 6th Order

    Higher-order stencils use more points but converge faster.
    The truncation error scales as $O(h^n)$ where $n$ is the accuracy order.

    | Order | Points | Error Scaling | Use Case |
    |-------|--------|---------------|----------|
    | 2nd   | 3      | $O(h^2)$      | Simple problems, quick tests |
    | 4th   | 5      | $O(h^4)$      | Production simulations |
    | 6th   | 7      | $O(h^6)$      | High-precision work |
    | 8th   | 9      | $O(h^8)$      | Spectral-like accuracy |
    """)
    return


@app.cell
def _(D, Function, Simplify, Symbol, ToStencil, mo):
    # Compare stencil orders for second derivative
    x_ord = Symbol('x')
    h_ord = Symbol('h')
    f_ord = Function('f')(x_ord)

    d2f = D(f_ord, (x_ord, 2))

    stencil_2nd = ToStencil(d2f, {x_ord: h_ord}, width=3)
    stencil_4th = ToStencil(d2f, {x_ord: h_ord}, width=5)
    stencil_6th = ToStencil(d2f, {x_ord: h_ord}, width=7)

    mo.md(f"""
    **Second Derivative Stencils by Order:**

    **2nd order (3-point):**
    ${Simplify(stencil_2nd)}$

    **4th order (5-point):**
    ${Simplify(stencil_4th)}$

    **6th order (7-point):**
    ${Simplify(stencil_6th)}$

    Note how higher-order stencils have smaller coefficients on the outer points,
    reducing numerical dispersion.
    """)
    return d2f, f_ord, h_ord, stencil_2nd, stencil_4th, stencil_6th, x_ord


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 11. Mixed Derivatives and Cross Terms

    The BSSN formulation of general relativity includes mixed partial derivatives
    like $\partial_x\partial_y\phi$. These require 2D stencils.
    """)
    return


@app.cell
def _(D, Discretize, Function, Simplify, mo, symbols):
    # Mixed derivative
    x_mix, y_mix = symbols('x y')
    h_mix = symbols('h')
    phi_mix = Function('phi')(x_mix, y_mix)

    # Mixed partial derivative
    d2_dxdy = D(D(phi_mix, x_mix), y_mix)

    # 9-point stencil for mixed derivative
    step_map_mix = {
        x_mix: ([x_mix - h_mix, x_mix, x_mix + h_mix], h_mix),
        y_mix: ([y_mix - h_mix, y_mix, y_mix + h_mix], h_mix),
    }
    mixed_stencil = Discretize(d2_dxdy, step_map_mix)

    mo.md(f"""
    **Mixed Partial Derivative:**

    Continuous: $\\frac{{\\partial^2\\phi}}{{\\partial x\\partial y}}$

    Discretized: ${Simplify(mixed_stencil)}$

    This is the standard 4-corner stencil:
    ```
    (-1)-----(0)-----(+1)
      |       |       |
    (+1)    (0,0)   (+1)
      |       |       |
    (-1)-----(0)-----(+1)
    ```
    Only the four corners contribute (with alternating signs).
    """)
    return d2_dxdy, h_mix, mixed_stencil, phi_mix, step_map_mix, x_mix, y_mix


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 12. The ADM Evolution Equations

    In numerical relativity, the ADM (Arnowitt-Deser-Misner) formalism evolves
    the 3-metric $\gamma_{ij}$ and extrinsic curvature $K_{ij}$:

    $$\partial_t \gamma_{ij} = -2\alpha K_{ij} + \mathcal{L}_\beta \gamma_{ij}$$

    $$\partial_t K_{ij} = -D_i D_j \alpha + \alpha(R_{ij} + K K_{ij} - 2K_{ik}K^k{}_j) + \mathcal{L}_\beta K_{ij}$$

    The spatial Ricci tensor $R_{ij}$ contains second derivatives of the metric,
    which we discretize using the stencils developed above.
    """)
    return


@app.cell
def _(D, Discretize, Function, R, Simplify, StencilCodeGen, mo, symbols):
    # Simplified ADM-like term: second derivative of metric component
    x_adm, y_adm = symbols('x y')
    h_adm = symbols('h')
    gamma_xx = Function('gamma_xx')(x_adm, y_adm)

    # Part of the Ricci tensor: d^2(gamma_xx)/dx^2
    ricci_term = D(gamma_xx, (x_adm, 2))

    # Discretize
    step_adm = {x_adm: ([x_adm - h_adm, x_adm, x_adm + h_adm], h_adm)}
    ricci_discrete = Discretize(ricci_term, step_adm)

    # Generate code
    ricci_code = StencilCodeGen(ricci_discrete, language='c',
                                 array_name='gamma_xx', index_var='i', spacing_name='dx')

    mo.md(f"""
    **Ricci Tensor Component (simplified):**

    One term in $R_{{xx}}$ involves: $\\frac{{\\partial^2 \\gamma_{{xx}}}}{{\\partial x^2}}$

    Discretized: ${Simplify(ricci_discrete)}$

    **C code:**
    ```c
    double d2gamma_dx2 = {ricci_code};
    ```

    The full Ricci tensor has many such terms for each metric component.
    symderive automates the error-prone process of deriving and coding each stencil.
    """)
    return (
        gamma_xx, h_adm, ricci_code, ricci_discrete, ricci_term,
        step_adm, x_adm, y_adm,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 13. Using the Metric Class for Tensor Calculus

    symderive's `diffgeo` module provides a `Metric` class for full tensor calculus.
    This computes Christoffel symbols, Riemann tensor, and Ricci tensor automatically.

    For numerical relativity, these tensors contain the derivatives we need to discretize.
    """)
    return


@app.cell
def _(Metric, Simplify, Symbol, symbols):
    # Define a general 2D metric (simplified example)
    x_m, y_m = symbols('x y', real=True)

    # Metric components as symbols (would be functions in full NR)
    g_xx = Symbol('g_xx', positive=True)
    g_yy = Symbol('g_yy', positive=True)

    # Create a diagonal metric: ds^2 = g_xx dx^2 + g_yy dy^2
    # Metric(coords, components)
    metric_2d = Metric(
        [x_m, y_m],
        [[g_xx, 0],
         [0, g_yy]]
    )

    # Christoffel symbols contain first derivatives of the metric
    christoffels = metric_2d.christoffel_second_kind()

    # Example: Gamma^x_xx = (1/2) g^xx * d(g_xx)/dx
    Gamma_x_xx = Simplify(christoffels[0, 0, 0])

    (metric_2d.g, Gamma_x_xx)
    return Gamma_x_xx, christoffels, g_xx, g_yy, metric_2d, x_m, y_m


@app.cell
def _(D, Discretize, Function, Simplify, StencilCodeGen, mo, symbols):
    # Now discretize a Christoffel-like term
    # Gamma^i_jk involves d(g_jk)/dx^i, so we discretize metric derivatives
    x_chr, y_chr = symbols('x y')
    h_chr = symbols('h')

    # Metric component as a function of position
    g_xx_func = Function('g_xx')(x_chr, y_chr)

    # The derivative that appears in Christoffel symbols
    dg_dx = D(g_xx_func, x_chr)

    # Discretize using central difference
    step_chr = {x_chr: ([x_chr - h_chr, x_chr, x_chr + h_chr], h_chr)}
    dg_discrete = Discretize(dg_dx, step_chr)

    # Code for Christoffel computation
    chr_code = StencilCodeGen(dg_discrete, language='c',
                               array_name='g_xx', index_var='i', spacing_name='dx')

    mo.md(f"""
    **Discretizing Christoffel Symbol Terms:**

    Christoffel symbols involve metric derivatives like $\\partial_x g_{{xx}}$

    Discretized: ${Simplify(dg_discrete)}$

    **C code:**
    ```c
    // dg_xx/dx for Christoffel computation
    double dg_dx = {chr_code};

    // Then Gamma^x_xx = 0.5 * g_xx_inv * dg_dx
    double Gamma_x_xx = 0.5 * g_xx_inv * dg_dx;
    ```

    The full BSSN evolution uses these discretized Christoffels throughout.
    """)
    return chr_code, dg_discrete, dg_dx, g_xx_func, h_chr, step_chr, x_chr, y_chr


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 14. Kreiss-Oliger Dissipation

    Numerical simulations often add artificial dissipation to control
    high-frequency noise. The Kreiss-Oliger operator for 4th order schemes:

    $$\epsilon (-1)^{r+1} h^{2r-1} D_+^r D_-^r \phi$$

    where $D_+$ and $D_-$ are forward/backward difference operators.
    For $r=2$ this gives a 5-point dissipation stencil.
    """)
    return


@app.cell
def _(D, Function, Simplify, Symbol, ToStencil, mo):
    # Kreiss-Oliger dissipation (4th derivative for 4th order scheme)
    x_ko = Symbol('x')
    h_ko = Symbol('h')
    eps = Symbol('epsilon')
    phi_ko = Function('phi')(x_ko)

    # Fourth derivative (appears in Kreiss-Oliger for 4th order methods)
    d4_phi = D(phi_ko, (x_ko, 4))

    # Discretize with 5-point stencil
    ko_stencil = ToStencil(d4_phi, {x_ko: h_ko}, width=5)

    mo.md(f"""
    **Kreiss-Oliger Dissipation Term:**

    Fourth derivative: $\\frac{{\\partial^4\\phi}}{{\\partial x^4}}$

    Discretized: ${Simplify(ko_stencil)}$

    Applied as: $\\phi \\leftarrow \\phi - \\epsilon \\cdot h^3 \\cdot (\\text{{stencil}})$

    The coefficient $\\epsilon \\sim 0.1$ controls dissipation strength.
    """)
    return d4_phi, eps, h_ko, ko_stencil, phi_ko, x_ko


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    This notebook demonstrated the complete pipeline from theoretical physics
    to production-ready numerical simulation code:

    **Physics to Code Pipeline:**
    1. **Variational Calculus**: Derive equations of motion from Lagrangians
    2. **Discretization**: Convert PDEs to finite difference stencils
    3. **Multi-dimensional**: Handle 3D Laplacians, mixed derivatives
    4. **Code Generation**: Output C, Fortran, or Python for direct use

    **Numerical Relativity Applications:**
    - 3D Laplacian (7-point stencil) for constraint equations
    - Mixed derivatives for BSSN formulation
    - ADM evolution equations with Ricci tensor terms
    - Metric class for Christoffel symbols and curvature tensors
    - Kreiss-Oliger dissipation for numerical stability

    **Accuracy Control:**
    - 2nd order (3-point) to 8th order (9-point) stencils
    - Error scaling from $O(h^2)$ to $O(h^8)$

    This workflow is directly applicable to numerical relativity codes like
    GRChombo (used in arXiv:1608.04408) for simulating inflation with
    inhomogeneous initial conditions.

    ### Key Functions:
    - `VariationalDerivative(L, field, coords)` - Euler-Lagrange equations
    - `Discretize(expr, step_map)` - Finite difference conversion
    - `ToStencil(expr, spacing, width)` - Auto-generate stencil points
    - `StencilCodeGen(expr, language)` - C/Fortran/Python code generation
    - `Metric(components, coords)` - Tensor calculus with auto Christoffels
    - `Pipe(expr).then(...)` - Composable API for chaining operations
    """)
    return


if __name__ == "__main__":
    app.run()
