# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import pytest
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.loads import ForcesOnSection
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.modeler import Point2d, SectionModeler
from pycivil.EXAStructural.plot import SectionPlot
from pycivil.EXAStructural.sections import SectionStates
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2


# --------------------
# BY-HAND TEST CASE #3
# --------------------
def test_symmetrical_uncracked_NM_001(tmp_path: Path):
    # --------------------------------------------------------------------------
    #                1. BUILD SECTION RECTANGULAR TEMPLATE
    # --------------------------------------------------------------------------
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
    rcSection.addSteelArea("LINE-MT", dist=50, d=20, nb=4, sd=40)
    rcSection.addSteelArea("LINE-MB", dist=50, d=20, nb=4, sd=40)

    # --------------------------------------------------------------------------
    #                2. BUILD GENERAL SECTION FROM TEMPLATE
    # --------------------------------------------------------------------------
    md = SectionModeler()
    md.addSection(1)
    md.importFromRCSection(rcSection)
    sp = SectionPlot()
    sp.modeler = md
    # sp.plot()
    # sp.show()

    # Geometrical properties
    md.nCoeff = 15
    assert pytest.approx(md.calcSolidArea()) == 180000
    assert pytest.approx(md.calcPointArea(), rel=1e-3) == 2513
    assert pytest.approx(md.calcIdealArea(), rel=1e-3) == 217699
    assert pytest.approx(md.calcIdealAreaProperties().ixx, rel=1e-3) == 7.755e09
    assert pytest.approx([md.calcSolidBarycenter().x, md.calcSolidBarycenter().y]) == [
        0.0,
        0.0,
    ]
    assert pytest.approx([md.calcPointBarycenter().x, md.calcPointBarycenter().y]) == [
        0.0,
        0.0,
    ]
    assert pytest.approx([md.calcIdealBarycenter().x, md.calcIdealBarycenter().y]) == [
        0.0,
        0.0,
    ]

    # Setting units
    KN = 1000
    KNm = 1000 * 1000
    force = ForcesOnSection()
    assert md.elSolve(force, uncracked=True)
    assert md.elExtremeStressConcrete()[0] == 0.0
    assert md.elExtremeStressSteel()[0] == 0.0

    for i in range(md.circlesSize()):
        assert md.elStressSteelNodeAt(i) == 0.0

    for i in range(md.triangleNodesSize()):
        assert md.elStressConcreteNodeAt(i) == 0.0

    force.Fz = 1000 * KN
    assert md.elSolve(force, uncracked=True)
    assert pytest.approx(md.elExtremeStressConcrete()[1], rel=1e-3) == 4.593
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-3) == 68.895
    for i in range(md.triangleNodesSize()):
        assert pytest.approx(md.elStressConcreteNodeAt(i), rel=1e-3) == 4.593
    for i in range(md.circlesSize()):
        assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == 68.895

    force.Fz = -1000 * KN
    assert md.elSolve(force, uncracked=True)
    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-3) == -4.593
    assert pytest.approx(md.elExtremeStressSteel()[0], rel=1e-3) == -68.895
    for i in range(md.triangleNodesSize()):
        assert pytest.approx(md.elStressConcreteNodeAt(i), rel=1e-3) == -4.593
    for i in range(md.circlesSize()):
        assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == -68.895

    force.Fz = 0.0 * KN
    force.Mx = 0.0 * KNm
    # y-axis from right to left
    force.My = 150.0 * KNm

    assert md.elSolve(force, uncracked=True)
    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-3) == -5.803
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-3) == 72.53

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == +5.803
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == +5.803
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-3) == -5.803
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-3) == -5.803

    # If node doesn't exists return 0.0 with message
    assert pytest.approx(md.elStressConcreteNodeId(5), rel=1e-3) == 0.0

    assert pytest.approx(md.elStressSteelCircleId(1), rel=1e-3) == -72.53
    assert pytest.approx(md.elStressSteelCircleId(2), rel=1e-3) == -72.53
    assert pytest.approx(md.elStressSteelCircleId(3), rel=1e-3) == -72.53
    assert pytest.approx(md.elStressSteelCircleId(4), rel=1e-3) == -72.53

    assert pytest.approx(md.elStressSteelCircleId(5), rel=1e-3) == 72.53
    assert pytest.approx(md.elStressSteelCircleId(6), rel=1e-3) == 72.53
    assert pytest.approx(md.elStressSteelCircleId(7), rel=1e-3) == 72.53
    assert pytest.approx(md.elStressSteelCircleId(8), rel=1e-3) == 72.53

    # If circle doesn't exists return 0.0 with message
    assert pytest.approx(md.elStressSteelCircleId(9), rel=1e-3) == 0.0

    md.rotate(90, Point2d(0.0, 0.0))
    # sp.plot()
    # sp.show()

    force.Fz = 0.0 * KN
    # y-axis from right to left
    # x-axis from bottom to top
    # z-axis counterclockwise (CCW) or anticlockwise (ACW)
    force.Mx = -150.0 * KNm
    force.My = 0.0 * KNm
    assert md.elSolve(force, uncracked=True)

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-3) == -5.803
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-3) == 72.53

    assert pytest.approx(md.elStressSteelCircleId(1), rel=1e-3) == -72.53
    assert pytest.approx(md.elStressSteelCircleId(2), rel=1e-3) == -72.53
    assert pytest.approx(md.elStressSteelCircleId(3), rel=1e-3) == -72.53
    assert pytest.approx(md.elStressSteelCircleId(4), rel=1e-3) == -72.53

    assert pytest.approx(md.elStressSteelCircleId(5), rel=1e-3) == 72.53
    assert pytest.approx(md.elStressSteelCircleId(6), rel=1e-3) == 72.53
    assert pytest.approx(md.elStressSteelCircleId(7), rel=1e-3) == 72.53
    assert pytest.approx(md.elStressSteelCircleId(8), rel=1e-3) == 72.53

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == +5.803
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == +5.803
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-3) == -5.803
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-3) == -5.803

    md.rotate(-90, Point2d(0.0, 0.0))
    # sp.plot()
    # sp.show()

    force.Fz = -1000.0 * KN
    force.Mx = 0.0 * KNm
    force.My = +150.0 * KNm
    assert md.elSolve(force, uncracked=True)

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-3) == -10.396
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-2) == +3.635

    assert pytest.approx(md.elStressSteelCircleId(1), rel=1e-3) == -141.425
    assert pytest.approx(md.elStressSteelCircleId(2), rel=1e-3) == -141.425
    assert pytest.approx(md.elStressSteelCircleId(3), rel=1e-3) == -141.425
    assert pytest.approx(md.elStressSteelCircleId(4), rel=1e-3) == -141.425

    assert pytest.approx(md.elStressSteelCircleId(5), rel=1e-2) == +3.635
    assert pytest.approx(md.elStressSteelCircleId(6), rel=1e-2) == +3.635
    assert pytest.approx(md.elStressSteelCircleId(7), rel=1e-2) == +3.635
    assert pytest.approx(md.elStressSteelCircleId(8), rel=1e-2) == +3.635

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-2) == +1.210
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-2) == +1.210
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-3) == -10.396
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-3) == -10.396

    force.Fz = -1000.0 * KN
    force.Mx = 0.0 * KNm
    force.My = -150.0 * KNm
    assert md.elSolve(force, uncracked=True)

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-3) == -10.396
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-2) == +3.635

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == -10.396
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == -10.396
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-2) == +1.210
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-2) == +1.210

    assert pytest.approx(md.elStressSteelCircleId(5), rel=1e-3) == -141.425
    assert pytest.approx(md.elStressSteelCircleId(6), rel=1e-3) == -141.425
    assert pytest.approx(md.elStressSteelCircleId(7), rel=1e-3) == -141.425
    assert pytest.approx(md.elStressSteelCircleId(8), rel=1e-3) == -141.425

    assert pytest.approx(md.elStressSteelCircleId(1), rel=1e-2) == +3.635
    assert pytest.approx(md.elStressSteelCircleId(2), rel=1e-2) == +3.635
    assert pytest.approx(md.elStressSteelCircleId(3), rel=1e-2) == +3.635
    assert pytest.approx(md.elStressSteelCircleId(4), rel=1e-2) == +3.635

    force.Fz = +1000.0 * KN
    force.Mx = 0.0 * KNm
    force.My = +150.0 * KNm
    assert md.elSolve(force, uncracked=True)

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-2) == -1.210
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-2) == +141.425

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == 10.396
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == 10.396
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-2) == -1.210
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-2) == -1.210

    assert pytest.approx(md.elStressSteelCircleId(5), rel=1e-3) == +141.425
    assert pytest.approx(md.elStressSteelCircleId(6), rel=1e-3) == +141.425
    assert pytest.approx(md.elStressSteelCircleId(7), rel=1e-3) == +141.425
    assert pytest.approx(md.elStressSteelCircleId(8), rel=1e-3) == +141.425

    assert pytest.approx(md.elStressSteelCircleId(1), rel=1e-2) == -3.635
    assert pytest.approx(md.elStressSteelCircleId(2), rel=1e-2) == -3.635
    assert pytest.approx(md.elStressSteelCircleId(3), rel=1e-2) == -3.635
    assert pytest.approx(md.elStressSteelCircleId(4), rel=1e-2) == -3.635

    force.Fz = +1000.0 * KN
    force.Mx = 0.0 * KNm
    force.My = -150.0 * KNm
    assert md.elSolve(force, uncracked=True)

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-2) == -1.210
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-2) == +141.425

    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-3) == 10.396
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-3) == 10.396
    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-2) == -1.210
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-2) == -1.210

    assert pytest.approx(md.elStressSteelCircleId(1), rel=1e-3) == +141.425
    assert pytest.approx(md.elStressSteelCircleId(2), rel=1e-3) == +141.425
    assert pytest.approx(md.elStressSteelCircleId(3), rel=1e-3) == +141.425
    assert pytest.approx(md.elStressSteelCircleId(4), rel=1e-3) == +141.425

    assert pytest.approx(md.elStressSteelCircleId(5), rel=1e-2) == -3.635
    assert pytest.approx(md.elStressSteelCircleId(6), rel=1e-2) == -3.635
    assert pytest.approx(md.elStressSteelCircleId(7), rel=1e-2) == -3.635
    assert pytest.approx(md.elStressSteelCircleId(8), rel=1e-2) == -3.635


