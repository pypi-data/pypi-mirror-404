# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from pycivil.EXAUtils.strand7PostPro import PostProcessor

def test_001(tmp_path: Path) -> None:
    pp = PostProcessor()

    workPath = str(Path(__file__).resolve().parent)+"/strand7_post_pro/001"
    pp.setWorkingPath(workPath)
    outPath = Path(workPath) / Path("out")
    outPath.mkdir(parents=True, exist_ok=True)

    pp.parse()

    pp.readResults(Path("Elements_Results_RC_SLU.txt"), "WA")
    pp.results_checker(None, check_required='SLU_NM')
    pp.export_checks_to_files(Path("Output_SLU_NM_RC_SLU"), True)
    pp.plot_figure("Elements_Results_RC_SLU.txt", "WA", "SLU_NM")

    pp.readResults(Path("Elements_Results_RC_SLV.txt"), "WA")
    pp.results_checker(1001, check_required='SLU_NM')
    pp.export_checks_to_files(Path("Output_SLU_NM_RC_SLV"), True)
    pp.plot_figure("Elements_Results_RC_SLV.txt", "WA", "SLU_NM")

    pp.readResults(Path("Elements_Results_Plates_Force_SLU.txt"), "FORCE")
    pp.results_checker(1001, check_required='SLU_T')
    pp.export_checks_to_files(Path("Output_Plates_Force_SLU_T_SLU"), True)
    pp.plot_figure("Elements_Results_Plates_Force_SLU.txt", "FORCE", "SLU_T")

    pp.readResults(Path("Elements_Results_Plates_Force_SLV.txt"), "FORCE")
    pp.results_checker(1001, check_required='SLU_T')
    pp.export_checks_to_files(Path("Output_Plates_Force_SLU_T_SLV"), True)
    pp.plot_figure("Elements_Results_Plates_Force_SLV.txt", "FORCE", "SLU_T", 1)

    pp.readResults(Path("Elements_Results_RC_SLE_R.txt"), "WA")
    pp.results_checker(1001, check_required='SLE_NM')
    pp.export_checks_to_files(Path("Output_RC_SLE_NM_SLE_R"), True)
    pp.plot_figure("Elements_Results_RC_SLE_R.txt", "WA", "SLE_NM")

    pp.readResults(Path("Elements_Results_RC_SLE_QP.txt"), "WA")
    pp.results_checker(1001, check_required='SLE_NM')
    pp.export_checks_to_files(Path("Output_RC_SLE_NM_SLE_QP"), True)
    pp.plot_figure("Elements_Results_RC_SLE_QP.txt", "WA", "SLE_NM")

    pp.readResults(Path("Elements_Results_RC_SLE_F.txt"), "WA")
    pp.results_checker(1001, check_required='SLE_F')
    pp.plot_figure("Elements_Results_RC_SLE_F.txt", "WA", "SLE_F")

    pp.readResults(Path("Elements_Results_RC_SLE_QP.txt"), "WA")
    pp.results_checker(1001, check_required='SLE_F')
    pp.plot_figure("Elements_Results_RC_SLE_QP.txt", "WA", "SLE_F")
