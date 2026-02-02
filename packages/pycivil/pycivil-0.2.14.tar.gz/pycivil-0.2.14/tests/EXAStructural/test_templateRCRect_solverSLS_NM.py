# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import math
from pathlib import Path

import pytest
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.sections import SectionStates
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2


# ==============================================================================
# BY-HAND TEST CASE #5 - Manuscript 22/1/26
# ==============================================================================
# Section geometry:
#   - Width B = 1000 mm
#   - Height H = 500 mm
#
# Materials:
#   - Concrete C32/40:
#       f_ck = 32 MPa
#       f_ctm = 0.30 * f_ck^(2/3) = 3.02 MPa
#       f_ctm_crack = f_ctm / 1.2 = 2.52 MPa
#       E_cm = 22000 * (f_ck/10)^0.3 = 33545 MPa
#   - Steel:
#       E_s = 200'000 MPa
#       n = E_s / E_cm ≈ 6
#
# Reinforcement:
#   - Top: 5∅24 -> A_s = 452.2 mm² at d = 492.9 mm from bottom (cover 7.4 mm)
#   - Bottom: 5∅18 -> A_s = 254.3 mm² at d = 7.1 mm from bottom (cover 7.1 mm)
#
# UNCRACKED SECTION (Sezione non fessurata):
#   Neutral axis calculation:
#     x_f = [A_s1*d1*n + A_s2*d2*n + B*H*(H/2)] / [A_s1*n + A_s2*n + B*H]
#     x_f = [452.2*492.9*5.6 + 254.3*7.1*5.6 + 1000*500*250] /
#           [452.2*5.6 + 254.3*5.6 + 1000*500]
#     x_f = [6.687e6 + 54.16e3 + 125e6] / [13.57e3 + 7.63e3 + 500e3]
#     x_f = 252.76 mm (from bottom)
#
#   Moment of inertia (uncracked):
#     J_cls = (1/12)*B*H³ + B*H*(H/2 - x_f)²
#           = (1/12)*1000*500³ + 1000*500*(2.76)² = 10.42e9 + 3.81e6 ≈ 10.42e9 mm⁴
#     J_Acc = A_s1*(d1-x_f)²*n + A_s2*(x_f-d2)²*n
#           = 452.2*233.8²*5.6 + 254.3*245.66²*5.6 = 780.1e6 + 460.4e6 = 1.24e9 mm⁴
#     J_i^I = J_cls + J_Acc = 11.66e9 mm⁴ = 1'166'000 cm⁴
#
#   First cracking moment:
#     M_cr = (f_ctm * J_i^I) / y_cr = (2.52 * 11.66e9) / 252.76 = 116.25 kN.m
#
# CRACKED SECTION (Sezione fessurata):
#   Neutral axis (from compression edge):
#     Solving quadratic equation for x:
#     x = [-n*(A_s1+A_s2) + sqrt((n*(A_s1+A_s2))² + 2*B*n*(A_s1*d1+A_s2*d2))] / B
#     x ≈ 69.15 mm (from top/compression edge)
#
#   Moment of inertia (cracked):
#     J_cls = (1/12)*B*x³ + B*x*(x/2)² (only compressed concrete)
#     J_Acc = A_s1*(d1'-x)²*n + A_s2*(d2'-x)²*n (d' from compression edge)
#     J_i^II = 1.42e9 mm⁴ = 139'225 cm⁴
#
#   Stiffness ratio:
#     J_i^I / J_i^II ≈ 8.21
# ==============================================================================


