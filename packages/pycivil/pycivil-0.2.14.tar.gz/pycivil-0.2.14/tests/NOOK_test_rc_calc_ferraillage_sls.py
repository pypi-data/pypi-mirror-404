# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

# VLAD 500.0 300.0 C32/40 B450C 0.85 0KN 193KNm alfa 0 603mm2
import csv
import os
import time

from pycivil.EXAStructural import templateRCRect as est
from pycivil.EXAUtils import codeAster as au

plottingOnScreen = False
markers = False

start = time.time()

errors = []
errors_skipped = []
columnForCSV = []

fileName = os.path.join(
    os.path.dirname(os.path.realpath(est.__file__)), "../tests/csv_sls.resu"
)

tableFerr12 = au.AsterTableReader(
    fileName, "#PYTHON_START_tbferr12", "#PYTHON_END_tbferr12"
)
tableFerr12.parse()
AYI = tableFerr12.fetchColumnWithName("AYI")
AYS = tableFerr12.fetchColumnWithName("AYS")

tableEfge12 = au.AsterTableReader(
    fileName, "#PYTHON_START_tbefge12", "#PYTHON_END_tbefge12"
)
tableEfge12.parse()
N = tableEfge12.fetchColumnWithName("N")
MFY = tableEfge12.fetchColumnWithName("MFY")
MFZ = tableEfge12.fetchColumnWithName("MFZ")

MAILLE12 = tableFerr12.fetchColumnWithName("MAILLE")

areaSteel12 = []
for idx, _v in enumerate(AYI):
    idx
    if AYI[idx] != 0.0:
        areaSteel12.append(AYI[idx] * 1e06)
    if AYS[idx] != 0.0:
        areaSteel12.append(AYS[idx] * 1e06)

MFZList12 = []
NList12 = []
for idx, _v in enumerate(MFZ[: int(len(MFZ) / 2)]):
    MFZList12.append(abs((MFZ[idx * 2] + MFZ[idx * 2 + 1]) / 2.0) * 1e03)
    NList12.append(-(N[idx * 2] + N[idx * 2 + 1]) / 2)

section = None
for idx, _v in enumerate(MFZList12):
    columnCSVName = "section_01-300x500"
    columnCSVPointN = str("%1.2f" % (NList12[idx] * 1e-03))
    columnCSVPointM = str("%1.2f" % (MFZList12[idx] * 1e-06))

    strCase = (
        columnCSVName
        + " - mesh: "
        + MAILLE12[idx]
        + " - "
        + "N="
        + columnCSVPointN
        + " [KN] - "
        + "M="
        + columnCSVPointM
        + " [KN*m]"
    )
    Area, extra, section = est.RCTemplRectEC2DesignNM(
        name=strCase,
        elementType="beam",
        steel="B450C",
        concrete="C32/40",
        sectionH=500.0,
        sectionW=300.0,
        topRecover=40.0,
        botRecover=40.0,
        N=NList12[idx],
        M=MFZList12[idx],
        toll=1e-5,
        toll_bisec=1e-3,
        maxIt=100,
        plot=plottingOnScreen,
        alphaTopBot=0,
        factorStart=0,
        factorEnd=1,
        points=100,
        logLevel=0,
        markersOnDomain=markers,
        savingSingleDomains=False,
        sigmacMax=0.65 * 32,
        sigmasMax=0.80 * 450,
        homogeneization=15.0,
        SLS=True,
        outSection=True,
    )
    columnCSVArea = "%1.3f" % Area
    print("===============")
    print("Case Test string:" + strCase)
    print("Area with bisection or secants: %1.3f" % Area)
    print("Area with FERRAILLAGE 1D: %1.3f" % areaSteel12[idx])

    if extra is not None:
        print("From elastic alghoritm ...")
        print(
            "sigma_c = %1.3E - sigma_s = %2.3E - xi = %3.3E "
            % (-extra[5], -extra[6], extra[7])
        )
        section.assignSteelAreaWithAlphaWeight(Area)
        if abs(NList12[idx]) < 0.0000005:
            # print(section)
            extra_analytical = section.solverSLS_M(MFZList12[idx])
            print("From analytical with only M ...")
        else:
            extra_analytical = section.solverSLS_NM(-NList12[idx], MFZList12[idx])
            print("From analytical with N and M ...")

        print(
            "sigma_c = %1.3E - sigma_s = %2.3E - xi = %3.3E "
            % (extra_analytical[0], extra_analytical[1], extra_analytical[2])
        )
        error1 = abs((-extra[5] - extra_analytical[0]) / extra_analytical[0])
        # in code_aster compression is positive
        # in python  compression is negative
        error2 = abs((-extra[6] - extra_analytical[1]) / extra_analytical[1])
        error3 = abs((extra[7] - extra_analytical[2]) / extra_analytical[2])
        error_from_analitycal = max(error1, error2, error3)
        print("Error from analytical : %1.3E" % error_from_analitycal)
    else:
        print("Elastic algorithm not defined ...")
        print("sigma_c = N.D. - sigma_s = N.D. - xi = N.D. ")
        print("Analytical algorithm not defined ...")
        print("sigma_c = N.D. - sigma_s = N.D. - xi = N.D. ")
        print("Error from analytical : N.D.")

    error = (areaSteel12[idx] - Area) / (Area)
    if not (areaSteel12[idx] == -1000000.0):
        errors.append(abs(error))
    else:
        errors_skipped.append(abs(error))
    print("Error: %1.3e" % error)
    print("===============")
    columnForCSV.append(
        [
            columnCSVName,
            "B450C",
            "C32/40",
            columnCSVPointN,
            columnCSVPointM,
            columnCSVArea,
        ]
    )

