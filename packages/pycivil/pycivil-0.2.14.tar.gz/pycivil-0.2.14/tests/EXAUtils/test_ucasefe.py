# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pycivil.EXAUtils.ucasefe import RCRectCalculator

def test_rc_rect_calculator_001(tmp_path):
    calc = RCRectCalculator("test", "sezione 1")
    calc.setDescription("sezione 1")
    calc.setLogLevel(3)
    calc.setJobPath(str(tmp_path))

    KN = 1000
    KNm = 1000000

    calc.setDimensions(300, 600)

    calc.addForce(N= 150*KN, M= 150*KNm, T=150*KN, descr="force_1",
                  limit_state="serviceability", frequency="characteristic",
                  check_required=["SLE-NM"])
    calc.addForce(N= 100*KN, M= 145*KNm, T=120*KN, descr="force_2",
                  limit_state="serviceability", frequency="quasi-permanent",
                  check_required=["SLE-NM"])
    calc.addForce(N=-100*KN, M= 145*KNm, T=120*KN, descr="force_3",
                  limit_state="serviceability", frequency="quasi-permanent",
                  check_required=["SLE-NM", "SLE-F"])
    calc.addForce(N=-125*KN, M= 125*KNm, T=125*KN, descr="force_4",
                  limit_state="serviceability", frequency="frequent",
                  check_required=["SLE-NM", "SLE-F"])
    calc.addForce(N=-200*KN, M= 200*KNm, T=200*KN, descr="force_5",
                  limit_state="ultimate",
                  check_required=["SLU-T", "SLU-NM"])
    calc.addForce(N=-200*KN, M=-200*KNm, T=100*KN, descr="force_6",
                  limit_state="ultimate",
                  check_required=["SLU-NM"])
    calc.addForce(N=-500*KN, M= 350*KNm, T=200*KN, descr="force_7",
                  limit_state="ultimate",
                  check_required=["SLU-NM"])
    calc.addForce(N= 100*KN, M=-200*KNm, T= 70*KN, descr="force_8",
                  limit_state="ultimate",
                  check_required=["SLU-NM"])

    calc.setMaterialConcrete("NTC2018","C25/30","not aggressive")
    calc.setMaterialRebars("NTC2018", "B450C", "not sensitive")
    calc.addRebarsFromTop(dist_from_top=40, dist_rebars=40, num=4, diam=20)
    calc.addRebarsFromBot(dist_from_bot=40, dist_rebars=40, num=4, diam=20)
    calc.setStirrup(area=100, step=150, angle=90)

    assert calc.run()
    assert calc.buildReport()


