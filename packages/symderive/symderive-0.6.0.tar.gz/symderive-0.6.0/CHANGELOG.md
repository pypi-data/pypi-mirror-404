# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-01-31

### Changed
- **PyPI package name: `symderive`** - Install with `pip install symderive`, import with `from derive import *`
- **README overhaul for better positioning** (#27, #30)
  - New tagline: "A Standalone Symbolic Engine for AI Agents and Mathematical Computing"
  - Added "Agent-Native Architecture" section documenting Pipe Framework and functional primitives
  - Added "Ergonomics" section highlighting Wolfram-style CamelCase syntax
  - Restructured content: capabilities first, humor/vibes moved to "Project Philosophy" section
  - Expanded agent persona documentation with concrete LLM usage examples
- **Installation documentation improved** (#29)
  - PyPI installation as primary method: `pip install symderive`
  - Source installation and uv as alternatives
  - Added `requirements.txt` for standard pip workflows
- **pytest moved to dev dependencies** - end users no longer install pytest unnecessarily

### Added
- `requirements.txt` file for standard Python installation workflows
- PyPI metadata: classifiers, keywords, project URLs for discoverability
- Victor (Mingsy) Chua added to authors

### Developer Notes
- Codebase audit (#28) identified test files importing lowercase sympy functions (sin/cos/exp) instead of derive's CamelCase versions (Sin/Cos/Exp) - cleanup pending

## [0.4.1] - 2026-01-29

### Fixed
- `DSolve()` now exposes `ics` parameter for initial conditions (#21)
  - Previously documented but not implemented, causing TypeError
  - Now correctly passes initial conditions to SymPy's dsolve
  - Always returns a list for consistent API
- Constrained Wild pattern combination no longer crashes (#22)
  - `Integer_('n') + Integer_('n')` previously crashed with TypeError
  - Constrained Wilds are now cached by (name, constraint_type)
  - Ensures same Wild object is returned for same arguments
- `ComplexNumber` and `Quaternion` now support division (#23)
  - Added `__truediv__` operator to both types
  - `ComplexNumber(1, 2) / ComplexNumber(3, 4)` now works correctly
- `Vector3D.normalize()` and `Quaternion.inverse()` now have zero guards (#24)
  - Raise `ValueError` with clear message instead of division by zero
- `NSolve()` now correctly handles three-valued `.is_real` logic (#26)
  - Previously could return unexpected complex values when `.is_real` was `None`
  - Now explicitly checks `is_real is True` before returning real part

### Added
- Test coverage for `calculus/greens.py` module (#25)
  - Tests for `GreenFunctionPoisson1D`, `GreenFunctionHelmholtz1D`, etc.
  - Verifies boundary conditions, symmetry, and mathematical properties
- Test coverage for `NSolve()` function (#26)
  - Tests for real and complex solutions
- Tests for `ComplexNumber`/`Quaternion` division and zero guards
- Tests for `Vector3D.normalize()` including zero vector case
- Tests for constrained Wild caching behavior

## [0.4.0] - 2026-01-23

### Added
- Mathematical and physics persona agents in `derive.agents` module for agentic workflows (#18)
  - **Ed**: Theoretical physicist (QFT, gravity, condensed matter, statistical mechanics)
  - **Steve**: Particle physicist and critical reviewer demanding experimental grounding
  - **Atiyah**: Geometric bridge-builder (index theory, K-theory, topology)
  - **Grothendieck**: Abstraction architect (category theory, schemes, universal properties)
  - **Bill Press**: Numerical algorithms expert (stability, conditioning, error analysis)
  - **Jim Simons**: Quantitative researcher (statistical signals, backtesting, risk)
  - **Edward Tufte**: Information design critic (clarity, density, honest encoding)
  - **Beavis**: Fast sanity checker for quick gut checks and obvious bugs
  - **Butt-Head**: Skeptical contrarian for stress-testing reasoning
- `AGENTS.yaml` index file for orchestrator routing
  - Lightweight metadata (~600 tokens) vs full agent files (~15,000 tokens)
  - Hierarchical categories: physics, mathematics, computation, quantitative, design, critique
  - Tags and `use_when` fields for semantic matching
- Documentation for agentic workflows in README
- New `compact` module for FDTD compact model generation
  - Convert optical device simulation data (spectra, S-parameters) into closed-form symbolic models
  - Data I/O: `LoadSParameters()`, `LoadSpectrum()`, `LoadTouchstone()` for loading simulation/measurement data
  - Model fitting: `FitCompactModel()` for symbolic regression, `FitRationalModel()` for vector fitting
  - Physical constraints: `KramersKronig()`, `EnforceKramersKronig()`, `CheckCausality()`, `HilbertTransform()`
  - Model classes: `CompactModel`, `RationalModel`, `PoleResidueModel` for circuit simulation export
- New example notebook `compact_models.py` demonstrating:
  - Loading and processing S-parameter data
  - Fitting rational models to optical device responses
  - Kramers-Kronig causality enforcement
  - Exporting models for SPICE/Verilog-A circuit simulation

### Changed
- Updated contributors to include Victor (Mingsy) Chua
- Code standards enforcer now exempts `examples/` directory from import-in-function check (marimo notebooks require imports inside cells)

### Fixed
- `_enforce_conjugate_pairs` in compact module now preserves pole count
  - Numerical errors could cause poles to be duplicated or lost, leading to shape mismatches in vector fitting
  - Fix properly pairs complex poles by sorting and averaging to enforce exact conjugacy

## [0.3.0] - 2026-01-18

### Added
- Claude Code enforcement agents in `agents/` directory
  - `code_standards_enforcer.py`: Validates code against project conventions
    - No imports inside functions
    - Self-reference derive API (not raw SymPy)
    - No nested for loops (use itertools.product)
    - No special characters/emojis
    - CamelCase naming for public API functions
    - Test file modification warnings
  - `test_coverage_check.sh`: Warns when source files lack corresponding tests
  - Hooks configured in `.claude/settings.json` for automatic enforcement
- New `discretization` module for converting symbolic PDEs to finite difference stencils (#3)
  - `Discretize()`: Convert derivatives to finite difference approximations
  - `ToStencil()`: Generate stencil weights from symbolic expressions
  - `StencilCodeGen()`: Generate numerical code in Python, C++, Julia, Fortran
  - `FiniteDiffWeights()`: Auto-compute stencil coefficients via Taylor series expansion
  - `Stencil()`: Convenience function returning stencil as {offset: weight} dict
  - Supports arbitrary derivative orders and accuracy
- New example notebook `numerical_relativity_stencils.py` demonstrating:
  - Deriving equations of motion from Lagrangians using variational calculus
  - Converting symbolic PDEs to finite difference stencils
  - Generating code for numerical simulations (based on arXiv:1608.04408)

### Changed
- **BREAKING**: All modules now import from `derive.core.math_api` instead of directly from sympy/numpy/scipy/mpmath
  - This enforces the centralized math library abstraction layer
  - External library usage is now fully encapsulated in `math_api.py`
  - Enables future library swapping without changing consumer code
- Added `Internal Refs:` docstring sections to all modified modules documenting math_api dependencies
- Extended `math_api.py` exports:
  - Integral transforms: `fourier_transform`, `inverse_fourier_transform`, `laplace_transform`, `inverse_laplace_transform`
  - Comparison operators: `Eq`, `Ne`, `Lt`, `Le`, `Gt`, `Ge`, `Max`, `Min`
  - Special functions: `gegenbauer`, `jacobi`, `Ynm`, `beta`, `li`
  - Array operations: `permutedims`
  - Arbitrary precision: `mpmath_mpf`, `mpmath_mpi`, `mpmath_mp`, `GetMpmath()`, `IsMpmathAvailable()`

### Fixed
- Removed redundant mid-function import in `discretization/stencils.py`
- PySR/Julia now truly lazy-loaded - only initialized when `FindFormula()` is called
  - Fixes marimo notebook export hanging due to Julia initialization
  - Importing `derive` no longer triggers Julia startup
- `Assuming` context manager now preserves pre-existing global assumptions on exit (#7)
- `OptVar` bounds parameter now enforced during optimization solve (#8)
  - Bounds are automatically collected and applied as constraints
- cvxpy helper functions now raise clear `ImportError` when cvxpy not installed (#9)
  - Affects `is_solved`, `Norm()`, `Sum()`, `Quad()`, `PositiveSemidefinite()`
- `Discretizer` now correctly handles mixed partial derivatives like d^2f/dxdy (#10)
  - Decomposes mixed partials into nested single-variable derivatives
  - Applies finite difference stencils in both directions
- `ChangeVariables` now warns when non-injective substitutions yield multiple solutions (#11)
  - Alerts users to use domain restrictions (e.g., `positive=True`)
- `OptVar` bounds no longer silently dropped for inline usage (#15)
  - `Minimize(OptVar('x', bounds=(0, 1)))` now correctly applies bounds
  - OptVars are held by the problem instance during solve, then cleaned from global registry
  - Fixes #12's `WeakValueDictionary` approach while still preventing memory leaks
- `ExpressionCache` docstring incorrectly claimed weak reference usage (#14)
  - Updated to accurately describe FIFO eviction behavior

### Changed
- `pysr` moved from base dependency to optional `regression` extra (#13)
  - Install with `uv sync --extra regression`
  - Prevents Julia installation for users who don't need `FindFormula`

## [0.2.0] - 2026-01-18

### Added
- New `regression` module with `FindFormula` for symbolic regression (#2)
  - Wraps PySR library for discovering mathematical formulas from data
  - Supports multiple data formats: list of pairs, numpy arrays, (X, y) tuples
  - Options: `target_functions`, `specificity_goal`, `time_constraint`, `performance_goal`
  - Returns SymPy expressions compatible with all derive symbolic tools
- Comprehensive symbolic regression example notebook (`examples/symbolic_regression.py`)
- New `core/math_api.py` module providing abstraction layer for math libraries
  - Centralizes NumPy/SymPy imports to enable future library swapping
  - Exposes vectorized operations: `array`, `zeros`, `ones`, `linspace`, `dot`, `norm`

### Changed
- `pysr` is now a required dependency (previously optional)
- `marimo` is now an optional dependency - install with `uv sync --extra notebooks`
- `cvxpy` is now an optional dependency - install with `uv sync --extra optimize`
- Simplified `optimize/core.py` and `regression/core.py` imports (removed try/except blocks)
- Re-rendered all example notebooks with cell outputs included
- Updated README with symbolic_regression example in notebooks table

### Fixed
- Symbolic regression notebook now uses `Collect()` for cleaner polynomial display
- Suppressed PySR warnings that exposed local file paths in rendered notebooks

## [0.1.0] - 2026-01-18

### Added
- Initial release of derive symbolic mathematics library
- Core symbolic computation functionality built on SymPy
- Numerical computation support via NumPy and SciPy
- Data manipulation with Polars integration
- Visualization capabilities through Matplotlib
- Interactive notebook support with marimo
- GitHub-rendered notebook exports
- New `utils/validation.py` module with reusable validation utilities
  - `validate_tuple`, `validate_range_tuple`, `validate_positive`, `validate_nonnegative`
  - `ValidationError` exception class for consistent error handling
- New `utils/functional.py` module with higher-order functions and functional patterns
  - `matrix_method` factory for creating matrix operations from method names
  - `symbolic_to_callable` wrapper for SymPy lambdify with sensible defaults
  - Functional utilities: `curry`, `flip`, `foldl`, `foldr`, `scanl`, `scanr`

### Changed
- Moved all mid-function imports to module top-level (PEP 8 compliance)
  - display.py: Optional dependencies (rich, IPython) now imported at module level with availability flags
  - notebook.py: IPython and Marimo imports moved to top with IPYTHON_AVAILABLE/MARIMO_AVAILABLE flags
  - numbers.py: Moved re and sympy.parsing imports to top level
  - optimize/core.py: cvxpy imports moved to top with CVXPY_AVAILABLE flag
  - functions/number.py: mpmath imports moved to top with MPMATH_AVAILABLE flag
  - compose.py: sympy simplify/expand/factor/collect moved to top level
  - transforms.py: sympy.Integral import moved to top level
  - indices.py: collections.Counter and sympy.tensorcontraction moved to top
  - symmetry.py: Removed redundant itertools.product imports from functions (already at module level)
  - cache.py: sympy.simplify moved to top level
  - lazy.py: sympy.simplify moved to top level
  - functions/utils.py: sympy.printing imports moved to top level

### Improved
- Refactored `algebra/linear.py` to use `matrix_method` factory pattern for DRY compliance
  - `Det`, `Tr`, `MatrixRank`, `NullSpace`, `MatrixExp` now use factory pattern
  - Added `_ensure_matrix` helper to reduce code duplication
- Added `@lru_cache` memoization to pure functions in `diffgeo/symmetry.py`
  - `symmetric_index_pairs` and `symmetric_christoffel_indices` now cached
- Optimized Ricci tensor and Einstein tensor computation to exploit symmetry
  - `ricci_tensor()` now computes only n(n+1)/2 unique components (R_uv = R_vu)
  - `einstein_tensor()` now computes only n(n+1)/2 unique components (G_uv = G_vu)
- Optimized nested loops using itertools.product for cleaner code
  - transforms.py: Jacobian and metric transformation now use iterproduct
  - metrics.py: Ricci tensor and Einstein tensor use iterproduct; covariant derivative uses sum comprehensions
- Documentation example in variational.py now uses derive's D() instead of SymPy's diff()
- Pre-computed metric substitutions in coordinate transforms for better performance

### Fixed
- LaTeX printing issue
- Variable aliasing issue (#1)
- Replaced bare `except` clauses with specific exception types for better error handling
  - `patterns/matching.py`: Rule.apply and ReplaceAll now catch (TypeError, ValueError, AttributeError)
  - `patterns/functions.py`: PatternFunction matching now catches specific exceptions
  - `utils/compose.py`: FixedPoint and FixedPointList now catch (TypeError, ValueError, AttributeError)
  - `core/numbers.py`: rationalize and nsimplify now catch (TypeError, ValueError)
