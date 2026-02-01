# symderive: Plotting

## Overview
symderive provides Mathematica-style plotting functions built on matplotlib.

```python
from symderive import *
from symderive.plotting import (
    Plot, Plot3D, ParametricPlot, ParametricPlot3D,
    ListPlot, ListLinePlot, ContourPlot, DensityPlot,
    VectorPlot, StreamPlot, PolarPlot,
)
```

## 2D Function Plots

### Basic Plot
```python
x = Symbol('x')

# Single function
Plot(Sin(x), (x, 0, 2*Pi))

# Multiple functions
Plot([Sin(x), Cos(x)], (x, 0, 2*Pi))

# With options
Plot(
    Sin(x),
    (x, 0, 2*Pi),
    PlotLabel="Sine Wave",
    AxesLabel=["x", "y"],
    PlotStyle="Blue",
    GridLines=True,
)
```

### Plot Options
```python
Plot(
    Sin(x),
    (x, 0, 2*Pi),
    # Labels
    PlotLabel="Title",
    AxesLabel=["x-axis", "y-axis"],

    # Style
    PlotStyle="Red",            # Single color
    PlotStyle=["Red", "Blue"],  # Multiple functions
    PlotStyle={"linewidth": 2, "linestyle": "--"},

    # Grid and axes
    GridLines=True,
    AxesOrigin=[0, 0],

    # Range
    PlotRange=[-1, 1],          # y-range
    PlotRange=[[-1, 7], [-2, 2]],  # [x-range, y-range]

    # Sampling
    PlotPoints=200,             # Number of sample points

    # Legend
    PlotLegends=["sin(x)", "cos(x)"],
)
```

## Parametric Plots

### 2D Parametric
```python
t = Symbol('t')

# Circle
ParametricPlot(
    [Cos(t), Sin(t)],
    (t, 0, 2*Pi),
    PlotLabel="Circle"
)

# Lissajous curve
ParametricPlot(
    [Sin(3*t), Sin(4*t)],
    (t, 0, 2*Pi),
    PlotLabel="Lissajous 3:4"
)

# Multiple curves
ParametricPlot(
    [[Cos(t), Sin(t)], [2*Cos(t), Sin(t)]],
    (t, 0, 2*Pi),
    PlotLegends=["Circle", "Ellipse"]
)
```

### 3D Parametric
```python
# Helix
ParametricPlot3D(
    [Cos(t), Sin(t), t],
    (t, 0, 4*Pi),
    PlotLabel="Helix"
)

# Toroidal curve
ParametricPlot3D(
    [(2 + Cos(3*t))*Cos(t), (2 + Cos(3*t))*Sin(t), Sin(3*t)],
    (t, 0, 2*Pi),
    PlotPoints=500
)
```

## 3D Surface Plots

```python
x, y = symbols('x y')

# Basic surface
Plot3D(
    Sin(x)*Cos(y),
    (x, -Pi, Pi),
    (y, -Pi, Pi),
    PlotLabel="sin(x)cos(y)"
)

# Options
Plot3D(
    x**2 - y**2,
    (x, -2, 2),
    (y, -2, 2),
    PlotLabel="Saddle Surface",
    AxesLabel=["x", "y", "z"],
    ColorFunction="viridis",  # Colormap
    PlotPoints=50,            # Resolution
)
```

## Contour and Density Plots

### Contour Plot
```python
ContourPlot(
    x**2 + y**2,
    (x, -2, 2),
    (y, -2, 2),
    Contours=10,              # Number of contours
    PlotLabel="Circles"
)

# Specific contour levels
ContourPlot(
    Sin(x)*Sin(y),
    (x, 0, Pi),
    (y, 0, Pi),
    Contours=[0, 0.5, 0.9],
    ContourLabels=True
)
```

### Density Plot
```python
DensityPlot(
    Sin(x)*Sin(y),
    (x, 0, Pi),
    (y, 0, Pi),
    ColorFunction="plasma",
    PlotLabel="Density"
)
```

## Vector and Stream Plots

