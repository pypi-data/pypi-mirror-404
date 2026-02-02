# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

"""
Created on Sat Dec 31 13:10:00 2022

@author: lpaone
"""
import json
import math
import os
import shutil
import tempfile
import pytest
import sys
from pathlib import Path
from uuid import uuid4

from code_aster_whale.tools.code_aster import AsterLauncher as ca
from code_aster_whale.tools.code_aster import ExportType, LauncherType

from pycivil.EXAGeometry.geometry import Point3d
from pycivil.settings import ServerSettings
from pycivil.EXAStructural import templateRCRect as est
from pycivil.EXAStructural.templateRCRectFire import (
    RCRectEC2FireDesign as SectionForFireDesign,
)
from pycivil.EXAStructural.templateRCRectFire import RMinutes as FireTime
from pycivil.EXAUtils.vtk import FileType
from pycivil.EXAUtils.vtk import Parser as vtkParser

@pytest.mark.codeaster
def test_00_launcher():
    appName = "test_00_launcher"
    jobToken = f"test-{str(uuid4())}"
    # Build launcher
    #
    launcher = ca(
        launcherType=LauncherType.CONTAINER,
        exportType=ExportType.VTK_FROM_MEDCOUPLING,
        appName=appName,
        jobToken=jobToken,
        containerName=ServerSettings().codeaster_container,
    )
    # Run Code Aster
    # NOTE: use test = True to post file
    #
    pathName = os.path.dirname(__file__)
    source_EXPORT_file = os.path.join(pathName, "thermNL01.export")
    source_COMM_file = os.path.join(pathName, "thermNL01.comm")
    source_MMED_file = os.path.join(pathName, "thermNL01.mmed")
    assert 0 == launcher.launch(
            exportFilePath=source_EXPORT_file,
            commFilePath=source_COMM_file,
            mmedFilePath=source_MMED_file,
            test=True), f"Can't launch Code Aster on {source_EXPORT_file}"
    # Exporting with option timeStep = -1 means that will be exported
    # complete time series
    #
    assert 0 == launcher.exportFromMEDFile(
            os.path.join(pathName, "thermNL01.rmed"),
            pointDataArr=["resther0TEMP"],
            test=True)
    # TODO: Adjust with matplotlib. Export images with pvbatch from thermal analysis
    #
    # launcher.exportImgsFromVtm(pathName, "vtm", pathName)
    logLevel = 3
    parser = vtkParser()
    parser.setFileType(FileType.VTU_TYPE)
    parser.parse(files=os.path.join(pathName, "vtu"), ll=logLevel)
    # k = parser.findMultiblockKeyByArrayValue(
    #     arrayName="TimeValue", value=6000.0, ll=logLevel
    # )
    # parser.setCurrentMultiblockByKey(key=k)
    parser.setCurrentFileByIndex(int(6000.0 / 100 / 60))
    parser.getPoints()
    parser.getPoint(300)
    parser.getPointValueById(arrayName="resther0TEMP", id=2, ll=logLevel)
    # Retrive value in point by nearest point
    print("---------------------------------------:")
    print("Retrive value in point by nearest point:")
    print("---------------------------------------:")
    testPoint = Point3d(0.15, -0.30, 0)
    pointFound = parser.getNearestPoint(p=testPoint)
    value = parser.getPointValueById(
        arrayName="resther0TEMP", id=pointFound.idn, ll=logLevel
    )
    print(
        "Distance beetwen point is {:.5f} m".format(
            pointFound.distanceFrom(testPoint)
        )
    )
    print(f"---> Temp in point id = {pointFound.idn} is {value:.1f}")
    print("---------------------------------------:")
    # Retrive value in point by interp on cellPoints
    print("-----------------------------------------------:")
    print("Retrive value in point by interp on cell points:")
    print("-----------------------------------------------:")
    testPoint = Point3d(+0.15, -0.30, 0)
    pointsFound = parser.getPointsCellNearestPoint(p=testPoint)
    value = parser.getPointValueInterpTriaByIds(
        p=testPoint,
        id0=pointsFound[0].idn,
        id1=pointsFound[1].idn,
        id2=pointsFound[2].idn,
        arrayName="resther0TEMP",
        ll=logLevel,
    )
    print(f"---> Temp in point is {value:.1f}")
    print("---------------------------------------:")
    # launcher.deleteArtifacts()

