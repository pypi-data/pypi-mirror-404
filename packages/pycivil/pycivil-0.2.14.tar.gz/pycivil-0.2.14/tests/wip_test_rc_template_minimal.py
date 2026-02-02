# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

# Drawing interation domain and evidenziate intersection on plot diagram

from pycivil.EXAStructural import templateRCRect as est

# Setting new instance of section with
# id = 1 and name = " testing intersection"
section = est.RCTemplRectEC2(1, "First Section testing intersection")

section.setDimH(500.0)
section.setDimW(300.0)

# 'MB' means medium bottom area
# 'MT' means medium top area
section.addSteelArea("MB", 40.0, 1000.0)
section.addSteelArea("MT", 40.0, 0.0)

section.setMaterials("C32/40", "B450C")

section.getMaterialConcr().set_alphacc(1.00)

# Adding Tension Point

pt = section.addTensionPoint2d(N=5.000e05, M=2.103e08)
p0 = section.addTensionPoint2d(N=000.0 * 1e3, M=000.0 * 1e6)

center = p0

# Building a set points of interaction diagramm
pointsCloud, bounding = section.interactionDomainBuild2d(nbPoints=200, bounding=True)

brox = bounding[1] - bounding[0]
broy = bounding[3] - bounding[2]

contained, pintersect, intfactor, other = pointsCloud.contains(
    pt.x, pt.y, rayFromCenter=True, center=p0, ro=(brox, broy)
)

linesOfMinimalPoints = []

if len(pintersect) == 2:
    section.addTensionPoint2d(pintersect[0])
    section.addTensionPoint2d(pintersect[1])
    linesOfMinimalPoints.append([pt, pintersect[0]])
    linesOfMinimalPoints.append([pt, pintersect[1]])
    print("intfactor = %1.6f" % intfactor)
    print("Punti di intersezione ....................")
    print(pintersect[0])
    print(pintersect[1])

section.addTensionPoint2d(center)

section.interactionDomainPlot2d(lines=linesOfMinimalPoints)

print("Contained = %1.0f" % contained)
print("Punto tensione ....................")
print(pt)
print("Centro ....................")
print(center)