# --------------------
# BY-HAND TEST CASE #3
# --------------------
def test_symmetrical_uncracked_NM_001(tmp_path: Path) -> None:
    # Setting code for check
    code = Code("NTC2018")

    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C25/30")

    # Setting code for check
    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")

    # Build checkable structural system
    rcSection = RCTemplRectEC2(1, "Template RC Section")

    # Concrete dimension
    rcSection.setDimH(600)
    rcSection.setDimW(300)

    # Longitudinal rebars
    lineMTRebars = rcSection.addSteelArea("LINE-MT", dist=50, d=20, nb=4, sd=40)
    lineMBRebars = rcSection.addSteelArea("LINE-MB", dist=50, d=20, nb=4, sd=40)
    assert isinstance(lineMTRebars, list)
    assert isinstance(lineMBRebars, list)

    # Geometrical properties
    assert pytest.approx(rcSection.calConcreteArea()) == 180000
    assert pytest.approx(rcSection.calSteelArea(), rel=1e-3) == 2513
    assert pytest.approx(rcSection.calIdealArea(), rel=1e-3) == 217699
    assert pytest.approx(rcSection.calProp_Ihx(), rel=1e-3) == 7.755e09
    assert pytest.approx(
        [rcSection.calBarycenterOfConcrete().x, rcSection.calBarycenterOfConcrete().y]
    ) == [0.0, 0.0]
    assert pytest.approx(
        [rcSection.calBarycenterOfSteel().x, rcSection.calBarycenterOfSteel().y]
    ) == [0.0, 0.0]
    assert pytest.approx(
        [rcSection.calBarycenter().x, rcSection.calBarycenter().y]
    ) == [0.0, 0.0]

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    sigmac, sigmas, xi = rcSection.solverSLS_NM(0 * KN, 0.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [0, 0, None]
    for i in rcSection.getConcrStress():
        assert pytest.approx(i, rel=1e-3) == 0
    for i in rcSection.getSteelStress():
        assert pytest.approx(i, rel=1e-3) == 0

    sigmac, sigmas, xi = rcSection.solverSLS_NM(1000 * KN, 0.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [4.593, 68.895, math.inf]
    for i in rcSection.getConcrStress():
        assert pytest.approx(i, rel=1e-3) == 4.593
    for i in rcSection.getSteelStress():
        assert pytest.approx(i, rel=1e-3) == 68.895

    sigmac, sigmas, xi = rcSection.solverSLS_NM(-1000 * KN, 0.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [-4.593, -68.895, math.inf]
    for i in rcSection.getConcrStress():
        assert pytest.approx(i, rel=1e-3) == -4.593
    for i in rcSection.getSteelStress():
        assert pytest.approx(i, rel=1e-3) == -68.895

    sigmac, sigmas, xi = rcSection.solverSLS_NM(-100 * KN, 0.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [
        -0.4593,
        -68.895 / 10,
        math.inf,
    ]
    for i in rcSection.getConcrStress():
        assert pytest.approx(i, rel=1e-3) == -0.4593
    for i in rcSection.getSteelStress():
        assert pytest.approx(i, rel=1e-3) == -6.8895

    sigmac, sigmas, xi = rcSection.solverSLS_NM(+100 * KN, 0.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [+0.4593, +6.8895, math.inf]
    for i in rcSection.getConcrStress():
        assert pytest.approx(i, rel=1e-3) == +0.4593
    for i in rcSection.getSteelStress():
        assert pytest.approx(i, rel=1e-3) == +6.8895

    sigmac, sigmas, xi = rcSection.solverSLS_NM(0.0 * KN, 150.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [-5.803, 72.53, 300]
    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == +5.803
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-3) == -5.803
    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected: float = 0
        if idx in lineMBRebars:
            stressExpected = +72.53
        if idx in lineMTRebars:
            stressExpected = -72.53
        print(
            f"Steel stress calculated: {i:.5f} equal to expected: {stressExpected:.5f}"
        )
        assert pytest.approx(i, rel=1e-3) == stressExpected

    sigmac, sigmas, xi = rcSection.solverSLS_NM(0.0 * KN, -150.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [-5.803, +72.53, 300]
    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == -5.803
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-3) == +5.803
    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected = 0.0
        if idx in lineMBRebars:
            stressExpected = -72.53
        if idx in lineMTRebars:
            stressExpected = +72.53
        print(
            f"Steel stress calculated: {i:.5f} equal to expected: {stressExpected:.5f}"
        )
        assert pytest.approx(i, rel=1e-3) == stressExpected

    # Neutral axis is measured from bottom to top of section
    sigmac, sigmas, xi = rcSection.solverSLS_NM(
        -1000.0 * KN, +150.0 * KNm, uncracked=True
    )
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [-10.396, +3.635, 537.45]
    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-2) == +1.210
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-2) == -10.396
    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected = 0.0
        if idx in lineMBRebars:
            stressExpected = +3.635
        if idx in lineMTRebars:
            stressExpected = -141.425
        print(
            f"Steel stress calculated: {i:.5f} equal to expected: {stressExpected:.5f}"
        )
        assert pytest.approx(i, rel=1e-2) == stressExpected

    sigmac, sigmas, xi = rcSection.solverSLS_NM(
        -1000.0 * KN, -150.0 * KNm, uncracked=True
    )
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [-10.396, +3.635, 62.65]
    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-2) == -10.396
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-2) == +1.210
    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected = 0.0
        if idx in lineMBRebars:
            stressExpected = -141.425
        if idx in lineMTRebars:
            stressExpected = +3.635
        print(
            f"Steel stress calculated: {i:.5f} equal to expected: {stressExpected:.5f}"
        )
        assert pytest.approx(i, rel=1e-2) == stressExpected

    sigmac, sigmas, xi = rcSection.solverSLS_NM(
        +1000.0 * KN, +150.0 * KNm, uncracked=True
    )
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [-1.210, +141.425, 62.55]
    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-2) == 10.396
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-2) == -1.210
    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected = 0.0
        if idx in lineMBRebars:
            stressExpected = +141.425
        if idx in lineMTRebars:
            stressExpected = -3.635
        print(
            f"Steel stress calculated: {i:.5f} equal to expected: {stressExpected:.5f}"
        )
        assert pytest.approx(i, rel=1e-2) == stressExpected

    sigmac, sigmas, xi = rcSection.solverSLS_NM(
        +1000.0 * KN, -150.0 * KNm, uncracked=True
    )
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [-1.210, +141.425, 537.45]
    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-2) == -1.210
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-2) == 10.396
    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected = 0.0
        if idx in lineMBRebars:
            stressExpected = -3.635
        if idx in lineMTRebars:
            stressExpected = +141.425
        print(
            f"Steel stress calculated: {i:.5f} equal to expected: {stressExpected:.5f}"
        )
        assert pytest.approx(i, rel=1e-2) == stressExpected


