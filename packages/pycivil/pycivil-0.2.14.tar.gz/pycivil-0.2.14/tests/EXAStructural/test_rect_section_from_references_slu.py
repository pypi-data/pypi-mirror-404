# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

"""
Created on Sun Dec 04 09:27:00 2022

@author: lpaone
"""
import json
import os
import unittest
from typing import Union

import pycivil.EXAStructural.templateRCRect as RCRect
from pycivil.EXAGeometry.geometry import Point2d
from pycivil.EXAGeometry.shapes import ShapeArea, ShapeRect
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.sections import ConcreteSection, StructSectionItem
from tests.EXAStructural.test_rect_section_from_references_sls import build_section


def rectSolverDomain_NM(
    dimW,
    dimH,
    steelAreaTop,
    steelAreaBottom,
    distFromTop,
    distFromBot,
    Ned,
    Med,
    homogenization=15.0,
):

    # Setting new instance of section with
    section = RCRect.RCTemplRectEC2(1, "First Section")

    # Setting dimension concrete
    section.setDimH(dimH)
    section.setDimW(dimW)

    # Setting rebar
    section.addSteelArea("MB", distFromBot, steelAreaBottom)
    section.addSteelArea("MT", distFromTop, steelAreaTop)

    # Setting materials
    section.setMaterials(homogenization=homogenization)

    sigma_c_domain, sigma_s_domain, xi_domain, _ = section.solverSLS_NM_withDomain(Ned, Med)

    return {"sigmac": sigma_c_domain, "sigmas": sigma_s_domain, "xi": xi_domain}


def rectSolverClassic_NM(
    dimW,
    dimH,
    steelAreaTop,
    steelAreaBottom,
    distFromTop,
    distFromBot,
    Ned,
    Med,
    homogenization=15.0,
):
    # Solver with roots
    #
    sol = build_section(dimW, dimH, Ned, Med, distFromTop, distFromBot, steelAreaBottom, steelAreaTop, homogenization)

    return {"sigmac": sol[0][0], "sigmas": sol[0][1], "xi": sol[0][2]}


def relativeError(valCal: float, valRef: Union[float, None]) -> float:
    if valRef is None:
        return 0.0
    else:
        return abs((valRef - valCal) / valRef)


