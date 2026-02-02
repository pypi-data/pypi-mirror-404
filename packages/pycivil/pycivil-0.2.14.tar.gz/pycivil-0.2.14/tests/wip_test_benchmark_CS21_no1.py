# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pycivil import EXAGeometry as eg
from pycivil.EXAStructural import codes, materials, sections
from pycivil.EXAStructural import plot as ep

# ******************* CONCRETE SECTION first method

# Setting working code
code_EC2 = codes.Code("EC2")
print(code_EC2)

# Setting concrete material
cls_material = materials.Concrete("EC2_C35/45")
cls_material.setByCode(code_EC2, "C35/45")
print(cls_material)

# Setting concrete shape
rect_shape = eg.ShapeRect(300, 500)
print(rect_shape)

rectangularSection = sections.StructSectionItem(rect_shape, cls_material)
print(rectangularSection)

# Setting steel material
steel_material = materials.ConcreteSteel("EC2_450C")
steel_material.setByCode(code_EC2, "B450C")
print(steel_material)

# Retriving special points
MB = rectangularSection.getShape().getShapePoint("MB")
MT = rectangularSection.getShape().getShapePoint("MT")

# Setting bottom steel shape

area_shape_1 = eg.ShapeArea(569.0)
area_shape_1.setOrigin(MB + eg.Point2d(0, 40))
steel_1 = sections.StructSectionItem(area_shape_1, steel_material)
print(steel_1)

# Setting top steel shape
area_shape_2 = eg.ShapeArea(0)
area_shape_2.setOrigin(MT + eg.Point2d(0, -40))
steel_2 = sections.StructSectionItem(area_shape_2, steel_material)

# TODO: __str__ for ConcreteSection
myfirstsection = sections.ConcreteSection(1, "300x500 EC2")
myfirstsection.setStructConcrItem(rectangularSection)
myfirstsection.setStructSteelItems([steel_1, steel_2])

myfirstsection.setConcreteMaterial(cls_material)
myfirstsection.setSteelMaterial(steel_material)

print(myfirstsection)

NxMz, Fields, NxMzBoundingRect = myfirstsection.build2dInteractionCompleteDomain()

strDimension = (
    "FERRAILLAGE 1D - CS21 - 300x500 - Ai=569.0 As=0 - Nx = +0KN - Mz = +98.85KN"
)
strMaterial = "concrete: B450C steel: C35/45 gammas: 1.15 gammac: 1.5"

tensionPoints = [[0, (104.0 + 93.7) / 2]]

ep.interactionDomainBasePlot2d(
    NxMz,
    Fields,
    xLabel="Nx [KN]",
    yLabel="Mz [KN*m]",
    titleAddStr=strDimension + "\n" + strMaterial,
    tensionPoints=tensionPoints,
    export="test_benchmark_CS21_no1.png",
    dpi=300,
)