# ----------------------
# BY-HAND TEST CASE #2.2
# ----------------------
def test_uncracked_NM_002(tmp_path: Path):
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
    rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)

    # --------------------------------------------------------------------------
    #                   BUILD GENERAL SECTION FROM TEMPLATE
    # --------------------------------------------------------------------------
    md = SectionModeler()
    md.addSection(1)
    md.importFromRCSection(rcSection)
    sp = SectionPlot()
    sp.modeler = md
    # sp.plot()
    # sp.show()

    # Geometrical properties
    md.nCoeff = 15
    assert pytest.approx(md.calcSolidArea()) == 960.00e03
    assert pytest.approx(md.calcPointArea(), rel=1e-3) == 18.09e03
    assert pytest.approx(md.calcIdealArea(), rel=1e-3) == 1.23135e06
    assert pytest.approx(md.calcIdealAreaProperties().ixx, rel=2e-2) == 176.24e09
    assert pytest.approx([md.calcSolidBarycenter().x, md.calcSolidBarycenter().y]) == [
        0.0,
        0.0,
    ]
    assert pytest.approx(
        [md.calcPointBarycenter().x, md.calcPointBarycenter().y], rel=1e-2, abs=1e-3
    ) == [0.0, -220.89]
    assert pytest.approx(
        [md.calcIdealBarycenter().x, md.calcIdealBarycenter().y], rel=1e-2, abs=1
    ) == [0.0, -49.39]

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    force = ForcesOnSection()
    force.Fz = 0.0 * KN
    force.Mx = 0.0 * KNm
    force.My = 2400.0 * KNm
    force.switchToNamedRef("ELASTIC")
    assert md.elSolve(force, uncracked=True)

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-2) == -8.84
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-2) == +96.97

    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-3) == -8.840
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-3) == -8.840
    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == +7.4988
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == +7.4988

    for i in range(md.circlesSize()):
        if i in range(0, 9):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == -117.11
        if i in range(10, 19):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-2) == +74.91
        if i in range(20, 29):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == +85.94
        if i in range(30, 39):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == +96.97