class Test(unittest.TestCase):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        concrete = Concrete()
        steel = ConcreteSteel()
        self.sec = ConcreteSection()
        self.sec.setStructConcrItem(
            StructSectionItem(
                shape=ShapeRect(ids=1, width=300, height=600), material=concrete
            )
        )
        self.sec.addSteelItem(
            StructSectionItem(
                shape=ShapeArea(area=314, ids=10, xo=-100.0, yo=-250.0), material=steel
            )
        )
        self.sec.addSteelItem(
            StructSectionItem(
                shape=ShapeArea(area=314, ids=11, xo=+100.0, yo=-250.0), material=steel
            )
        )
        self.sec.addSteelItem(
            StructSectionItem(
                shape=ShapeArea(area=200, ids=12, xo=+100.0, yo=+250.0), material=steel
            )
        )
        self.sec.addSteelItem(
            StructSectionItem(
                shape=ShapeArea(area=200, ids=13, xo=-100.0, yo=+250.0), material=steel
            )
        )

    def test_110_Rectangular_Shape_getArea(self):
        self.assertEqual(
            300 * 600, self.sec.getStructConcretelItem().getShape().getArea()
        )

    def test_112_Rectangular_Shape_getOrigin(self):
        self.assertEqual(
            0.0, self.sec.getStructConcretelItem().getShape().getOrigin().x
        )
        self.assertEqual(
            0.0, self.sec.getStructConcretelItem().getShape().getOrigin().y
        )

    def test_120_Rectangular_Shape_translate_concreteOrigin(self):
        shape = self.sec.getStructConcretelItem().getShape()
        shape.translate(Point2d(0.0, 0.0), Point2d(150, 0))
        self.assertEqual(
            150.0, self.sec.getStructConcretelItem().getShape().getOrigin().x
        )

    def test_121_Rectangular_Shape_translate_concreteItem(self):
        shape = self.sec.getStructConcretelItem().getShape()
        shape.translate(Point2d(0.0, 0.0), Point2d(0, 300))
        self.assertEqual(
            300.0, self.sec.getStructConcretelItem().getShape().getOrigin().y
        )

    def test_122_Rectangular_Shape_translateConcreteItem(self):
        # reset position
        self.sec.getStructConcretelItem().getShape().setOrigin(Point2d(0.0, 0.0))

        self.sec.translateConcreteItem(Point2d(0.0, 0.0), Point2d(150, 300))
        self.assertEqual(
            300.0, self.sec.getStructConcretelItem().getShape().getOrigin().y
        )
        self.assertEqual(
            150.0, self.sec.getStructConcretelItem().getShape().getOrigin().x
        )

    def test_123_Rectangular_Shape_translateSteelItems(self):
        # reset position
        self.sec.getStructConcretelItem().getShape().setOrigin(Point2d(0.0, 0.0))

        # translate steel rebars
        self.sec.translateSteelItems(Point2d(0.0, 0.0), Point2d(5.0, 5.0))

        self.assertEqual(-95.0, self.sec.getSteelRebar()[0].getOrigin().x)
        self.assertEqual(-245.0, self.sec.getSteelRebar()[0].getOrigin().y)
        self.assertEqual(105.0, self.sec.getSteelRebar()[1].getOrigin().x)
        self.assertEqual(-245.0, self.sec.getSteelRebar()[1].getOrigin().y)
        self.assertEqual(105.0, self.sec.getSteelRebar()[2].getOrigin().x)
        self.assertEqual(255.0, self.sec.getSteelRebar()[2].getOrigin().y)
        self.assertEqual(-95.0, self.sec.getSteelRebar()[3].getOrigin().x)
        self.assertEqual(255.0, self.sec.getSteelRebar()[3].getOrigin().y)

    def test_200_Rectangular_Domain(self):
        """
        ....dimension: 300x500-code: EC2-concrete: C32/40-steel: B450C
        """
        # Setting working code
        code_EC2 = Code("EC2")

        # Setting concrete material
        cls_material = Concrete(descr="EC2_C32/40")
        cls_material.setByCode(code_EC2, "C32/40")

        # Setting concrete shape
        rect_shape = ShapeRect(300, 500)

        rectangularSection = StructSectionItem(rect_shape, cls_material)

        # Setting steel material
        steel_material = ConcreteSteel(descr="EC2_450C")
        steel_material.setByCode(code_EC2, "B450C")

        # Retriving special points
        MB = rectangularSection.getShape().getShapePoint("MB")
        MT = rectangularSection.getShape().getShapePoint("MT")

        # Setting bottom steel shape
        area_shape_1 = ShapeArea(600)
        area_shape_1.setOrigin(MB + Point2d(0, 38))
        steel_1 = StructSectionItem(area_shape_1, steel_material)

        # Setting top steel shape
        area_shape_2 = ShapeArea(600)
        area_shape_2.setOrigin(MT + Point2d(0, -40))
        steel_2 = StructSectionItem(area_shape_2, steel_material)

        # Forming section
        myfirstsection = ConcreteSection(1, "300x500 EC2")
        myfirstsection.setStructConcrItem(rectangularSection)
        myfirstsection.setStructSteelItems([steel_1, steel_2])

        # Stetting material for whole secction
        myfirstsection.setConcreteMaterial(cls_material)
        myfirstsection.setSteelMaterial(steel_material)

        (
            NxMz,
            fields,
            NxMzBoundingRect,
        ) = myfirstsection.build2dInteractionCompleteDomain()

        domain = {"points": NxMz, "fields": fields, "bounding": NxMzBoundingRect}

        # NOTE: Decomment this only for create benchmark file
        #
        # with open(os.path.join(os.path.dirname(__file__),'test_200_Rectangular_Domain.json'), 'w') as outfile:
        #     json.dump(domain,outfile,indent=4)

        fileName = os.path.join(
            os.path.dirname(__file__), "test_200_Rectangular_Domain.json"
        )
        with open(fileName) as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()

        for i, p in enumerate(jsonObject["points"]):
            self.assertAlmostEqual(domain["points"][i][0], p[0])

        for i, p in enumerate(jsonObject["fields"]):
            self.assertAlmostEqual(domain["fields"][i], p)

        for i, p in enumerate(jsonObject["bounding"]):
            self.assertAlmostEqual(domain["bounding"][i], p)

    def autoTestFun(self, tollReg, sigmacReg, sigmasReg, xiReg, sol, title):
        print("\n")
        print("-" * len(title))
        print(title)
        print("-" * len(title))

        if sigmacReg is not None:
            self.assertLessEqual(
                relativeError(sol["sigmac"], sigmacReg),
                tollReg,
                "sigmac \n from cal {:.9f} \n from ref {:.9f} ... failed".format(
                    sol["sigmac"], sigmacReg
                ),
            )
            print(
                "sigmac \n from cal {:.9f} \n from ref {:.9f} ... passed".format(
                    sol["sigmac"], sigmacReg
                )
            )

        if sigmasReg is not None:
            self.assertLessEqual(
                relativeError(sol["sigmas"], sigmasReg),
                tollReg,
                "sigmas \n from cal {:.9f} \n from ref {:.9f} ... failed".format(
                    sol["sigmas"], sigmasReg
                ),
            )
            print(
                "sigmas \n from cal {:.9f} \n from ref {:.9f} ... passed".format(
                    sol["sigmas"], sigmasReg
                )
            )

        if xiReg is not None:
            self.assertLessEqual(
                relativeError(sol["xi"], xiReg),
                tollReg,
                "xi \n from cal {:.9f} \n from ref {:.9f} ... failed".format(
                    sol["xi"], xiReg
                ),
            )
            print(
                "xi \n from cal {:.9f} \n from ref {:.9f} ... passed".format(
                    sol["xi"], xiReg
                )
            )

    def test_301_solver_NM(self):

        sectionVal = {
            "dimW": 1000.0,
            "dimH": 1300.0,
            "steelAreaTop": 1571.0,
            "steelAreaBottom": 3142.0,
            "distFromTop": 50.0,
            "distFromBot": 50.0,
            "Ned": -964.0,
            "Med": +1081.0,
        }

        title = "Classic Solution not regression"
        solClassic = rectSolverClassic_NM(**sectionVal)
        self.autoTestFun(
            1e-7, -6.165762118, 168.627969091, 442.748616437, solClassic, title
        )

        sectionVal["steelAreaTop"] = 3142.0
        sectionVal["steelAreaBottom"] = 1571.0
        sectionVal["Med"] = -1081.0

        title = "Classic Solution Mirrored not regression"
        solClassic = rectSolverClassic_NM(**sectionVal)
        self.autoTestFun(
            1e-7, -6.165762118, 168.627969091, 1300 - 442.748616437, solClassic, title
        )

        title = "Classic Solution with reference sws_sheet_1.pdf nb.1 (+)"
        self.autoTestFun(1e-3, -6.17, 168.70, None, solClassic, title)

        title = "Domain Solution not regression"
        solDomain = rectSolverDomain_NM(**sectionVal)
        self.autoTestFun(
            1e-7, -6.165583947, 168.637729637, 442.772865303, solDomain, title
        )

    def test_302_solver_NM(self):

        sectionVal = {
            "dimW": 1000.0,
            "dimH": 2300.0,
            "steelAreaTop": 1901.0,
            "steelAreaBottom": 3801.0,
            "distFromTop": 50.0,
            "distFromBot": 50.0,
            "Ned": -2123.6,
            "Med": +941.5,
        }

        title = "Classic Solution not regression"
        solClassic = rectSolverClassic_NM(**sectionVal)
        self.autoTestFun(
            1e-7, -1.904332499, 0.940037791, 2178.314420458, solClassic, title
        )

        sectionVal["steelAreaTop"] = 3801.0
        sectionVal["steelAreaBottom"] = 1901.0
        sectionVal["Med"] = -941.5

        title = "Classic Solution Mirrored not regression"
        solClassic = rectSolverClassic_NM(**sectionVal)
        self.autoTestFun(
            1e-7, -1.904332499, 0.940037791, 121.685579542, solClassic, title
        )

        title = "Classic Solution with reference sws_sheet_1.pdf nb.2 (+)"
        self.autoTestFun(1e-2, -1.90, 0.94, None, solClassic, title)

        title = "Domain Solution not regression"
        solDomain = rectSolverDomain_NM(**sectionVal)
        self.autoTestFun(
            1e-7, -1.905293686, 0.972074155, 2177.316605858, solDomain, title
        )

    def test_303_solver_NM(self):

        sectionVal = {
            "dimW": 1000.0,
            "dimH": 2200.0,
            "steelAreaTop": 1901.0,
            "steelAreaBottom": 3801.0,
            "distFromTop": 50.0,
            "distFromBot": 50.0,
            "Ned": -2123.8,
            "Med": +1695.4,
        }

        title = "Classic Solution not regression"
        solClassic = rectSolverClassic_NM(**sectionVal)
        self.autoTestFun(
            1e-8, -3.389217826, 34.788136630, 1276.501988257, solClassic, title
        )

        sectionVal["steelAreaTop"] = 3801.0
        sectionVal["steelAreaBottom"] = 1901.0
        sectionVal["Med"] = -1695.4

        title = "Classic Solution Mirrored not regression"
        solClassic = rectSolverClassic_NM(**sectionVal)
        self.autoTestFun(
            1e-8, -3.389217826, 34.788136630, 923.498011743, solClassic, title
        )

        title = "Classic Solution with reference sws_sheet_1.pdf nb.3 (+)"
        self.autoTestFun(1e-2, -3.39, 34.78, None, solClassic, title)

        title = "Domain Solution not regression"
        solDomain = rectSolverDomain_NM(**sectionVal)
        self.autoTestFun(
            1e-9, -3.389365155, 34.802086954, 1276.475731762, solDomain, title
        )


if __name__ == "__main__":
    unittest.main()
