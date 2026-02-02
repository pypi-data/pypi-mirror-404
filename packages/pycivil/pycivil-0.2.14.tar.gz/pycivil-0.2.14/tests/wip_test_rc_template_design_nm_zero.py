# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import math

from pycivil.EXAStructural import templateRCRect as est

# Setting new instance of section with
# id = 1 and name = "First Section"
section = est.RCTemplRectEC2(1, "First Section")
section.setElementType("beam")

# Setting dimension
section.setDimH(500.0)
section.setDimW(300.0)

# Setting materials
section.setMaterials("C32/40", "B450C")

# Adding Tension point Area
pt = est.eg.Point2d(+2.5 * 1e3 * 1e3, 2.93 * 1e2 * 1e6)
section.addTensionPoint2d(N=pt.x, M=pt.y)
# section can have many tension points then we need choosing the current
section.setCurrentIdxTensionPoint2d(0)

# Finding area max and min with current tension point
print("Values after tension point")
print("Steel Area max = %1.3f" % section.calSteelAreaMax())
print("Steel Area min = %1.3f" % section.calSteelAreaMin())

AsteelMax = section.calSteelAreaMax()
AsteelMin = section.calSteelAreaMin()
AsteelMed = (AsteelMax + AsteelMin) / 2

# 'MB' means medium bottom area
# 'MT' means medium top area
section.addSteelArea("MB", 40.0, AsteelMed / 2)
section.addSteelArea("MT", 40.0, AsteelMed / 2)

# Building points set of interaction diagramm with min and max
areaFactor0 = 0
minPointsCloud = section.interactionDomainBuild2d(
    nbPoints=100, alpha=section.alphaPhi(AsteelMin, AsteelMax, areaFactor0)
)
areaFactor1 = 1
maxPointsCloud, bounding = section.interactionDomainBuild2d(
    nbPoints=100,
    alpha=section.alphaPhi(AsteelMin, AsteelMax, areaFactor1),
    bounding=True,
)

print("Bounding of MAXIMUM domain")
print(bounding)

brox = bounding[1] - bounding[0]
broy = bounding[3] - bounding[2]

linesOfMinimalPoints = []

contained, pintersect, intfactor0, other = minPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=(brox, broy)
)

print("Intersection factor")
print(intfactor0)
section.addTensionPoints2d(pintersect)
if contained:
    raise Exception("Pt - Containted in MIN !!!")
else:
    print("[500.0,191.2] - Not containted in MIN !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])

contained, pintersect, intfactor1, other = maxPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=(brox, broy)
)

print("Intersection factor")
print(intfactor1)
section.addTensionPoints2d(pintersect)
if contained:
    print("[+2.5*1E+3*1E+3,2.93*1E+2*1E+6] - Containted in MAX !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])
else:
    raise Exception("Pt - Not containted in MAX !!!")

Area_n = areaFactor1
Area_nm1 = areaFactor0
Fx_n = intfactor1 - 1.0
Fx_nm1 = intfactor0 - 1.0

toll = 1e-5
maxIt = 100
for i in range(1, maxIt):
    print("Step i= %1.i" % i)

    Area_np1 = Area_n - ((Area_n - Area_nm1) / (Fx_n - Fx_nm1)) * Fx_n
    print("Area_np1= %1.6e" % Area_np1)

    Area_nm1 = Area_n
    Area_n = Area_np1

    Fx_nm1 = Fx_n

    pointsCloud = section.interactionDomainBuild2d(
        nbPoints=100, alpha=section.alphaPhi(AsteelMin, AsteelMax, Area_n)
    )
    contained, pintersect, intfactor, other = pointsCloud.contains(
        pt.x, pt.y, rayFromCenter=True, ro=(brox, broy)
    )

    Fx_n = intfactor - 1.0
    print("toll = %1.6e" % math.sqrt(math.pow(Fx_n, 2)))

    if math.sqrt(math.pow(Fx_n, 2)) < toll:
        break


# Plot
section.interactionDomainPlot2d(lines=linesOfMinimalPoints, markers=False)