# ----------------------
# BY-HAND TEST CASE #2.2
# ----------------------
def test_uncracked_NM_003(tmp_path: Path):
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
    rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=130, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=184, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)

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

    # --------------------------------------------------------------------------
    #                   BUILD GENERAL SECTION FROM TEMPLATE
    # --------------------------------------------------------------------------
    md = SectionModeler()
    md.addSection(1)
    md.importFromRCSection(rcSection)
    sp = SectionPlot()
    sp.modeler = md
    # sp.plot()
    # sp.show()

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    force = ForcesOnSection()
    force.Fz = 0.0 * KN
    force.Mx = 0.0 * KNm
    force.My = -2400.0 * KNm

    assert md.elSolve(force, uncracked=True)

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-2) == -8.84
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-2) == +96.97

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == -8.840
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == -8.840
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-3) == +7.4988
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-3) == +7.4988

    for i in range(md.circlesSize()):
        if i in range(0, 9):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == +96.97
        if i in range(10, 19):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == +85.94
        if i in range(20, 29):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-2) == +74.91
        if i in range(30, 39):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == -117.11


# ----------------------
# BY-HAND TEST CASE #2.5
# ----------------------
def test_cracked_stretched_NM_004(tmp_path: Path):
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
    rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    # --------------------------------------------------------------------------
    #                   BUILD GENERAL SECTION FROM TEMPLATE
    # --------------------------------------------------------------------------
    md = SectionModeler()
    md.addSection(1)
    md.importFromRCSection(rcSection)
    sp = SectionPlot()
    sp.modeler = md
    # sp.plot()
    # sp.show()

    force = ForcesOnSection()
    force.Fz = +3619.0 * KN
    force.Mx = 0.0 * KNm
    force.My = 0.0 * KNm

    md.setLogLevel(1)
    assert md.elSolve(force, uncracked=False)
    assert md.elIsCalculated()
    assert md.elSectionState() == SectionStates.STRETCHED
    assert not md.elCalOptionUncracked()

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-2) == 0.0
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-2) == +376.27

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == 0.0
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == 0.0
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-3) == 0.0
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-3) == 0.0

    for i in range(md.circlesSize()):
        if i in range(0, 9):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-2) == 376.27
        if i in range(10, 19):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == 153.86
        if i in range(20, 29):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == 141.05
        if i in range(30, 39):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == 128.27


