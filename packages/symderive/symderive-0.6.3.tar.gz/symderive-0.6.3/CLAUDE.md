# CLAUDE.md

This file provides guidance to coding agents when working with code in this repository.

## Development Commands

```bash
uv sync                              # Install dependencies
uv run pytest tests/                 # Run all tests
uv run pytest tests/test_api.py -v   # Run specific test file
uv run marimo edit examples/quantum_mechanics.py  # Interactive notebook
```

## Architecture

symderive is a symbolic mathematics library built on SymPy, providing intuitive APIs for calculus, linear algebra, differential geometry, and more.

### Module Structure (src/symderive/)

- **core/**: Foundational types - `Symbol()`, `Function()`, constants, smart number handling with automatic rationalization
- **calculus/**: `D()` differentiation, `Integrate()`, `Limit()`, `Series()`, transforms (Fourier/Laplace), variational calculus
- **algebra/**: `Solve()`, `Simplify()`, `Factor()`, `Matrix()`, `Eigenvalues()`
- **diffgeo/**: `Metric()` class with automatic Christoffel/Riemann/Ricci computation, xAct-style abstract index notation, tensor symmetry optimization
- **ode/**: `DSolve()` symbolic and `NDSolve()` numerical differential equation solvers
- **functions/**: Trig, exponential, complex, 30+ special functions (Bessel, Legendre, Gamma, etc.)
- **patterns/**: `Replace()`, `ReplaceAll()`, `DefineFunction()` for pattern matching and custom functions
- **utils/**: `Pipe()` composable API, `TeXForm()` display, `Assuming()` context, `memoize()` caching
- **types/**: `Quaternion()`, `Vector3D()`, `DefineType()` for custom mathematical objects
- **plotting/**: Matplotlib-based `Plot()`, `ContourPlot()`, `ParametricPlot()`
- **optimize/**: `Minimize()`, `Maximize()`, `OptVar()` for constrained optimization (requires cvxpy)
- **regression/**: `FindFormula()` symbolic regression via PySR (requires optional `regression` extra)
- **discretization/**: `Discretize()`, `ToStencil()`, `StencilCodeGen()` for PDE finite difference stencils
- **compact/**: `FitCompactModel()`, `FitRationalModel()` for FDTD compact model generation from S-parameters
- **data/**: Data I/O utilities for loading simulation/measurement data
- **probability/**: Probability distributions and statistical functions
- **agents/**: Mathematical persona agents (Ed, Steve, Atiyah, etc.) for agentic workflows

### Key Design Patterns

**Expression-first**: Everything wraps SymPy's `Expr` class with cleaner APIs.

**Smart number handling**: Floats auto-convert to rationals (`0.5` → `Rational(1,2)`). Use `exact()` / `numerical()` context managers to control.

**Composable API**: Chain operations via `Pipe(expr).then(Expand).then(Simplify).value` or functional `pipe(expr, Simplify)`.

**Tensor symmetry optimization**: diffgeo module exploits Christoffel lower-index symmetry (Γ^ρ_μν = Γ^ρ_νμ) and Ricci symmetry for ~4x speedup.

### Test Structure

Tests in `tests/` mirror module structure. Key test files: `test_api.py` (core functions), `test_tensors.py` (diffgeo), `test_patterns.py` (pattern matching), `test_compose.py` (Pipe API).

## Code Conventions

- **No imports inside functions**: All imports belong at module top-level.
- **Self-reference the API**: Use symderive's own functions (e.g., `D()`, `Simplify()`) rather than calling SymPy directly. The library should dogfood itself.
- **Avoid nested for loops**: Prefer `itertools.product()`, comprehensions, or vectorized NumPy/SymPy operations for cleaner, more performant code.
- **No special characters or emojis**: Keep code and documentation ASCII-clean.
- **Tests are mandatory**: Write tests for all new code. Never modify tests just to make them pass—fix the code instead. Test changes are only acceptable when refactoring genuinely requires updating test structure.
- **CamelCase for public API**: Public functions use `CamelCase()` naming (e.g., `Symbol()`, `Integrate()`, `Simplify()`).

## Enforcement

Code standards are automatically enforced by Claude Code hooks in `agents/`. These run on every file write/edit and will block violations:

| Agent | Enforces |
|-------|----------|
| `code_standards_enforcer.py` | Imports, SymPy usage, loops, ASCII, CamelCase naming |
| `test_coverage_check.sh` | Warns when test files are missing |

See `agents/README.md` for details on customizing or extending enforcement.

See `SECRETS.md` for test generation workflows and other development details.
