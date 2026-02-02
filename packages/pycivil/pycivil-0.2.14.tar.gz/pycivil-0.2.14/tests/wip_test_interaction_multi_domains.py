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
cls_material = materials.Concrete("EC2_C32/40")
cls_material.setByCode(code_EC2, "C32/40")
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

area_shape_1 = eg.ShapeArea(600)
area_shape_1.setOrigin(MB + eg.Point2d(0, 38))
steel_1 = sections.StructSectionItem(area_shape_1, steel_material)
print(steel_1)

# Setting top steel shape
area_shape_2 = eg.ShapeArea(600)
area_shape_2.setOrigin(MT + eg.Point2d(0, -40))
steel_2 = sections.StructSectionItem(area_shape_2, steel_material)

# TODO: __str__ for ConcreteSection
myfirstsection = sections.ConcreteSection(1, "300x500 EC2")
myfirstsection.setStructConcrItem(rectangularSection)
myfirstsection.setStructSteelItems([steel_1, steel_2])

# Stetting material for whole secction
myfirstsection.setConcreteMaterial(cls_material)
myfirstsection.setSteelMaterial(steel_material)

print(myfirstsection)

NxMz, Fields, NxMzBoundingRect = myfirstsection.build2dInteractionCompleteDomain()

myfirstsection.getStructSteelItems()[0].getShape().setArea(300)
myfirstsection.getStructSteelItems()[1].getShape().setArea(300)
# area_shape_
NxMz2, Fields2, NxMzBoundingRect = myfirstsection.build2dInteractionCompleteDomain()

myfirstsection.getStructSteelItems()[0].getShape().setArea(100)
myfirstsection.getStructSteelItems()[1].getShape().setArea(100)
# area_shape_
NxMz3, Fields3, NxMzBoundingRect = myfirstsection.build2dInteractionCompleteDomain()

strDimension = "MANY DOMAINS - Ai=600.0-1200 As=0 - (Nx,Mz) = (0.0,104.0) - (500,191.2)"
strMaterial = "concrete: B450C steel: C32/40"

# tensionPoints = [[+0,+58.49]]
tensionPoints = [[0, +104.00], [500, +191.2]]

ep.interactionDomainBasePlot2d(
    [NxMz, NxMz2, NxMz3],
    [Fields, Fields2, Fields3],
    xLabel="Nx [KN]",
    yLabel="Mz [KN*m]",
    titleAddStr=strDimension + "\n" + strMaterial,
    tensionPoints=tensionPoints,
)

ep.interactionDomainBasePlot2d(
    [NxMz, NxMz2, NxMz3],
    [Fields, Fields2, Fields3],
    xLabel="Nx [KN]",
    yLabel="Mz [KN*m]",
    titleAddStr=strDimension + "\n" + strMaterial,
    tensionPoints=tensionPoints,
    printDomains=[0, 1],
)
