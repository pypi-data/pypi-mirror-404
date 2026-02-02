# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
import pytest

from pycivil.EXAStructural.codes import Code
from pycivil.EXAUtils.latexReportMakers import CodesFB
from pycivil.EXAUtils.report import (
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)

@pytest.mark.needLatex
def test_report_latex_codes(tmp_path: Path):

    c = Code()
    c.setCodeStr("EC2:ITA")
    print(c.tabKeys)

    c1 = Code("NTC2008")
    c2 = Code("EC2:ITA")
    c3 = Code("CIRC2008")
    c4 = Code("CIRC2018")
    c5 = Code("EC2")

    latexTemplatePath = getTemplatesPath()
    codes = CodesFB(latexTemplatePath, [c1, c2, c3])
    codes.appendUniqueCode(c4)
    codes.appendUniqueCode(c3)
    codes.appendUniqueCode(c5)

    codes.setOptionNameList("Laws used")
    codes.setOptionEnvironnment(True)
    codes.setOptionSection()

    reporter = Reporter(latexTemplatePath)
    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_ENG_CAL,
        fragments=[codes.buildFragment()],
    )
    reporter.compileDocument(path=str(tmp_path))
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()

@pytest.mark.needLatex
def test_report_latex_codes_with_str(tmp_path: Path):
    codes = CodesFB(getTemplatesPath())

    codes.appendUniqueCode(code_str="NTC2008")
    codes.appendUniqueCode(code_str="EC2:ITA")
    codes.appendUniqueCode(code_str="CIRC2008")
    codes.appendUniqueCode(code_str="CIRC2018")
    codes.appendUniqueCode(code_str="EC2")

    codes.setOptionNameList("Laws used")
    codes.setOptionEnvironnment(True)
    codes.setOptionSection()

    reporter = Reporter(getTemplatesPath())

    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_ENG_CAL,
        builder=codes,
    )

    reporter.compileDocument(path=str(tmp_path))
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()
