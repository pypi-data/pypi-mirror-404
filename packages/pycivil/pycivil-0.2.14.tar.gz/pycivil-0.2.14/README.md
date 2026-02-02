![alt text](pycivil/templates/latex/logo.png)

# What's PyCivil

A Python library for structural engineers that aims to make them as free as possible from commercial software while preserving their knowledge.

**Version:** 0.2.14 | **Python:** 3.9 - 3.12 | **License:** BSD-3-Clause

## Features

1. **EXAGeometry** - Low-level geometry classes for 2D/3D spatial calculations: `Point2d`, `Point3d`, `Vector2d`, `Vector3d`, `Polyline2d`, `Polyline3d`, `Edge`, `Node`, `ShapeRect`, `ShapeCircle`, `ShapePoly`

2. **EXAStructural** - Core structural engineering domain models:
   - `sections.py` - Reinforced concrete section models (`RectangularShape`, `TShape`, `IShape`, polygonal shapes) with reinforcement disposers
   - `materials.py` - Concrete and Steel material definitions with code-based properties
   - `loads.py` - Load and force representations with limit state enums
   - `codes.py` - Code management system for EC2, NTC2008, NTC2018
   - `templateRCRect.py` - RC rectangular section template with SLS/SLU analysis and fire design

3. **EXAStructural/lawcodes** - Implementation of structural codes with rules, strength formulas, loads and materials:
   - `codeEC211.py` - Eurocode 2-1-1 (concrete in compression)
   - `codeEC212.py` - Eurocode 2-1-2 (fire design rules)
   - `codeNTC2018.py` - Italian NTC2018 standard

4. **EXAStructural/rcrecsolver** - Solver for checking rectangular reinforced concrete sections under bending, axial and shear forces

5. **EXAStructural/rcgensolver** - Solver for checking generic shaped reinforced concrete sections under bending, axial and shear forces

6. **EXAStructuralModel** - FEM-agnostic finite element modeler (`FEModel`) with support for various load types, materials, section shapes, GMSH mesh generation, and MIDAS export

7. **EXAStructuralCheckable** - Structural verification against design codes with multiple criteria: SLE-NM, SLE-F, SLU-NM, SLU-T, SLU-NM-FIRE, and crack severity classification

8. **EXAParametric** - Parametric structural analysis for box and tube sections

9. **EXAGeotechnical** - Geotechnical formulas and soil mechanics: Young's modulus tables, Poisson's ratio tables, Winkler foundation model, Bussinesque formulas

10. **EXAUtils** - Utilities and tools:
    - `strand7PostPro.py` - Post-processor for Strand7 FEM results
    - `ucasefe.py` - Utilities for Code Aster FEM solver
    - `latexReportMakers.py` - LaTeX-based report generation
    - `latexCheatSheets.py` - Quick reference sheet generation
    - `vtk.py` - VTK visualization wrapper
    - `gmsh.py` - GMSH mesh generation wrapper

## Quick Start

### Geometry Basics

```python
from pycivil.EXAGeometry.geometry import Point2d, Point3d, Vector2d, Polyline2d, Node2d

# 2D Points
p1 = Point2d(0, 0)
p2 = Point2d(100, 200)
distance = p1.distance(p2)
midpoint = p1.midpoint(p2)

# 2D Vectors
v = Vector2d(p1, p2)
v.normalize()

# Polylines
nodes = [
    Node2d(0.0, 0.0, 1),
    Node2d(300.0, 0.0, 2),
    Node2d(300.0, 500.0, 3),
    Node2d(0.0, 500.0, 4),
]
poly = Polyline2d(nodes)
poly.setClosed()
```

### RC Section Analysis (SLS)

