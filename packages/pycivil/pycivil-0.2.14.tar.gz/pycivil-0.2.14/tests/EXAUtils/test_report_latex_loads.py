# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
import pytest

from pycivil.EXAStructural.loads import (
    ForcesOnSection,
)
from pycivil.EXAStructural.loads import Frequency_Enum as Fr
from pycivil.EXAStructural.loads import LimiteState_Enum as Ls
from pycivil.EXAUtils.latexReportMakers import ForcesOnSectionListFB
from pycivil.EXAUtils.report import (
    ReportDriverEnum,
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)

@pytest.mark.needLatex
def test_report_latex_loads(tmp_path: Path):

    latexTemplatePath = getTemplatesPath()
    fragmentBuilder = ForcesOnSectionListFB(latexTemplatePath)
    listOfForces = fragmentBuilder.forces()

    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 101,
            Fy=1e3 * 201,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f1",
            id=1,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 102,
            Fy=1e3 * 202,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f2",
            id=2,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 103,
            Fy=1e3 * 203,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f3",
            id=3,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 104,
            Fy=1e3 * 204,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f4",
            id=4,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 105,
            Fy=1e3 * 205,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f5",
            id=5,
            limitState=Ls.SERVICEABILITY,
            frequency=Fr.CHARACTERISTIC,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 106,
            Fy=1e3 * 206,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f6",
            id=6,
            limitState=Ls.SERVICEABILITY,
            frequency=Fr.FREQUENT,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 107,
            Fy=1e3 * 207,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f7",
            id=7,
            limitState=Ls.SERVICEABILITY,
            frequency=Fr.QUASI_PERMANENT,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 108,
            Fy=1e3 * 208,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f9",
            id=8,
            limitState=Ls.LIMIT_STATE_ND,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 101,
            Fy=1e3 * 201,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f1",
            id=1,
            frequency=Fr.FREQUENCY_ND,
            limitState=Ls.ULTIMATE,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 102,
            Fy=1e3 * 202,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f2",
            id=2,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 103,
            Fy=1e3 * 203,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f3",
            id=3,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 104,
            Fy=1e3 * 204,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f4",
            id=4,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 105,
            Fy=1e3 * 205,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f5",
            id=5,
            limitState=Ls.SERVICEABILITY,
            frequency=Fr.CHARACTERISTIC,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 106,
            Fy=1e3 * 206,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f6",
            id=6,
            limitState=Ls.SERVICEABILITY,
            frequency=Fr.FREQUENT,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 107,
            Fy=1e3 * 207,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f7",
            id=7,
            limitState=Ls.SERVICEABILITY,
            frequency=Fr.QUASI_PERMANENT,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 108,
            Fy=1e3 * 208,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f9",
            id=8,
            limitState=Ls.LIMIT_STATE_ND,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 101,
            Fy=1e3 * 201,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f1",
            id=1,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 102,
            Fy=1e3 * 202,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f2",
            id=2,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 103,
            Fy=1e3 * 203,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f3",
            id=3,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )
    listOfForces.append(
        ForcesOnSection(
            Fx=1e3 * 104,
            Fy=1e3 * 204,
            Fz=1e3 * 300,
            Mx=1e3 * 100000,
            My=1e3 * 200000,
            Mz=1e3 * 300000,
            descr="f4",
            id=4,
            limitState=Ls.ULTIMATE,
            frequency=Fr.FREQUENCY_ND,
        )
    )

    f1 = fragmentBuilder.buildFragment()

    print(f1.frags())

    reporter = Reporter(latexTemplatePath)
    reporter.linkFragments(template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[f1])
    reporter.compileDocument(path=str(tmp_path))
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()
