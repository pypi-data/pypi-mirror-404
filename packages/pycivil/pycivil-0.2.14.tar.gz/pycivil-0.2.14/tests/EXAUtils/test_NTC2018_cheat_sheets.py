# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
import pytest

from pycivil.EXAStructural.cheatsheets.codeNTC2018Rules import (
    BeamMinimumArea,
    BeamMinimumAreaInput,
    BeamMinimumAreaOutput,
    BeamMinimumAreaLogs,
    ConcreteMaterial,
    ConcreteMaterialInput,
    ConcreteMaterialOutput,
    RebarMaterial,
    RebarMaterialInput,
    RebarMaterialOutput,
    SolverBeamMinRebar,
    SolverConcrete,
    SolverSteelRebar,
)
from pycivil.EXAUtils import latexCheatSheets
from pycivil.EXAUtils.report import (
    Fragment,
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)

@pytest.mark.needLatex
def test_concrete_by_law(tmp_path: Path):
    matInput = ConcreteMaterialInput()
    solver = SolverConcrete(inputModel=matInput)

    assert solver.run()

    outputData = solver.getModelOutput()
    assert isinstance(outputData, ConcreteMaterialOutput)
    material = ConcreteMaterial(inputData=matInput, outputData=outputData)

    latexTemplatePath = getTemplatesPath()

    print(f"Latex Templates path for test is {latexTemplatePath}")
    fragBuilder = latexCheatSheets.ConcreteMaterialCS(
        latexTemplatePath=latexTemplatePath, data=material
    )

    frag_title = Fragment()
    frag_title.add(line=r"\section{Calcestruzzo adottato per l'elemento}")
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
        main_file_name="sheet-MatConcrete-NTC2018-ita-main.tex",
        fragments=[frag],
    )
    reporter.compileDocument(path=str(tmp_path), fileName="TEX_MAIN")
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("TEX_MAIN.pdf").exists()
    assert tmp_path.joinpath("TEX_MAIN.tex").exists()

@pytest.mark.needLatex
def test_steelRebar_by_law(tmp_path: Path):
    matInput = RebarMaterialInput()
    solver = SolverSteelRebar(inputModel=matInput)

    assert solver.run()
    outputData = solver.getModelOutput()
    assert isinstance(outputData, RebarMaterialOutput)
    material = RebarMaterial(inputData=matInput, outputData=outputData)

    latexTemplatePath = getTemplatesPath()
    print(f"Latex Templates path for test is {latexTemplatePath}")
    fragBuilder = latexCheatSheets.RebarMaterialCS(
        latexTemplatePath=latexTemplatePath, data=material
    )
    frag_title = Fragment()
    frag_title.add(line=r"\section{Acciaio adottato per l'elemento}")
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
        main_file_name="sheet-MatRebar-NTC2018-ita-main.tex",
        fragments=[frag],
    )
    reporter.compileDocument(path=str(tmp_path), fileName="TEX_MAIN")
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("TEX_MAIN.pdf").exists()
    assert tmp_path.joinpath("TEX_MAIN.tex").exists()

@pytest.mark.needLatex
def test_beam_minimum_area_default(tmp_path: Path):
    dataInput = BeamMinimumAreaInput()
    solver = SolverBeamMinRebar(inputModel=dataInput)

    assert solver.run()

    logsData = solver.getModelLogs()
    assert isinstance(logsData, BeamMinimumAreaLogs)

    outputData = solver.getModelOutput()
    assert isinstance(outputData, BeamMinimumAreaOutput)

    data = BeamMinimumArea(
        inputData=dataInput,
        logsData=logsData,
        outputData=outputData,
    )

    latexTemplatePath = getTemplatesPath()

    print(f"Latex Templates path for test is {latexTemplatePath}")
    fragBuilder = latexCheatSheets.BeamMinimumAreaCS(
        latexTemplatePath=latexTemplatePath, data=data
    )

    frag_title = Fragment()
    frag_title.add(line=r"\section{Area minima delle travi secondo NTC2018}")
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
        main_file_name="sheet-BeamMinimumArea-NTC2018-ita-main.tex",
        fragments=[frag],
    )
    reporter.compileDocument(path=str(tmp_path), fileName="TEX_MAIN")
    print(f"Temporary path for test is {tmp_path}")
    assert tmp_path.joinpath("TEX_MAIN.pdf").exists()
    assert tmp_path.joinpath("TEX_MAIN.tex").exists()