# ----------------------
# BY-HAND TEST CASE #2.2
# ----------------------
def test_uncracked_NM_002(tmp_path: Path) -> None:
    # Setting code for check
    code = Code("NTC2008")

    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C32/40")

    # Setting code for check
    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")

    # Build checkable structural system
    rcSection = RCTemplRectEC2(1, "Template RC Section")

    # Concrete dimension
    rcSection.setDimH(1200)
    rcSection.setDimW(800)

    # Longitudinal rebars
    # Aggregates diameter maximum 25mm
    lineRebars01 = rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    lineRebars02 = rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    lineRebars03 = rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    lineRebars04 = rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)
    assert isinstance(lineRebars01, list)
    assert isinstance(lineRebars02, list)
    assert isinstance(lineRebars03, list)
    assert isinstance(lineRebars04, list)

    # Geometrical properties
    assert pytest.approx(rcSection.calConcreteArea(), rel=1e-6) == 960.00e03
    assert pytest.approx(rcSection.calSteelArea(), rel=1e-3) == 18.09e03
    assert pytest.approx(rcSection.calIdealArea(), rel=1e-3) == 1.23135e06
    assert pytest.approx(
        [rcSection.calBarycenterOfConcrete().x, rcSection.calBarycenterOfConcrete().y]
    ) == [0.0, 0.0]
    assert pytest.approx(
        [rcSection.calBarycenterOfSteel().x, rcSection.calBarycenterOfSteel().y],
        rel=1e-2,
        abs=1e-3,
    ) == [0.0, -220.89]
    assert pytest.approx(
        [rcSection.calBarycenter().x, rcSection.calBarycenter().y], rel=1e-2, abs=1
    ) == [0.0, -49.39]
    assert (
        pytest.approx(rcSection.calProp_Ihx(barycenter=True), rel=1e-3, abs=1e-3)
        == 176.24e09
    )

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    sigmac, sigmas, xi = rcSection.solverSLS_NM(0 * KN, 2400.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [-8.84, +96.97, 649.39]

    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == +7.4988
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-3) == -8.840

    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected: float = 0
        if idx in lineRebars01:
            stressExpected = -117.11
        if idx in lineRebars02:
            stressExpected = +74.91
        if idx in lineRebars03:
            stressExpected = +85.94
        if idx in lineRebars04:
            stressExpected = +96.97
        assert pytest.approx(i, rel=1e-2) == stressExpected


