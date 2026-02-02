# Tutorials

This section provides practical examples to help you get started with PyCivil.

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

---

## Marimo Notebook Examples

The following examples are adapted from interactive Marimo notebooks. They demonstrate more advanced use cases of PyCivil.

### Material Properties: Concrete

This example shows how to access concrete material properties according to different building codes.

```python
from pycivil.EXAStructural import materials, codes

# Select code and concrete class
code = codes.Code("NTC2018")
concrete = materials.Concrete(1, "Column C1")
concrete.setByCode(code, "C30/37")

# Characteristic values
print(f"Rck = {concrete.get_Rck():.1f} MPa")
print(f"fck = {concrete.get_fck():.1f} MPa")
print(f"fcm = {concrete.get_fcm():.1f} MPa")
print(f"fctm = {concrete.get_fctm():.1f} MPa")
print(f"Ecm = {concrete.get_Ecm():.0f} MPa")

# Design values
print(f"alpha_cc = {concrete.get_alphacc():.2f}")
print(f"gamma_c = {concrete.get_gammac():.1f}")
print(f"fcd = {concrete.cal_fcd():.1f} MPa")
print(f"sigma_c,max (characteristic) = {concrete.get_sigmac_max_c():.1f} MPa")
print(f"sigma_c,max (quasi-permanent) = {concrete.get_sigmac_max_q():.1f} MPa")
```

### Material Properties: Reinforcing Steel

This example shows how to access rebar material properties according to different building codes.

```python
from pycivil.EXAStructural import materials, codes

# Select code and steel class
code = codes.Code("NTC2018")
steel = materials.ConcreteSteel(1, "Rebars")
steel.setByCode(code, "B450C")

# Characteristic values
print(f"fyk = {steel.get_fsy():.1f} MPa")
print(f"ftk = {steel.get_fuk():.1f} MPa")
print(f"Es = {steel.get_Es():.0f} MPa")

# Design values
print(f"gamma_s = {steel.get_gammas():.2f}")
print(f"fyd = {steel.cal_fyd():.1f} MPa")
print(f"sigma_s,max (characteristic) = {steel.get_sigmas_max_c():.1f} MPa")
```

### RC Calculator with Multiple Load Cases

This example demonstrates a complete RC rectangular section check with multiple load combinations.

```python
from pycivil.EXAUtils.ucasefe import RCRectCalculator

calc = RCRectCalculator("python_course", "Section 1")
calc.setDescription("Beam section with multiple load cases")
calc.setLogLevel(3)  # verbose output
calc.setJobPath("./output")

KN = 1000
KNm = 1000000

# Section geometry
calc.setDimensions(300, 600)

# Materials
calc.setMaterialConcrete("NTC2018", "C25/30", "not aggressive")
calc.setMaterialRebars("NTC2018", "B450C", "not sensitive")

# Reinforcement
calc.addRebarsFromTop(dist_from_top=40, dist_rebars=40, num=3, diam=14)
calc.addRebarsFromBot(dist_from_bot=40, dist_rebars=40, num=6, diam=20)
calc.setStirrup(area=100, step=150, angle=90)

# SLS load cases
calc.addForce(N=150*KN, M=150*KNm, T=150*KN, descr="SLS Characteristic 1",
              limit_state="serviceability", frequency="characteristic",
              check_required=["SLE-NM"])

calc.addForce(N=100*KN, M=145*KNm, T=120*KN, descr="SLS Characteristic 2",
              limit_state="serviceability", frequency="quasi-permanent",
              check_required=["SLE-NM"])

calc.addForce(N=-100*KN, M=145*KNm, T=120*KN, descr="SLS Q-P with crack",
              limit_state="serviceability", frequency="quasi-permanent",
              check_required=["SLE-NM", "SLE-F"])

calc.addForce(N=-125*KN, M=125*KNm, T=125*KN, descr="SLS Frequent",
              limit_state="serviceability", frequency="frequent",
              check_required=["SLE-NM", "SLE-F"])

# ULS load cases
calc.addForce(N=-200*KN, M=200*KNm, T=200*KN, descr="ULS Combo 1",
              limit_state="ultimate",
              check_required=["SLU-T", "SLU-NM"])

calc.addForce(N=-200*KN, M=-200*KNm, T=100*KN, descr="ULS Combo 2",
              limit_state="ultimate",
              check_required=["SLU-NM"])

calc.addForce(N=-500*KN, M=350*KNm, T=200*KN, descr="ULS Combo 3",
              limit_state="ultimate",
              check_required=["SLU-NM"])

calc.addForce(N=100*KN, M=-200*KNm, T=70*KN, descr="ULS Combo 4",
              limit_state="ultimate",
              check_required=["SLU-NM"])

# Run and generate report
calc.run()
calc.buildReport()
```

### Generic Section Modeler (RCGenSectionsModeler)

This example shows how to model and analyze generic shaped RC sections with biaxial bending.