tableFerr34 = au.AsterTableReader(
    fileName, "#PYTHON_START_tbferr34", "#PYTHON_END_tbferr34"
)
tableFerr34.parse()
AZI = tableFerr34.fetchColumnWithName("AZI")
AZS = tableFerr34.fetchColumnWithName("AZS")

tableEfge34 = au.AsterTableReader(
    fileName, "#PYTHON_START_tbefge34", "#PYTHON_END_tbefge34"
)
tableEfge34.parse()

N = tableEfge34.fetchColumnWithName("N")
MFY = tableEfge34.fetchColumnWithName("MFY")
MFZ = tableEfge34.fetchColumnWithName("MFZ")

MAILLE34 = tableFerr34.fetchColumnWithName("MAILLE")

areaSteel34 = []
for idx, _v in enumerate(AZI):
    if AZI[idx] != 0.0:
        areaSteel34.append(AZI[idx] * 1e06)
    if AZS[idx] != 0.0:
        areaSteel34.append(AZS[idx] * 1e06)

MFYList34 = []
NList34 = []
for idx, _v in enumerate(MFY[: int(len(MFY) / 2)]):
    # MFYList34.append(abs( ( MFY[idx*2] + MFY[idx*2+1] ) / 2.0 )*1E+03 )
    MFYList34.append(abs((MFY[idx * 2] + MFY[idx * 2 + 1]) / 2.0) * 1e03)
    NList34.append(-(N[idx * 2] + N[idx * 2 + 1]) / 2)