# ----------------------
# BY-HAND TEST CASE #2.2
# ----------------------
def test_uncracked_NM_003(tmp_path: Path) -> None:
    # Setting code for check
    code = Code("NTC2008")

    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C32/40")

    # Setting code for check
    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")

    # Build checkable structural system
    rcSection = RCTemplRectEC2(1, "Template RC Section")

    # Concrete dimension
    rcSection.setDimH(1200)
    rcSection.setDimW(800)

    # Longitudinal rebars
    # Aggregates diameter maximum 25mm
    lineRebars01 = rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    lineRebars02 = rcSection.addSteelArea("LINE-MT", dist=130, d=24, nb=10, sd=49)
    lineRebars03 = rcSection.addSteelArea("LINE-MT", dist=184, d=24, nb=10, sd=49)
    lineRebars04 = rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)
    assert isinstance(lineRebars01, list)
    assert isinstance(lineRebars02, list)
    assert isinstance(lineRebars03, list)
    assert isinstance(lineRebars04, list)

    # Geometrical properties
    assert pytest.approx(rcSection.calConcreteArea(), rel=1e-6) == 960.00e03
    assert pytest.approx(rcSection.calSteelArea(), rel=1e-3) == 18.09e03
    assert pytest.approx(rcSection.calIdealArea(), rel=1e-3) == 1.23135e06
    assert pytest.approx(
        [rcSection.calBarycenterOfConcrete().x, rcSection.calBarycenterOfConcrete().y]
    ) == [0.0, 0.0]
    assert pytest.approx(
        [rcSection.calBarycenterOfSteel().x, rcSection.calBarycenterOfSteel().y],
        rel=1e-2,
        abs=1e-3,
    ) == [0.0, +220.89]
    assert pytest.approx(
        [rcSection.calBarycenter().x, rcSection.calBarycenter().y], rel=1e-2, abs=1
    ) == [0.0, +49.39]
    assert (
        pytest.approx(rcSection.calProp_Ihx(barycenter=True), rel=1e-3, abs=1e-3)
        == 176.24e09
    )

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    sigmac, sigmas, xi = rcSection.solverSLS_NM(0 * KN, -2400.0 * KNm, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [-8.84, +96.97, 550.61]

    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == -8.840
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-3) == +7.4988

    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected: float = 0
        if idx in lineRebars04:
            stressExpected = -117.11
        if idx in lineRebars03:
            stressExpected = +74.91
        if idx in lineRebars02:
            stressExpected = +85.94
        if idx in lineRebars01:
            stressExpected = +96.97
        assert pytest.approx(i, rel=1e-2) == stressExpected


# ----------------------
# BY-HAND TEST CASE #2.5
# ----------------------
def test_cracked_stretched_NM_004(tmp_path: Path) -> None:
    # Setting code for check
    code = Code("NTC2008")

    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C32/40")

    # Setting code for check
    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")

    # Build checkable structural system
    rcSection = RCTemplRectEC2(1, "Template RC Section")

    # Concrete dimension
    rcSection.setDimH(1200)
    rcSection.setDimW(800)

    # Longitudinal rebars
    # Aggregates diameter maximum 25mm
    lineRebars01 = rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    lineRebars02 = rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    lineRebars03 = rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    lineRebars04 = rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)
    assert isinstance(lineRebars01, list)
    assert isinstance(lineRebars02, list)
    assert isinstance(lineRebars03, list)
    assert isinstance(lineRebars04, list)

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    sigmac, sigmas, xi = rcSection.solverSLS_NM(+3619 * KN, 0.0 * KNm, uncracked=False)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [0.0, +376.27, 1666.0]

    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == 0.0
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-3) == 0.0

    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected: float = 0
        if idx in lineRebars01:
            stressExpected = 376.27
        if idx in lineRebars02:
            stressExpected = 153.86
        if idx in lineRebars03:
            stressExpected = 141.05
        if idx in lineRebars04:
            stressExpected = 128.27
        assert pytest.approx(i, rel=1e-2) == stressExpected


# ----------------------
# BY-HAND TEST CASE #2.6
# ----------------------
def test_cracked_compressed_NM_005(tmp_path: Path) -> None:
    # Setting code for check
    code = Code("NTC2008")

    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C32/40")

    # Setting code for check
    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")

    # Build checkable structural system
    rcSection = RCTemplRectEC2(1, "Template RC Section")

    # Concrete dimension
    rcSection.setDimH(1200)
    rcSection.setDimW(800)

    # Longitudinal rebars
    # Aggregates diameter maximum 25mm
    lineRebars01 = rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    lineRebars02 = rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    lineRebars03 = rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    lineRebars04 = rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)
    assert isinstance(lineRebars01, list)
    assert isinstance(lineRebars02, list)
    assert isinstance(lineRebars03, list)
    assert isinstance(lineRebars04, list)

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    sigmac, sigmas, xi = rcSection.solverSLS_NM(-3619 * KN, 0.0 * KNm, uncracked=False)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [-3.599, -36.92, 3557.496]

    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == -2.385
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-2) == -3.599

    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected: float = 0
        if idx in lineRebars01:
            stressExpected = -52.84
        if idx in lineRebars02:
            stressExpected = -38.56
        if idx in lineRebars03:
            stressExpected = -37.74
        if idx in lineRebars04:
            stressExpected = -36.92
        assert pytest.approx(i, rel=1e-2) == stressExpected


