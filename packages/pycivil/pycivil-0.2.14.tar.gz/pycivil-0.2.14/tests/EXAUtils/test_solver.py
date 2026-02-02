# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from pycivil.EXAUtils.solver import *


class FuckIn(BaseModel):
    pass


class FuckOut(BaseModel):
    pass


class FuckLogs(BaseModel):
    pass


class FuckRes(BaseModel):
    pass


def test_solver_init() -> None:
    solver = Solver(FuckIn())

    assert isinstance(solver.getModelInput(), FuckIn)
    assert solver.getModelOutput() is None
    assert solver.getModelLogs() is None

    with pytest.raises(NotImplementedError):
        solver.setModelInput(FuckIn())
    assert solver._setModelOutput(FuckOut())
    assert solver._setModelLogs(FuckLogs())
    assert solver._setModelResources(FuckRes())

    assert solver.setJobPath("fuck")
    assert solver.getJobPath() == "fuck"

    assert solver.getModelResources() == FuckRes()

    with pytest.raises(NotImplementedError):
        solver.run()

    with pytest.raises(NotImplementedError):
        solver.buildReport()

    with pytest.raises(NotImplementedError):
        solver.buildResources()

    with pytest.raises(NotImplementedError):
        solver.setModelInput(FuckIn())

    with pytest.raises(NotImplementedError):
        solver.exportModelInput()
