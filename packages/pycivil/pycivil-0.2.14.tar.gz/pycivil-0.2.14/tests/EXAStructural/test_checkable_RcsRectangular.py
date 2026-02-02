# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import json
import os
import unittest

from pycivil.EXAStructural.checkable import Checker
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.loads import ForcesOnSection as Load
from pycivil.EXAStructural.loads import (
    Frequency_Enum,
    LimiteState_Enum,
)
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2
from pycivil.EXAStructuralCheckable.RcsRectangular import RcsRectangular


class Test(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_110_Rectangular_Shape_getArea(self):
        # Setting code for check
        code = Code("NTC2018")

        concrete = Concrete(descr="My concrete")
        concrete.setByCode(code, "C25/30")
        concrete.setEnvironmentNotAggressive()

        # Setting code for check
        steel = ConcreteSteel(descr="My steel")
        steel.setByCode(code, "B450C")
        steel.setEnvironmentNotSensitive()

        # Setting units
        KN = 1000
        KNm = 1000 * 1000

        # Loads on structural system
        force_1 = Load(Fx=+150.0 * KN, My=+150.0 * KNm, Fz=150 * KN, descr="force_1")
        force_1.frequency = Frequency_Enum.CHARACTERISTIC
        force_1.limitState = LimiteState_Enum.SERVICEABILITY

        force_2 = Load(Fx=+100.0 * KN, My=+145.0 * KNm, Fz=120 * KN, descr="force_2")
        force_2.frequency = Frequency_Enum.QUASI_PERMANENT
        force_1.limitState = LimiteState_Enum.SERVICEABILITY

        force_3 = Load(Fx=-100.0 * KN, My=+145.0 * KNm, Fz=120 * KN, descr="force_3")
        force_3.frequency = Frequency_Enum.QUASI_PERMANENT
        force_3.limitState = LimiteState_Enum.SERVICEABILITY

        force_4 = Load(Fx=+125.0 * KN, My=+125.0 * KNm, Fz=125 * KN, descr="force_4")
        force_4.frequency = Frequency_Enum.FREQUENT
        force_4.limitState = LimiteState_Enum.SERVICEABILITY

        force_5 = Load(Fx=-200.0 * KN, My=+200.0 * KNm, Fz=200 * KN, descr="force_5")
        force_5.limitState = LimiteState_Enum.ULTIMATE

        force_6 = Load(Fx=+200.0 * KN, My=-200.0 * KNm, Fz=100 * KN, descr="force_6")
        force_6.limitState = LimiteState_Enum.ULTIMATE

        force_7 = Load(Fx=-500.0 * KN, My=+350.0 * KNm, Fz=200 * KN, descr="force_7")
        force_7.limitState = LimiteState_Enum.ULTIMATE

        force_8 = Load(Fx=+100.0 * KN, My=-200.0 * KNm, Fz=70 * KN, descr="force_8")
        force_8.limitState = LimiteState_Enum.ULTIMATE

        force_9 = Load(Fx=+200.0 * KN, My=-219.0 * KNm, Fz=100 * KN, descr="force_9")
        force_9.limitState = LimiteState_Enum.ULTIMATE

        force_10 = Load(Fx=+1050.0 * KN, My=0.0 * KNm, Fz=100 * KN, descr="force_10")
        force_10.limitState = LimiteState_Enum.ULTIMATE

        force_11 = Load(Fx=-3700.0 * KN, My=0.0 * KNm, Fz=100 * KN, descr="force_10")
        force_11.limitState = LimiteState_Enum.ULTIMATE

        # Build checkable structural system
        section = RCTemplRectEC2(1, "Template RC Section")

        section.setConcreteMaterial(concrete)
        section.setSteelMaterial(steel)

        section.setDimH(600)
        section.setDimW(300)

        section.addSteelArea("LINE-MT", dist=20, d=20, nb=4, sd=40)
        section.addSteelArea("LINE-MB", dist=20, d=20, nb=4, sd=40)

        section.setStirrupt(area=100, dist=150, angle=90)

        # --------------------
        # BY-HAND TEST CASE #3
        # --------------------
        self.assertAlmostEqual(section.calConcreteArea(), 180000, 6)
        self.assertAlmostEqual(section.calSteelArea(), 2513.274123, 6)
        self.assertAlmostEqual(section.calBarycenterOfConcrete().y, 0, 6)
        self.assertAlmostEqual(section.calBarycenterOfSteel().y, 0, 6)
        # --------------------

        print(section.getConcreteMaterial())
        print(section.getSteelMaterial())

        checkable = RcsRectangular(section)

        locationArtifacts = os.path.dirname(__file__)
        fileNameAArtifact = os.path.basename(__file__).split(".")[0] + ".out.png"
        checkable.setOption_SLU_NM_save(
            True, filePath=locationArtifacts, fileName=fileNameAArtifact
        )

        # Use tool for check
        checker = Checker()
        checker.setCheckable(checkable)

        # Perform check
        criteria = ["SLE-NM", "SLE-F", "SLU-T", "SLU-NM"]
        forces = [
            force_1,
            force_2,
            force_3,
            force_4,
            force_5,
            force_6,
            force_7,
            force_8,
            force_9,
            force_10,
            force_11,
        ]
        loadsInCriteria = [[0, 1, 2, 3], [2, 3], [4], [4, 5, 6, 7, 8, 9, 10]]
        checker.check(criteria, forces, code, loadsInCriteria)

        # Retrive and print results
        results = checker.getResults()
        print(json.dumps(results, indent=2))

    # It does'nt do nothing !!!
    def test_210_Rectangular_single_check_SLU_NM(self):
        code = Code("NTC2018")

        concrete = Concrete(descr="My concrete")
        concrete.setByCode(code, "C25/30")
        concrete.setEnvironment("not aggressive")

        steel = ConcreteSteel(descr="My steel")
        steel.setByCode(code, "B450C")
        steel.setSensitivity("not sensitive")

        KN = 1000
        KNm = 1000 * 1000
        force = Load(Fx=-200.0 * KN, My=+200.0 * KNm, Fz=200 * KN, descr="single_force")
        force.limitState = LimiteState_Enum.ULTIMATE

        section = RCTemplRectEC2(1, "Template RC Section")
        section.setConcreteMaterial(concrete)
        section.setSteelMaterial(steel)

        section.setDimH(600)
        section.setDimW(300)

        section.addSteelArea("LINE-MT", dist=20, d=20, nb=4, sd=40)
        section.addSteelArea("LINE-MB", dist=20, d=20, nb=4, sd=40)
        checkable = RcsRectangular(section)
        checkable.check_SLU_NM_NTC2018(force)

    #
    # Produced 2025/07/18 launching massive computations with strand7 results
    #
    # WARNING: intersection with point P=(-115980.0-0.0) are 1 not 2 !!!
    # seg P1 = (1202520.830214809, -108043575.76061487) - P2 = (1433877.5234923575, -1.4901161193847656e-08)
    # Point2d: (1.43e+06, -1.49e-08)
    # WARNING: Safety factor is 0.0 for plate 2679 layer 3 combo_name SLU_16
    #        : Group Name: Model\Piedritti\ARM2_7_SX Thickness is 1160
    #        : Med = -0.0 Ned = -115.98 Rebar: [[5, 21.6, 200, -73], [5, 21.6, 200, 73]]

    def test_211_Rectangular_single_check_SLU_NM(self):
        code = Code("NTC2018")

        concrete = Concrete(descr="My concrete")
        concrete.setByCode(code, "C25/30")
        concrete.setEnvironment("not aggressive")

        steel = ConcreteSteel(descr="My steel")
        steel.setByCode(code, "B450C")
        steel.setSensitivity("not sensitive")

        KN = 1000
        KNm = 1000 * 1000

        force_1 = Load(Fx=-115.98 * KN, My=-0.0 * KNm, descr="single_force")
        force_1.limitState = LimiteState_Enum.ULTIMATE

        section = RCTemplRectEC2(1, "Template RC Section")

        section.setConcreteMaterial(concrete)
        section.setSteelMaterial(steel)

        section.setDimH(1080)
        section.setDimW(1000)

        section.addSteelArea("LINE-MT", dist=73, d=21.6, nb=5, sd=200)
        section.addSteelArea("LINE-MB", dist=73, d=21.6, nb=5, sd=200)
        checkable = RcsRectangular(section)
        checkable.setMaxPointsForSLUDomain(20)
        checkable.check_SLU_NM_NTC2018(force_1)

        locationArtifacts = os.path.dirname(__file__)
        fileNameAArtifact = os.path.basename(__file__).split(".")[0] + "_211.png"
        checkable.setOption_SLU_NM_save(
            True, filePath=locationArtifacts, fileName=fileNameAArtifact
        )
        # res = checkable.check_SLU_NM_NTC2018(force)
        # print(res)

        # Use tool for check
        checker = Checker()
        checker.setCheckable(checkable)

        # Perform check
        criteria = ["SLU-NM"]
        forces = [force_1]
        loadsInCriteria = [[0]]
        checker.check(criteria, forces, code, loadsInCriteria)

        # Retrive and print results
        results = checker.getResults()
        print(json.dumps(results, indent=2))
        assert (
                results["resultsForCriteria"][0]["results"][0]
                ["safetyFactor"]["interactionDomain"] > 0.0
        )

    #
    # Produced 2025/07/18 launching massive computations with strand7 results
    #
    # WARNING: intersection with point P=(348900.0, -97940000.0) are 3 not 2 !!!
    #          seg P1=(2619300.056842802, -129812832.21945465)-P2=(2974951.6519645965, 1.043081283569336e-07)
    # Point2d: (-8.14e+06,2.28e+09)
    # Point2d: (-8.14e+06,2.28e+09)
    # Point2d: (1.73e+06,-4.84e+08)
    # WARNING: Safety factor is 0.0 for plate 316 layer 4 combo_name SLU_11
    #        : Group Name: Model\Piedritti\ARM2_14_SX Thickness is 1000
    #        : Med = -97.94 Ned = 348.9 Rebar: [[10, 22, 200, -95], [10, 22, 200, 95]]

    def test_212_Rectangular_single_check_SLU_NM(self):
        code = Code("NTC2018")

        concrete = Concrete(descr="My concrete")
        concrete.setByCode(code, "C25/30")
        concrete.setEnvironment("not aggressive")

        steel = ConcreteSteel(descr="My steel")
        steel.setByCode(code, "B450C")
        steel.setSensitivity("not sensitive")

        KN = 1000
        KNm = 1000 * 1000

        force_1 = Load(Fx=348.9 * KN, My=-97.94 * KNm, descr="single_force")
        force_1.limitState = LimiteState_Enum.ULTIMATE

        section = RCTemplRectEC2(1, "Template RC Section")

        section.setConcreteMaterial(concrete)
        section.setSteelMaterial(steel)

        section.setDimH(920)
        section.setDimW(1000)

        section.addSteelArea("LINE-MT", dist=95, d=22, nb=10, sd=200)
        section.addSteelArea("LINE-MB", dist=95, d=22, nb=10, sd=200)
        checkable = RcsRectangular(section)
        checkable.setMaxPointsForSLUDomain(20)
        checkable.check_SLU_NM_NTC2018(force_1)

        locationArtifacts = os.path.dirname(__file__)
        fileNameAArtifact = os.path.basename(__file__).split(".")[0] + "_211.png"
        checkable.setOption_SLU_NM_save(
            True, filePath=locationArtifacts, fileName=fileNameAArtifact
        )

        # Use tool for check
        checker = Checker()
        checker.setCheckable(checkable)

        # Perform check
        criteria = ["SLU-NM"]
        forces = [force_1]
        loadsInCriteria = [[0]]
        checker.check(criteria, forces, code, loadsInCriteria)

        # Retrive and print results
        results = checker.getResults()
        print(json.dumps(results, indent=2))
        assert (
                results["resultsForCriteria"][0]["results"][0]
                ["safetyFactor"]["interactionDomain"] > 0.0
        )


    def test_213_Rectangular_single_check_SLU_NM(self):
        code = Code("NTC2018")

        concrete = Concrete(descr="My concrete")
        concrete.setByCode(code, "C25/30")
        concrete.setEnvironment("not aggressive")

        steel = ConcreteSteel(descr="My steel")
        steel.setByCode(code, "B450C")
        steel.setSensitivity("not sensitive")

        KN = 1000
        KNm = 1000 * 1000

        force_1 = Load(Fx=-712660.0, My=--102330000.0, descr="single_force")
        force_1.limitState = LimiteState_Enum.ULTIMATE

        section = RCTemplRectEC2(1, "Template RC Section")

        section.setConcreteMaterial(concrete)
        section.setSteelMaterial(steel)

        section.setDimH(1040)
        section.setDimW(1000)

        section.addSteelArea("LINE-MT", dist=95, d=16, nb=5, sd=200)
        section.addSteelArea("LINE-MB", dist=95, d=16, nb=5, sd=200)
        checkable = RcsRectangular(section)
        checkable.setMaxPointsForSLUDomain(20)
        checkable.check_SLU_NM_NTC2018(force_1)

        locationArtifacts = os.path.dirname(__file__)
        fileNameAArtifact = os.path.basename(__file__).split(".")[0] + "_212.png"
        checkable.setOption_SLU_NM_save(
            True, filePath=locationArtifacts, fileName=fileNameAArtifact
        )

        # Use tool for check
        checker = Checker()
        checker.setCheckable(checkable)

        # Perform check
        criteria = ["SLU-NM"]
        forces = [force_1]
        loadsInCriteria = [[0]]
        checker.check(criteria, forces, code, loadsInCriteria)

        # Retrive and print results
        results = checker.getResults()
        print(json.dumps(results, indent=2))
        assert (
                results["resultsForCriteria"][0]["results"][0]
                ["safetyFactor"]["interactionDomain"] > 0.0
        )


if __name__ == "__main__":
    unittest.main()