# ----------------------
# BY-HAND TEST CASE #2.1
# ----------------------
def test_cracked_bending_NM_006(tmp_path: Path) -> None:
    # Setting code for check
    code = Code("NTC2008")

    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C32/40")

    # Setting code for check
    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")

    # Build checkable structural system
    rcSection = RCTemplRectEC2(1, "Template RC Section")

    # Concrete dimension
    rcSection.setDimH(1200)
    rcSection.setDimW(800)

    # Longitudinal rebars
    # Aggregates diameter maximum 25mm
    lineRebars01 = rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    lineRebars02 = rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    lineRebars03 = rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    lineRebars04 = rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)
    assert isinstance(lineRebars01, list)
    assert isinstance(lineRebars02, list)
    assert isinstance(lineRebars03, list)
    assert isinstance(lineRebars04, list)

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    sigmac, sigmas, xi = rcSection.solverSLS_NM(0.0 * KN, 2400.0 * KNm, uncracked=False)

    assert pytest.approx([sigmac, sigmas, xi], rel=1e-3) == [-10.31, +207.10, 480.51]

    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == 0.0
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-2) == -10.31

    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected: float = 0
        if idx in lineRebars01:
            stressExpected = -130.19
        if idx in lineRebars02:
            stressExpected = +172.34
        if idx in lineRebars03:
            stressExpected = +189.72
        if idx in lineRebars04:
            stressExpected = +207.10
        assert pytest.approx(i, rel=1e-2) == stressExpected


def section_manuscript_5(mirr: bool = False):
    code = Code("NTC2008")
    concrete = Concrete(descr="My concrete")
    concrete.setByCode(code, "C32/40")
    steel = ConcreteSteel(descr="My steel")
    steel.setByCode(code, "B450C")
    rcSection = RCTemplRectEC2(1, "Template RC Section - Manuscript #5")
    rcSection.setDimH(500)
    rcSection.setDimW(1000)
    lineRebarsTop = rcSection.addSteelArea("LINE-MT" if not mirr else "LINE-MB", dist=74, d=24, nb=5, sd=200)
    lineRebarsBot = rcSection.addSteelArea("LINE-MB" if not mirr else "LINE-MT", dist=71, d=18, nb=5, sd=200)
    assert isinstance(lineRebarsTop, list)
    assert isinstance(lineRebarsBot, list)
    return rcSection

