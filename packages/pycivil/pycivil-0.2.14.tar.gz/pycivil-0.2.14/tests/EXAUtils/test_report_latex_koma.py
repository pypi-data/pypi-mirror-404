# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
import pytest

import numpy as np
import pandas as pd
from pycivil.EXAUtils.report import (
    Fragment,
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath,
)

@pytest.mark.needLatex
def test_report_latex_koma_01(tmp_path: Path):
    # Test per documenti latex
    latexTemplatePath = getTemplatesPath()

    f1 = Fragment(latexTemplatePath)
    f1.add("Hello world EN")

    f2 = Fragment(latexTemplatePath)
    f2.add("Ciao mondo IT")

    reporter = Reporter(latexTemplatePath)
    reporter.linkFragments(template=ReportTemplateEnum.TEX_KOMA, fragments=[f1, f2])

    reporter.compileDocument(path=str(tmp_path))
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()



@pytest.mark.needLatex
def test_report_latex_koma_02(tmp_path: Path):
    """Latex PDF document is created successfully."""
    f1 = Fragment(latexTemplatePath=getTemplatesPath())
    f1.add("Hello world EN")

    f2 = Fragment(latexTemplatePath=getTemplatesPath())
    f2.add(r"\textbf{Ciao mondo IT}")

    random_data = pd.DataFrame(np.random.random((5, 5)))
    f2.add(random_data.to_latex())

    reporter = Reporter(latexTemplatePath=getTemplatesPath())
    reporter.linkFragments(template=ReportTemplateEnum.TEX_KOMA, fragments=[f1, f2])

    reporter.compileDocument(path=str(tmp_path))
    assert tmp_path.joinpath("report.pdf").exists()
    assert tmp_path.joinpath("report.tex").exists()
