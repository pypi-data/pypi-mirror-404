# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import json
import sys
from pathlib import Path
from typing import Any
import shutil

import pytest
from pycivil.EXAStructural.checkable import CheckableCriteriaEnum
from pycivil.EXAStructural.rcrecsolver.srvRcSecCheck import (
    ModelInputRcSecCheck,
    ModelOutputRcSecCheck,
    RcSecRectSolver,
    SolverOptions,
    ReportOption
)
from pycivil.EXAStructuralCheckable.RcsRectangular import ThermalMapSolverIn

from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteModel, ConcreteSteel, SteelModel
from pycivil.EXAStructural.loads import ForcesOnSection
from pycivil.EXAStructural.sections import (
    RectangularShape,
    ShapePositionEnum,
    ConcreteSectionModel,
    SteelDisposerOnLine,
    SteelDisposerStirrup,
)


def read_json(file_name: str) -> dict[str, Any]:
    """Reads a JSON file placed in this directory."""
    base_path = Path(__file__).parent
    return json.loads(base_path.joinpath(file_name).read_text())


@pytest.mark.parametrize("file_name", [f"test_0{n}_RcSecSolver" for n in range(1, 5)])
def test_rc_sec_solver_by_hand(tmp_path: Path, file_name: str) -> None:
    solver = RcSecRectSolver()
    solver.setJobPath(str(tmp_path))

    jsonObjectStatic = read_json(f"{file_name}.json")
    shutil.copyfile(src=Path(__file__).parent.joinpath(f"{file_name}.json"), dst=tmp_path.joinpath(f"{file_name}.json"))

    iDataStatic = ModelInputRcSecCheck(**jsonObjectStatic)


    # TODO: skip this if server is unavailable
    if CheckableCriteriaEnum.SLU_NM_FIRE in iDataStatic.criteria:
        jsonObject = read_json(f"{file_name}_Thermal.json")
        iDataThermal = ThermalMapSolverIn(**jsonObject)
        solver.setModelInput(iDataThermal)
        solver.run(SolverOptions.THERMAL)

    solver.setModelInput(iDataStatic)
    solver.run(SolverOptions.STATIC)

    oData = solver.getModelOutput()
    assert isinstance(oData, ModelOutputRcSecCheck)
    for _i, c in enumerate(oData.results.resultsForCriteria):
        c.media = None

    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile = Path(__file__).parent.joinpath(f"{file_name}_nr.json")
    # outfile.write_text(json.dumps(oData.model_dump(), indent=4))

    # Testing data persistence on file for oData
    data = ModelOutputRcSecCheck(**read_json(f"{file_name}_nr.json"))
    for _i, c in enumerate(data.results.resultsForCriteria):
        c.media = None

    assert data == oData

    solver.modelInputFile = f"{file_name}.json"
    shutil.copyfile(src=Path(__file__).parent.joinpath(f"{file_name}_nr.json"), dst=tmp_path.joinpath(f"{file_name}_nr.json"))
    solver.modelOutputFile = f"{file_name}_nr.json"
    solver.reportName = file_name
    assert solver.buildReport()

@pytest.mark.parametrize("file_name", [f"test_0{n}_RcSecSolver" for n in range(6, 12)])
def test_rc_sec_solver_front_end_case(tmp_path: Path, file_name: str) -> None:
    solver = RcSecRectSolver()
    solver.setJobPath(str(tmp_path))

    jsonObjectStatic = read_json(f"{file_name}.json")
    shutil.copyfile(src=Path(__file__).parent.joinpath(f"{file_name}.json"), dst=tmp_path.joinpath(f"{file_name}.json"))

    iDataStatic = ModelInputRcSecCheck(**jsonObjectStatic)

    # TODO: skip this if server is unavailable
    if CheckableCriteriaEnum.SLU_NM_FIRE in iDataStatic.criteria:
        jsonObject = read_json(f"{file_name}_Thermal.json")
        iDataThermal = ThermalMapSolverIn(**jsonObject)
        solver.setModelInput(iDataThermal)
        solver.run(SolverOptions.THERMAL)

    solver.setModelInput(iDataStatic)
    solver.run(SolverOptions.STATIC)

    oData = solver.getModelOutput()
    assert isinstance(oData, ModelOutputRcSecCheck)
    for _i, c in enumerate(oData.results.resultsForCriteria):
        c.media = None

    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile = Path(__file__).parent.joinpath(f"{file_name}_nr.json")
    # outfile.write_text(json.dumps(oData.model_dump(), indent=4))

    # Testing data persistence on file for oData
    data = ModelOutputRcSecCheck(**read_json(f"{file_name}_nr.json"))
    for _i, c in enumerate(data.results.resultsForCriteria):
        c.media = None

    assert data == oData

    solver.modelInputFile = f"{file_name}.json"
    shutil.copyfile(src=Path(__file__).parent.joinpath(f"{file_name}_nr.json"), dst=tmp_path.joinpath(f"{file_name}_nr.json"))

    solver.modelOutputFile = f"{file_name}_nr.json"
    solver.reportName = file_name
    assert solver.buildReport()

