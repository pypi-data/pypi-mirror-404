# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import json
from pathlib import Path
import pytest

from pycivil.EXAStructural.rcrecsolver.srvRcSecCheck import ModelInputRcSecCheck
from pycivil.EXAUtils.latexReportMakers import ConcreteSectionFB
from pycivil.EXAUtils.report import (
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)


@pytest.mark.needLatex
def test_report_latex_section_01(tmp_path: Path):

    with open(Path(__file__).parent / "test_report_latex_sections_01.json") as jsonFile:
        jsonObject = json.load(jsonFile)
        jsonFile.close()

    iData = ModelInputRcSecCheck(**jsonObject)

    print(json.dumps(iData.model_dump(), indent=3))

    section = iData.buildRcsRectangular()
    if section is not None:
        latexTemplatePath = getTemplatesPath()
        f = ConcreteSectionFB(latexTemplatePath, rcs=section).buildFragment()
        print(f.frags())
        reporter = Reporter(latexTemplatePath)
        reporter.linkFragments(
            template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[f]
        )
        reporter.compileDocument(path=str(tmp_path))
        print(f"Temporary path for test is {tmp_path}")
        assert tmp_path.joinpath("report.pdf").exists()
        assert tmp_path.joinpath("report.tex").exists()


@pytest.mark.needLatex
def test_report_latex_section_02(tmp_path: Path):

    with open(Path(__file__).parent / "test_report_latex_sections_02.json") as jsonFile:
        jsonObject = json.load(jsonFile)
        jsonFile.close()

    iData = ModelInputRcSecCheck(**jsonObject)

    print(json.dumps(iData.model_dump(), indent=3))

    section = iData.buildRcsRectangular()
    if section is not None:
        latexTemplatePath = getTemplatesPath()
        f = ConcreteSectionFB(latexTemplatePath, rcs=section).buildFragment()
        print(f.frags())
        reporter = Reporter(latexTemplatePath)
        reporter.linkFragments(
            template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[f]
        )
        reporter.compileDocument(path=str(tmp_path))
        print(f"Temporary path for test is {tmp_path}")
        assert tmp_path.joinpath("report.pdf").exists()
        assert tmp_path.joinpath("report.tex").exists()
