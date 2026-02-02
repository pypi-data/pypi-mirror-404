# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from pycivil.EXAUtils.EXAExceptions import EXAExceptions as EXAExcept
from pycivil.EXAStructural.cheatsheets.codeNTC2018Rules import (
    BeamMinimumArea,
    BeamMinimumAreaInput,
    ConcreteMaterialInput,
    ConcreteMaterialOutput,
    RebarMaterialInput,
    RebarMaterialOutput,
    SolverBeamMinRebar,
    SolverConcrete,
    SolverSteelRebar,
)
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pydantic import ValidationError
from rich import print

VALID_CONCRETE_CODES = [
    (code, mat)
    for code, concretes in Concrete.tab_fck.items()
    for mat in concretes.keys()
]

INVALID_CONCRETE_CODES_MAT = [
    (code, mat + "_")
    for code, concretes in Concrete.tab_fck.items()
    for mat in concretes.keys()
]

INVALID_CONCRETE_CODES_CODE = [
    (code + "_", mat)
    for code, concretes in Concrete.tab_fck.items()
    for mat in concretes.keys()
]


def test_solver_concrete_raise() -> None:
    with pytest.raises(ValueError):
        SolverConcrete(ConcreteMaterialOutput())


@pytest.mark.parametrize(("code_key", "mat_key"), INVALID_CONCRETE_CODES_CODE)
def test_solver_concrete_code_invalid(code_key: str, mat_key: str) -> None:
    matIn = ConcreteMaterialInput()
    matIn.keyCode = code_key
    matIn.concreteClass = mat_key
    solver = SolverConcrete(matIn)
    with pytest.raises(ValueError):
        solver.run()


@pytest.mark.parametrize(("code_key", "mat_key"), INVALID_CONCRETE_CODES_MAT)
def test_solver_concrete_mat_invalid(code_key: str, mat_key: str) -> None:
    matIn = ConcreteMaterialInput()
    matIn.keyCode = code_key
    matIn.concreteClass = mat_key
    solver = SolverConcrete(matIn)
    with pytest.raises(EXAExcept):
        solver.run()


@pytest.mark.parametrize(("code_key", "mat_key"), VALID_CONCRETE_CODES)
def test_solver_concrete(code_key: str, mat_key: str) -> None:
    matIn = ConcreteMaterialInput()
    matIn.keyCode = code_key
    matIn.concreteClass = mat_key
    solver = SolverConcrete(matIn)
    assert solver.run()
    assert not solver.run(3)

    out = solver.getModelOutput()
    assert isinstance(out, ConcreteMaterialOutput)

    assert out.value_fck == float(mat_key[1 : mat_key.find("/")])
    assert out.value_Rck == float(mat_key[mat_key.find("/") + 1 :])


VALID_STEEL_CODES = [
    (code, mat)
    for code, steels in ConcreteSteel.tab_steel.items()
    for mat in steels.keys()
]

INVALID_STEEL_CODES_MAT = [
    (code, mat + "_")
    for code, steels in ConcreteSteel.tab_steel.items()
    for mat in steels.keys()
]

INVALID_STEEL_CODES_CODE = [
    (code + "_", mat)
    for code, steels in ConcreteSteel.tab_steel.items()
    for mat in steels.keys()
]


def test_solver_steel_raise() -> None:
    with pytest.raises(ValueError):
        SolverSteelRebar(ConcreteMaterialOutput())


@pytest.mark.parametrize(("code_key", "mat_key"), INVALID_STEEL_CODES_CODE)
def test_solver_steel_code_invalid(code_key: str, mat_key: str) -> None:
    matIn = RebarMaterialInput()
    matIn.keyCode = code_key
    matIn.steelClass = mat_key
    solver = SolverSteelRebar(matIn)
    with pytest.raises(ValueError):
        solver.run()


@pytest.mark.parametrize(("code_key", "mat_key"), INVALID_STEEL_CODES_MAT)
def test_solver_steel_mat_invalid(code_key: str, mat_key: str) -> None:
    matIn = RebarMaterialInput()
    matIn.keyCode = code_key
    matIn.steelClass = mat_key
    solver = SolverSteelRebar(matIn)
    with pytest.raises(EXAExcept):
        solver.run()


@pytest.mark.parametrize(("code_key", "mat_key"), VALID_STEEL_CODES)
def test_solver_steel(code_key: str, mat_key: str) -> None:
    matIn = RebarMaterialInput()
    matIn.keyCode = code_key
    matIn.steelClass = mat_key
    solver = SolverSteelRebar(matIn)
    assert solver.run()

    out = solver.getModelOutput()
    assert isinstance(out, RebarMaterialOutput)

    assert out.value_fyk == float(mat_key[1:4])


def test_beam_minimum_area_input():
    with pytest.raises(ValidationError):
        BeamMinimumAreaInput(hEl=-1.0)

    with pytest.raises(ValidationError):
        BeamMinimumAreaInput(hEl="-1.0")

    with pytest.raises(ValidationError):
        BeamMinimumAreaInput(rebarDComp="-1.0")

    with pytest.raises(ValidationError):
        BeamMinimumAreaInput(elementDescr=2)

    with pytest.raises(ValidationError):
        BeamMinimumAreaInput(hEl=100.0, cover=80.0, rebarD=21)

    with pytest.raises(ValidationError):
        BeamMinimumAreaInput(rebarD=-12)


def test_solver_beamMinimumArea() -> None:
    dataInput = BeamMinimumAreaInput()
    dataInput.keyCode = "NTC2018"
    dataInput.concreteClass = "C25/30"
    dataInput.steelClass = "B450C"

    # Test fake input model
    with pytest.raises(ValueError):
        SolverBeamMinRebar(RebarMaterialInput)

    solver = SolverBeamMinRebar(dataInput)
    assert solver.run()
    results = BeamMinimumArea(
        inputData=dataInput,
        logsData=solver.getModelLogs(),
        outputData=solver.getModelOutput(),
    )
    print("\n")
    print(results)
