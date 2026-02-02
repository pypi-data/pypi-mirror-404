# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

"""
Created on Sun Nov 07 16:33:00 2021

@author: lpaone
"""

import math
import unittest

import pycivil.EXAStructural.templateRCRect as Est

def build_section(dimW, dimH, Ned, Med, distFromTop, distFromBot, steelAreaBottom, steelAreaTop, homogenization):

    section = Est.RCTemplRectEC2(1, "First Section")

    # Setting dimension concrete
    section.setDimH(dimH)
    section.setDimW(dimW)

    # Setting rebar
    section.addSteelArea("MB", distFromBot, steelAreaBottom)
    section.addSteelArea("MT", distFromTop, steelAreaTop)

    # Setting materials
    section.setMaterials(homogenization=homogenization)

    # Solver with iteration method
    #
    sol = section.solverSLS_NM(N=Ned * 1e3, M=Med * 1e6)

    return sol, section

def buildTest(
    dimW,
    dimH,
    steelAreaTop,
    steelAreaBottom,
    distFromTop,
    distFromBot,
    Ned,
    Med,
    sigmacRef=None,
    sigmasRef=None,
    xiRef=None,
    toll=0.001,
    homogenization=15.0,
    name="",
    sigmacReg=None,
    sigmasReg=None,
    xiReg=None,
    plot=False,
):
    # Solver with iteration method
    #
    sol, section = build_section(
        dimW,
        dimH,
        Ned,
        Med,
        distFromTop,
        distFromBot,
        steelAreaBottom,
        steelAreaTop,
        homogenization
    )
    # From Tuple to List for modification
    sol_list = list(sol)

    # Because solverSLS_NM method use xi measure from top to bottom always, when
    # happen that compressions are on bottom we need to change with top measure.
    if section.getConcrStress()[0] < 0:
        sol_list[2] = dimH - sol_list[2]

    sigma_c_domain, sigma_s_domain, xi_domain, pintersect = (
        section.solverSLS_NM_withDomain(Ned=Ned, Med=Med, points_on_domain=300))

    section.addTensionPoint2d(N=-Ned * 1e3, M=Med * 1e6)
    assert isinstance(pintersect, list)
    section.addTensionPoint2d(N=pintersect[0].x, M=pintersect[0].y)

    tensionPoint = Est.Point2d(-Ned * 1e3, Med * 1e6)
    zeroPoint = Est.Point2d(0, 0)

    lines = [
        [tensionPoint, pintersect[0]],
        [zeroPoint, tensionPoint]
    ]

    if plot:
        section.interactionDomainPlot2d(xLabel="xxx", yLabel="yyy", lines=lines)

    # Reference errors
    #
    if sigmacRef is None:
        sigmacRef = -1
        sigmacErr = -1
    elif sigmacRef == 0.0:
        sigmacErr = abs(sigmacRef - sol_list[0])
    else:
        sigmacErr = abs((sigmacRef - sol_list[0]) / sigmacRef)

    if sigmasRef is None:
        sigmasRef = -1
        sigmasErr = -1
    else:
        sigmasErr = abs((sigmasRef - sol_list[1]) / sigmasRef)

    if xiRef is None:
        xiRef = -1
        xiErr = -1
    else:
        xiErr = abs((xiRef - sol_list[2]) / xiRef)

    if max([sigmacErr, sigmasErr, xiErr]) < toll:
        sentence = "--> OK"
    else:
        sentence = "<<<<<<<<<<<<<<<<<<<<<<<<< KO"

    # Not regression errors
    #
    if sigmacReg is None:
        sigmacErrReg = -1
    elif sigmacReg == 0.0:
        sigmacErrReg = abs(sigmacReg - sol_list[0])
    else:
        sigmacErrReg = abs((sigmacReg - sol_list[0]) / sigmacReg)

    if sigmasReg is None:
        sigmasReg = -1
        sigmasErrReg = -1
    else:
        sigmasErrReg = abs((sigmasReg - sol_list[1]) / sigmasReg)

    if xiReg is None:
        xiErrReg = -1
    else:
        xiErrReg = abs((xiReg - sol_list[2]) / xiReg)

    if max([sigmacErrReg, sigmasErrReg, xiErrReg]) < toll:
        sentenceReg = "--> OK"
    else:
        sentenceReg = "<<<<<<<<<<<<<<<<<<<<<<<<< KO"

    # From elastic domain errors
    #
    if sigma_c_domain != 0.0:
        sigmacErrDom = abs((sigma_c_domain - sol_list[0]) / sigma_c_domain)
    else:
        sigmacErrDom = abs(sigma_c_domain - sol_list[0])

    sigmasErrDom = abs((sigma_s_domain - sol_list[1]) / sigma_s_domain)
    xiErrDom = abs((xi_domain - sol_list[2]) / xi_domain)

    if max([sigmacErrDom, sigmasErrDom, xiErrDom]) < toll:
        sentenceDom = "--> OK"
    else:
        sentenceDom = "<<<<<<<<<<<<<<<<<<<<<<<<< KO"

    print(
        "--------------------------------------------------------------------------------"
    )
    print(f"Ned = {Ned:3.0f} Med = {Med:3.0f}")
    print("Concrete stresses: ", section.getConcrStress())
    print("Steel    stresses: ", section.getSteelStress())
    print(
        "W = %3.f H = %3.f area Top = %3.f area Bottom = %3.f topDist = %3.f botDist = %3.f "
        % (dimW, dimH, steelAreaTop, steelAreaBottom, distFromTop, distFromBot)
    )
    print(
        "      ref sigmac =%8.3f -       ref sigmas =%8.3f -       ref xi =%8.3f name of reference ** %s **"
        % (sigmacRef, sigmasRef, xiRef, name)
    )
    assert sigmacReg is not None
    print(
        f"      reg sigmac =%8.3f -       reg sigmas =%8.3f -       reg xi =%8.3f"
        % (sigmacReg, sigmasReg, xiReg)
    )
    assert sol_list[0] is not None
    assert sol_list[1] is not None
    assert sol_list[2] is not None
    print(
        "          sigmac =%8.3f -           sigmas =%8.3f -           xi =%8.3f from classical algorythm"
        % (sol_list[0], sol_list[1], sol_list[2])
    )
    print(
        "      dom sigmac =%8.3f -       dom sigmas =%8.3f -       dom xi =%8.3f from elastic domain"
        % (sigma_c_domain, sigma_s_domain, xi_domain)
    )
    print(
        "--------------------------------------------------------------------------------"
    )
    print(
        "ERR   ref sigmac =%8.3f -       ref sigmas =%8.3f -       ref xi =%8.3f - RESULT: %s"
        % (sigmacErr, sigmasErr, xiErr, sentence)
    )
    print(
        "ERR   reg sigmac =%8.3f -       reg sigmas =%8.3f -       reg xi =%8.3f - RESULT: %s"
        % (sigmacErrReg, sigmasErrReg, xiErrReg, sentenceReg)
    )
    print(
        "ERR   dom sigmac =%8.3f -       dom sigmas =%8.3f -       dom xi =%8.3f - RESULT: %s"
        % (sigmacErrDom, sigmasErrDom, xiErrDom, sentenceDom)
    )
    print(
        "--------------------------------------------------------------------------------"
    )
    return sigmacErr, sigmasErr, xiErr, sentence, sentenceReg, sentenceDom