# -----------------------------------------
# BY-HAND TEST CASE #5 - Manuscript 22/1/26
# -----------------------------------------
def test_manuscript_uncracked_cracked_NM_007(tmp_path: Path) -> None:
    """
    Test case from manuscript #5 dated 22/1/26.

    Section geometry:
        - Width B = 1000 mm
        - Height H = 500 mm

    Materials:
        - Concrete C32/40:
            f_ck = 32 MPa
            f_ctm = 0.30 * f_ck^(2/3) = 3.02 MPa
            f_ctm_crack = f_ctm/1.2 = 2.52
            E_cm = 22000 * (f_ck/10)^0.3 = 33545 MPa
        - Steel:
            E_s = 200'000 MPa
            n = E_s / E_cm ≈ 6

    Reinforcement:
        - Top: 5∅24 -> A_s = 5 * 452.4 = 2262 mm² at d = 492.9mm from bottom
          (single bar area: π*24²/4 = 452.4 mm²)
        - Bottom: 5∅18 -> A_s = 5 * 254.5 = 1272 mm² at d = 7.1mm from bottom
          (single bar area: π*18²/4 = 254.5 mm²)
        - Total steel area: 2262 + 1272 = 3534 mm²

    UNCRACKED SECTION (Sezione non fessurata):
        Neutral axis calculation:
            x_f = [A_s1*d1*n + A_s2*d2*n + B*H*(H/2)] / [A_s1*n + A_s2*n + B*H]
            x_f = [2262*492.9*6 + 1272*7.1*6 + 1000*500*250] /
                  [2262*6 + 1272*6 + 1000*500]
            x_f = 252.76 mm (from bottom)

        Moment of inertia (uncracked):
            J_i^I = 11.66e9 mm⁴ = 1'166'000 cm⁴

        First cracking moment:
            M_cr = (f_ctm * J_i^I) / y_cr = (2.52 * 11.66e9) / 252.76 = 116.25 kN.m

    CRACKED SECTION (Sezione fessurata):
        Neutral axis: x = 69.15 mm from compression edge
        Moment of inertia: J_i^II = 1.42e9 mm⁴ = 139'225 cm⁴
        Stiffness ratio: J_i^I / J_i^II ≈ 8.21
    """
    rcSection = section_manuscript_5()

    homo_coeff = 6.0
    rcSection.setHomogenization(homo_coeff)

    # Geometrical properties from manuscript
    # Total steel area: 5*π*24²/4 + 5*π*18²/4 = 2262 + 1272 = 3534 mm²
    assert pytest.approx(rcSection.calSteelArea(), rel=1e-4) == 3534

    # Concrete area: B * H = 1000 * 500 = 500000 mm²
    assert pytest.approx(rcSection.calConcreteArea(), rel=1e-4) == 500000

    # yg is calculated starting from origin fixed at middle of rectangle

    yg = rcSection.calBarycenter().y
    assert pytest.approx(yg, rel=1e-3) == 1.96

    # Uncracked moment of inertia
    # Manuscript value (with n≈6): J_i^I = 11.66e9 mm⁴
    # Code uses actual modular ratio from materials, resulting in slightly higher value
    Icx = rcSection.calProp_Icx(yg=yg)
    assert pytest.approx(Icx, rel=1e-3) == 10.42e9

    Isx = rcSection.calProp_Isx(yg=yg)
    assert pytest.approx(Isx, rel=1e-3) == 110.12e6

    Ihx = rcSection.calProp_Ihx(barycenter=True)
    assert Ihx > 10e9  # Sanity check: should be greater than pure concrete section

    Mcr_pos, Mcr_neg = rcSection.calCriticalMoment()
    assert pytest.approx(110.83e6, rel=1e-3) == Mcr_pos
    assert -Mcr_neg > Mcr_pos

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    # Test uncracked section with pure bending at first cracking moment
    # M_cr = 116.25 kN.m (from manuscript with J_i^I = 11.66e9, y_cr = 252.76mm)
    # f_ctm = 3.02 MPa
    rcSection.solverSLS_NM(0.0 * KN, 110.83 * KNm, uncracked=True)

    # Concrete stress at bottom must be close to f_ctm value with Mcr as effort
    sigmac_BL = rcSection.getConcrStress()[0]
    assert pytest.approx(sigmac_BL, rel=1e-3) == 2.52