# This test case build a input as in test_01_RcSecSolver
def test_rc_solver_cl_usability_001(tmp_path):

    f5 = ForcesOnSection(Fx=-200000.0, My= 200000000.0, Fz=200000.0, descr="force_5")
    f6 = ForcesOnSection(Fx= 200000.0, My=-200000000.0, Fz=100000.0, descr="force_6")
    f7 = ForcesOnSection(Fx=-500000.0, My= 350000000.0, Fz=200000.0, descr="force_7")
    f8 = ForcesOnSection(Fx= 100000.0, My=-200000000.0, Fz= 70000.0, descr="force_8")

    loads = [f5, f6, f7, f8]
    for l in loads:
        l.setLimitState("ultimate")

    code = Code(codeStr="NTC2018")
    concrete = Concrete(descr="Concrete NTC2018 - C25/30")
    concrete.setByCode(code, "C25/30")
    concrete.setEnvironment("not aggressive")
    concreteModel = ConcreteModel()
    concreteModel.fromMaterial(concrete)

    steel = ConcreteSteel(descr="Steel NTC2018 - B450C")
    steel.setByCode(code, "B450C")
    steel.setSensitivity("not sensitive")
    steelModel = SteelModel()
    steelModel.fromMaterial(steel)

    shape = RectangularShape(width=300, height=600, descr="Template RC Section")
    section = ConcreteSectionModel(concreteMat=concreteModel, steelMat=steelModel, shape=shape)

    rebarsOnTop = SteelDisposerOnLine(
        fromPos=ShapePositionEnum.MT,
        diameter=16,
        steelInterDistance=40,
        distanceFromPos=40,
        number=4
    )

    rebarsOnBot = SteelDisposerOnLine(
        fromPos=ShapePositionEnum.MB,
        diameter=24,
        steelInterDistance=40,
        distanceFromPos=40,
        number=4
    )
    section.disposerOnLine = [rebarsOnTop, rebarsOnBot]

    section_solver_input = ModelInputRcSecCheck(loads=loads, section=section)

    section_solver_input.criteria = [CheckableCriteriaEnum.SLU_NM]
    section_solver_input.loadsInCriteria = [[0, 1, 2, 3]]

    solver = RcSecRectSolver()
    solver.setJobPath(str(tmp_path))
    solver.setModelInput(section_solver_input)
    solver.run(SolverOptions.STATIC)
    solver.reportName = "test_rc_solver_cl_usability_001"
    solver.buildReport(opt=ReportOption.REPORT_FROM_RUN)