class Test(unittest.TestCase):
    def test_101_sws_excel_1_plus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=1300.0,
            steelAreaTop=1571.0,
            steelAreaBottom=3142.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-964.0,
            Med=+1081.0,
            sigmacRef=-6.17,
            sigmasRef=168.70,
            toll=0.005,
            name="excel 1 (+)",
            sigmacReg=-6.166,
            sigmasReg=168.628,
            xiReg=442.749,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_102_sws_excel_2_plus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=2300.0,
            steelAreaTop=1901.0,
            steelAreaBottom=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-2123.6,
            Med=+941.5,
            sigmacRef=-1.90,
            sigmasRef=0.94,
            toll=0.035,
            name="excel 2 (+)",
            sigmacReg=-1.904,
            sigmasReg=0.940,
            xiReg=2178.314,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_103_sws_excel_3_plus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=2200.0,
            steelAreaTop=1901.0,
            steelAreaBottom=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-2123.8,
            Med=+1695.4,
            sigmacRef=-3.39,
            sigmasRef=34.78,
            toll=0.005,
            name="excel 3 (+)",
            sigmacReg=-3.389,
            sigmasReg=34.788,
            xiReg=1276.502,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_104_sws_excel_4_plus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=2200.0,
            steelAreaTop=1901.0,
            steelAreaBottom=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-1920.6,
            Med=+1940.8,
            sigmacRef=-4.02,
            sigmasRef=65.97,
            toll=0.005,
            name="excel 4 (+)",
            sigmacReg=-4.019,
            sigmasReg=65.983,
            xiReg=1026.430,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_105_sws_excel_5_plus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=1700.0,
            steelAreaTop=1901.0,
            steelAreaBottom=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-1639.2,
            Med=+1940.8,
            sigmacRef=-6.55,
            sigmasRef=158.13,
            toll=0.005,
            name="excel 5 (+)",
            sigmacReg=-6.546,
            sigmasReg=158.145,
            xiReg=632.011,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_106_sws_excel_6_plus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=1000.0,
            steelAreaTop=1571.0,
            steelAreaBottom=1571.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-678.5,
            Med=+574.6,
            sigmacRef=-6.30,
            sigmasRef=219.37,
            toll=0.005,
            name="excel 6 (+)",
            sigmacReg=-6.298,
            sigmasReg=219.324,
            xiReg=286.000,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_101_sws_excel_1_minus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=1300.0,
            steelAreaBottom=1571.0,
            steelAreaTop=3142.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-964.0,
            Med=-1081.0,
            sigmacRef=-6.17,
            sigmasRef=168.70,
            toll=0.005,
            name="excel 1 (-)",
            sigmacReg=-6.166,
            sigmasReg=168.628,
            xiReg=442.749,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_102_sws_excel_2_minus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=2300.0,
            steelAreaBottom=1901.0,
            steelAreaTop=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-2123.6,
            Med=-941.5,
            sigmacRef=-1.90,
            sigmasRef=0.94,
            toll=0.040,
            name="excel 2 (-)",
            sigmacReg=-1.904,
            sigmasReg=0.940,
            xiReg=2178.314,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_103_sws_excel_3_minus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=2200.0,
            steelAreaBottom=1901.0,
            steelAreaTop=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-2123.8,
            Med=-1695.4,
            sigmacRef=-3.39,
            sigmasRef=34.78,
            toll=0.005,
            name="excel 3 (-)",
            sigmacReg=-3.389,
            sigmasReg=34.788,
            xiReg=1276.502,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_104_sws_excel_4_minus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=2200.0,
            steelAreaBottom=1901.0,
            steelAreaTop=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-1920.6,
            Med=-1940.8,
            sigmacRef=-4.02,
            sigmasRef=65.97,
            toll=0.005,
            name="excel 4 (-)",
            sigmacReg=-4.019,
            sigmasReg=65.983,
            xiReg=1026.430,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_105_sws_excel_5_minus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=1700.0,
            steelAreaBottom=1901.0,
            steelAreaTop=3801.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-1639.2,
            Med=-1940.8,
            sigmacRef=-6.55,
            sigmasRef=158.13,
            toll=0.005,
            name="excel 5 (-)",
            sigmacReg=-6.546,
            sigmasReg=158.145,
            xiReg=632.011,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_106_sws_excel_6_minus(self):
        res = buildTest(
            dimW=1000.0,
            dimH=1000.0,
            steelAreaBottom=1571.0,
            steelAreaTop=1571.0,
            distFromTop=50.0,
            distFromBot=50.0,
            Ned=-678.5,
            Med=-574.6,
            sigmacRef=-6.30,
            sigmasRef=219.37,
            toll=0.005,
            name="excel 6 (-)",
            sigmacReg=-6.298,
            sigmasReg=219.324,
            xiReg=286.000,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_107_exagon_5_plus(self):
        res = buildTest(
            dimW=300.0,
            dimH=600.0,
            steelAreaBottom=1256.0,
            steelAreaTop=1256.0,
            distFromTop=20.0,
            distFromBot=20.0,
            Ned=-0.0,
            Med=+1000.0,
            sigmacRef=-43.22,
            sigmasRef=1485.70,
            toll=0.005,
            name="EXAGONE test 5 (+)",
            sigmacReg=-43.222,
            sigmasReg=1484.733,
            xiReg=176.286,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_107_exagon_5_minus(self):
        res = buildTest(
            dimW=300.0,
            dimH=600.0,
            steelAreaBottom=1256.0,
            steelAreaTop=1256.0,
            distFromTop=20.0,
            distFromBot=20.0,
            Ned=-0.0,
            Med=-1000.0,
            sigmacRef=-43.22,
            sigmasRef=1485.70,
            toll=0.005,
            name="EXAGONE test 5 (-)",
            sigmacReg=-43.222,
            sigmasReg=1484.733,
            xiReg=176.286,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_108_prefle_1_plus(self):
        res = buildTest(
            dimW=300.0,
            dimH=600.0,
            steelAreaBottom=1256.0,
            steelAreaTop=312.0,
            distFromTop=20.0,
            distFromBot=20.0,
            Ned=-100.0,
            Med=+100.0,
            sigmacRef=-6.94573,
            sigmasRef=184.056,
            xiRef=209.6427517,
            toll=0.340,
            name="PREFLE+ (+)",
            sigmacReg=-6.118,
            sigmasReg=122.680,
            xiReg=248.196,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_108_prefle_1_minus(self):
        res = buildTest(
            dimW=300.0,
            dimH=600.0,
            steelAreaBottom=1256.0,
            steelAreaTop=312.0,
            distFromTop=20.0,
            distFromBot=20.0,
            Ned=-100.0,
            Med=-100.0,
            sigmacRef=-8.02624,
            sigmasRef=428.737,
            xiRef=127.1615167,
            toll=0.340,
            name="PREFLE+",
            sigmacReg=-7.063,
            sigmasReg=425.114,
            xiReg=115.704,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_109_manual_1_plus(self):
        res = buildTest(
            dimW=300.0,
            dimH=600.0,
            steelAreaBottom=1256.0,
            steelAreaTop=1256.0,
            distFromTop=20.0,
            distFromBot=20.0,
            Ned=+1000.0,
            Med=0.0,
            sigmacRef=0.0,
            sigmasRef=398.089,
            toll=0.005,
            name="Manual reference (+)",
            sigmacReg=0.0,
            sigmasReg=398.0891,
            xiReg=math.inf,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")

    def test_109_manual_1_minus(self):
        res = buildTest(
            dimW=300.0,
            dimH=600.0,
            steelAreaBottom=1256.0,
            steelAreaTop=1256.0,
            distFromTop=20.0,
            distFromBot=20.0,
            Ned=-1000.0,
            Med=0.0,
            sigmacRef=-4.59,
            sigmasRef=-68.90,
            toll=0.005,
            name="Manual reference (-)",
            sigmacReg=-4.5938,
            sigmasReg=-68.9084,
            xiReg=math.inf,
        )
        sentence = res[3]
        sentenceReg = res[4]
        sentenceDom = res[5]
        self.assertEqual(sentence, "--> OK")
        self.assertEqual(sentenceReg, "--> OK")
        self.assertEqual(sentenceDom, "--> OK")


if __name__ == "__main__":
    unittest.main()