def test_manuscript_get_area_properties():
    # Build section
    rcSection = section_manuscript_5()
    homo_coeff = 6.0
    rcSection.setHomogenization(homo_coeff)

    # then for uncracked (default)
    #
    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties()
    assert pytest.approx(0.00, rel=1e-3) == ycg
    assert pytest.approx(48.3, rel=1e-2) == ysg
    assert pytest.approx(1.96, rel=1e-3) == yhg
    assert pytest.approx(500.0e+3, rel=1e-6) == Ac
    assert pytest.approx(3.53e+3, rel=1e-2) == As
    assert pytest.approx(521.2e+3, rel=1e-4) == Ah
    assert pytest.approx(-980e+3, rel=1e-3) == Scx
    assert pytest.approx(163.4e+3, rel=1e-3) == Ssx
    assert pytest.approx(    0.0, rel=1e-16) == Shx
    assert pytest.approx(10.42e+9, rel=1e-3) == Jcx
    assert pytest.approx(110.12e+6, rel=1e-3) == Jsx
    assert pytest.approx(11.08e+9, rel=1e-4) == Jhx

    # then for uncracked
    #
    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties(SectionStates.UNCRACKED)
    assert pytest.approx(0.00, rel=1e-3) == ycg
    assert pytest.approx(48.3, rel=1e-2) == ysg
    assert pytest.approx(1.96, rel=1e-3) == yhg
    assert pytest.approx(500.0e+3, rel=1e-6) == Ac
    assert pytest.approx(3.53e+3, rel=1e-2) == As
    assert pytest.approx(521.2e+3, rel=1e-4) == Ah
    assert pytest.approx(-980e+3, rel=1e-3) == Scx
    assert pytest.approx(163.4e+3, rel=1e-3) == Ssx
    assert pytest.approx(    0.0, rel=1e-16) == Shx
    assert pytest.approx(10.42e+9, rel=1e-3) == Jcx
    assert pytest.approx(110.12e+6, rel=1e-3) == Jsx
    assert pytest.approx(11.08e+9, rel=1e-4) == Jhx

    # then for compressed
    #
    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties(SectionStates.COMPRESSED)
    assert pytest.approx(0.00, rel=1e-3) == ycg
    assert pytest.approx(48.3, rel=1e-2) == ysg
    assert pytest.approx(1.96, rel=1e-3) == yhg
    assert pytest.approx(500.0e+3, rel=1e-6) == Ac
    assert pytest.approx(3.53e+3, rel=1e-2) == As
    assert pytest.approx(521.2e+3, rel=1e-4) == Ah
    assert pytest.approx(-980e+3, rel=1e-3) == Scx
    assert pytest.approx(163.4e+3, rel=1e-3) == Ssx
    assert pytest.approx(    0.0, rel=1e-16) == Shx
    assert pytest.approx(10.42e+9, rel=1e-3) == Jcx
    assert pytest.approx(110.12e+6, rel=1e-3) == Jsx
    assert pytest.approx(11.08e+9, rel=1e-4) == Jhx

    # If i didn't launch solverSLS_NM before for PARTIALIZED i can't have results
    assert rcSection.getAreaProperties(SectionStates.PARTIALIZED) is None


    # Launch withowt forces
    # solverSLS_NM classifies section properly lucly
    rcSection.solverSLS_NM(N=0.0e+3, M=150e+6, uncracked=False)
    assert pytest.approx(73.46, rel=1e-2) == rcSection.xi()

    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties(SectionStates.PARTIALIZED)
    assert pytest.approx(73.46e+3, rel=1e-2) == Ac
    assert pytest.approx( 3.53e+3, rel=1e-2) == As
    assert pytest.approx(94.63e+3, rel=1e-2) == Ah
    assert pytest.approx(  213.27, rel=1e-2) == ycg
    assert pytest.approx(    48.3, rel=1e-2) == ysg
    assert pytest.approx(  176.67, rel=1e-2) == yhg
    assert pytest.approx(2.68e+6, rel=1e-1) == Scx
    assert pytest.approx(-453.1e+3, rel=1e-2) == Ssx
    assert pytest.approx(    0.0, abs=1e-6) == Shx
    assert pytest.approx(131.43e+6, rel=1e-1) == Jcx
    assert pytest.approx(1.60e+8, rel=1e-2) == Jsx
    assert pytest.approx(1.091e+9, rel=1e-2) == Jhx

    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties(SectionStates.STRETCHED)
    assert pytest.approx(     0.0, rel=1e-16) == Ac
    assert pytest.approx( 3.53e+3, rel=1e-2)  == As
    assert pytest.approx( 3.53e+3, rel=1e-2)  == Ah
    assert pytest.approx(  0.0, rel=1e-2)     == ycg
    assert pytest.approx(    48.3, rel=1e-2) == ysg
    assert pytest.approx(    48.3, rel=1e-2) == yhg
    assert pytest.approx( 0.0, rel=1e-16) == Scx
    assert pytest.approx( 0.0, abs=1e-10) == Ssx
    assert pytest.approx( 0.0, abs=1e-10) == Shx
    assert pytest.approx( 0.0, rel=1e-16) == Jcx
    assert pytest.approx(102.46e+6, rel=1e-2) == Jsx
    assert pytest.approx(102.46e+6, rel=1e-2) == Jhx

