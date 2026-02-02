# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause


import pytest
from pycivil.EXAStructural.cheatsheets.codeEC2Rules import (
    PlateMinimumArea,
    PlateMinimumAreaInput,
    SolverPlateMinRebar,
)
from pydantic import ValidationError
from rich import print


def test_plate_minimum_area_input():

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(hEl=-1.0)
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(hEl="-1.0")
    PlateMinimumAreaInput(hEl=600)

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(rebarD=-1.0)
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(rebarD="-1.0")
    PlateMinimumAreaInput(rebarD=12)

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(cover=-1.0)
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(cover="-1.0")
    PlateMinimumAreaInput(cover=52)

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(rebarDSec=-1.0)
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(rebarDSec="-1.0")
    PlateMinimumAreaInput(rebarDSec=12)

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(coverSec=-1.0)
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(coverSec="-1.0")
    PlateMinimumAreaInput(coverSec=40)

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(stirrupD=-1.0)
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(stirrupD="-1.0")
    PlateMinimumAreaInput(stirrupD=8)

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(nbLegDirX=-1.0)
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(nbLegDirX="-1.0")
    PlateMinimumAreaInput(nbLegDirX=2)

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(elementDescr=-1.0)
    PlateMinimumAreaInput(elementDescr="Nome elemento")

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(keyCode=-1.0)
    PlateMinimumAreaInput(keyCode="NTC2018")

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(steelClass=-1.0)
    PlateMinimumAreaInput(steelClass="B450C")

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(concreteClass=-1.0)
    PlateMinimumAreaInput(concreteClass="C20/25")

    data = {
        "elementDescr": "Nome elemento",
        "keyCode": "NTC2018",
        "steelClass": "B450C",
        "concreteClass": "C20/25",
        "hEl": 600.0,
        "rebarD": 12,
        "cover": 52.0,
        "rebarDSec": 12,
        "coverSec": 50.0,
        "stirrupD": 8,
        "nbLegDirX": 2,
    }

    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(**data)

    data["coverSec"] = 40
    PlateMinimumAreaInput(**data)

    data["hEl"] = 100
    with pytest.raises(ValidationError):
        PlateMinimumAreaInput(**data)


def test_solver_plate_min_rebar() -> None:
    dataInput = PlateMinimumAreaInput()
    dataInput.keyCode = "NTC2018"
    dataInput.concreteClass = "C25/30"
    dataInput.steelClass = "B450C"

    # Test fake input model
    with pytest.raises(ValueError):
        SolverPlateMinRebar(12)

    solver = SolverPlateMinRebar(dataInput)
    assert solver.run()
    results = PlateMinimumArea(
        inputData=dataInput,
        logsData=solver.getModelLogs(),
        outputData=solver.getModelOutput(),
    )
    print("\n")
    print(results)

    solver = SolverPlateMinRebar(dataInput)
    assert solver.run()
    results = PlateMinimumArea(
        inputData=dataInput,
        logsData=solver.getModelLogs(),
        outputData=solver.getModelOutput(),
    )
    print("\n")
    print(results)
