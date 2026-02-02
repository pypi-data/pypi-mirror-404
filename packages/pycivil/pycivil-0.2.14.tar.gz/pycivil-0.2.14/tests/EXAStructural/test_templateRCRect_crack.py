# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import pytest
from pycivil.EXAStructural.lawcodes.codeNTC2018 import crackMeasure
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.materials import Concrete, ConcreteSteel
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2, SectionCrackedStates


# ----------------------
# BY-HAND TEST CASE #2.7
# ----------------------
def test_no_symmetric_M_unknown_001(tmp_path: Path) -> None:
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
    Ned = 0 * KN
    Med = 2400.0 / 3 * KNm
    assert rcSection.crackState() == SectionCrackedStates.UNKNOWN

    rcSection.solverCrack(Ned, Med)
    assert rcSection.crackState() != SectionCrackedStates.UNKNOWN


# ----------------------
# BY-HAND TEST CASE #2.7
# ----------------------
def test_no_symmetric_M_decompressed_002(tmp_path: Path) -> None:
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
    Ned = 0 * KN
    Med = 2400.0 / 3 * KNm
    sigmac, sigmas, xi = rcSection.solverSLS_NM(Ned, Med, uncracked=True)
    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [
        -8.84 / 3,
        +96.97 / 3,
        649.39,
    ]

    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == +7.4988 / 3
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-3) == -8.840 / 3

    for idx, i in enumerate(rcSection.getSteelStress()):
        stressExpected: float = 0
        if idx in lineRebars01:
            stressExpected = -117.11 / 3
        if idx in lineRebars02:
            stressExpected = +74.91 / 3
        if idx in lineRebars03:
            stressExpected = +85.94 / 3
        if idx in lineRebars04:
            stressExpected = +96.97 / 3
        assert pytest.approx(i, rel=1e-2) == stressExpected

    assert pytest.approx(rcSection.getConcreteMaterial().get_fctm(), rel=1e-2) == 3.02
    assert (
        pytest.approx(rcSection.getConcreteMaterial().get_fct_crack(), rel=1e-2) == 2.51
    )

    rcSection.solverCrack(Ned, Med)
    assert rcSection.crackState() == SectionCrackedStates.DECOMPRESSED


# ----------------------
# BY-HAND TEST CASE #2.3
# ----------------------
def test_no_symmetric_M_cracked_bot_003(tmp_path: Path) -> None:
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
    Ned = 0 * KN
    Med = 2400.0 * KNm

    sigmac, sigmas, xi = rcSection.solverSLS_NM(Ned, Med, uncracked=False)

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

    assert pytest.approx(rcSection.getConcreteMaterial().get_fctm(), rel=1e-2) == 3.02
    assert (
        pytest.approx(rcSection.getConcreteMaterial().get_fct_crack(), rel=1e-2) == 2.51
    )
    rcSection.solverCrack(Ned, Med)
    assert rcSection.crackState() == SectionCrackedStates.CRACKED_BOT
    print("Crack parameters for BOT")
    print(rcSection.crackParam()[0])
    print("Crack parameters for TOP")
    print(rcSection.crackParam()[1])
    assert pytest.approx(rcSection.crackParam()[0].epsi, rel=1e-2) == +1.10869e-3
    assert pytest.approx(rcSection.crackParam()[0].coverInMaxSteel, rel=1e-2) == +64
    assert pytest.approx(rcSection.crackParam()[0].rebarDistance, rel=1e-2) == +25
    assert pytest.approx(rcSection.crackParam()[0].deq, rel=1e-2) == +24

    assert pytest.approx(rcSection.crackParam()[0].dgs, rel=1e-2) == +1070
    assert pytest.approx(rcSection.crackParam()[0].hcEff, rel=1e-2) == +239.73
    assert pytest.approx(rcSection.crackParam()[0].steelArea, rel=1e-2) == +13.572e3
    assert pytest.approx(rcSection.crackParam()[0].sigmasMax, rel=1e-2) == +207.2

    assert pytest.approx(rcSection.crackParam()[1].epsi, rel=1e-2) == -736.429e-6
    assert rcSection.crackParam()[1].coverInMaxSteel is None
    assert rcSection.crackParam()[1].rebarDistance is None
    assert rcSection.crackParam()[1].deq is None

    assert rcSection.crackParam()[1].dgs is None
    assert rcSection.crackParam()[1].hcEff is None
    assert rcSection.crackParam()[1].steelArea is None
    assert rcSection.crackParam()[1].sigmasMax is None

    xi_val = rcSection.xi()
    assert xi_val is not None
    crackOut = crackMeasure(
        epsiBot=rcSection.crackParam()[0].epsi,
        epsiTop=rcSection.crackParam()[1].epsi,
        deq=rcSection.crackParam()[0].deq,
        As=rcSection.crackParam()[0].steelArea,
        rebarsCover=rcSection.crackParam()[0].coverInMaxSteel,
        rebarsDistance=rcSection.crackParam()[0].rebarDistance,
        hcEff=rcSection.crackParam()[0].hcEff,
        beff=rcSection.getDimW(),
        hsec=rcSection.getDimH(),
        xi=xi_val,
        fck=rcSection.getConcreteMaterial().get_fck(),
        sigmas=rcSection.crackParam()[0].sigmasMax,
        Es=rcSection.getSteelMaterial().get_Es(),
        load="long",
    )

    print(crackOut.toDict())
    assert pytest.approx(crackOut.roeff, rel=1e-4) == +70.767e-3
    assert pytest.approx(crackOut.epsism, rel=1e-3) == +869.162e-6
    assert pytest.approx(crackOut.sigmas_stiffning, rel=1e-2) == +24.678
    sigmasMax = rcSection.crackParam()[0].sigmasMax
    assert crackOut.sigmas_stiffning <= 0.4 * sigmasMax
    assert pytest.approx(crackOut.deltasm, rel=1e-3) == +161.911
    assert pytest.approx(crackOut.deltasm1, rel=1e-4) == +161.911
    assert pytest.approx(crackOut.deltasm2, rel=1e-3) == +539.62
    assert crackOut.deltasm == crackOut.deltasm1
    assert pytest.approx(crackOut.zoneC, rel=1e-4) == +380.00
    assert pytest.approx(crackOut.wk, rel=1e-2) == +0.23923
    assert pytest.approx(crackOut.k2, rel=1e-10) == +0.5
    assert pytest.approx(crackOut.alpham, rel=1e-4) == +6.298


