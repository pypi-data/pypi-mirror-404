# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
import pytest

from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAUtils.latexReportMakers import ConcreteFB, SteelConcreteFB
from pycivil.EXAUtils.report import (
    EnumFBSection,
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)

@pytest.mark.needLatex
def test_report_materials_latex_0001(tmp_path: Path):

    code = Code("NTC2018")

    concrete = Concrete()
    concrete.setByCode(codeObj=code, catstr="C25/30")

    latexTemplatePath = getTemplatesPath()
    fragmentBuilder = ConcreteFB(latexTemplatePath, concrete)

    fragmentBuilder.setFragmentOptions({"glossary": True})

    f = fragmentBuilder.buildFragment()

    reporter = Reporter(latexTemplatePath)
    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[f], glossary=True
    )
    reporter.compileDocument(path=str(tmp_path))
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()


@pytest.mark.needLatex
def test_report_materials_latex_0002(tmp_path: Path):

    code = Code("NTC2018")

    steel = ConcreteSteel()

    steel.setByCode(code, "B450A")
    latexTemplatePath = getTemplatesPath()

    fragmentBuilder = SteelConcreteFB(latexTemplatePath, steel)

    fragmentBuilder.setFragmentOptions(
        {"section_title": "Acciaio B450A", "section_level": EnumFBSection.SEC_SECTION}
    )
    f1 = fragmentBuilder.buildFragment()

    steel.setByCode(code, "B450C")
    fragmentBuilder = SteelConcreteFB(latexTemplatePath, steel)

    fragmentBuilder.setFragmentOptions(
        {"section_title": "Acciaio B450C", "section_level": EnumFBSection.SEC_SECTION}
    )

    # Here unsetted by code, the builder strip code used and kind of sensitivity
    steel.set_gammas(1.0)
    f2 = fragmentBuilder.buildFragment()

    reporter = Reporter(latexTemplatePath)
    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_ENG_CAL, fragments=[f1, f2]
    )
    reporter.compileDocument(path=str(tmp_path))

    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()