```python
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2

# Set code and materials
code = Code("NTC2018")

concrete = Concrete(descr="My concrete")
concrete.setByCode(code, "C25/30")

steel = ConcreteSteel(descr="My steel")
steel.setByCode(code, "B450C")

# Create rectangular RC section
rcSection = RCTemplRectEC2(1, "Beam Section")
rcSection.setDimH(600)  # height in mm
rcSection.setDimW(300)  # width in mm

# Add reinforcement (LINE-MB = bottom, LINE-MT = top)
rcSection.addSteelArea("LINE-MB", dist=50, d=20, nb=4, sd=40)  # 4Ø20 bottom
rcSection.addSteelArea("LINE-MT", dist=50, d=20, nb=4, sd=40)  # 4Ø20 top

# Calculate section properties
print(f"Concrete area: {rcSection.calConcreteArea()} mm²")
print(f"Steel area: {rcSection.calSteelArea():.0f} mm²")
print(f"Ideal area: {rcSection.calIdealArea():.0f} mm²")

# SLS analysis under N and M
KN = 1000
KNm = 1000 * 1000
N = -1000 * KN   # axial force (negative = compression)
M = 150 * KNm    # bending moment

sigmac, sigmas, xi = rcSection.solverSLS_NM(N, M, uncracked=True)
print(f"Concrete stress: {sigmac:.2f} MPa")
print(f"Steel stress: {sigmas:.2f} MPa")
print(f"Neutral axis: {xi:.2f} mm")
```

### Section Modeler

```python
from pycivil.EXAStructural.modeler import SectionModeler

# Create modeler
md = SectionModeler()
md.addSection(1, True)

# Define concrete shape (300x600 rectangle)
md.addNode(1, 0, 0)
md.addNode(2, 300, 0)
md.addNode(3, 300, 600)
md.addNode(4, 0, 600)
md.addTriangle(1, 1, 2, 3)
md.addTriangle(2, 3, 4, 1)

# Add bottom reinforcement (4Ø28)
for i, x in enumerate([60, 120, 180, 240]):
    md.addNode(20 + i, x, 40)
    md.addCircle(20 + i, 20 + i, 28 / 2)

# Add top reinforcement (4Ø16)
for i, x in enumerate([60, 120, 180, 240]):
    md.addNode(10 + i, x, 560)
    md.addCircle(10 + i, 10 + i, 16 / 2)

# Calculate properties
print(f"Solid barycenter: {md.calcSolidBarycenter()}")
print(f"Solid area: {md.calcSolidArea()} mm²")
print(f"Point area (rebars): {md.calcPointArea():.0f} mm²")
```

### ULS Interaction Domain (N-M)

```python
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2

# Set code and materials
code = Code("NTC2018")

concrete = Concrete(descr="My concrete")
concrete.setByCode(code, "C25/30")

steel = ConcreteSteel(descr="My steel")
steel.setByCode(code, "B450C")

# Create rectangular RC section
rcSection = RCTemplRectEC2(1, "Beam Section")
rcSection.setDimH(600)  # height in mm
rcSection.setDimW(300)  # width in mm

# Add reinforcement
rcSection.addSteelArea("LINE-MB", dist=50, d=20, nb=4, sd=40)  # 4Ø20 bottom
rcSection.addSteelArea("LINE-MT", dist=50, d=16, nb=4, sd=40)  # 4Ø16 top

# Build ULS interaction domain (N-M)
pointCloud, bounding = rcSection.interactionDomainBuild2d(
    nbPoints=100, SLS=False, bounding=True
)

# Bounding box: [Nmin, Nmax, Mmin, Mmax]
print(f"N range: {bounding[0]/1000:.0f} to {bounding[1]/1000:.0f} kN")
print(f"M range: {bounding[2]/1e6:.0f} to {bounding[3]/1e6:.0f} kNm")

# Check if a load point is inside the domain
N_ed = -200.0 * 1000  # -200 kN (compression)
M_ed = 100.0 * 1e6    # 100 kNm

contained, pintersect, intfactor, pindex = pointCloud.contains(
    N_ed, M_ed, rayFromCenter=True,
    ro=(bounding[1] - bounding[0], bounding[3] - bounding[2])
)

print(f"Load N_Ed={N_ed/1000:.0f} kN, M_Ed={M_ed/1e6:.0f} kNm")
print(f"Inside domain: {contained}")
print(f"Utilization factor: {1/intfactor:.2f}")
```

### Critical Moment (Cracking Moment)