# ----------------------
# BY-HAND TEST CASE #2.3
# ----------------------
# As for test_no_symmetric_M_cracked_bot_003 mirroring section and forces
# produces cracked for top.
def test_no_symmetric_M_cracked_top_004(tmp_path: Path) -> None:
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
    lineRebars01 = rcSection.addSteelArea("LINE-MT", dist=1200 - 76, d=24, nb=10, sd=49)
    lineRebars02 = rcSection.addSteelArea(
        "LINE-MT", dist=1200 - 1016, d=24, nb=10, sd=49
    )
    lineRebars03 = rcSection.addSteelArea(
        "LINE-MT", dist=1200 - 1070, d=24, nb=10, sd=49
    )
    lineRebars04 = rcSection.addSteelArea(
        "LINE-MT", dist=1200 - 1124, d=24, nb=10, sd=49
    )
    assert isinstance(lineRebars01, list)
    assert isinstance(lineRebars02, list)
    assert isinstance(lineRebars03, list)
    assert isinstance(lineRebars04, list)
    # Setting units
    KN = 1000
    KNm = 1000 * 1000
    Ned = 0.0 * KN
    Med = -2400.0 * KNm

    sigmac, sigmas, xi = rcSection.solverSLS_NM(Ned, Med, uncracked=False)

    assert pytest.approx([sigmac, sigmas, xi], rel=1e-2) == [
        -10.31,
        +207.10,
        1200 - 480.51,
    ]
    for idx, i in enumerate(rcSection.getConcrStress()):
        if idx < 2:
            # BL and BR
            assert pytest.approx(i, rel=1e-3) == -10.31
        else:
            # TL and TR
            assert pytest.approx(i, rel=1e-3) == 0.0

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

    assert pytest.approx(rcSection.getConcreteMaterial().get_fctm(), rel=1e-2) == 3.02
    assert (
        pytest.approx(rcSection.getConcreteMaterial().get_fct_crack(), rel=1e-2) == 2.51
    )
    rcSection.solverCrack(Ned, Med)
    assert rcSection.crackState() == SectionCrackedStates.CRACKED_TOP
    print("Crack parameters for BOT")
    print(rcSection.crackParam()[0])
    print("Crack parameters for TOP")
    print(rcSection.crackParam()[1])

    assert pytest.approx(rcSection.crackParam()[1].epsi, rel=1e-2) == +1.10869e-3
    assert pytest.approx(rcSection.crackParam()[1].coverInMaxSteel, rel=1e-2) == +64
    assert pytest.approx(rcSection.crackParam()[1].rebarDistance, rel=1e-2) == +25
    assert pytest.approx(rcSection.crackParam()[1].deq, rel=1e-2) == +24

    assert pytest.approx(rcSection.crackParam()[1].dgs, rel=1e-2) == +1070
    assert pytest.approx(rcSection.crackParam()[1].hcEff, rel=1e-2) == +239.73
    assert pytest.approx(rcSection.crackParam()[1].steelArea, rel=1e-2) == +13.572e3
    assert pytest.approx(rcSection.crackParam()[1].sigmasMax, rel=1e-2) == +207.2

    assert pytest.approx(rcSection.crackParam()[0].epsi, rel=1e-2) == -736.429e-6
    assert rcSection.crackParam()[0].coverInMaxSteel is None
    assert rcSection.crackParam()[0].rebarDistance is None
    assert rcSection.crackParam()[0].deq is None

    assert rcSection.crackParam()[0].dgs is None
    assert rcSection.crackParam()[0].hcEff is None
    assert rcSection.crackParam()[0].steelArea is None
    assert rcSection.crackParam()[0].sigmasMax is None

    xi_val = rcSection.xi()
    assert xi_val is not None
    crackOut = crackMeasure(
        epsiBot=rcSection.crackParam()[0].epsi,
        epsiTop=rcSection.crackParam()[1].epsi,
        deq=rcSection.crackParam()[1].deq,
        As=rcSection.crackParam()[1].steelArea,
        rebarsCover=rcSection.crackParam()[1].coverInMaxSteel,
        rebarsDistance=rcSection.crackParam()[1].rebarDistance,
        hcEff=rcSection.crackParam()[1].hcEff,
        beff=rcSection.getDimW(),
        hsec=rcSection.getDimH(),
        xi=xi_val,
        fck=rcSection.getConcreteMaterial().get_fck(),
        sigmas=rcSection.crackParam()[1].sigmasMax,
        Es=rcSection.getSteelMaterial().get_Es(),
        load="long",
    )

    print(crackOut.toDict())
    assert pytest.approx(crackOut.roeff, rel=1e-4) == +70.767e-3
    assert pytest.approx(crackOut.epsism, rel=1e-3) == +869.162e-6
    assert pytest.approx(crackOut.sigmas_stiffning, rel=1e-2) == +24.678
    sigmasMax = rcSection.crackParam()[1].sigmasMax
    assert crackOut.sigmas_stiffning <= 0.4 * sigmasMax
    assert pytest.approx(crackOut.deltasm, rel=1e-3) == +161.911
    assert pytest.approx(crackOut.deltasm1, rel=1e-4) == +161.911
    assert pytest.approx(crackOut.deltasm2, rel=1e-3) == +539.62
    assert crackOut.deltasm == crackOut.deltasm1
    assert pytest.approx(crackOut.zoneC, rel=1e-4) == +380.00
    assert pytest.approx(crackOut.wk, rel=1e-2) == +0.23923
    assert pytest.approx(crackOut.k2, rel=1e-10) == +0.5
    assert pytest.approx(crackOut.alpham, rel=1e-4) == +6.298


