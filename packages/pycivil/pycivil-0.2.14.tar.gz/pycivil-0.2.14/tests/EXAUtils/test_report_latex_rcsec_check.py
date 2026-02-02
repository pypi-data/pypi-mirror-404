# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import json
from pathlib import Path
import pytest

from pycivil.EXAStructural.rcrecsolver.srvRcSecCheck import (
    ModelInputRcSecCheck,
    ModelOutputRcSecCheck,
    ReportBuilder,
)
from pycivil.EXAUtils.report import (
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)


@pytest.mark.needLatex
def test_report_latex_rcsec_check_01(tmp_path: Path):

    with open(
        Path(__file__).parent / "test_report_latex_rcsec_check_in_01.json"
    ) as jsonFile:
        jsonObjectIn = json.load(jsonFile)
        jsonFile.close()

    with open(
        Path(__file__).parent / "test_report_latex_rcsec_check_out_01.json"
    ) as jsonFile:
        jsonObjectOut = json.load(jsonFile)
        jsonFile.close()

    iData = ModelInputRcSecCheck(**jsonObjectIn)
    oData = ModelOutputRcSecCheck(**jsonObjectOut)

    rb = ReportBuilder(iData, oData)

    f = rb.buildFragment()

    latexTemplatePath = getTemplatesPath()
    reporter = Reporter(latexTemplatePath)

    reporter.linkFragments(template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[f])
    reporter.compileDocument(path=str(tmp_path))
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()


@pytest.mark.needLatex
def test_report_latex_rcsec_check_02(tmp_path: Path):

    with open(
        Path(__file__).parent / "test_report_latex_rcsec_check_in_02.json"
    ) as jsonFile:
        jsonObjectIn = json.load(jsonFile)
        jsonFile.close()

    with open(
        Path(__file__).parent / "test_report_latex_rcsec_check_out_02.json"
    ) as jsonFile:
        jsonObjectOut = json.load(jsonFile)
        jsonFile.close()

    iData = ModelInputRcSecCheck(**jsonObjectIn)
    oData = ModelOutputRcSecCheck(**jsonObjectOut)

    rb = ReportBuilder(iData, oData)

    f = rb.buildFragment()

    latexTemplatePath = getTemplatesPath()
    reporter = Reporter(latexTemplatePath)

    reporter.linkFragments(template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[f])
    reporter.compileDocument(path=str(tmp_path))
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()