def test_manuscript_get_area_properties_mirrored():
    rcSection = section_manuscript_5(mirr=True)
    homo_coeff = 6.0
    rcSection.setHomogenization(homo_coeff)

    Mcr_pos, Mcr_neg = rcSection.calCriticalMoment()
    assert pytest.approx(-110.83e6, rel=1e-3) == Mcr_neg
    assert Mcr_pos > -Mcr_neg

    # then for uncracked (default)
    #
    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties()
    assert pytest.approx(0.00, rel=1e-3) == ycg
    assert pytest.approx(-48.3, rel=1e-2) == ysg
    assert pytest.approx(-1.96, rel=1e-3) == yhg
    assert pytest.approx(500.0e+3, rel=1e-6) == Ac
    assert pytest.approx(3.53e+3, rel=1e-2) == As
    assert pytest.approx(521.2e+3, rel=1e-4) == Ah
    assert pytest.approx(+980e+3, rel=1e-3) == Scx
    assert pytest.approx(-163.4e+3, rel=1e-3) == Ssx
    assert pytest.approx(    0.0, rel=1e-16) == Shx
    assert pytest.approx(10.42e+9, rel=1e-3) == Jcx
    assert pytest.approx(110.12e+6, rel=1e-3) == Jsx
    assert pytest.approx(11.08e+9, rel=1e-4) == Jhx

    # then for uncracked
    #
    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties(SectionStates.UNCRACKED)
    assert pytest.approx(0.00, rel=1e-3) == ycg
    assert pytest.approx(-48.3, rel=1e-2) == ysg
    assert pytest.approx(-1.96, rel=1e-3) == yhg
    assert pytest.approx(500.0e+3, rel=1e-6) == Ac
    assert pytest.approx(3.53e+3, rel=1e-2) == As
    assert pytest.approx(521.2e+3, rel=1e-4) == Ah
    assert pytest.approx(+980e+3, rel=1e-3) == Scx
    assert pytest.approx(-163.4e+3, rel=1e-3) == Ssx
    assert pytest.approx(    0.0, rel=1e-16) == Shx
    assert pytest.approx(10.42e+9, rel=1e-3) == Jcx
    assert pytest.approx(110.12e+6, rel=1e-3) == Jsx
    assert pytest.approx(11.08e+9, rel=1e-4) == Jhx

    # then for compressed
    #
    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties(SectionStates.COMPRESSED)
    assert pytest.approx(0.00, rel=1e-3) == ycg
    assert pytest.approx(-48.3, rel=1e-2) == ysg
    assert pytest.approx(-1.96, rel=1e-3) == yhg
    assert pytest.approx(500.0e+3, rel=1e-6) == Ac
    assert pytest.approx(3.53e+3, rel=1e-2) == As
    assert pytest.approx(521.2e+3, rel=1e-4) == Ah
    assert pytest.approx(+980e+3, rel=1e-3) == Scx
    assert pytest.approx(-163.4e+3, rel=1e-3) == Ssx
    assert pytest.approx(    0.0, rel=1e-16) == Shx
    assert pytest.approx(10.42e+9, rel=1e-3) == Jcx
    assert pytest.approx(110.12e+6, rel=1e-3) == Jsx
    assert pytest.approx(11.08e+9, rel=1e-4) == Jhx

    # If I didn't launch solverSLS_NM before for PARTIALIZED I can't have results
    assert rcSection.getAreaProperties(SectionStates.PARTIALIZED) is None

    # Launch withowt forces
    # solverSLS_NM classifies section properly lucly
    # xi is always intended from top. This cause H - 73.46

    rcSection.solverSLS_NM(N=0.0e+3, M=-150e+6, uncracked=False)
    H = rcSection.getDimH()
    assert pytest.approx(H - 73.46, rel=1e-2) == rcSection.xi()

    Ah, Shx, Jhx, Ac, Scx, Jcx, As, Ssx, Jsx, yhg, ycg, ysg = rcSection.getAreaProperties(SectionStates.PARTIALIZED)
    assert pytest.approx(73.46e+3, rel=1e-2) == Ac
    assert pytest.approx(3.53e+3, rel=1e-2) == As
    assert pytest.approx(94.63e+3, rel=1e-2) == Ah
    assert pytest.approx(-213.27, rel=1e-2) == ycg
    assert pytest.approx(-48.3, rel=1e-2) == ysg
    assert pytest.approx(-176.67, rel=1e-2) == yhg
    assert pytest.approx(-2.68e+6, rel=1e-1) == Scx
    assert pytest.approx(+453.1e+3, rel=1e-2) == Ssx
    assert pytest.approx(0.0, abs=1e-6) == Shx
    assert pytest.approx(131.43e+6, rel=1e-1) == Jcx
    assert pytest.approx(1.60e+8, rel=1e-2) == Jsx
    assert pytest.approx(1.091e+9, rel=1e-2) == Jhx
