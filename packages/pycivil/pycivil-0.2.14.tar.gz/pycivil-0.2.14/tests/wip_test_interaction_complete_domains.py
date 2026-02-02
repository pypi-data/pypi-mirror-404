# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pycivil import EXAGeometry as eg
from pycivil.EXAStructural import codes, materials, sections
from pycivil.EXAStructural import plot as ep

# import numpy as np
# from matplotlib.path import Path
# from matplotlib.patches import PathPatch
# import matplotlib.pyplot as plt
# from matplotlib.ticker import FormatStrFormatter

# ******************* CONCRETE SECTION first method

# Setting working code
code_EC2 = codes.Code("EC2")
print(code_EC2)

# Setting concrete material
cls_material = materials.Concrete("EC2_C20/25")
cls_material.setByCode(code_EC2, "C20/25")
print(cls_material)

# Setting concrete shape
rect_shape = eg.ShapeRect(300, 600)
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

# Setting steel shape
area_shape_1 = eg.ShapeArea(2461.76)
area_shape_1.setOrigin(MB + eg.Point2d(0, 50))
steel_1 = sections.StructSectionItem(area_shape_1, steel_material)
print(steel_1)

area_shape_2 = eg.ShapeArea(803.84)
area_shape_2.setOrigin(MT + eg.Point2d(0, -50))
steel_2 = sections.StructSectionItem(area_shape_2, steel_material)

# TODO: __str__ for ConcreteSection
myfirstsection = sections.ConcreteSection(1, "300x500 EC2")
myfirstsection.setStructConcrItem(rectangularSection)
myfirstsection.setStructSteelItems([steel_1, steel_2])

print(myfirstsection)

NxMz, Fields, NxMzBoundingRect = myfirstsection.build2dInteractionCompleteDomain(
    negative_compression=True
)

strDimension = "section 300x600 - Ai=2461.76 As=803.84"
strMaterial = "concrete: B450C steel: C20/25"

tensionPoints = [[-300 * 1e3, +300 * 1e6], [-400 * 1e3, +400 * 1e6]]

ep.interactionDomainBasePlot2d(
    NxMz,
    Fields,
    xLabel="Nx [KN]",
    yLabel="Mz [KN*m]",
    titleAddStr=strDimension + "\n" + strMaterial,
    tensionPoints=tensionPoints,
)