### Vector Field
```python
VectorPlot(
    [-y, x],                  # [F_x, F_y]
    (x, -2, 2),
    (y, -2, 2),
    PlotLabel="Rotation Field"
)
```

### Stream Plot
```python
StreamPlot(
    [-y, x],
    (x, -2, 2),
    (y, -2, 2),
    PlotLabel="Streamlines"
)
```

## Polar Plots

```python
theta = Symbol('theta')

# Rose curve
PolarPlot(
    Cos(3*theta),
    (theta, 0, 2*Pi),
    PlotLabel="3-Petal Rose"
)

# Spiral
PolarPlot(
    theta,
    (theta, 0, 4*Pi),
    PlotLabel="Archimedean Spiral"
)

# Cardioid
PolarPlot(
    1 + Cos(theta),
    (theta, 0, 2*Pi),
    PlotLabel="Cardioid"
)
```

## Data Plots

### List Plot (Scatter)
```python
data = [(1, 2), (2, 4), (3, 1), (4, 5), (5, 3)]

ListPlot(
    data,
    PlotLabel="Scatter Plot",
    PlotStyle={"marker": "o", "markersize": 8}
)
```

### List Line Plot
```python
ListLinePlot(
    data,
    PlotLabel="Line Plot",
    PlotStyle="Blue"
)

# Multiple series
ListLinePlot(
    [data1, data2],
    PlotLegends=["Series 1", "Series 2"]
)
```

### Combined Plot
```python
import matplotlib.pyplot as plt

# Manual combination
fig, ax = plt.subplots()

# Plot function
x_vals = np.linspace(0, 10, 100)
ax.plot(x_vals, np.sin(x_vals), label='sin(x)')

# Add data points
ax.scatter([1, 2, 3], [0.8, 0.9, 0.1], label='Data')

ax.legend()
plt.show()
```

## Styling

### Colors
```python
# Named colors
PlotStyle="Red"
PlotStyle="Blue"
PlotStyle="Green"

# Hex colors
PlotStyle="#FF5733"

# RGB tuples
PlotStyle=(0.2, 0.4, 0.6)

# Multiple colors
PlotStyle=["Red", "Blue", "Green"]
```

### Line Styles
```python
PlotStyle={"linestyle": "-"}   # Solid
PlotStyle={"linestyle": "--"}  # Dashed
PlotStyle={"linestyle": ":"}   # Dotted
PlotStyle={"linestyle": "-."}  # Dash-dot
```

### Colormaps (for 3D/contour)
```python
ColorFunction="viridis"    # Default
ColorFunction="plasma"
ColorFunction="inferno"
ColorFunction="magma"
ColorFunction="coolwarm"   # Diverging
ColorFunction="RdBu"       # Red-Blue diverging
```

## Saving Plots

```python
# Using matplotlib directly
import matplotlib.pyplot as plt

Plot(Sin(x), (x, 0, 2*Pi))
plt.savefig("sine.png", dpi=300, bbox_inches='tight')
plt.savefig("sine.pdf")  # Vector format
plt.savefig("sine.svg")  # SVG format
```

## Physics Visualizations

### Wave Function
```python
x = Symbol('x')
n = 3  # Quantum number

# Particle in a box
psi_n = Sqrt(2) * Sin(n * Pi * x)
Plot(psi_n, (x, 0, 1), PlotLabel=f"ψ_{n}(x)")
```

### Probability Density
```python
Plot(psi_n**2, (x, 0, 1), PlotLabel=f"|ψ_{n}|²")
```

### Electric Field
```python
# Dipole field
x, y = symbols('x y')
r = Sqrt(x**2 + y**2)
Ex = x / r**3
Ey = y / r**3

VectorPlot([Ex, Ey], (x, -2, 2), (y, -2, 2), PlotLabel="Dipole Field")
```

### Phase Space
```python
# Harmonic oscillator phase portrait
x, p = symbols('x p')
H = p**2/2 + x**2/2

ContourPlot(H, (x, -2, 2), (p, -2, 2), PlotLabel="Phase Space")
```