```python
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2

# Set code and materials
code = Code("NTC2018")

concrete = Concrete(descr="My concrete")
concrete.setByCode(code, "C25/30")

steel = ConcreteSteel(descr="My steel")
steel.setByCode(code, "B450C")

# Create rectangular RC section
rcSection = RCTemplRectEC2(1, "Beam Section")
rcSection.setDimH(600)  # height in mm
rcSection.setDimW(300)  # width in mm

# Add reinforcement
rcSection.addSteelArea("LINE-MB", dist=50, d=20, nb=4, sd=40)  # 4Ø20 bottom
rcSection.addSteelArea("LINE-MT", dist=50, d=16, nb=4, sd=40)  # 4Ø16 top

# Calculate critical moment (moment that cracks the section)
KN = 1000
KNm = 1000 * 1000

# Without axial force
mcr_pos, mcr_neg = rcSection.calCriticalMoment()
print(f"Mcr+ = {mcr_pos/KNm:.2f} kNm")   # 63.16 kNm
print(f"Mcr- = {mcr_neg/KNm:.2f} kNm")   # -59.87 kNm

# With compressive axial force (N = -500 kN)
mcr_pos, mcr_neg = rcSection.calCriticalMoment(N=-500 * KN)
print(f"Mcr+ (with N) = {mcr_pos/KNm:.2f} kNm")  # 122.59 kNm
print(f"Mcr- (with N) = {mcr_neg/KNm:.2f} kNm")  # -116.19 kNm
```

### RC Section Checker (ucasefe)

```python
from pycivil.EXAUtils.ucasefe import RCRectCalculator

# Create calculator
calc = RCRectCalculator("My Project", "Beam B1")
calc.setLogLevel(0)  # quiet mode
calc.setJobPath("/path/to/output")  # where reports will be saved

# Units
KN = 1000
KNm = 1000000

# Section dimensions (mm)
calc.setDimensions(w=300, h=600)

# Materials
calc.setMaterialConcrete("NTC2018", "C25/30", "not aggressive")
calc.setMaterialRebars("NTC2018", "B450C", "not sensitive")

# Reinforcement
calc.addRebarsFromTop(num=4, diam=20, dist_from_top=40, dist_rebars=40)
calc.addRebarsFromBot(num=4, diam=20, dist_from_bot=40, dist_rebars=40)
calc.setStirrup(area=100, step=150, angle=90)

# Add load cases with checks
calc.addForce(N=-100*KN, M=145*KNm, T=120*KN,
              limit_state="serviceability", frequency="quasi-permanent",
              check_required=["SLE-NM", "SLE-F"], descr="Load case 1")

calc.addForce(N=-200*KN, M=200*KNm, T=200*KN,
              limit_state="ultimate",
              check_required=["SLU-T", "SLU-NM"], descr="Load case 2")

# Run analysis and build report
if calc.run():
    calc.buildReport()  # generates LaTeX report
```

## Install

PyCivil releases are available as wheel packages for Windows and Linux on [PyPI](https://pypi.org/project/pycivil/):

```shell
pip install pycivil
```

## Prerequisites

1. **LaTeX** installation (if you need to build reports)
2. **Docker Engine** (useful if you need to generate thermal maps or use Code Aster)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Docs

The documentation is built with [MkDocs](https://www.mkdocs.org/) and the [Material theme](https://squidfunk.github.io/mkdocs-material/).

### Serve documentation locally

Start a local development server with live-reload:

```shell
task docs
```

This will start a server at `http://127.0.0.1:8000` where you can browse the documentation.

### Build static documentation

To build the static HTML documentation:

```shell
uv run --only-group docs mkdocs build
```

The output will be generated in the `site/` directory.

> **NOTE**: The documentation is still being written. In the meantime, check the [tutorials](docs/tutorials.md) and the tests for practical examples.

## Development

- Install [task](https://taskfile.dev/installation/)
- run `task init` do initialize the python environment and install the pre-commit hooks
- before committing code changes, you can run `task` to perform automated checks. You can also run them separately:
    - `task lint` fixes and checks the code and documentation
    - `task mypy` performs type checking
    - `task test` runs the tests with `pytest`
    - `task security` scans the dependencies for known vulnerabilities

> **NOTE**: the `lint` task is executed automatically when you commit the changes to ensure that only good quality code is added to the repository.


### Docker container

If you're a docker-compose guy, you can run the [docker-compose.yml](docker-compose.yml) file with:

```shell
docker-compose up --build
```

This will also create Code_Aster containers, and you will be able to use Code_Aster as FEM solver.

#### Remove all volumes

This remove all volumes and data. Next relaunch the volumes will be build

```shell
docker-compose down -v
```
