# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

# trace generated using paraview version 5.11.0-RC2
# import paraview
# paraview.compatibility.major = 5
# paraview.compatibility.minor = 11
import os
import glob

#### import the simple module from the paraview
from paraview.simple import *

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new 'XML MultiBlock Data Reader'
seriesName = "{{ seriesName }}"
fullPathVtmSeries = "{{ fullPathVtmSeries }}"
fullPathImgs = "{{ fullPathImgs }}"

vtmFileList = glob.glob(os.path.join(fullPathVtmSeries, seriesName, "*.vtm"))

vtm_0vtm = XMLMultiBlockDataReader(FileName=vtmFileList)

# get animation scene
animationScene1 = GetAnimationScene()

# get active view
renderView1 = GetActiveViewOrCreate("RenderView")

# update animation scene based on data timesteps
animationScene1.UpdateAnimationUsingDataTimeSteps()

# set active source
SetActiveSource(vtm_0vtm)

# show data in view
vtm_0vtmDisplay = Show(vtm_0vtm, renderView1, "UnstructuredGridRepresentation")

# trace defaults for the display properties.
vtm_0vtmDisplay.Representation = "Surface"
vtm_0vtmDisplay.ColorArrayName = [None, ""]
vtm_0vtmDisplay.SelectTCoordArray = "None"
vtm_0vtmDisplay.SelectNormalArray = "None"
vtm_0vtmDisplay.SelectTangentArray = "None"
vtm_0vtmDisplay.OSPRayScaleArray = "FamilyIdNode"
vtm_0vtmDisplay.OSPRayScaleFunction = "PiecewiseFunction"
vtm_0vtmDisplay.SelectOrientationVectors = "None"
vtm_0vtmDisplay.ScaleFactor = 0.06
vtm_0vtmDisplay.SelectScaleArray = "FamilyIdNode"
vtm_0vtmDisplay.GlyphType = "Arrow"
vtm_0vtmDisplay.GlyphTableIndexArray = "FamilyIdNode"
vtm_0vtmDisplay.GaussianRadius = 0.003
vtm_0vtmDisplay.SetScaleArray = ["POINTS", "FamilyIdNode"]
vtm_0vtmDisplay.ScaleTransferFunction = "PiecewiseFunction"
vtm_0vtmDisplay.OpacityArray = ["POINTS", "FamilyIdNode"]
vtm_0vtmDisplay.OpacityTransferFunction = "PiecewiseFunction"
vtm_0vtmDisplay.DataAxesGrid = "GridAxesRepresentation"
vtm_0vtmDisplay.PolarAxes = "PolarAxesRepresentation"
vtm_0vtmDisplay.ScalarOpacityUnitDistance = 0.06897266091960903
vtm_0vtmDisplay.OpacityArrayName = ["POINTS", "FamilyIdNode"]
vtm_0vtmDisplay.SelectInputVectors = [None, ""]
vtm_0vtmDisplay.WriteLog = ""

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
vtm_0vtmDisplay.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 8.0, 1.0, 0.5, 0.0]

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
vtm_0vtmDisplay.OpacityTransferFunction.Points = [
    0.0,
    0.0,
    0.5,
    0.0,
    8.0,
    1.0,
    0.5,
    0.0,
]

# get the material library
materialLibrary1 = GetMaterialLibrary()
# Adjust camera

# reset view to fit data
renderView1.ResetCamera(False)

# show data in view
vtm_0vtmDisplay = Show(vtm_0vtm, renderView1, "UnstructuredGridRepresentation")

# reset view to fit data
renderView1.ResetCamera(False)

# update the view to ensure updated data information
renderView1.Update()

# Adjust camera

# set scalar coloring
ColorBy(vtm_0vtmDisplay, ("POINTS", "resther0TEMP"))

# rescale color and/or opacity maps used to include current data range
vtm_0vtmDisplay.RescaleTransferFunctionToDataRange(True, False)

# show color bar/color legend
vtm_0vtmDisplay.SetScalarBarVisibility(renderView1, True)

# get 2D transfer function for 'resther0TEMP'
resther0TEMPTF2D = GetTransferFunction2D("resther0TEMP")

# get color transfer function/color map for 'resther0TEMP'
resther0TEMPLUT = GetColorTransferFunction("resther0TEMP")
# resther0TEMPLUT.TransferFunction2D = resther0TEMPTF2D
# resther0TEMPLUT.RGBPoints = [20.0, 0.231373, 0.298039, 0.752941, 20.001953125, 0.865003, 0.865003, 0.865003, 20.00390625, 0.705882, 0.0156863, 0.14902]
# resther0TEMPLUT.ScalarRangeInitialized = 1.0

# get opacity transfer function/opacity map for 'resther0TEMP'
# resther0TEMPPWF = GetOpacityTransferFunction('resther0TEMP')
# resther0TEMPPWF.Points = [20.0, 0.0, 0.5, 0.0, 20.00390625, 1.0, 0.5, 0.0]
# resther0TEMPPWF.ScalarRangeInitialized = 1
# Adjust camera

# Rescale transfer function
resther0TEMPLUT.RescaleTransferFunction(19.999999999999986, 1350.0000000000002)

minutes = 60.0

# Properties modified on animationScene1
animationScene1.AnimationTime = 30 * minutes
SaveScreenshot(
    os.path.join(fullPathImgs, "30.png"), renderView1, ImageResolution=[1920, 1080]
)

# Properties modified on animationScene1
animationScene1.AnimationTime = 60 * minutes
SaveScreenshot(
    os.path.join(fullPathImgs, "60.png"), renderView1, ImageResolution=[1920, 1080]
)

# Properties modified on animationScene1
animationScene1.AnimationTime = 90 * minutes
SaveScreenshot(
    os.path.join(fullPathImgs, "90.png"), renderView1, ImageResolution=[1920, 1080]
)

# Properties modified on animationScene1
animationScene1.AnimationTime = 120 * minutes
SaveScreenshot(
    os.path.join(fullPathImgs, "120.png"), renderView1, ImageResolution=[1920, 1080]
)

# Properties modified on animationScene1
animationScene1.AnimationTime = 150 * minutes
SaveScreenshot(
    os.path.join(fullPathImgs, "150.png"), renderView1, ImageResolution=[1920, 1080]
)

# Properties modified on animationScene1
animationScene1.AnimationTime = 180 * minutes
SaveScreenshot(
    os.path.join(fullPathImgs, "180.png"), renderView1, ImageResolution=[1920, 1080]
)

# get layout
# layout1 = GetLayout()

# layout/tab size in pixels
# layout1.SetSize(1360, 719)

# --------------------------------------------
# uncomment the following to render all views
# RenderAllViews()
# alternatively, if you want to write images, you can use SaveScreenshot(...).
