# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

# VLAD 500.0 300.0 C32/40 B450C 0.85 0KN 193KNm alfa 0 603mm2
import time

from pycivil.EXAStructural import templateRCRect as est

start = time.time()

plotDomain = True

Area = est.RCTemplRectEC2DesignNM(
    name="section_01",
    elementType="beam",
    steel="B450C",
    concrete="C32/40",
    sectionH=500.0,
    sectionW=300.0,
    topRecover=40.0,
    botRecover=40.0,
    N=+0.00 * 1e3 * 1e3,
    M=(+1.04 + 0.94) / 2 * 1e2 * 1e6,
    toll=1e-5,
    toll_bisec=1e-3,
    maxIt=100,
    plot=True,
    alphaTopBot=0,
    factorStart=0,
    factorEnd=1,
    points=100,
    logLevel=1,
)

print(Area)
print("******************")
print("Minimal steel area: %1.1f" % Area[0])
print("******************")

section = est.RCTemplRectEC2(1, "section_01")
section.setDimH(500.0)
section.setDimW(300.0)
section.addSteelArea("MB", 40.0, 572.0)
section.addSteelArea("MT", 40.0, 0.0)

section.setMaterials("C32/40", "B450C")
section.addTensionPoint2d(N=0.0, M=(+1.04 + 0.94) / 2 * 1e2 * 1e6)
section.interactionDomainBuild2d(nbPoints=100, alpha=1.0)
section.interactionDomainPlot2d()

Area = est.RCTemplRectEC2DesignNM(
    name="section_02",
    elementType="beam",
    steel="B450C",
    concrete="C32/40",
    sectionH=500.0,
    sectionW=300.0,
    topRecover=40.0,
    botRecover=40.0,
    N=+0.5 * 1e3 * 1e3,
    M=(+1.91 + 1.72) / 2 * 1e2 * 1e6,
    toll=1e-5,
    toll_bisec=1e-3,
    maxIt=100,
    plot=plotDomain,
    alphaTopBot=0,
    factorStart=0,
    factorEnd=1,
    points=100,
    logLevel=1,
)

print("******************")
print("Minimal steel area: %1.1f" % Area[0])
print("******************")

Area = est.RCTemplRectEC2DesignNM(
    name="section_03",
    elementType="beam",
    steel="B450C",
    concrete="C32/40",
    sectionH=500.0,
    sectionW=300.0,
    topRecover=30.0,
    botRecover=30.0,
    N=+2.0 * 1e3 * 1e3,
    M=+1.91 * 1e2 * 1e6,
    toll=1e-5,
    toll_bisec=1e-3,
    maxIt=100,
    plot=plotDomain,
    alphaTopBot=0.0,
    factorStart=0,
    factorEnd=1,
    points=50,
    logLevel=1,
)
print("******************")
print("Minimal steel area: %1.1f" % Area[0])
print("******************")

Area = est.RCTemplRectEC2DesignNM(
    name="section_04",
    elementType="beam",
    steel="B450C",
    concrete="C32/40",
    sectionH=500.0,
    sectionW=300.0,
    topRecover=30.0,
    botRecover=30.0,
    N=-1.9 * 1e3 * 1e3,
    M=+6.00 * 1e2 * 1e6,
    toll=1e-5,
    toll_bisec=1e-3,
    maxIt=100,
    plot=plotDomain,
    alphaTopBot=0.0,
    factorStart=0,
    factorEnd=1,
    logLevel=1,
)

print("******************")
print("Minimal steel area: %1.1f" % Area[0])
print("******************")

end = time.time()
print(end - start)