# This test case build a input as in test_02_RcSecSolver
def test_rc_solver_cl_usability_002(tmp_path):
    f1 = ForcesOnSection(Fx= 150000.0, My= 150000000.0, Fz=150000.0, descr="force_1", id=1)
    f2 = ForcesOnSection(Fx= 100000.0, My= 145000000.0, Fz=120000.0, descr="force_2", id=2)
    f3 = ForcesOnSection(Fx=-100000.0, My= 145000000.0, Fz=120000.0, descr="force_3", id=3)
    f4 = ForcesOnSection(Fx=-125000.0, My= 125000000.0, Fz=125000.0, descr="force_4", id=4)
    f5 = ForcesOnSection(Fx=-200000.0, My= 200000000.0, Fz=200000.0, descr="force_5", id=5)
    f6 = ForcesOnSection(Fx= 200000.0, My=-200000000.0, Fz=100000.0, descr="force_6", id=6)
    f7 = ForcesOnSection(Fx=-500000.0, My= 350000000.0, Fz=200000.0, descr="force_7", id=7)
    f8 = ForcesOnSection(Fx= 100000.0, My=-200000000.0, Fz= 70000.0, descr="force_8", id=8)

    f1.setLimitState("serviceability")
    f1.setFrequency("characteristic")
    f2.setLimitState("serviceability")
    f2.setFrequency("quasi-permanent")
    f3.setLimitState("serviceability")
    f3.setFrequency("quasi-permanent")
    f4.setLimitState("serviceability")
    f4.setFrequency("frequent")

    loads = [f1, f2, f3, f4, f5, f6, f7, f8]
    for l in [f5, f6, f7, f8]:
        l.setLimitState("ultimate")

    code = Code(codeStr="NTC2018")
    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C25/30")
    concrete.setEnvironment("not aggressive")
    concreteModel = ConcreteModel()
    concreteModel.fromMaterial(concrete)

    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")
    steel.setSensitivity("not sensitive")
    steelModel = SteelModel()
    steelModel.fromMaterial(steel)

    shape = RectangularShape(width=300, height=600, descr="Template RC Section")
    section = ConcreteSectionModel(concreteMat=concreteModel, steelMat=steelModel, shape=shape)

    rebarsOnTop = SteelDisposerOnLine(
        fromPos=ShapePositionEnum.MT,
        diameter=20,
        steelInterDistance=40,
        distanceFromPos=40,
        number=4
    )

    rebarsOnBot = SteelDisposerOnLine(
        fromPos=ShapePositionEnum.MB,
        diameter=20,
        steelInterDistance=40,
        distanceFromPos=40,
        number=4
    )
    section.disposerOnLine = [rebarsOnTop, rebarsOnBot]

    stirrup = SteelDisposerStirrup(
        area=100,
        step=150,
        angle=90
    )
    section.stirrup = stirrup

    section_solver_input = ModelInputRcSecCheck(loads=loads, section=section)

    section_solver_input.criteria = [
        CheckableCriteriaEnum.SLE_NM,
        CheckableCriteriaEnum.SLE_F,
        CheckableCriteriaEnum.SLU_T,
        CheckableCriteriaEnum.SLU_NM
    ]
    section_solver_input.loadsInCriteria = [[0,1,2,3],[2,3],[4],[3,5,6,7]]

    solver = RcSecRectSolver()
    solver.setJobPath(str(tmp_path))
    solver.setModelInput(section_solver_input)
    solver.run(SolverOptions.STATIC)
    solver.reportName = "test_rc_solver_cl_usability_002"
    solver.buildReport(opt=ReportOption.REPORT_FROM_RUN)

@pytest.mark.codeaster
@pytest.mark.parametrize("file_name", [f"test_0{n}_RcSecSolver" for n in range(5, 6)])
def test_rc_sec_solver_thermal(tmp_path: Path, file_name: str) -> None:
    solver = RcSecRectSolver()
    # solver.setJobPath(str(Path(__file__).parent))
    solver.setJobPath(str(tmp_path))

    jsonObjectStatic = read_json(f"{file_name}.json")
    shutil.copyfile(src=Path(__file__).parent.joinpath(f"{file_name}.json"), dst=tmp_path.joinpath(f"{file_name}.json"))
    iDataStatic = ModelInputRcSecCheck(**jsonObjectStatic)

    # TODO: skip this if server is unavailable
    if CheckableCriteriaEnum.SLU_NM_FIRE in iDataStatic.criteria:
        jsonObject = read_json(f"{file_name}_Thermal.json")
        iDataThermal = ThermalMapSolverIn(**jsonObject)
        solver.setModelInput(iDataThermal)
        assert solver.run(SolverOptions.THERMAL, jobToken="pippo", test=True)

    solver.setModelInput(iDataStatic)
    solver.run(SolverOptions.STATIC)

    oData = solver.getModelOutput()
    assert isinstance(oData, ModelOutputRcSecCheck)
    for _i, c in enumerate(oData.results.resultsForCriteria):
        c.media = None

    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile = Path(__file__).parent.joinpath(f"{file_name}_nr.json")
    # outfile.write_text(json.dumps(oData.model_dump(), indent=4))

    # Testing data persistence on file for oData
    data = ModelOutputRcSecCheck(**read_json(f"{file_name}_nr.json"))
    for _i, c in enumerate(data.results.resultsForCriteria):
        c.media = None

    assert data == oData

    solver.modelInputFile = f"{file_name}.json"
    shutil.copyfile(src=Path(__file__).parent.joinpath(f"{file_name}_nr.json"), dst=tmp_path.joinpath(f"{file_name}_nr.json"))
    solver.modelOutputFile = f"{file_name}_nr.json"
    solver.reportName = file_name
    solver.setLogLevel(3)
    assert solver.buildReport()

if __name__ == "__main__":
    sys.exit(pytest.main(Path(__file__)))