# ----------------------
# BY-HAND TEST CASE #2.6
# ----------------------
def test_cracked_compressed_NM_005(tmp_path: Path):
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
    rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)

    # --------------------------------------------------------------------------
    #                   BUILD GENERAL SECTION FROM TEMPLATE
    # --------------------------------------------------------------------------
    md = SectionModeler()
    md.addSection(1)
    md.importFromRCSection(rcSection)
    sp = SectionPlot()
    sp.modeler = md
    # sp.plot()
    # sp.show()

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    force = ForcesOnSection()
    force.Fz = -3619.0 * KN
    force.Mx = 0.0 * KNm
    force.My = 0.0 * KNm

    assert md.elSolve(force, uncracked=False)
    assert md.elIsCalculated()
    assert md.elSectionState() == SectionStates.COMPRESSED
    assert not md.elCalOptionUncracked()

    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-2) == -3.599
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-3) == -36.92

    assert pytest.approx(md.elStressConcreteNodeId(1), rel=1e-3) == -2.385
    assert pytest.approx(md.elStressConcreteNodeId(2), rel=1e-3) == -2.385
    assert pytest.approx(md.elStressConcreteNodeId(3), rel=1e-2) == -3.599
    assert pytest.approx(md.elStressConcreteNodeId(4), rel=1e-2) == -3.599

    for i in range(md.circlesSize()):
        if i in range(0, 9):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-2) == -52.84
        if i in range(10, 19):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == -38.56
        if i in range(20, 29):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == -37.74
        if i in range(30, 39):
            assert pytest.approx(md.elStressSteelNodeAt(i), rel=1e-3) == -36.92


# ----------------------
# BY-HAND TEST CASE #2.1
# ----------------------
def test_cracked_bending_NM_006(tmp_path: Path):
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
    rcSection.addSteelArea("LINE-MT", dist=76, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1016, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1070, d=24, nb=10, sd=49)
    rcSection.addSteelArea("LINE-MT", dist=1124, d=24, nb=10, sd=49)

    # --------------------------------------------------------------------------
    #                   BUILD GENERAL SECTION FROM TEMPLATE
    # --------------------------------------------------------------------------
    md = SectionModeler()
    md.addSection(1)
    md.importFromRCSection(rcSection)
    sp = SectionPlot()
    sp.modeler = md
    # sp.plot()
    # sp.show()

    # Setting units
    KN = 1000
    KNm = 1000 * 1000

    force = ForcesOnSection()
    force.Fz = 0.0 * KN
    force.Mx = 0.0 * KNm
    force.My = +2400.0 * KNm

    md.setLogLevel(1)
    assert md.elSolve(force, uncracked=False)
    assert md.elIsCalculated()
    assert md.elSectionState() == SectionStates.PARTIALIZED
    assert not md.elCalOptionUncracked()
    #
    assert pytest.approx(md.elExtremeStressConcrete()[0], rel=1e-2) == -10.31
    assert pytest.approx(md.elExtremeStressSteel()[1], rel=1e-3) == +207.10