idxerror = []
for idx, _v in enumerate(MFYList34):
    columnCSVName = "section_02-500x300"
    columnCSVPointN = str("%1.2f" % (NList34[idx] * 1e-03))
    columnCSVPointM = str("%1.2f" % (MFYList34[idx] * 1e-06))

    strCase = (
        columnCSVName
        + " - mesh: "
        + MAILLE34[idx]
        + " - N="
        + columnCSVPointN
        + " [KN] - "
        + "M="
        + columnCSVPointM
        + " [KN*m]"
    )
    Area, extra, section = est.RCTemplRectEC2DesignNM(
        name=strCase,
        elementType="beam",
        steel="B450C",
        concrete="C32/40",
        alphacc=1.00,
        sectionH=300.0,
        sectionW=500.0,
        topRecover=40.0,
        botRecover=40.0,
        N=NList34[idx],
        M=MFYList34[idx],
        toll=1e-5,
        toll_bisec=1e-3,
        maxIt=100,
        plot=plottingOnScreen,
        alphaTopBot=0,
        factorStart=0,
        factorEnd=1,
        points=100,
        logLevel=0,
        markersOnDomain=markers,
        savingSingleDomains=False,
        sigmacMax=0.65 * 32,
        sigmasMax=0.80 * 450,
        homogeneization=15.0,
        SLS=True,
        outSection=True,
    )
    columnCSVArea = "%1.3f" % Area
    print("===============")
    print("Case Test string:" + strCase)
    print("Area with bisection or secants: %1.3f" % Area)
    print("Area with FERRAILLAGE 1D: %1.3f" % areaSteel34[idx])

    if extra is not None:
        print("From elastic alghoritm ...")
        print(
            "sigma_c = %1.3E - sigma_s = %2.3E - xi = %3.3E "
            % (-extra[5], -extra[6], extra[7])
        )
        section.assignSteelAreaWithAlphaWeight(Area)
        if abs(NList34[idx]) < 0.0000005:
            # print(section)
            extra_analytical = section.solverSLS_M(MFYList34[idx])
            print("From analytical with only M ...")
        else:
            extra_analytical = section.solverSLS_NM(-NList34[idx], MFYList34[idx])
            print("From analytical with N and M ...")

        print(
            "sigma_c = %1.3E - sigma_s = %2.3E - xi = %3.3E "
            % (extra_analytical[0], extra_analytical[1], extra_analytical[2])
        )
        error1 = abs((-extra[5] - extra_analytical[0]) / extra_analytical[0])
        # in code_aster compression is positive
        # in python  compression is negative
        error2 = abs((-extra[6] - extra_analytical[1]) / extra_analytical[1])
        error3 = abs((extra[7] - extra_analytical[2]) / extra_analytical[2])
        error_from_analitycal = max(error1, error2, error3)
        print("Error from analytical : %1.3E" % error_from_analitycal)
    else:
        print("Elastic algorithm not defined ...")
        print("sigma_c = N.D. - sigma_s = N.D. - xi = N.D. ")
        print("Analytical algorithm not defined ...")
        print("sigma_c = N.D. - sigma_s = N.D. - xi = N.D. ")
        print("Error from analytical : N.D.")

    error = (areaSteel34[idx] - Area) / (Area)
    if not (areaSteel34[idx] == -1000000.0):
        if abs(error) > 1e-02:
            idxerror.append(idx)
            print("INDICE ERRORE %1.0i" % idx)
            print(
                "ERRORE ECCESSIVO *******************************************************************"
            )
            raise Exception("ERRORE ECCESSIVO")
        errors.append(abs(error))
    else:
        errors_skipped.append(abs(error))
    print("Error: %1.3e" % error)
    print("===============")
    columnForCSV.append(
        [
            columnCSVName,
            "B450C",
            "C32/40",
            columnCSVPointN,
            columnCSVPointM,
            columnCSVArea,
        ]
    )

tableFerr56 = au.AsterTableReader(
    fileName, "#PYTHON_START_tbferr56", "#PYTHON_END_tbferr56"
)
tableFerr56.parse()
ATOT = tableFerr56.fetchColumnWithName("ATOT")
ATOT5 = tableFerr56.fetchColumnWithName("ATOT", 5)
ATOT6 = tableFerr56.fetchColumnWithName("ATOT", 6)

tableEfge56 = au.AsterTableReader(
    fileName, "#PYTHON_START_tbefge56", "#PYTHON_END_tbefge56"
)
tableEfge56.parse()
N = tableEfge56.fetchColumnWithName("N")
MFY = tableEfge56.fetchColumnWithName("MFY")
MFZ = tableEfge56.fetchColumnWithName("MFZ")

MAILLE56 = tableFerr56.fetchColumnWithName("MAILLE")

areaSteel56 = []
# for idx, v in enumerate(ATOT):
#    areaSteel56.append(ATOT[idx]*1E+06)

MFYList56 = []
NList56 = []
B56 = []
H56 = []

for idx, _v in enumerate(MFY[: int(len(MFY) / 2)]):
    MFYi = ((MFY[idx * 2] + MFY[idx * 2 + 1]) / 2.0) * 1e03
    MFZi = ((MFZ[idx * 2] + MFZ[idx * 2 + 1]) / 2.0) * 1e03
    if abs(MFYi) > abs(MFZi) and abs(MFZi) / abs(MFYi) < 0.05:
        MFYList56.append(MFYi)
        B56.append(500.0)
        H56.append(300.0)
        NList56.append(-(N[idx * 2] + N[idx * 2 + 1]) / 2)
        areaSteel56.append(ATOT6[idx - (len(ATOT6))] * 1e06)
    elif abs(MFZi) > abs(MFYi) and abs(MFYi) / abs(MFZi) < 0.05:
        MFYList56.append(MFZi)
        B56.append(300.0)
        H56.append(500.0)
        NList56.append(-(N[idx * 2] + N[idx * 2 + 1]) / 2)
        areaSteel56.append(ATOT5[idx] * 1e06)

