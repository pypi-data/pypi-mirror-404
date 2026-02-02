# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pycivil.EXAStructural import templateRCRect as est

# Setting new instance of section with
# id = 1 and name = "First Section"
section = est.RCTemplRectEC2(1, "First Section")

section.setDimH(500.0)
section.setDimW(300.0)

# 'MB' means medium bottom area
# 'MT' means medium top area
section.addSteelArea("MB", 40.0, 600.0)
section.addSteelArea("MT", 40.0, 600.0)

section.setMaterials("C32/40", "B450C")

# Adding Tension Points
KN = 1000
KNm = 1000000
section.addTensionPoint2d(N=500.0 * KN, M=191.2 * KNm)
section.addTensionPoint2d(N=0.0 * KN, M=104.0 * KNm)

nb = 30

# Building a set points of interaction diagramm
section.interactionDomainBuild2d(nbPoints=nb)

# Adding new Area
section.addSteelArea("MB", 40.0, 600.0)
section.addSteelArea("MT", 40.0, 600.0)


# Building a new points set of interaction diagramm
section.interactionDomainBuild2d(nbPoints=nb, SLS=False)
section.interactionDomainBuild2d(nbPoints=nb, SLS=True)
section.interactionDomainBuild2d(nbPoints=nb, alpha=2.0)
section.interactionDomainBuild2d(nbPoints=nb, alpha=3.0)

section.interactionDomainPlot2d(xLabel="N [KN]", yLabel="M [KN*m]")

print(section)
