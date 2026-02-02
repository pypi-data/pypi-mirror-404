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
section.addTensionPoint2d(N=+4.0 * 1e3 * 1e3, M=-4.0 * 1e2 * 1e6)
section.addTensionPoint2d(N=+1.0 * 1e3 * 1e3, M=0.0)
section.setCurrentIdxTensionPoint2d(0)

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
minPointsCloud = section.interactionDomainBuild2d(
    nbPoints=100, alpha=section.alphaPhi(AsteelMin, AsteelMax, 0)
)
maxPointsCloud, bounding = section.interactionDomainBuild2d(
    nbPoints=100, alpha=section.alphaPhi(AsteelMin, AsteelMax, 1), bounding=True
)

print("Bounding of MAXIMUM domain")
print(bounding)

brox = bounding[1] - bounding[0]
broy = bounding[3] - bounding[2]

linesOfMinimalPoints = []

pt = est.eg.Point2d(500.0 * 1e3, 191.2 * 1e6)
contained, pintersect, intfactor, other = minPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy]
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    raise Exception("[500.0,191.2] - Containted in MIN !!!")
else:
    print("[500.0,191.2] - Not containted in MIN !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])


pt = est.eg.Point2d(+2.5 * 1e3 * 1e3, 2.93 * 1e2 * 1e6)
section.addTensionPoint2d(N=pt.x, M=pt.y)
contained, pintersect, intfactor, other = maxPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy]
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    print("[+2.5*1E+3*1E+3,2.93*1E+2*1E+6] - Containted in MAX !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])
else:
    raise Exception("[+2.5*1E+3*1E+3,2.93*1E+2*1E+6] - Not containted in MAX !!!")

pt = est.eg.Point2d(+2.5 * 1e3 * 1e3, 2.93 * 1e2 * 1e6)
section.addTensionPoint2d(N=pt.x, M=pt.y)
contained, pintersect, intfactor, other = maxPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy], center=est.eg.Point2d(pt.x, 0)
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    print("[+2.5*1E+3*1E+3,2.93*1E+2*1E+6] - Containted in MAX !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])
else:
    raise Exception("[+2.5*1E+3*1E+3,2.93*1E+2*1E+6] - Not containted in MAX !!!")

pt = est.eg.Point2d(+2.5 * 1e3 * 1e3, 2.93 * 1e2 * 1e6)
section.addTensionPoint2d(N=pt.x, M=pt.y)
contained, pintersect, intfactor, other = maxPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy], center=est.eg.Point2d(0, pt.y)
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    print("[+2.5*1E+3*1E+3,2.93*1E+2*1E+6] - Containted in MAX !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])
else:
    raise Exception("[+2.5*1E+3*1E+3,2.93*1E+2*1E+6] - Not containted in MAX !!!")


pt = est.eg.Point2d(500.0 * 1e3, 191.2 * 1e6)
contained, pintersect, intfactor, other = maxPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy]
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    print("[500.0,191.2] - Containted in MAX !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])
else:
    raise Exception("[500.0,191.2] - Not containted in MAX !!!")

pt = est.eg.Point2d(+4.0 * 1e3 * 1e3, -4.0 * 1e2 * 1e6)
contained, pintersect, intfactor, other = minPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy]
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    raise Exception("[-1.00*1E+3,-4.00*1E+2] - Containted in MIN !!!")
else:
    print("[-1.00*1E+3,-4.00*1E+2] - Not containted in MIN !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])

pt = est.eg.Point2d(+4.0 * 1e3 * 1e3, -4.0 * 1e2 * 1e6)
contained, pintersect, intfactor, other = maxPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy]
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    raise Exception("[-1.00*1E+3,-4.00*1E+2] - Containted in MAX !!!")
else:
    print("[-1.00*1E+3,-4.00*1E+2] - Not containted in MAX !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])


pt = est.eg.Point2d(+1.0 * 1e3 * 1e3, 0.0)
contained, pintersect, intfactor, other = minPointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, ro=[brox, broy]
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    print("[+1.00*1E+3,0.0] - Containted in MIN !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])
else:
    raise Exception("[+1.00*1E+3,0.0] - Not containted in MIN !!!")

pt = est.eg.Point2d(+1.0 * 1e3 * 1e3, 0.0)
contained, pintersect, intfactor, other = maxPointsCloud.contains(
    +1.0 * 1e3 * 1e3, 0.0, rayFromCenter=True, ro=[brox, broy]
)
print("Intersection factor")
print(intfactor)
section.addTensionPoints2d(pintersect)
if contained:
    print("[+1.00*1E+3,0.0] - Containted in MAX !!!")
    # print("Minimal distance: %1.6e"%minDistance)
    if len(pintersect) == 2:
        linesOfMinimalPoints.append([pt, pintersect[0]])
        linesOfMinimalPoints.append([pt, pintersect[1]])
else:
    raise Exception("[+1.00*1E+3,0.0] - Not containted in MAX !!!")

# Plot
section.interactionDomainPlot2d(lines=linesOfMinimalPoints)

# Some value
print(" Concrete Area = %1.3f" % section.calConcreteArea())
print("    Steel Area = %1.3f" % section.calSteelArea())
