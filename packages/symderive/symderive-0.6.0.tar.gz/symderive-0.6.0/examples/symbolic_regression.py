"""Symbolic Regression with Derive: Discovering Mathematical Formulas from Data"""

import marimo

__generated_with = "0.19.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import warnings
    # Suppress PySR warnings about constraints (shows local paths)
    warnings.filterwarnings('ignore', module='pysr')
    from symderive import (
        Symbol, symbols, Simplify, Expand, Collect,
        Sin, Cos, Exp, Log, Sqrt, Pi,
        D, Integrate,
    )
    from symderive.regression import FindFormula
    from symderive.plotting import Plot, ListPlot
    return (
        Collect,
        D,
        Exp,
        FindFormula,
        ListPlot,
        Plot,
        Simplify,
        Sin,
        Symbol,
        mo,
        np,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Symbolic Regression with Derive

    This notebook demonstrates **symbolic regression** - the task of discovering
    mathematical formulas that fit data. Derive wraps the powerful PySR library
    with an intuitive `FindFormula` interface.

    ## What is Symbolic Regression?

    Unlike traditional regression (linear, polynomial, etc.) which fits parameters
    to a *fixed* functional form, symbolic regression searches the space of
    *all possible mathematical expressions* to find the simplest formula that
    explains your data.

    This is especially useful for:
    - **Scientific discovery**: Finding laws from experimental data
    - **Interpretable ML**: Getting human-readable models instead of black boxes
    - **Physics**: Rediscovering known equations from simulation data
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Basic Usage: Linear Relationships

    Let's start with a simple example - discovering a linear relationship.
    """)
    return


@app.cell
def _(FindFormula, ListPlot, Symbol, np):
    # Generate data for y = 2x + 1
    x_lin = Symbol('x')
    data_linear = [[i, 2*i + 1] for i in range(20)]

    # Find the formula
    formula_linear = FindFormula(
        data_linear, x_lin,
        niterations=10,
        max_complexity=8
    )

    # Visualize
    plot_linear = ListPlot(data_linear)
    formula_linear, plot_linear
    return data_linear, formula_linear, plot_linear, x_lin


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Quadratic and Polynomial Relationships

    FindFormula can discover more complex polynomial relationships.
    """)
    return


@app.cell
def _(Collect, FindFormula, ListPlot, Symbol, np):
    # Generate data for y = x^2 - 3x + 2
    x_quad = Symbol('x')
    data_quadratic = [[i, i**2 - 3*i + 2] for i in range(-5, 10)]

    formula_quadratic_raw = FindFormula(
        data_quadratic, x_quad,
        niterations=15,
        max_complexity=12
    )
    # Collect by powers of x for cleaner display
    formula_quadratic = Collect(formula_quadratic_raw, x_quad)

    plot_quadratic = ListPlot(data_quadratic)
    formula_quadratic, plot_quadratic
    return data_quadratic, formula_quadratic, formula_quadratic_raw, plot_quadratic, x_quad


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Trigonometric Functions

    By specifying `target_functions`, we can guide the search toward specific
    function classes. Here we look for sine/cosine patterns.
    """)
    return


@app.cell
def _(FindFormula, ListPlot, Symbol, np):
    # Generate sinusoidal data
    x_trig = Symbol('x')
    x_vals = np.linspace(0, 4*np.pi, 50)
    data_trig = [[float(x), float(np.sin(x))] for x in x_vals]

    # Restrict to trigonometric functions
    formula_trig = FindFormula(
        data_trig, x_trig,
        target_functions=['Sin', 'Cos', 'Plus', 'Times'],
        niterations=15,
        max_complexity=10
    )

    plot_trig = ListPlot(data_trig)
    formula_trig, plot_trig
    return data_trig, formula_trig, plot_trig, x_trig, x_vals


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Exponential Decay

    Physical processes often follow exponential laws.
    """)
    return


@app.cell
def _(FindFormula, ListPlot, Symbol, np):
    # Exponential decay: y = 5 * exp(-0.3 * x)
    x_exp = Symbol('x')
    x_vals_exp = np.linspace(0, 10, 30)
    data_exp = [[float(x), float(5 * np.exp(-0.3 * x))] for x in x_vals_exp]

    formula_exp = FindFormula(
        data_exp, x_exp,
        target_functions=['Exp', 'Plus', 'Times'],
        niterations=20,
        max_complexity=12
    )

    plot_exp = ListPlot(data_exp)
    formula_exp, plot_exp
    return data_exp, formula_exp, plot_exp, x_exp, x_vals_exp


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Noisy Data

    Real-world data has noise. FindFormula can still recover underlying patterns.
    """)
    return


@app.cell
def _(FindFormula, ListPlot, Symbol, np):
    # Linear with noise
    np.random.seed(42)
    x_noisy = Symbol('x')
    noise = np.random.normal(0, 0.5, 30)
    data_noisy = [[float(i), float(2*i + 1 + noise[i])] for i in range(30)]

    formula_noisy = FindFormula(
        data_noisy, x_noisy,
        niterations=15,
        max_complexity=8
    )

    plot_noisy = ListPlot(data_noisy)
    formula_noisy, plot_noisy
    return data_noisy, formula_noisy, noise, plot_noisy, x_noisy


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Multiple Candidate Formulas

    Request multiple formulas to see the trade-off between complexity and accuracy.
    """)
    return


