# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import unittest

from pycivil.EXAGeometry.shapes import Point2d, ShapeArea, ShapeCircle, ShapeRect
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.sections import ConcreteSection, StructSectionItem


class Test(unittest.TestCase):
    def test_001_rc_rectangular(self):
        bar = ShapeCircle(300)
        print(bar)

        area_shape = ShapeArea(1000)
        print(area_shape)

        # ******************* CONCRETE SECTION first method

        # Setting working code
        code_EC2 = Code("EC2")
        print(code_EC2)

        # Setting concrete material
        cls_material = Concrete("EC2_C20/25")
        cls_material.setByCode(code_EC2, "C20/25")
        print(cls_material)

        # Setting concrete shape
        rect_shape = ShapeRect(300, 500)
        print(rect_shape)

        # Test iterate over vertex coords
        print("Max in x is %1.f" % rect_shape.vertexMaxInX()[0])
        print("Max in y is %1.f" % rect_shape.vertexMaxInY()[0])
        print("Min in x is %1.f" % rect_shape.vertexMinInX()[0])
        print("Min in y is %1.f" % rect_shape.vertexMinInY()[0])

        rectangularSection = StructSectionItem(rect_shape, cls_material)
        print(rectangularSection)

        # Setting steel material
        steel_material = ConcreteSteel("EC2_450C")
        steel_material.setByCode(code_EC2, "B450C")
        print(steel_material)

        # Testing special vertex
        TL = rectangularSection.getShape().getShapePoint("TL")
        print(TL)
        TR = rectangularSection.getShape().getShapePoint("TR")
        print(TR)
        BL = rectangularSection.getShape().getShapePoint("BL")
        print(BL)
        BR = rectangularSection.getShape().getShapePoint("BR")
        print(BR)
        MB = rectangularSection.getShape().getShapePoint("MB")
        print(MB)
        MT = rectangularSection.getShape().getShapePoint("MT")
        print(MT)
        G = rectangularSection.getShape().getShapePoint("G")
        print(G)

        # Setting steel shape
        area_shape_1 = ShapeArea(200)
        area_shape_1.setOrigin(MB + Point2d(0, 50))

        steel_1 = StructSectionItem(area_shape_1, steel_material)
        print(steel_1)

        area_shape_2 = ShapeArea(200)
        area_shape_2.setOrigin(MT + Point2d(0, -50))

        steel_2 = StructSectionItem(area_shape_2, steel_material)
        print(steel_2)

        # TODO: __str__ for ConcreteSection
        myfirstsection = ConcreteSection(1, "300x500 EC2")
        myfirstsection.setStructConcrItem(rectangularSection)
        myfirstsection.setStructSteelItems([steel_1, steel_2])

        print(myfirstsection)

        print("Min steel items !!!")
        print(myfirstsection.findLowSteelItem())
        print("Max steel items !!!")
        print(myfirstsection.findHitSteelItem())
        print("Steel top recover !!!")
        print(myfirstsection.getSteelTopRecover())
        print("Steel bot recover !!!")
        print(myfirstsection.getSteelTopRecover())


if __name__ == "__main__":
    unittest.main()
