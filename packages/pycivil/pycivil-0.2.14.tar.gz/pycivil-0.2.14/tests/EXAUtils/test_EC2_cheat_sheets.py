# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import pytest

from pycivil.EXAStructural.cheatsheets.codeEC2Rules import (
    PlateMinimumArea,
    PlateMinimumAreaInput,
    SolverPlateMinRebar,
    PlateMinimumAreaLogs,
    PlateMinimumAreaOutput
)
from pycivil.EXAUtils import latexCheatSheets
from pycivil.EXAUtils.report import (
    Fragment,
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)

@pytest.mark.needLatex
def test_plates_minimum_area_default(tmp_path: Path):
    dataInput = PlateMinimumAreaInput()
    solver = SolverPlateMinRebar(inputModel=dataInput)

    assert solver.run()

    modelLogs = solver.getModelLogs()
    assert isinstance(modelLogs, PlateMinimumAreaLogs)

    modelOuts = solver.getModelOutput()
    assert isinstance(modelOuts, PlateMinimumAreaOutput)

    data = PlateMinimumArea(
        inputData=dataInput,
        logsData=modelLogs,
        outputData=modelOuts,
    )

    latexTemplatePath = getTemplatesPath()

    print(f"Latex Templates path for test is {latexTemplatePath}")
    fragBuilder = latexCheatSheets.PlateMinimumAreaCS(
        latexTemplatePath=latexTemplatePath, data=data
    )

    frag_title = Fragment()
    frag_title.add(line=r"\section{Area minima delle piastre secondo EC2}")
    frag = fragBuilder.buildFragment()

    reporter = Reporter(latexTemplatePath)

    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[frag_title, frag]
    )
    reporter.compileDocument(path=str(tmp_path), fileName="TEX_ENG_CAL")
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("TEX_ENG_CAL.pdf").exists()
    assert tmp_path.joinpath("TEX_ENG_CAL.tex").exists()

    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_KOMA, fragments=[frag_title, frag]
    )
    reporter.compileDocument(path=str(tmp_path), fileName="TEX_KOMA")
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("TEX_KOMA.pdf").exists()
    assert tmp_path.joinpath("TEX_KOMA.tex").exists()

    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_MAIN,
        main_file_name="sheet-PlateMinimumArea-EC211-ita-main.tex",
        fragments=[frag],
    )
    reporter.compileDocument(path=str(tmp_path), fileName="TEX_MAIN")
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("TEX_MAIN.pdf").exists()
    assert tmp_path.joinpath("TEX_MAIN.tex").exists()