for idx, _v in enumerate(MFYList56):
    strs = f"{B56[idx]:1.0f}x{H56[idx]:2.0f}"

    columnCSVName = "section_03-" + strs
    columnCSVPointN = str("%1.2f" % (NList56[idx] * 1e-03))
    columnCSVPointM = str("%1.2f" % (MFYList56[idx] * 1e-06))

    strCase = (
        columnCSVName
        + "- mesh: "
        + MAILLE56[idx]
        + " - N="
        + str("%1.2f" % (NList56[idx] * 1e-03))
        + " [KN] - "
        + "M="
        + str("%1.2f" % (MFYList56[idx] * 1e-06))
        + " [KN*m]"
    )
    Area, extra, section = est.RCTemplRectEC2DesignNM(
        name=strCase,
        elementType="column",
        steel="B450C",
        concrete="C32/40",
        alphacc=1.00,
        sectionH=H56[idx],
        sectionW=B56[idx],
        topRecover=40.0,
        botRecover=40.0,
        N=NList56[idx],
        M=MFYList56[idx],
        toll=1e-5,
        toll_bisec=1e-5,
        maxIt=100,
        plot=plottingOnScreen,
        alphaTopBot=1,
        factorStart=0,
        factorEnd=1,
        points=100,
        logLevel=0,
        markersOnDomain=markers,
        savingSingleDomains=False,
        sigmacMax=0.65 * 32,
        sigmasMax=0.80 * 450,
        homogeneization=15.0,
        SLS=True,
        outSection=True,
    )
    columnCSVArea = "%1.3f" % Area
    print("===============")
    print("Case Test string:" + strCase)
    print("Area with bisection or secants: %1.3f" % Area)
    print("Area with FERRAILLAGE 1D: %1.3f" % areaSteel56[idx])

    if extra is not None:
        print("From elastic alghoritm ...")
        print(
            "sigma_c = %1.3E - sigma_s = %2.3E - xi = %3.3E "
            % (-extra[5], -extra[6], extra[7])
        )
        section.assignSteelAreaWithAlphaWeight(Area)
        if abs(NList56[idx]) < 0.0000005:
            # print(section)
            extra_analytical = section.solverSLS_M(MFYList56[idx])
            print("From analytical with only M ...")
        else:
            extra_analytical = section.solverSLS_NM(-NList56[idx], MFYList56[idx])
            print("From analytical with N and M ...")

        print(
            "sigma_c = %1.3E - sigma_s = %2.3E - xi = %3.3E "
            % (extra_analytical[0], extra_analytical[1], extra_analytical[2])
        )
        error1 = abs((-extra[5] - extra_analytical[0]) / extra_analytical[0])
        # in code_aster compression is positive
        # in python  compression is negative
        error2 = abs((-extra[6] - extra_analytical[1]) / extra_analytical[1])
        error3 = abs((extra[7] - extra_analytical[2]) / extra_analytical[2])
        error_from_analitycal = max(error1, error2, error3)
        print("Error from analytical : %1.3E" % error_from_analitycal)
    else:
        print("Elastic algorithm not defined ...")
        print("sigma_c = N.D. - sigma_s = N.D. - xi = N.D. ")
        print("Analytical algorithm not defined ...")
        print("sigma_c = N.D. - sigma_s = N.D. - xi = N.D. ")
        print("Error from analytical : N.D.")

    if not (areaSteel56[idx] == -1000000.0):
        error = (areaSteel56[idx] - Area) / (Area)
        errors.append(abs(error))
    else:
        errors_skipped.append(abs(error))
    print("Error: %1.3e" % error)
    print("===============")
    columnForCSV.append(
        [
            columnCSVName,
            "B450C",
            "C32/40",
            columnCSVPointN,
            columnCSVPointM,
            columnCSVArea,
        ]
    )

print("===============")
print("   Nb tests: %1.0i" % len(errors))
print(" Nb skipped: %1.0i" % len(errors_skipped))
print("  Max error: %1.3e" % max(errors))
print("  Min error: %1.3e" % min(errors))
print("===============")

end = time.time()
print(end - start)

with open("for_latex_results_sls.csv", mode="w") as csv_file:
    csv_writer = csv.writer(
        csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
    )
    for r in columnForCSV:
        csv_writer.writerow(r)