@app.cell
def _(FindFormula, Symbol, np):
    # Get multiple candidates
    x_multi = Symbol('x')
    data_multi = [[i, i**2 + 2*i] for i in range(15)]

    formulas_multi = FindFormula(
        data_multi, x_multi,
        n=5,  # Return up to 5 formulas
        niterations=20,
        max_complexity=15
    )

    formulas_multi
    return data_multi, formulas_multi, x_multi


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7. Getting Detailed Results

    Use `prop='All'` to get scores, errors, and complexity for each candidate.
    """)
    return


@app.cell
def _(FindFormula, Symbol):
    x_props = Symbol('x')
    data_props = [[i, 3*i**2 - 2*i + 1] for i in range(-5, 10)]

    results = FindFormula(
        data_props, x_props,
        n=5,
        prop='All',
        niterations=20,
        max_complexity=15
    )

    # Show the results dictionary
    results
    return data_props, results, x_props


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8. Physics Example: Kepler's Third Law

    A famous example: discovering Kepler's law from planetary data.

    Kepler's third law states: $T^2 \propto a^3$

    Where T is the orbital period and a is the semi-major axis.
    """)
    return


@app.cell
def _(FindFormula, Symbol, np):
    # Planetary data (approximate): [semi-major axis (AU), period (years)]
    planets = [
        [0.387, 0.241],   # Mercury
        [0.723, 0.615],   # Venus
        [1.000, 1.000],   # Earth
        [1.524, 1.881],   # Mars
        [5.203, 11.86],   # Jupiter
        [9.537, 29.46],   # Saturn
        [19.19, 84.01],   # Uranus
        [30.07, 164.8],   # Neptune
    ]

    a = Symbol('a')  # semi-major axis

    # We're looking for T as a function of a
    # The relationship is T = a^(3/2) (in appropriate units)
    kepler_formula = FindFormula(
        planets, a,
        target_functions=['Power', 'Times', 'Plus'],
        niterations=20,
        max_complexity=10
    )

    kepler_formula
    return a, kepler_formula, planets


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 9. Using NumPy Arrays

    FindFormula accepts various data formats including NumPy arrays.
    """)
    return


@app.cell
def _(FindFormula, Symbol, np):
    # Using (X, y) tuple format
    x_np = Symbol('x')
    X = np.linspace(0, 5, 50)
    y = np.sqrt(X) + 0.5

    formula_np = FindFormula(
        (X, y), x_np,
        target_functions=['Sqrt', 'Plus', 'Times'],
        niterations=15,
        max_complexity=8
    )

    formula_np
    return X, formula_np, x_np, y


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 10. Combining with Derive's Symbolic Tools

    The formulas returned by FindFormula are SymPy expressions that work
    seamlessly with Derive's other tools.
    """)
    return


@app.cell
def _(D, FindFormula, Integrate, Simplify, Symbol):
    # Find a formula
    x_sym = Symbol('x')
    data_sym = [[i, i**3 - i] for i in range(-3, 4)]

    formula_sym = FindFormula(
        data_sym, x_sym,
        niterations=15,
        max_complexity=10
    )

    # Now use Derive's symbolic tools on it
    derivative = D(formula_sym, x_sym)
    integral = Integrate(formula_sym, x_sym)
    simplified = Simplify(derivative)

    {
        'formula': formula_sym,
        'derivative': simplified,
        'integral': integral
    }
    return data_sym, derivative, formula_sym, integral, simplified, x_sym


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    `FindFormula` provides a powerful interface for symbolic regression:

    - **Basic usage**: `FindFormula(data, x)` - finds the best formula
    - **Multiple results**: `FindFormula(data, x, n=5)` - returns top n candidates
    - **Targeted search**: `target_functions=['Sin', 'Exp', ...]` - restrict function space
    - **Detailed output**: `prop='All'` - get scores, errors, complexity
    - **Performance**: `performance_goal='Quality'` for more thorough search

    The discovered formulas integrate seamlessly with Derive's symbolic
    computation tools for differentiation, integration, and simplification.
    """)
    return


if __name__ == "__main__":
    app.run()
