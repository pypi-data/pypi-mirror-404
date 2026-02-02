# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import json

import pytest
from pycivil.EXAUtils.EXAExceptions import EXAExceptions
from pycivil.EXAGeometry.geometry import twoPointsDivide, twoPointsOffset
from pycivil.EXAStructural.loads import ForcesOnSection
from pycivil.EXAStructural.rcgensolver.templateRCGen import *
from pycivil.EXAUtils.report import (
    ReportDriverEnum,
    Reporter,
    ReportTemplateEnum,
    getTemplatesPath
)
from pycivil.EXAStructural.codes import Code

def ppr(jsonFrag):
    print(json.dumps(jsonFrag.model_dump(mode="json"), indent=4))


def test_001_base(tmp_path: Path):
    # Build a modeler
    modeler = RCGenSectionsModeler()
    modeler.setJobPath(os.path.dirname(__file__))

    idSectionModel = modeler.addSectionModel(key="section_1", current=True)
    assert idSectionModel != -1
    assert modeler.addSectionModel(key="section_1", current=True) == -1

    # Build solid part
    w = 300
    h = 600
    shapeRectangular = ShapeRect(width=w, height=h)
    modeler.addSolid(shape=shapeRectangular)

    # Add single rebars with point
    cc = 50
    rebarsDiameterTOP = 8
    rebarsDiameterBOT = 24
    barBL = ShapeCircle(
        radius=rebarsDiameterBOT / 2,
        center=shapeRectangular.getShapePoint("BL") + Point2d(cc, cc),
    )
    modeler.addRebar(shape=barBL)
    barBR = ShapeCircle(
        radius=rebarsDiameterBOT / 2,
        center=shapeRectangular.getShapePoint("BR") + Point2d(-cc, cc),
    )
    modeler.addRebar(shape=barBR)
    barTR = ShapeCircle(
        radius=rebarsDiameterTOP / 2,
        center=shapeRectangular.getShapePoint("TR") + Point2d(-cc, -cc),
    )
    modeler.addRebar(shape=barTR)
    barTL = ShapeCircle(
        radius=rebarsDiameterTOP / 2,
        center=shapeRectangular.getShapePoint("TL") + Point2d(cc, -cc),
    )
    modeler.addRebar(shape=barTL)

    # Add multiple rebar with point
    barsBOT_1, barsBOT_2 = twoPointsOffset(barBL.center(), barBR.center())
    barsBOT = twoPointsDivide(barsBOT_1, barsBOT_2, 4, False)
    barsTOP_1, barsTOP_2 = twoPointsOffset(barTR.center(), barTL.center())
    barsTOP = twoPointsDivide(barsTOP_1, barsTOP_2, 4, False)
    modeler.addRebarsGroup(shape=barBL, points=barsBOT)
    modeler.addRebarsGroup(shape=barTL, points=barsTOP)

    # Setting code
    code = Code("NTC2018")

    # Build concrete material by law
    concreteMat = Concrete(descr="Concrete as NTC2018 Law")
    concreteMat.setByCode(code, "C30/37")

    # Build rebar material by law
    rebarMat = ConcreteSteel(descr="Steel as NTC2018 Law")
    rebarMat.setByCode(code, "B450C")

    # Assign materials
    idMatCon = modeler.addConcreteLaw(mat=concreteMat)
    modeler.assignConcreteLawToCurrentModel(idMatCon)
    idMatReb = modeler.addRebarLaw(mat=rebarMat)
    modeler.assignRebarLawToCurrentModel(idMatReb)

    rebarArea = modeler.calcRebarArea()
    concreteArea = modeler.calcConcreteArea()

    fcd = concreteMat.get_fck() * concreteMat.get_alphacc() / concreteMat.get_gammac()
    fyd = rebarMat.get_fsy() / rebarMat.get_gammas()

    N_Rd_comp = -(fyd * rebarArea + fcd * concreteArea)
    print(f"N_Rd_comp (analytical)= {N_Rd_comp}")
    N_Rd_tens = fyd * rebarArea
    print(f"N_Rd_tens (analytical)= {N_Rd_tens}")

    assert modeler.run(opt=Analysis.BOUNDING_SLU)
    results = modeler.getModelOutput().sectionResults[idSectionModel]

    # Test for minimum bounding relative to N force
    x0 = results.boundingSLU.minForces.Fz
    x1 = N_Rd_comp
    print(f"N_Rd_comp (from domain)= {x0}")
    assert x1 == pytest.approx(x0, 1e-12)

    # Test for maximum bounding relative to N force
    x0 = results.boundingSLU.maxForces.Fz
    x1 = N_Rd_tens
    print(f"N_Rd_tens (from domain)= {x0}")
    assert x1 == pytest.approx(x0, 1e-12)

    # Moments for later use
    Mxmin = results.boundingSLU.minForces.Mx
    print(f"Mxmin (from domain)= {Mxmin}")
    Mxmax = results.boundingSLU.maxForces.Mx
    print(f"Mxmax (from domain)= {Mxmax}")
    Mymin = results.boundingSLU.minForces.My
    print(f"Mymin (from domain)= {Mymin}")
    Mymax = results.boundingSLU.maxForces.My
    print(f"Mymax (from domain)= {Mymax}")

    nbForcesGenerated = 10
    forces = {}
    for i in range(nbForcesGenerated):
        Fzi = (N_Rd_tens - N_Rd_comp) / (nbForcesGenerated + 2) * (i + 1) + N_Rd_comp
        forces[i + 1] = ForcesOnSection(id=i + 1, Fx=0, Fy=0, Fz=Fzi, Mx=0, My=0, Mz=0)

    nbForcesNull = 4
    for i in range(nbForcesNull):
        forces[len(forces) + 100] = ForcesOnSection(
            id=len(forces) + 100,
            Fx=0,
            Fy=0,
            Fz=0,
            Mx=0,
            My=0,
            Mz=0,
            limitState=LimitState.ULTIMATE,
        )

    # Model without forces make error
    assert not modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)
    results = modeler.getModelOutput().sectionResults[idSectionModel]
    assert "|ERR --->| Forces with lenght=0 !!! Stop." == results.domainSLU.logs[0]

    # Model with forces go well
    modeler.assignForces(forces)
    assert modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)
    results = modeler.getModelOutput().sectionResults[idSectionModel]

    outfile = Path(__file__).parent.joinpath("test_001_base_nr_1.json")
    jsonObject = json.loads(outfile.read_text())
    assert results == Results(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile.write_text(json.dumps(results.model_dump(), indent=4))

    assert "|INF| Successfully assigned forces for analysis ...", results.domainSLU.logs[
        0
    ]
    assert (
        f"|WRN ->| All {len(forces)} forces are null or not SLU !!!"
    ), results.domainSLU.logs[1]
    assert (
        f"|INF| Nb. {nbForcesNull}/{len(forces)} forces are null !!!"
    ), results.domainSLU.logs[2]
    assert (
        f"|INF| Nb. {len(forces)}/{len(forces)} forces are not ULS !!!"
    ), results.domainSLU.logs[3]

    # Assign ultimate limit state
    for _k, f in forces.items():
        f.limitState = LimitState.ULTIMATE

    assert modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)
    results = modeler.getModelOutput().sectionResults[idSectionModel]

    outfile = Path(__file__).parent.joinpath("test_001_base_nr_2.json")
    jsonObject = json.loads(outfile.read_text())
    assert results == Results(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile.write_text(json.dumps(results.model_dump(), indent=4))

    for v in results.domainSLU.loadsCheckLogs.values():
        assert "Domain ok", v.logs[0]
        assert "N is contained in bounding", v.logs[1]
        assert "Moments Mx and My are nulls. Banal solution", v.logs[2]

    i = 0
    for force in forces.values():
        force.Mx = (Mxmax - Mxmin) / (nbForcesGenerated + 2) * (i + 1) + Mxmin
        force.My = (Mymax - Mymin) / (nbForcesGenerated + 2) * (i + 1) + Mymin
        i += 1
    assert modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)

    modeler.plot(pfx="test_001_base_compact_")
    modeler.plot(pfx="test_001_base_extended_", onlyWorst=False)

    # results = modeler.getModelOutput().sectionResults[idSectionModel]
    results = modeler.getModelOutput()
    outfile = Path(__file__).parent.joinpath("test_001_base_nr_3.json")
    jsonObject = json.loads(outfile.read_text())
    assert results == RCGenSectionsOutput(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile.write_text(results.model_dump_json(indent=4))

    input_model = modeler.exportModelInput()
    input_file = Path(__file__).parent.joinpath("test_001_base_input_nr_3.json")
    jsonObject = json.loads(input_file.read_text())
    assert input_model == RCGenSectionsInput(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # input_file.write_text(input_model.model_dump_json(indent=4))


def test_002_domain_multisections(tmp_path: Path):
    modeler = RCGenSectionsModeler()
    with pytest.raises(EXAExceptions):
        modeler.run(opt=Analysis.BOUNDING_SLU)

    modeler.setJobPath(os.path.dirname(__file__))

    # ----------
    # SECTION #1
    # ----------
    idSec1 = modeler.addSectionModel(key="section_1", current=True)
    modeler.addSolid(shape=ShapeRect(width=300, height=600))

    # Geometry
    cc1 = 50
    nb1 = 4
    dTOP1 = 8
    dBOT1 = 24
    lpBOT1 = modeler.getShapeVertex("BL") + Point2d(cc1, cc1)
    rpBOT1 = modeler.getShapeVertex("BR") + Point2d(-cc1, cc1)
    lpTOP1 = modeler.getShapeVertex("TL") + Point2d(cc1, -cc1)
    rpTOP1 = modeler.getShapeVertex("TR") + Point2d(-cc1, -cc1)
    pointsBOT1 = twoPointsDivide(lpBOT1, rpBOT1, nb1, True)
    pointsTOP1 = twoPointsDivide(lpTOP1, rpTOP1, nb1, True)
    modeler.addRebarsGroup(diameter=dBOT1, points=pointsBOT1)
    modeler.addRebarsGroup(diameter=dTOP1, points=pointsTOP1)

    # Setting code
    code1 = Code("NTC2008")

    # Build concrete material by law
    concreteMat1 = Concrete(descr="Concrete as NTC2008 Law")
    concreteMat1.setByCode(code1, "C32/40")

    # Build rebar material by law
    rebarMat1 = ConcreteSteel(descr="Steel as NTC2018 Law")
    rebarMat1.setByCode(code1, "B450C")

    # Assign materials
    idMatConcrete1 = modeler.addConcreteLaw(mat=concreteMat1)
    idMatRebar1 = modeler.addRebarLaw(mat=rebarMat1)
    modeler.assignConcreteLawToCurrentModel(idm=idMatConcrete1)
    modeler.assignRebarLawToCurrentModel(idm=idMatRebar1)

    assert modeler.run(opt=Analysis.BOUNDING_SLU)
    results = modeler.getModelOutput().sectionResults[idSec1]

    # Moments for generator
    Fzmin = results.boundingSLU.minForces.Fz
    Fzmax = results.boundingSLU.maxForces.Fz
    Mxmin = results.boundingSLU.minForces.Mx
    Mxmax = results.boundingSLU.maxForces.Mx
    Mymin = results.boundingSLU.minForces.My
    Mymax = results.boundingSLU.maxForces.My

    nbForcesGenerated = 10
    forces = {}
    for i in range(nbForcesGenerated):
        Fzi = (Fzmax - Fzmin) / (nbForcesGenerated + 2) * (i + 1) + Fzmin
        Mxi = (Mxmax - Mxmin) / (nbForcesGenerated + 2) * (i + 1) + Mxmin
        Myi = (Mymax - Mymin) / (nbForcesGenerated + 2) * (i + 1) + Mymin
        forces[i + 1] = ForcesOnSection(
            id=i + 1, Fz=Fzi, Mx=Mxi, My=Myi, limitState=LimitState.ULTIMATE
        )

    modeler.assignForces(forces)

    # ----------
    # SECTION #2
    # ----------
    idSec2 = modeler.addSectionModel(key="section_2", current=True)
    modeler.addSolid(shape=ShapeRect(width=800, height=1200))

    cc2 = 70
    nb2 = 10
    dTOP2 = 26
    dBOT2 = 26
    lpBOT2 = modeler.getShapeVertex("BL") + Point2d(cc2, cc2)
    rpBOT2 = modeler.getShapeVertex("BR") + Point2d(-cc2, cc2)
    lpTOP2 = modeler.getShapeVertex("TL") + Point2d(cc2, -cc2)
    rpTOP2 = modeler.getShapeVertex("TR") + Point2d(-cc2, -cc2)
    pointsBOT2 = twoPointsDivide(lpBOT2, rpBOT2, nb2, True)
    pointsTOP2 = twoPointsDivide(lpTOP2, rpTOP2, nb2, True)
    modeler.addRebarsGroup(diameter=dBOT2, points=pointsBOT2)
    modeler.addRebarsGroup(diameter=dTOP2, points=pointsTOP2)

    # Setting code
    code2 = Code("NTC2018")

    # Build concrete material by law
    concreteMat2 = Concrete(descr="Concrete as NTC2018 Law")
    concreteMat2.setByCode(code2, "C35/45")

    # Build rebar material by law
    rebarMat2 = ConcreteSteel(descr="Steel as NTC2018 Law")
    rebarMat2.setByCode(code2, "B450C")

    # Assign materials
    idMatConcrete2 = modeler.addConcreteLaw(mat=concreteMat2)
    idMatRebar2 = modeler.addRebarLaw(mat=rebarMat2)
    modeler.assignConcreteLawToCurrentModel(idm=idMatConcrete2)
    modeler.assignRebarLawToCurrentModel(idm=idMatRebar2)

    assert modeler.run(opt=Analysis.BOUNDING_SLU)
    results = modeler.getModelOutput().sectionResults[idSec2]

    # Moments for generator
    Fzmin = results.boundingSLU.minForces.Fz
    Fzmax = results.boundingSLU.maxForces.Fz
    Mxmin = results.boundingSLU.minForces.Mx
    Mxmax = results.boundingSLU.maxForces.Mx
    Mymin = results.boundingSLU.minForces.My
    Mymax = results.boundingSLU.maxForces.My

    nbForcesGenerated = 10
    forces = {}
    for i in range(nbForcesGenerated):
        Fzi = (Fzmax - Fzmin) / (nbForcesGenerated + 2) * (i + 1) + Fzmin
        Mxi = (Mxmax - Mxmin) / (nbForcesGenerated + 2) * (i + 1) + Mxmin
        Myi = (Mymax - Mymin) / (nbForcesGenerated + 2) * (i + 1) + Mymin
        forces[i + 1] = ForcesOnSection(
            id=i + 1, Fz=Fzi, Mx=Mxi, My=Myi, limitState=LimitState.ULTIMATE
        )

    modeler.assignForces(forces)
    modeler.setCurrentModel("section_1")
    assert modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)
    modeler.setCurrentModel("section_2")
    assert modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)

    modeler.logLevel = 3
    modeler.plot(pfx="test_002_multisections_compact_")
    modeler.plot(pfx="test_002_multisections_extended_", onlyWorst=False)

    results = modeler.getModelOutput()
    outfile = Path(__file__).parent.joinpath("test_002_domain_multisections_nr.json")
    jsonObject = json.loads(outfile.read_text())
    assert results == RCGenSectionsOutput(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile.write_text(results.model_dump_json(indent=4))

    input_model = modeler.exportModelInput()
    input_file = Path(__file__).parent.joinpath(
        "test_002_domain_multisection_input_nr.json"
    )
    jsonObject = json.loads(input_file.read_text())
    assert input_model == RCGenSectionsInput(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # input_file.write_text(input_model.model_dump_json(indent=4))


def test_003_elastic_multisections(tmp_path: Path):
    modeler = RCGenSectionsModeler()
    modeler.logLevel = 3
    modeler.setJobPath(os.path.dirname(__file__))

    # ---------------------------
    # Assign material to sections
    # ---------------------------
    # Setting code
    code = Code("NTC2018")
    # Build concrete material by law
    concreteMat = Concrete(descr="Concrete as NTC2018 Law")
    concreteMat.setByCode(code, "C30/37")
    # Build rebar material by law
    rebarMat = ConcreteSteel(descr="Steel as NTC2018 Law")
    rebarMat.setByCode(code, "B450C")
    # Assign materials
    idMatCon = modeler.addConcreteLaw(mat=concreteMat)
    idMatReb = modeler.addRebarLaw(mat=rebarMat)

    # ------------------------------------
    # SEZIONE [1] exagon_test_numerici.pdf
    # ------------------------------------
    idSec1 = modeler.addSectionModel(key="section_1", current=True)
    modeler.assignConcreteLawToCurrentModel(idMatCon)
    modeler.assignRebarLawToCurrentModel(idMatReb)

    modeler.addSolid(shape=ShapeRect(width=300, height=600))
    vBL = modeler.getShapeVertex("BL")
    vBR = modeler.getShapeVertex("BR")
    vTL = modeler.getShapeVertex("TL")
    vTR = modeler.getShapeVertex("TR")
    modeler.addRebar(center=vBL + Point2d(20, 20), diameter=20)
    modeler.addRebar(center=vBL + Point2d(100, 20), diameter=20)
    modeler.addRebar(center=vBR + Point2d(-20, 20), diameter=20)
    modeler.addRebar(center=vBR + Point2d(-100, 20), diameter=20)
    modeler.addRebar(center=vTL + Point2d(20, -20), diameter=20)
    modeler.addRebar(center=vTL + Point2d(100, -20), diameter=20)
    modeler.addRebar(center=vTR + Point2d(-20, -20), diameter=20)
    modeler.addRebar(center=vTR + Point2d(-100, -20), diameter=20)

    KN = 1000
    KNm = 1000 * 1000
    forces = dict()
    forces[6] = ForcesOnSection(
        id=6,
        Fz=0.0 * KN,
        Mx=1000 * KNm,
        My=1000 * KNm,
        limitState=LimitState.SERVICEABILITY,
    )
    forces[7] = ForcesOnSection(
        id=7,
        Fz=0.0 * KN,
        Mx=100 * KNm,
        My=1000 * KNm,
        limitState=LimitState.SERVICEABILITY,
    )
    forces[8] = ForcesOnSection(
        id=8,
        Fz=0.0 * KN,
        Mx=500 * KNm,
        My=1000 * KNm,
        limitState=LimitState.SERVICEABILITY,
    )
    forces[9] = ForcesOnSection(
        id=9,
        Fz=0.0 * KN,
        Mx=-1000 * KNm,
        My=0.0 * KNm,
        limitState=LimitState.SERVICEABILITY,
    )
    forces[10] = ForcesOnSection(id=10, Fz=0.0 * KN, Mx=500 * KNm, My=1000 * KNm)
    forces[11] = ForcesOnSection(id=11, Fz=0.0 * KN, Mx=-1000 * KNm, My=0.0 * KNm)

    # Without forces runner gives False
    assert not modeler.run(opt=Analysis.ELASTIC_SOLVER)

    # Without run ELASTIC_SOLVER before gives False
    assert not modeler.run(opt=Analysis.CHECK_ELASTIC)

    modeler.assignForces(forces)
    assert modeler.run(opt=Analysis.ELASTIC_SOLVER)

    # Without frequency for force ELASTIC_SOLVER before gives False
    assert not modeler.run(opt=Analysis.CHECK_ELASTIC)

    forces[6].frequency = Frequency.CHARACTERISTIC
    forces[7].frequency = Frequency.CHARACTERISTIC
    forces[8].frequency = Frequency.CHARACTERISTIC
    forces[9].frequency = Frequency.QUASI_PERMANENT

    modeler.assignForces(forces)
    assert modeler.run(opt=Analysis.CHECK_ELASTIC)

    modeler.plot(pfx="test_003_elastic_multisections_")
    modeler.plot(pfx="test_003_elastic_multisections_extended_", onlyWorst=False)

    outModel = modeler.getModelOutput()
    assert type(outModel) == RCGenSectionsOutput

    outModelCasted = RCGenSectionsOutput.model_validate(outModel.model_dump())
    resultsForForce = outModelCasted.sectionResults[
        idSec1
    ].elasticSolver.elasticResults[6]
    assert pytest.approx(resultsForForce.sigmacMin, rel=1e-4) == -199.6
    assert pytest.approx(resultsForForce.sigmacMax, rel=1e-4) == 0.0
    assert pytest.approx(resultsForForce.sigmasMin, rel=1e-4) == -2464
    assert pytest.approx(resultsForForce.sigmasMax, rel=1e-4) == 5426

    resultsForForce = outModelCasted.sectionResults[
        idSec1
    ].elasticSolver.elasticResults[7]
    assert pytest.approx(resultsForForce.sigmacMin, rel=1e-3) == -62.2
    assert pytest.approx(resultsForForce.sigmacMax, rel=1e-3) == 0.0
    assert pytest.approx(resultsForForce.sigmasMin, rel=1e-3) == -819
    assert pytest.approx(resultsForForce.sigmasMax, rel=1e-3) == 1755

    resultsForForce = outModelCasted.sectionResults[
        idSec1
    ].elasticSolver.elasticResults[8]
    assert pytest.approx(resultsForForce.sigmacMin, rel=1e-4) == -128.9
    assert pytest.approx(resultsForForce.sigmacMax, rel=1e-4) == 0.0
    assert pytest.approx(resultsForForce.sigmasMin, rel=1e-3) == -1636
    assert pytest.approx(resultsForForce.sigmasMax, rel=1e-4) == 3263

    resultsForForce = outModelCasted.sectionResults[
        idSec1
    ].elasticSolver.elasticResults[9]
    assert pytest.approx(resultsForForce.sigmacMin, rel=1e-3) == -136.3
    assert pytest.approx(resultsForForce.sigmacMax, rel=1e-4) == 0.0
    assert pytest.approx(resultsForForce.sigmasMin, rel=1e-3) == -1580
    assert pytest.approx(resultsForForce.sigmasMax, rel=1e-3) == 4448

    outfile = Path(__file__).parent.joinpath("test_003_elastic_multisections_nr.json")
    jsonObject = json.loads(outfile.read_text())
    assert outModel == RCGenSectionsOutput(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # outfile.write_text(outModelCasted.model_dump_json(indent=4))

    input_model = modeler.exportModelInput()
    input_file = Path(__file__).parent.joinpath(
        "test_003_elastic_multisections_input_nr.json"
    )
    jsonObject = json.loads(input_file.read_text())
    assert input_model == RCGenSectionsInput(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # input_file.write_text(input_model.model_dump_json(indent=4))


# Test 2nd way to shape a section with general commands.
# Section is the same of test_001.
#
def test_004_base_general(tmp_path: Path):
    # Build a modeler
    modeler = RCGenSectionsModeler()
    modeler.setJobPath(os.path.dirname(__file__))

    idSectionModel = modeler.addSectionModel(key="section_1", current=True, ids=1)
    assert idSectionModel == 1
    # Test same key
    assert modeler.addSectionModel(key="section_1", current=True) == -1
    # Test same id
    assert modeler.addSectionModel(key="section_2", current=True, ids=1) == -1

    nodeBL = Node2d(x=-150, y=-300, idn=1)
    nodeBR = Node2d(x=+150, y=-300, idn=2)
    nodeTR = Node2d(x=+150, y=+300, idn=3)
    nodeTL = Node2d(x=-150, y=+300, idn=4)
    modeler.addNode(nodeBL)
    modeler.addNode(nodeBR)
    modeler.addNode(nodeTR)
    modeler.addNode(nodeTL)

    modeler.addTriangle(nodeBL.idn, nodeBR.idn, nodeTL.idn, 1)
    modeler.addTriangle(nodeBR.idn, nodeTR.idn, nodeTL.idn, 2)

    # Add single rebars with point
    cc = 50
    rebarsDiameterTOP = 8
    rebarsDiameterBOT = 24
    barBL = ShapeCircle(radius=rebarsDiameterBOT / 2, center=nodeBL + Point2d(cc, cc))
    modeler.addRebar(shape=barBL, idn=5, idr=1)
    barBR = ShapeCircle(radius=rebarsDiameterBOT / 2, center=nodeBR + Point2d(-cc, cc))
    modeler.addRebar(shape=barBR, idn=6, idr=2)
    barTR = ShapeCircle(radius=rebarsDiameterTOP / 2, center=nodeTR + Point2d(-cc, -cc))
    modeler.addRebar(shape=barTR, idn=7, idr=3)
    barTL = ShapeCircle(radius=rebarsDiameterTOP / 2, center=nodeTL + Point2d(cc, -cc))
    modeler.addRebar(shape=barTL, idn=8, idr=4)

    # Add multiple rebar with point
    barsBOT_1, barsBOT_2 = twoPointsOffset(barBL.center(), barBR.center())
    barsBOT = twoPointsDivide(barsBOT_1, barsBOT_2, 4, False)
    barsTOP_1, barsTOP_2 = twoPointsOffset(barTR.center(), barTL.center())
    barsTOP = twoPointsDivide(barsTOP_1, barsTOP_2, 4, False)
    modeler.addRebarsGroup(
        shape=barBL, points=barsBOT, id_nodes=[9, 10, 11], id_rebars=[7, 6, 5]
    )
    modeler.addRebarsGroup(
        shape=barTL, points=barsTOP, id_nodes=[12, 13, 14], id_rebars=[8, 9, 10]
    )

    modeler.plot(pfx="test_004_base_compact_")

    # Setting code
    code = Code("NTC2018")

    # Build concrete material by law
    concreteMat = Concrete(descr="Concrete as NTC2018 Law")
    concreteMat.setByCode(code, "C30/37")

    # Build rebar material by law
    rebarMat = ConcreteSteel(descr="Steel as NTC2018 Law")
    rebarMat.setByCode(code, "B450C")

    # Assign materials
    idMatCon = modeler.addConcreteLaw(mat=concreteMat, idm=1)
    assert idMatCon == 1
    modeler.assignConcreteLawToCurrentModel(idMatCon)
    idMatReb = modeler.addRebarLaw(mat=rebarMat, idm=2)
    assert idMatReb > 0
    modeler.assignRebarLawToCurrentModel(idMatReb)

    assert modeler.run(opt=Analysis.BOUNDING_SLU)
    results = modeler.getModelOutput().sectionResults[idSectionModel]

    N_Rd_comp = results.boundingSLU.minForces.Fz
    N_Rd_tens = results.boundingSLU.maxForces.Fz

    assert N_Rd_comp == pytest.approx(-4043455.0915585444, 1e-12)
    assert N_Rd_tens == pytest.approx(983455.0915585441, 1e-12)

    # Moments for later use
    Mxmin = results.boundingSLU.minForces.Mx
    Mxmin_expected = -468694010.4534114
    Mxmax_expected = 468694010.45341134
    Mymin_expected = -160832599.8557186
    Mymax_espected = 160832599.8557186
    assert Mxmin == pytest.approx(Mxmin_expected, 1e-12)
    Mxmax = results.boundingSLU.maxForces.Mx
    assert Mxmax == pytest.approx(Mxmax_expected, 1e-12)
    Mymin = results.boundingSLU.minForces.My
    assert Mymin == pytest.approx(Mymin_expected, 1e-12)
    Mymax = results.boundingSLU.maxForces.My
    assert Mymax == pytest.approx(Mymax_espected, 1e-12)

    input_model = modeler.exportModelInput()
    input_file = Path(__file__).parent.joinpath("test_004_base_general_input_nr.json")
    jsonObject = json.loads(input_file.read_text())
    assert input_model == RCGenSectionsInput(**jsonObject)
    # ------------------------------------------------
    # using this for generate not regression json file
    # ------------------------------------------------
    # input_file.write_text(input_model.model_dump_json(indent=4))

#
# This test take tests above and rebuilds models
#
def test_005_solver_from_model(tmp_path: Path):
    def in_and_out(file_name: str):
        #
        # Read JSON input file
        #
        input_file = Path(__file__).parent.joinpath(file_name)
        jsonObject = json.loads(input_file.read_text())
        input_model = RCGenSectionsInput(**jsonObject)
        #
        # Build modeler with minimal settings
        #
        modeler = RCGenSectionsModeler()
        modeler.logLevel = 3
        assert modeler.setJobPath(os.path.dirname(__file__))
        assert modeler.setModelInput(input_model)
        #
        # Export and test
        #
        input_model = modeler.exportModelInput()
        input_file = Path(__file__).parent.joinpath(file_name)
        jsonObject = json.loads(input_file.read_text())
        assert input_model == RCGenSectionsInput(**jsonObject)

    ###########################################################################
    # File:                   test_001_base_input_nr_3.json
    ###########################################################################
    in_and_out("test_001_base_input_nr_3.json")
    ###########################################################################
    # File:            test_002_domain_multisection_input_nr.json
    ###########################################################################
    in_and_out("test_002_domain_multisection_input_nr.json")
    ###########################################################################
    # File:            test_003_elastic_multisections_input_nr.json
    ###########################################################################
    in_and_out("test_003_elastic_multisections_input_nr.json")
    ###########################################################################
    # File:                test_004_base_general_input_nr.json
    ###########################################################################
    in_and_out("test_004_base_general_input_nr.json")

def input_model_from_file(file_name: str) -> RCGenSectionsInput:
    #
    # Read JSON input file
    #
    input_file = Path(__file__).parent.joinpath(file_name)
    jsonObject = json.loads(input_file.read_text())
    return RCGenSectionsInput(**jsonObject)

def output_model_from_file(file_name: str) -> RCGenSectionsOutput:
    #
    # Read JSON output file
    #
    input_file = Path(__file__).parent.joinpath(file_name)
    jsonObject = json.loads(input_file.read_text())
    return RCGenSectionsOutput(**jsonObject)

def test_006_report_builder(tmp_path: Path):
    i_model = input_model_from_file("test_001_base_input_nr_3.json")
    o_model = output_model_from_file("test_001_base_nr_3.json")
    solver_name = "./RCGen"
    job_path =  Path(os.path.dirname(__file__)) / Path(solver_name)
    rb = ReportBuilder(i_model, o_model, job_path)
    reporter = Reporter(getTemplatesPath())
    reporter.linkFragments(
        driver=ReportDriverEnum.PDFLATEX,
        template=ReportTemplateEnum.TEX_ENG_CAL,
        builder=rb)
    reporter.compileDocument(path=str(tmp_path), fileName="test_006_1_report_builder")

    i_model = input_model_from_file("test_002_domain_multisection_input_nr.json")
    o_model = output_model_from_file("test_002_domain_multisections_nr.json")
    solver_name = "./RCGen"
    job_path =  Path(os.path.dirname(__file__)) / Path(solver_name)
    rb = ReportBuilder(i_model, o_model, job_path)
    reporter = Reporter(getTemplatesPath())
    reporter.linkFragments(
        driver=ReportDriverEnum.PDFLATEX,
        template=ReportTemplateEnum.TEX_ENG_CAL,
        builder=rb)
    reporter.compileDocument(path=str(tmp_path), fileName="test_006_2_report_builder")

    i_model = input_model_from_file("test_003_elastic_multisections_input_nr.json")
    o_model = output_model_from_file("test_003_elastic_multisections_nr.json")
    solver_name = "./RCGen"
    job_path =  Path(os.path.dirname(__file__)) / Path(solver_name)
    rb = ReportBuilder(i_model, o_model, job_path)
    reporter = Reporter(getTemplatesPath())
    reporter.linkFragments(
        template=ReportTemplateEnum.TEX_ENG_CAL,
        builder=rb)
    reporter.compileDocument(path=str(tmp_path), fileName="test_006_3_report_builder")

def test_007_multi_section_multi_check(tmp_path: Path):
    modeler = RCGenSectionsModeler()
    # modeler.logLevel = 3
    modeler.setJobPath(tmp_path)


    modeler.addSectionModel(key="section_1", current=True)

    nodeBL_1 = Node2d(x=-150, y=-300)
    nodeBR_1 = Node2d(x=+150, y=-300)
    nodeTR_1 = Node2d(x=+150, y=+300)
    nodeTL_1 = Node2d(x=-150, y=+300)

    id_nodeBL_1 = modeler.addNode(nodeBL_1)
    id_nodeBR_1 = modeler.addNode(nodeBR_1)
    id_nodeTR_1 = modeler.addNode(nodeTR_1)
    id_nodeTL_1 = modeler.addNode(nodeTL_1)

    modeler.addTriangle(id_nodeBL_1, id_nodeBR_1, id_nodeTL_1)
    modeler.addTriangle(id_nodeBR_1, id_nodeTR_1, id_nodeTL_1)

    cc = 50
    rebarsDiameterTOP = 8
    rebarsDiameterBOT = 24

    rebar_center_BL_1 = nodeBL_1 + Point2d(cc, cc)
    rebar_center_BR_1 = nodeBR_1 + Point2d(-cc, cc)
    rebar_center_TR_1 = nodeTR_1 + Point2d(-cc, -cc)
    rebar_center_TL_1 = nodeTL_1 + Point2d(cc, -cc)
    modeler.addRebar(center=rebar_center_BL_1, diameter=rebarsDiameterBOT)
    modeler.addRebar(center=rebar_center_BR_1, diameter=rebarsDiameterBOT)
    modeler.addRebar(center=rebar_center_TR_1, diameter=rebarsDiameterTOP)
    modeler.addRebar(center=rebar_center_TL_1, diameter=rebarsDiameterTOP)

    modeler.addSectionModel(key="section_2", current=True)

    nodeBL_2 = Node2d(x=-150, y=-300)
    nodeBR_2 = Node2d(x=+150, y=-300)
    nodeML_2 = Node2d(x=+150, y=+100)
    nodeMR_2 = Node2d(x=+300, y=+100)
    nodeTR_2 = Node2d(x=+300, y=+300)
    nodeTL_2 = Node2d(x=-150, y=+300)

    id_nodeBL_2 = modeler.addNode(nodeBL_2)
    id_nodeBR_2 = modeler.addNode(nodeBR_2)
    id_nodeML_2 = modeler.addNode(nodeML_2)
    id_nodeMR_2 = modeler.addNode(nodeMR_2)
    id_nodeTR_2 = modeler.addNode(nodeTR_2)
    id_nodeTL_2 = modeler.addNode(nodeTL_2)

    modeler.addTriangle(id_nodeBL_2, id_nodeML_2, id_nodeTL_2)
    modeler.addTriangle(id_nodeBL_2, id_nodeBR_2, id_nodeML_2)
    modeler.addTriangle(id_nodeTL_2, id_nodeML_2, id_nodeTR_2)
    modeler.addTriangle(id_nodeML_2, id_nodeMR_2, id_nodeTR_2)

    rebar_center_BL_2 = nodeBL_2 + Point2d(cc, cc)
    rebar_center_BR_2 = nodeBR_2 + Point2d(-cc, cc)
    rebar_center_TR_2 = nodeTR_2 + Point2d(-cc, -cc)
    rebar_center_TL_2 = nodeTL_2 + Point2d(cc, -cc)
    modeler.addRebar(center=rebar_center_BL_2, diameter=rebarsDiameterBOT)
    modeler.addRebar(center=rebar_center_BR_2, diameter=rebarsDiameterBOT)
    modeler.addRebar(center=rebar_center_TR_2, diameter=rebarsDiameterTOP)
    modeler.addRebar(center=rebar_center_TL_2, diameter=rebarsDiameterTOP)

    # Add multiple rebar with point
    modeler.setCurrentModel("section_1")
    barsBOT_1_1, barsBOT_2_1 = twoPointsOffset(rebar_center_BL_1, rebar_center_BR_1)
    barsBOT_1 = twoPointsDivide(barsBOT_1_1, barsBOT_2_1, 4, False)
    barsTOP_1_1, barsTOP_2_1 = twoPointsOffset(rebar_center_TR_1, rebar_center_TL_1)
    barsTOP_1 = twoPointsDivide(barsTOP_1_1, barsTOP_2_1, 4, False)
    modeler.addRebarsGroup(
        diameter=rebarsDiameterBOT, points=barsBOT_1
    )
    modeler.addRebarsGroup(
        diameter=rebarsDiameterTOP, points=barsTOP_1
    )

    # Add multiple rebar with point
    modeler.setCurrentModel("section_2")
    barsBOT_1_2, barsBOT_2_2 = twoPointsOffset(rebar_center_BL_2, rebar_center_BR_2)
    barsBOT_2 = twoPointsDivide(barsBOT_1_2, barsBOT_2_2, 4, False)
    barsTOP_1_2, barsTOP_2_2 = twoPointsOffset(rebar_center_TR_2, rebar_center_TL_2)
    barsTOP_2 = twoPointsDivide(barsTOP_1_2, barsTOP_2_2, 4, False)
    modeler.addRebarsGroup(
        diameter=rebarsDiameterBOT, points=barsBOT_2
    )
    modeler.addRebarsGroup(
        diameter=rebarsDiameterTOP, points=barsTOP_2
    )

    # Setting code
    code = Code("NTC2018")

    # Build concrete material by law
    concreteMat = Concrete(descr="Concrete as NTC2018 Law")
    concreteMat.setByCode(code, "C30/37")

    # Build rebar material by law
    rebarMat = ConcreteSteel(descr="Steel as NTC2018 Law")
    rebarMat.setByCode(code, "B450C")

    # Assign materials
    idMatCon = modeler.addConcreteLaw(mat=concreteMat, idm=1)
    idMatReb = modeler.addRebarLaw(mat=rebarMat, idm=2)

    modeler.setCurrentModel("section_1")
    modeler.assignConcreteLawToCurrentModel(idMatCon)
    modeler.assignRebarLawToCurrentModel(idMatReb)
    modeler.setCurrentModel("section_2")
    modeler.assignConcreteLawToCurrentModel(idMatCon)
    modeler.assignRebarLawToCurrentModel(idMatReb)

    KN = 1000
    KNm = 1000 * 1000
    forces = dict()
    forces[1] = ForcesOnSection(
        id=1, Fz=-100.0 * KN, Mx=70 * KNm, My=70 * KNm,
        limitState=LimitState.SERVICEABILITY,
        frequency=Frequency.CHARACTERISTIC
    )
    forces[2] = ForcesOnSection(
        id=2, Fz=-50.0 * KN, Mx=65 * KNm, My=45 * KNm,
        limitState=LimitState.SERVICEABILITY,
        frequency=Frequency.CHARACTERISTIC
    )
    forces[3] = ForcesOnSection(
        id=3, Fz=50.0 * KN, Mx=90 * KNm, My=-90 * KNm,
        limitState=LimitState.SERVICEABILITY,
        frequency=Frequency.CHARACTERISTIC
    )
    forces[4] = ForcesOnSection(
        id=4, Fz=80.0 * KN, Mx=80 * KNm, My=80 * KNm,
        limitState=LimitState.SERVICEABILITY,
        frequency=Frequency.QUASI_PERMANENT
    )
    forces[5] = ForcesOnSection(
        id=5, Fz=30.0 * KN, Mx=80 * KNm, My=-80 * KNm,
        limitState=LimitState.SERVICEABILITY,
        frequency=Frequency.QUASI_PERMANENT
    )
    forces[6] = ForcesOnSection(
        id=6, Fz=-30.0 * KN, Mx=-80 * KNm, My=80 * KNm,
        limitState=LimitState.SERVICEABILITY,
        frequency=Frequency.QUASI_PERMANENT
    )
    forces[7] = ForcesOnSection(
        id=7, Fz=80.0 * KN, Mx=80 * KNm, My=80 * KNm,
        limitState=LimitState.ULTIMATE
    )
    forces[8] = ForcesOnSection(
        id=8, Fz=30.0 * KN, Mx=80 * KNm, My=-80 * KNm,
        limitState=LimitState.ULTIMATE
    )
    forces[9] = ForcesOnSection(
        id=9, Fz=-30.0 * KN, Mx=-80 * KNm, My=80 * KNm,
        limitState=LimitState.ULTIMATE
    )
    forces[10] = ForcesOnSection(
        id=10, Fz=-30.0 * KN, Mx=0.0 * KNm, My=80 * KNm,
        limitState=LimitState.ULTIMATE
    )

    modeler.setCurrentModel("section_1")
    modeler.assignForces(forces)
    modeler.run(opt=Analysis.ELASTIC_SOLVER)
    modeler.run(opt=Analysis.CHECK_ELASTIC)
    modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)

    modeler.setCurrentModel("section_2")
    modeler.assignForces(forces)
    modeler.run(opt=Analysis.ELASTIC_SOLVER)
    modeler.run(opt=Analysis.CHECK_ELASTIC)
    modeler.run(opt=Analysis.CHECK_DOMAIN_SLU)

    input_model = modeler.exportModelInput()
    input_file = tmp_path.joinpath("test_007_input_model.json")
    input_file.write_text(input_model.model_dump_json(indent=4))

    output_model = modeler.getModelOutput()
    output_file = tmp_path.joinpath("test_007_output_model.json")
    output_file.write_text(output_model.model_dump_json(indent=4))

    modeler.plot(onlyWorst=False)