```python
from pathlib import Path
from pycivil.EXAStructural.rcgensolver.templateRCGen import (
    RCGenSectionsModeler,
    Analysis,
    ReportBuilder
)
from pycivil.EXAGeometry.geometry import (
    Node2d,
    Point2d,
    twoPointsOffset,
    twoPointsDivide
)
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.loads import (
    ForcesOnSection,
    Frequency_Enum,
    LimiteState_Enum
)

# Initialize modeler
modeler = RCGenSectionsModeler()
modeler.logLevel = 0
modeler.setJobPath("./output")

# Create rectangular section
modeler.addSectionModel(key="section_1", current=True)

# Define section geometry (300x600 centered at origin)
nodeBL = Node2d(x=-150, y=-300)
nodeBR = Node2d(x=+150, y=-300)
nodeTR = Node2d(x=+150, y=+300)
nodeTL = Node2d(x=-150, y=+300)

id_nodeBL = modeler.addNode(nodeBL)
id_nodeBR = modeler.addNode(nodeBR)
id_nodeTR = modeler.addNode(nodeTR)
id_nodeTL = modeler.addNode(nodeTL)

modeler.addTriangle(id_nodeBL, id_nodeBR, id_nodeTL)
modeler.addTriangle(id_nodeBR, id_nodeTR, id_nodeTL)

# Add corner rebars
cc = 50  # cover
rebarsDiameterTOP = 16
rebarsDiameterBOT = 22

rebar_center_BL = nodeBL + Point2d(cc, cc)
rebar_center_BR = nodeBR + Point2d(-cc, cc)
rebar_center_TR = nodeTR + Point2d(-cc, -cc)
rebar_center_TL = nodeTL + Point2d(cc, -cc)

modeler.addRebar(center=rebar_center_BL, diameter=rebarsDiameterBOT)
modeler.addRebar(center=rebar_center_BR, diameter=rebarsDiameterBOT)
modeler.addRebar(center=rebar_center_TR, diameter=rebarsDiameterTOP)
modeler.addRebar(center=rebar_center_TL, diameter=rebarsDiameterTOP)

# Add intermediate rebars along bottom and top edges
barsBOT_1, barsBOT_2 = twoPointsOffset(rebar_center_BL, rebar_center_BR)
barsBOT = twoPointsDivide(barsBOT_1, barsBOT_2, 4, False)
barsTOP_1, barsTOP_2 = twoPointsOffset(rebar_center_TR, rebar_center_TL)
barsTOP = twoPointsDivide(barsTOP_1, barsTOP_2, 4, False)

modeler.addRebarsGroup(diameter=rebarsDiameterBOT, points=barsBOT)
modeler.addRebarsGroup(diameter=rebarsDiameterTOP, points=barsTOP)

# Assign materials
code = Code("NTC2018")

concreteMat = Concrete(descr="Concrete C30/37")
concreteMat.setByCode(code, "C30/37")

rebarMat = ConcreteSteel(descr="Steel B450C")
rebarMat.setByCode(code, "B450C")

idMatCon = modeler.addConcreteLaw(mat=concreteMat, idm=1)
idMatReb = modeler.addRebarLaw(mat=rebarMat, idm=2)

modeler.assignConcreteLawToCurrentModel(idMatCon)
modeler.assignRebarLawToCurrentModel(idMatReb)

# Define load cases with biaxial bending
KN = 1000
KNm = 1000 * 1000

forces = {
    1: ForcesOnSection(
        id=1, Fz=-100.0 * KN, Mx=70 * KNm, My=70 * KNm,
        limitState=LimiteState_Enum.SERVICEABILITY,
        frequency=Frequency_Enum.CHARACTERISTIC
    ),
    2: ForcesOnSection(
        id=2, Fz=-50.0 * KN, Mx=65 * KNm, My=45 * KNm,
        limitState=LimiteState_Enum.SERVICEABILITY,
        frequency=Frequency_Enum.CHARACTERISTIC
    ),
    3: ForcesOnSection(
        id=3, Fz=80.0 * KN, Mx=80 * KNm, My=80 * KNm,
        limitState=LimiteState_Enum.ULTIMATE
    ),
    4: ForcesOnSection(
        id=4, Fz=-30.0 * KN, Mx=-80 * KNm, My=80 * KNm,
        limitState=LimiteState_Enum.ULTIMATE
    ),
}

# Assign forces and run analysis
modeler.assignForces(forces)
modeler.run(opt=Analysis.ELASTIC_SOLVER)
modeler.run(opt=Analysis.CHECK_ELASTIC)
modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)

# Plot results
modeler.plot(onlyWorst=False)
```

---

## Available Codes

PyCivil supports the following structural codes:

- **EC2** - Eurocode 2-1-1 (concrete in compression)
- **EC2-1-2** - Eurocode 2-1-2 (fire design)
- **NTC2008** - Italian NTC2008 standard
- **NTC2018** - Italian NTC2018 standard

```python
from pycivil.EXAStructural.codes import Code

# List available codes
print(Code.tabKeys)  # ['EC2', 'NTC2008', 'NTC2018', 'CIRC2008', 'CIRC2018']
```

## Check Types

PyCivil supports the following verification types:

| Check Code | Description |
|------------|-------------|
| `SLE-NM` | Serviceability Limit State - Normal stress and Moment |
| `SLE-F` | Serviceability Limit State - Crack width (Fessuration) |
| `SLU-NM` | Ultimate Limit State - Normal force and Moment |
| `SLU-T` | Ultimate Limit State - Shear (Taglio) |
| `SLU-NM-FIRE` | Ultimate Limit State - Fire design |