@pytest.mark.codeaster
def test_01_not_regression_domain():
    section = est.RCTemplRectEC2(1, "Template RC Section")
    section.setMaterials(
        concreteStr="C30/37", steelStr="B450C", homogenization=15.0
    )
    section.setDimH(600.0)
    section.setDimW(300.0)
    d20 = math.pi * 20 * 20 / 4
    d16 = math.pi * 16 * 16 / 4
    section.addSteelArea("XY", area=d20, x=-150.0 + 20, y=-300.0 + 20)
    section.addSteelArea("XY", area=d20, x=-150.0 + 100, y=-300.0 + 20)
    section.addSteelArea("XY", area=d20, x=+150.0 - 100, y=-300.0 + 20)
    section.addSteelArea("XY", area=d20, x=+150.0 - 20, y=-300.0 + 20)
    section.addSteelArea("XY", area=d16, x=-150.0 + 20, y=+300.0 - 20)
    section.addSteelArea("XY", area=d16, x=-150.0 + 100, y=+300.0 - 20)
    section.addSteelArea("XY", area=d16, x=+150.0 - 100, y=+300.0 - 20)
    section.addSteelArea("XY", area=d16, x=+150.0 - 20, y=+300.0 - 20)
    # Adding Tension Points
    KN = 1000
    KNm = 1000000
    section.addTensionPoint2d(N=500.0 * KN, M=191.2 * KNm)
    section.addTensionPoint2d(N=0.0 * KN, M=104.0 * KNm)
    section.interactionDomainBuild2d(nbPoints=100)
    sectionFd = SectionForFireDesign(
        section,
        logLevel=3,
        jobToken=f"test-{str(uuid4())}",
        codeAsterLauncher=ServerSettings().codeaster_launcher,
        codeAsterTemplatePath=ServerSettings().codeaster_templates_path,
        codeAsterContainerName=ServerSettings().codeaster_container,
    )
    sectionFd.setLogLevel(1)
    # Opening JSON file
    f = open(os.path.join(os.path.dirname(__file__), "notregression.json"))
    # returns JSON object as a dictionary
    data = json.load(f)
    f.close()
    #
    # build temporary dir for test
    #
    tmpdirname = tempfile.mkdtemp(suffix=None, prefix=None, dir=None)
    print(f"Temporary path --> {tmpdirname}")
    sectionFd.setWorkingPath(tmpdirname, True)
    assert sectionFd.buildMesh(), "Building mesh failed"
    sectionFd.setEsposedBottom(True)
    sectionFd.setEsposedLeft(False)
    sectionFd.setEsposedRight(False)
    sectionFd.setEsposedTop(False)
    assert sectionFd.buildThermalMap(test=True), "Building thermal maps"
    # TODO: need to fix it
    #
    # sectionFd.exportThermalImgs()
    sectionFd.setTime(FireTime.R180)
    sectionFd.parse()
    sectionFd.buildHotSection()
    sectionFd.deleteArtifacts()
    assert sectionFd.getSection() is not None
    section.interactionDomainBuild2d(nbPoints=200, hotPoints=True)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # thisPath = os.path.dirname(os.path.abspath(__file__))
    # with open(os.path.join(thisPath, "notregression.json"), "w") as outfile:
    #     json.dump(section.getInteractionDomainDict(), outfile, indent=4)
    assert dict(data) == section.getInteractionDomainDict()
    fireFactorsNotRegression = [
        0.05688497578862946,
        0.05689855014757066,
        0.05677341540764942,
        0.05679166542990918,
        1.0,
        1.0,
        1.0,
        1.0,
    ]
    steelTempsNotRegression = [
        915.5751210568527,
        915.5072492621467,
        916.1329229617529,
        916.0416728504541,
        20.000342941411276,
        20.0004018915307,
        20.000457508601922,
        20.00052850487601,
    ]
    for idx in range(len(steelTempsNotRegression)):
        assert fireFactorsNotRegression[idx] == pytest.approx(section.getSteelFireFactors()[idx], abs=2)
        assert steelTempsNotRegression[idx] == pytest.approx(section.getSteelTemperatures()[idx], abs=2)
        assert sectionFd.getDeltas()[0] == pytest.approx( 0.000, abs=2)
        assert sectionFd.getDeltas()[1] == pytest.approx( 0.000, abs=2)
        assert sectionFd.getDeltas()[2] == pytest.approx( 0.000, abs=2)
        assert sectionFd.getDeltas()[3] == pytest.approx(61.314, abs=2)
    # -----------------------------------
    # using this for generate plot window
    # -----------------------------------
    # self.__section.interactionDomainPlot2d(xLabel = 'N [KN]', yLabel = 'M [KN*m]')
    #
    # remove temporary dir for test
    #
    shutil.rmtree(tmpdirname)


if __name__ == "__main__":
    sys.exit(pytest.main(Path(__file__)))
