# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pycivil.EXAStructural import templateRCRect as est

# Setting new instance of section with
# id = 1 and name = "First Section"
section = est.RCTemplRectEC2(1, "First Section")
section.setElementType("beam")

section.setDimH(500.0)
section.setDimW(300.0)

section.setMaterials("C32/40", "B450C")

print("Values before tension point")
print("Steel Area max = %1.3f" % section.calSteelAreaMax())
print("Steel Area min = %1.3f" % section.calSteelAreaMin())

# Adding Tension point Area
section.addTensionPoint2d(N=500.0 * 1e3, M=191.2 * 1e6)
section.addTensionPoint2d(N=-1.0 * 1e3 * 1e3, M=-4.0 * 1e2 * 1e6)
section.addTensionPoint2d(N=+1.0 * 1e3 * 1e3, M=0.0)
section.setCurrentIdxTensionPoint2d(0)

print("Values after tension point")
print("Steel Area max = %1.3f" % section.calSteelAreaMax())
print("Steel Area min = %1.3f" % section.calSteelAreaMin())

AsteelMax = section.calSteelAreaMax()
# AsteelMin = section.calSteelAreaMin()
AsteelMin = 10
AsteelMed = (AsteelMax + AsteelMin) / 2

# 'MB' means medium bottom area
# 'MT' means medium top area
section.addSteelArea("MB", 40.0, AsteelMed / 10)
# section.addSteelArea('MT',40.0,AsteelMed/2)
section.addSteelArea("MT", 40.0, 0.0)

# Building points set of interaction diagramm with min and max
minPointsCloud = section.interactionDomainBuild2d(
    nbPoints=100, alpha=section.alphaPhi(AsteelMin / 100, AsteelMax, 0), bounding=False
)
section.interactionDomainBuild2d(
    nbPoints=100,
    alpha=section.alphaPhi(AsteelMin / 100, AsteelMax, 0.01),
    bounding=False,
)
section.interactionDomainBuild2d(
    nbPoints=100,
    alpha=section.alphaPhi(AsteelMin / 100, AsteelMax, 0.1),
    bounding=False,
)
section.interactionDomainBuild2d(
    nbPoints=100,
    alpha=section.alphaPhi(AsteelMin / 100, AsteelMax, 0.2),
    bounding=False,
)
maxPointsCloud, bounding = section.interactionDomainBuild2d(
    nbPoints=100, alpha=section.alphaPhi(AsteelMin / 100, AsteelMax, 1), bounding=True
)

print("Bounding of MAXIMUM domain")
print(bounding)

linesOfMinimalPoints = []

brox = bounding[1] - bounding[0]
broy = bounding[3] - bounding[2]
print(f"Rox = {brox:1.6e} - Roy = {broy:1.6e}")

contained, minDistance, minPoint = minPointsCloud.contains(
    500.0 * 1e3, 191.2 * 1e6, convex=True
)
section.addTensionPoint2d(minPoint.x, minPoint.y)
if contained:
    raise Exception("[500.0,191.2] - Containted in MIN !!!")
else:
    print("[500.0,191.2] - Not containted in MIN !!!")
    print("Minimal distance: %1.6e" % minDistance)
    linesOfMinimalPoints.append([est.eg.Point2d(500.0 * 1e3, 191.2 * 1e6), minPoint])

contained, minDistance, minPoint = maxPointsCloud.contains(
    500.0 * 1e3, 191.2 * 1e6, convex=True
)
section.addTensionPoint2d(minPoint.x, minPoint.y)
if contained:
    print("[500.0,191.2] - Containted in MAX !!!")
    print("Minimal distance: %1.6e" % minDistance)
    linesOfMinimalPoints.append([est.eg.Point2d(500.0 * 1e3, 191.2 * 1e6), minPoint])
else:
    raise Exception("[500.0,191.2] - Not containted in MAX !!!")

contained, minDistance, minPoint = minPointsCloud.contains(
    -1.0 * 1e3 * 1e3, -4.0 * 1e2 * 1e6, convex=True
)
section.addTensionPoint2d(minPoint.x, minPoint.y)
if contained:
    raise Exception("[-1.00*1E+3,-4.00*1E+2] - Containted in MIN !!!")
else:
    print("[-1.00*1E+3,-4.00*1E+2] - Not containted in MIN !!!")
    print("Minimal distance: %1.6e" % minDistance)
    linesOfMinimalPoints.append(
        [est.eg.Point2d(-1.0 * 1e3 * 1e3, -4.0 * 1e2 * 1e6), minPoint]
    )

contained, minDistance, minPoint = maxPointsCloud.contains(
    -1.0 * 1e3 * 1e3, -4.0 * 1e2 * 1e6, convex=True
)
section.addTensionPoint2d(minPoint.x, minPoint.y)
if contained:
    raise Exception("[-1.00*1E+3,-4.00*1E+2] - Containted in MAX !!!")
else:
    print("[-1.00*1E+3,-4.00*1E+2] - Not containted in MAX !!!")
    print("Minimal distance: %1.6e" % minDistance)
    linesOfMinimalPoints.append(
        [est.eg.Point2d(-1.0 * 1e3 * 1e3, -4.0 * 1e2 * 1e6), minPoint]
    )

contained, minDistance, minPoint = minPointsCloud.contains(
    +1.0 * 1e3 * 1e3, 0.0, convex=True
)
section.addTensionPoint2d(minPoint.x, minPoint.y)
if contained:
    print("[+1.00*1E+3,0.0] - Containted in MIN !!!")
    print("Minimal distance: %1.6e" % minDistance)
    linesOfMinimalPoints.append([est.eg.Point2d(+1.0 * 1e3 * 1e3, 0.0), minPoint])
else:
    raise Exception("[+1.00*1E+3,0.0] - Not containted in MIN !!!")

contained, minDistance, minPoint = maxPointsCloud.contains(
    +1.0 * 1e3 * 1e3, 0.0, convex=True
)
section.addTensionPoint2d(minPoint.x, minPoint.y)
if contained:
    print("[+1.00*1E+3,0.0] - Containted in MAX !!!")
    print("Minimal distance: %1.6e" % minDistance)
    linesOfMinimalPoints.append([est.eg.Point2d(+1.0 * 1e3 * 1e3, 0.0), minPoint])
else:
    raise Exception("[+1.00*1E+3,0.0] - Not containted in MAX !!!")

# Plot
section.interactionDomainPlot2d(lines=linesOfMinimalPoints, markers=False)

# Some value
print(" Concrete Area = %1.3f" % section.calConcreteArea())
print("    Steel Area = %1.3f" % section.calSteelArea())