# ----------------------
# BY-HAND TEST CASE #2.9
# ----------------------
def test_no_symmetric_N_cracked_005(tmp_path: Path) -> None:
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
    Ned = +3619 * KN
    Med = 0.0 * KNm
    sigmac, sigmas, xi = rcSection.solverSLS_NM(Ned, Med, uncracked=False)
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

    rcSection.solverCrack(Ned, Med)
    assert rcSection.crackState() == SectionCrackedStates.CRACKED

    print("Crack parameters for TOP AND BOTTOM")
    print("-------------- BOT ----------------")
    print(rcSection.crackParam()[0])
    print("-------------- TOP ----------------")
    print(rcSection.crackParam()[1])

    assert pytest.approx(rcSection.crackParam()[0].epsi, rel=1e-2) == +525.118e-6
    assert pytest.approx(rcSection.crackParam()[0].coverInMaxSteel, rel=1e-2) == +64
    assert pytest.approx(rcSection.crackParam()[0].rebarDistance, rel=1e-2) == +25
    assert pytest.approx(rcSection.crackParam()[0].deq, rel=1e-2) == +24

    assert pytest.approx(rcSection.crackParam()[0].dgs, rel=1e-2) == +1070
    assert pytest.approx(rcSection.crackParam()[0].hcEff, rel=1e-2) == +325.0
    assert pytest.approx(rcSection.crackParam()[0].steelArea, rel=1e-2) == +13572
    assert pytest.approx(rcSection.crackParam()[0].sigmasMax, rel=1e-2) == +153.86

    assert pytest.approx(rcSection.crackParam()[1].epsi, rel=1e-2) == +1.877e-3
    assert pytest.approx(rcSection.crackParam()[1].coverInMaxSteel, rel=1e-2) == +64
    assert pytest.approx(rcSection.crackParam()[1].rebarDistance, rel=1e-2) == +25
    assert pytest.approx(rcSection.crackParam()[1].deq, rel=1e-2) == +24

    assert pytest.approx(rcSection.crackParam()[1].dgs, rel=1e-2) == +1124
    assert pytest.approx(rcSection.crackParam()[1].hcEff, rel=1e-2) == +190.0
    assert pytest.approx(rcSection.crackParam()[1].steelArea, rel=1e-2) == +4523.893
    assert pytest.approx(rcSection.crackParam()[1].sigmasMax, rel=1e-2) == +376.27

    xi_val = rcSection.xi()
    assert xi_val is not None
    crackOutTop = crackMeasure(
        epsiBot=rcSection.crackParam()[0].epsi,
        epsiTop=rcSection.crackParam()[1].epsi,
        deq=rcSection.crackParam()[1].deq,
        As=rcSection.crackParam()[1].steelArea,
        rebarsCover=rcSection.crackParam()[1].coverInMaxSteel,
        rebarsDistance=rcSection.crackParam()[1].rebarDistance,
        hcEff=rcSection.crackParam()[1].hcEff,
        beff=rcSection.getDimW(),
        hsec=rcSection.getDimH(),
        xi=xi_val,
        fck=rcSection.getConcreteMaterial().get_fck(),
        sigmas=rcSection.crackParam()[1].sigmasMax,
        Es=rcSection.getSteelMaterial().get_Es(),
        load="long",
    )

    print(crackOutTop.toDict())
    assert pytest.approx(crackOutTop.roeff, rel=1e-3) == +29.757e-3
    assert pytest.approx(crackOutTop.epsism, rel=1e-2) == +1.562e-3
    assert pytest.approx(crackOutTop.sigmas_stiffning, rel=1e-2) == +48.203
    assert pytest.approx(crackOutTop.deltasm, rel=1e-2) == +231.22
    assert pytest.approx(crackOutTop.deltasm1, rel=1e-2) == +231.22
    assert pytest.approx(crackOutTop.deltasm2, rel=1e-3) == +1249.5
    assert crackOutTop.deltasm == crackOutTop.deltasm1
    assert pytest.approx(crackOutTop.zoneC, rel=1e-4) == +380.00
    assert pytest.approx(crackOutTop.wk, rel=1e-2) == +0.61398
    assert pytest.approx(crackOutTop.k2, rel=1e-3) == +0.6399
    assert pytest.approx(crackOutTop.alpham, rel=1e-4) == +6.298

    crackOutBot = crackMeasure(
        epsiBot=rcSection.crackParam()[0].epsi,
        epsiTop=rcSection.crackParam()[1].epsi,
        deq=rcSection.crackParam()[0].deq,
        As=rcSection.crackParam()[0].steelArea,
        rebarsCover=rcSection.crackParam()[0].coverInMaxSteel,
        rebarsDistance=rcSection.crackParam()[0].rebarDistance,
        hcEff=rcSection.crackParam()[0].hcEff,
        beff=rcSection.getDimW(),
        hsec=rcSection.getDimH(),
        xi=xi_val,
        fck=rcSection.getConcreteMaterial().get_fck(),
        sigmas=rcSection.crackParam()[0].sigmasMax,
        Es=rcSection.getSteelMaterial().get_Es(),
        load="long",
    )

    print(crackOutBot.toDict())
    assert pytest.approx(crackOutBot.roeff, rel=1e-4) == +52.2e-3
    assert pytest.approx(crackOutBot.sigmas_stiffning, rel=1e-2) == +30.75
    assert pytest.approx(crackOutBot.epsism, rel=1e-3) == +586.238e-6
    assert pytest.approx(crackOutBot.deltasm, rel=1e-3) == +186.84
    assert pytest.approx(crackOutBot.deltasm1, rel=1e-3) == +186.84
    assert pytest.approx(crackOutBot.deltasm2, rel=1e-3) == +1249.5
    assert crackOutTop.deltasm == crackOutTop.deltasm1
    assert pytest.approx(crackOutTop.zoneC, rel=1e-4) == +380.00
    assert pytest.approx(crackOutBot.wk, rel=1e-2) == +0.186205
    assert pytest.approx(crackOutBot.k2, rel=1e-3) == +0.6399
    assert pytest.approx(crackOutBot.alpham, rel=1e-4) == +6.298


# ----------------------
# BY-HAND TEST CASE #2.6
# ----------------------
def test_cracked_compressed_NM_006(tmp_path: Path) -> None:
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
    Ned = -3619.0 * KN
    Med = 0.0 * KNm
    sigmac, sigmas, xi = rcSection.solverSLS_NM(Ned, Med, uncracked=False)
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

    rcSection.solverCrack(Ned, Med)
    assert rcSection.crackState() == SectionCrackedStates.COMPRESSED
