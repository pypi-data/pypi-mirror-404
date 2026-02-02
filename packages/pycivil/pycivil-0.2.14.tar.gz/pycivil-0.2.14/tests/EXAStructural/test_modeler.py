# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import math
import unittest
from pathlib import Path

from pycivil.EXAStructural.modeler import Point2d, SectionModeler
from pycivil.EXAStructural.plot import SectionPlot
from pycivil.EXAStructural.plot import SectionPlotViewEnum as ViewEnum


class Test(unittest.TestCase):
    def test_105_modeler_garbage(self):
        md = SectionModeler()
        md.setLogLevel(1)

        md.printInfo("AFTER CREATION")
        md.addSection(1, True)
        md.printInfo("AFTER ADD SECTION")
        md.addNode(1, 0, 0)
        md.addNode(2, 300, 0)
        md.addNode(3, 300, 600)
        md.addNode(4, 0, 600)
        md.getNodes()
        md.addTriangle(1, 1, 2, 3)
        md.addTriangle(2, 3, 4, 1)

        md.addNode(20, 60, 40)
        md.addNode(21, 120, 40)
        md.addNode(22, 180, 40)
        md.addNode(23, 240, 40)

        md.addCircle(20, 20, 28 / 2)
        md.addCircle(21, 21, 28 / 2)
        md.addCircle(22, 22, 28 / 2)
        md.addCircle(23, 23, 28 / 2)

        self.assertEqual(md.getCircles()[20].center.id, 20)

    def test_101_modeler(self):
        md = SectionModeler()
        md.printInfo("AFTER CREATION")

        md.setLogLevel(1)
        # test of addSection
        self.assertTrue(md.addSection(1, True))
        self.assertTrue(md.addSection(2, True))
        self.assertFalse(md.addSection(1, True))

        # test of setCurrent
        self.assertTrue(md.setCurrent(1))
        self.assertFalse(md.setCurrent(3))

        # test of getCurrent
        self.assertTrue(md.getCurrent())
        self.assertFalse(md.getCurrent() == 2)

        # test of getCurrentType
        self.assertTrue(md.getCurrentType() == "SectionModel")

        # test of getModelIndexes
        self.assertEqual(md.getModelIndices(), [1, 2])

        # test of sizeOfSectionModels
        self.assertEqual(md.sizeOfSectionModels(), 2)

        # test of addNode
        self.assertTrue(md.addNode(1, 0, 0))
        self.assertTrue(md.addNode(2, 300, 0))
        self.assertTrue(md.addNode(3, 299, 599))
        self.assertTrue(md.addNode(4, 0, 600))

        # test of nodesSize
        self.assertEqual(md.nodesSize(), 4)

        # test of getNodeX
        self.assertEqual(md.getNodeX(3), 299)
        self.assertRaises(RuntimeError, md.getNodeX, 11)

        # test of getNodeY
        self.assertEqual(md.getNodeY(3), 599)

        # test of setNodeX
        self.assertTrue(md.setNodeX(3, 300))
        self.assertTrue(md.setNodeY(3, 600))
        self.assertEqual(md.getNodeX(3), 300)
        self.assertEqual(md.getNodeY(3), 600)
        # test of getNodes
        nodes = md.getNodes()
        coords = ((0, 0), (300, 0), (300, 600), (0, 600))
        ids = (1, 2, 3, 4)
        for idn in nodes:
            idx = ids.index(idn)
            self.assertEqual(nodes[idn].xn, coords[idx][0])
            self.assertEqual(nodes[idn].yn, coords[idx][1])

        # test of addTriangle
        self.assertTrue(md.addTriangle(1, 1, 2, 3))
        self.assertTrue(md.addTriangle(2, 3, 4, 1))
        self.assertFalse(md.addTriangle(1, 1, 2, 3))
        self.assertFalse(md.addTriangle(3, 1, 2, 5))

        # test of getTriangles
        trianglesId = md.getTrianglesIds()
        trianglesCheck = ((1, 1, 2, 3), (2, 3, 4, 1))
        idx = 0
        for k in trianglesId:
            self.assertEqual(trianglesId[k][0], trianglesCheck[idx][1])
            self.assertEqual(trianglesId[k][1], trianglesCheck[idx][2])
            self.assertEqual(trianglesId[k][2], trianglesCheck[idx][3])
            idx += 1

        # test of trianglesSize
        self.assertEqual(md.trianglesSize(), 2)

        # test of addCircles
        self.assertTrue(md.addNode(20, 60, 40))
        self.assertTrue(md.addNode(21, 120, 40))
        self.assertTrue(md.addNode(22, 180, 40))
        self.assertTrue(md.addNode(23, 240, 40))
        self.assertTrue(md.addNode(10, 60, 560))
        self.assertTrue(md.addNode(11, 120, 560))
        self.assertTrue(md.addNode(12, 180, 560))
        self.assertTrue(md.addNode(13, 240, 560))

        self.assertTrue(md.addCircle(20, 20, 28 / 2))
        self.assertTrue(md.addCircle(21, 21, 28 / 2))
        self.assertTrue(md.addCircle(22, 22, 28 / 2))
        self.assertTrue(md.addCircle(23, 23, 28 / 2))
        self.assertTrue(md.addCircle(10, 10, 16 / 2))
        self.assertTrue(md.addCircle(11, 11, 16 / 2))
        self.assertTrue(md.addCircle(12, 12, 16 / 2))
        self.assertTrue(md.addCircle(13, 13, 16 / 2))

        self.assertFalse(md.addCircle(13, 13, 16 / 2))
        self.assertFalse(md.addCircle(13, -1, 16 / 2))

        # test of circlesSize
        self.assertEqual(md.circlesSize(), 8)

        # test of setCircleRadius
        oldRadius = md.getCircles()[20].radius
        self.assertTrue(md.setCircleRadius(20, 12 / 2))
        self.assertEqual(md.getCircles()[20].radius, 12 / 2)
        self.assertTrue(md.setCircleRadius(20, oldRadius))
        self.assertEqual(md.getCircles()[20].radius, oldRadius)

        # test of getTriangles
        circles = md.getCircles()
        circlesCheck = (
            (10, 10, 8),
            (11, 11, 8),
            (12, 12, 8),
            (13, 13, 8),
            (20, 20, 14),
            (21, 21, 14),
            (22, 22, 14),
            (23, 23, 14),
        )
        for idc in circlesCheck:
            self.assertEqual(circles[idc[0]].id, idc[0])
            self.assertEqual(circles[idc[0]].center.id, idc[1])
            self.assertEqual(circles[idc[0]].radius, idc[2])

        # test of addLawParaboleRectangle and addLawBilinear
        self.assertTrue(
            md.addLawParaboleRectangle(100, "C20/25", 20 / 1.5, 0.002, 0.0035)
        )
        self.assertTrue(md.addLawBilinear(200, "B450C", 450 / 1.15, 210000, 0.010))
        self.assertFalse(
            md.addLawParaboleRectangle(200, "C20/25", 20 / 1.5, 0.002, 0.0035)
        )

        # test of setTrianglesLaw setCirclesLaw
        self.assertTrue(md.setTrianglesLawInAllModels(100))
        self.assertTrue(md.setCirclesLawInAllModels(200))
        self.assertFalse(md.setTrianglesLawInAllModels(101))
        self.assertFalse(md.setCirclesLawInAllModels(101))

        # test of meshMake
        self.assertTrue(md.meshMake())

        # test of meshSize
        self.assertTrue(md.meshSize(), 2)

        # test of nodesSizeAtMesh, getNodesAtMesh,
        #         trianglesSizeAtMesh, getTrianglesAtMesh
        #         circlesSizeAtMesh
        nodesCheck = [
            [(0.0, 0.0), (300.0, 0.0), (300.0, 600.0)],
            [(300.0, 600.0), (0.0, 600.0), (0.0, 0.0)],
        ]
        trianglesCheck = [(1, 2, 3), (3, 4, 1)]
        for i in range(md.meshSize()):
            nbNodes = md.nodesSizeAtMesh(i)
            self.assertEqual(nbNodes, 3)

            nodes = md.getNodesAtMesh(i)
            for ii in range(nbNodes):
                node = nodes[ii]
                self.assertEqual(node.xn, nodesCheck[i][ii][0])
                self.assertEqual(node.yn, nodesCheck[i][ii][1])
                print(f"(id: *{node.id}* {node.xn},{node.yn})")
                del node

            nbTriangles = md.trianglesSizeAtMesh(i)
            self.assertEqual(nbTriangles, 1)

            trianglesIds = md.getTrianglesIdsAtMesh(i)
            for k in trianglesIds:
                triangle = trianglesIds[k]
                self.assertEqual(triangle[0], trianglesCheck[i][0])
                self.assertEqual(triangle[1], trianglesCheck[i][1])
                self.assertEqual(triangle[2], trianglesCheck[i][2])
                del triangle

            nbCircles = md.circlesSizeAtMesh(i)
            self.assertEqual(nbCircles, 0)

        self.assertEqual(md.calcSolidBarycenter(), Point2d(150, 300))

        # test of printInfo
        md.printInfo()

        # Need to do this because in getNodes(), getTriangles(), getCircles()
        # we make a copy of instances that doesn't destroy with garbage collector
        # ad ex. above using del
        #                  --------------------------
        #                        before garbage
        #                  --------------------------
        #                  Section models     ==> 2
        #                  Nodes              ==> 12
        #                  Triangles          ==> 2
        #                  Circles            ==> 8
        #                  Edges              ==> 0
        #                  Laws bilinear      ==> 1
        #                  Laws parabola rec. ==> 1
        #                  Deleting XStruModeler ...
        #                  --------------------------
        #                        after deleting
        #                  --------------------------
        #                  Section models     ==> 0
        #                  Nodes              ==> 0
        #                  Triangles          ==> 0
        #                  Circles            ==> 0
        #                  Edges              ==> 0
        #                  Laws bilinear      ==> 0
        #                  Laws parabola rec. ==> 0
        # del nodes
        # del circles
        # del triangles

    def test_102_modeler_calc(self):
        # Build modeler
        md = SectionModeler()

        # Add section and make it current
        md.addSection(1, True)

        # Add node for section
        md.addNode(1, 0, 0)
        md.addNode(2, 300, 0)
        md.addNode(3, 300, 600)
        md.addNode(4, 0, 600)

        md.addTriangle(1, 1, 2, 3)
        md.addTriangle(2, 3, 4, 1)

        # Add node and rebar on bottom
        md.addNode(20, 60, 40)
        md.addNode(21, 120, 40)
        md.addNode(22, 180, 40)
        md.addNode(23, 240, 40)

        diameterBot = 28
        md.addCircle(20, 20, diameterBot / 2)
        md.addCircle(21, 21, diameterBot / 2)
        md.addCircle(22, 22, diameterBot / 2)
        md.addCircle(23, 23, diameterBot / 2)

        # Add node and rebar on top
        md.addNode(10, 60, 560)
        md.addNode(11, 120, 560)
        md.addNode(12, 180, 560)
        md.addNode(13, 240, 560)

        diameterTop = 16
        md.addCircle(10, 10, diameterTop / 2)
        md.addCircle(11, 11, diameterTop / 2)
        md.addCircle(12, 12, diameterTop / 2)
        md.addCircle(13, 13, diameterTop / 2)

        solidBary = md.calcSolidBarycenter()
        print(f"solidBary = {solidBary}")
        self.assertEqual(solidBary.x, 150.0)
        self.assertEqual(solidBary.y, 300.0)

        pointBary = md.calcPointBarycenter(area=False)
        print(f"pointBary unary = {pointBary}")
        self.assertAlmostEqual(pointBary.x, 150.0)
        self.assertAlmostEqual(pointBary.y, 300.0)

        pointBary = md.calcPointBarycenter(area=True)
        print(f"pointBary with area = {pointBary}")

        areaTop = 4 * math.pow(diameterTop, 2) * math.pi / 4
        yTop = 600 - 40
        areaBot = 4 * math.pow(diameterBot, 2) * math.pi / 4
        yBot = 40
        yg = (areaTop * yTop + areaBot * yBot) / (areaTop + areaBot)
        self.assertAlmostEqual(pointBary.y, yg)

        # TODO: Need to be fixed calc in exagone
        md.calcSolidAreaProperties()

        self.assertTrue(areaTop + areaBot, md.calcPointArea())
        self.assertTrue(300 * 600, md.calcSolidArea())

        md.printInfo()

    def test_103_modeler_plot(self):
        # Build modeler
        md = SectionModeler()

        # Add section and make it current
        md.addSection(1, True)

        # Add node for section
        md.addNode(1, 0, 0)
        md.addNode(2, 300, 0)
        md.addNode(3, 300, 600)
        md.addNode(4, 0, 600)

        md.addTriangle(1, 1, 2, 3)
        md.addTriangle(2, 3, 4, 1)

        # Add node and rebar on bottom
        md.addNode(20, 60, 40)
        md.addNode(21, 120, 40)
        md.addNode(22, 180, 40)
        md.addNode(23, 240, 40)

        diameterBot = 28
        md.addCircle(20, 20, diameterBot / 2)
        md.addCircle(21, 21, diameterBot / 2)
        md.addCircle(22, 22, diameterBot / 2)
        md.addCircle(23, 23, diameterBot / 2)

        # Add node and rebar on top
        md.addNode(10, 60, 560)
        md.addNode(11, 120, 560)
        md.addNode(12, 180, 560)
        md.addNode(13, 240, 560)

        diameterTop = 16
        md.addCircle(10, 10, diameterTop / 2)
        md.addCircle(11, 11, diameterTop / 2)
        md.addCircle(12, 12, diameterTop / 2)
        md.addCircle(13, 13, diameterTop / 2)

        sp = SectionPlot()
        sp.modeler = md
        sp.setView(ViewEnum.SP_VIEW_SECTION)
        sp.plot()
        sp.save(Path(__file__).parent / "test_103_modeler_plot_1.png")
        sp.setView(ViewEnum.SP_VIEW_TRIANGLES)
        sp.plot()
        sp.save(Path(__file__).parent / "test_103_modeler_plot_2.png")
        sp.setView(ViewEnum.SP_VIEW_SECTION_NOID)
        sp.plot()
        sp.save(Path(__file__).parent / "test_103_modeler_plot_3.png")
        sp.setView(ViewEnum.SP_VIEW_TRIANGLE_NOID)
        sp.plot()
        sp.save(Path(__file__).parent / "test_103_modeler_plot_4.png")
        sp.setView(ViewEnum.SP_VIEW_SECTION)
        sp.setView(ViewEnum.SP_VIEW_GRID)
        sp.plot()
        sp.save(Path(__file__).parent / "test_103_modeler_plot_5.png")
        sp.setView(ViewEnum.SP_VIEW_TRIANGLES)
        sp.setView(ViewEnum.SP_HIDE_NODES)
        sp.plot()
        sp.save(Path(__file__).parent / "test_103_modeler_plot_6.png")
        # sp.show()
        md.setLogLevel(1)
        del md

    # --------------------
    # BY-HAND TEST CASE #1
    # --------------------
    def test_104_modeler_calc(self):
        # Build modeler
        md = SectionModeler()

        # Add section and make it current
        md.addSection(1, True)

        # Add node for section
        md.addNode(1, 0, 0)
        md.addNode(2, 300, 0)
        md.addNode(3, 300, 600)
        md.addNode(4, 0, 600)

        md.addTriangle(1, 1, 2, 3)
        md.addTriangle(2, 3, 4, 1)

        # Add node and rebar on bottom
        md.addNode(20, 60, 54)
        md.addNode(21, 120, 54)
        md.addNode(22, 180, 54)
        md.addNode(23, 240, 54)

        diameterBot = 28
        md.addCircle(20, 20, diameterBot / 2)
        md.addCircle(21, 21, diameterBot / 2)
        md.addCircle(22, 22, diameterBot / 2)
        md.addCircle(23, 23, diameterBot / 2)

        # Add node and rebar on top
        md.addNode(10, 60, 550)
        md.addNode(11, 120, 550)
        md.addNode(12, 180, 550)
        md.addNode(13, 240, 550)

        diameterTop = 20
        md.addCircle(10, 10, diameterTop / 2)
        md.addCircle(11, 11, diameterTop / 2)
        md.addCircle(12, 12, diameterTop / 2)
        md.addCircle(13, 13, diameterTop / 2)

        md.nCoeff = 15

        solidBary = md.calcSolidBarycenter()
        print("\n")
        print(f"solidBary = ({solidBary.x:.3f}, {solidBary.y:.3f})")
        self.assertEqual(solidBary.x, 150.0)
        self.assertEqual(solidBary.y, 300.0)

        pointBary = md.calcPointBarycenter()
        print(f"pointBary = ({pointBary.x:.3f}, {pointBary.y:.3f})")
        self.assertAlmostEqual(pointBary.x, 150.0)
        self.assertAlmostEqual(pointBary.y, 221.6, delta=0.1)

        idealBary = md.calcIdealBarycenter()
        print(f"idealBary = ({idealBary.x:.3f}, {idealBary.y:.3f})")
        self.assertAlmostEqual(idealBary.x, 150.0)
        self.assertAlmostEqual(idealBary.y, 281.38, delta=0.1)

        solidArea = md.calcSolidArea()
        print(f"solidArea = {solidArea:.3f}")
        self.assertAlmostEqual(solidArea, 180.0e3, delta=0.1)

        pointArea = md.calcPointArea()
        print(f"pointArea = {pointArea:.3f}")
        self.assertAlmostEqual(pointArea, 3.72e3, delta=1.0)

        idealArea = md.calcIdealArea()
        print(f"idealArea = {idealArea:.3f}")
        self.assertAlmostEqual(idealArea, 235.8e3, delta=6.0)

        md.setLogLevel(1)

    def test_106_modeler_plot_mesh(self):
        # Build modeler
        md = SectionModeler()

        # Add section and make it current
        md.addSection(1, True)

        # Add node for section
        md.addNode(1, 0, 0)
        md.addNode(2, 300, 0)
        md.addNode(3, 300, 600)
        md.addNode(4, 0, 600)

        md.addTriangle(1, 1, 2, 3)
        md.addTriangle(2, 3, 4, 1)

        # Add node and rebar on bottom
        md.addNode(20, 60, 40)
        md.addNode(21, 120, 40)
        md.addNode(22, 180, 40)
        md.addNode(23, 240, 40)

        diameterBot = 28
        md.addCircle(20, 20, diameterBot / 2)
        md.addCircle(21, 21, diameterBot / 2)
        md.addCircle(22, 22, diameterBot / 2)
        md.addCircle(23, 23, diameterBot / 2)

        # Add node and rebar on top
        md.addNode(10, 60, 560)
        md.addNode(11, 120, 560)
        md.addNode(12, 180, 560)
        md.addNode(13, 240, 560)

        diameterTop = 16
        md.addCircle(10, 10, diameterTop / 2)
        md.addCircle(11, 11, diameterTop / 2)
        md.addCircle(12, 12, diameterTop / 2)
        md.addCircle(13, 13, diameterTop / 2)

        md.meshMake()

        md.meshesSliceAtYrays([100, 200, 300, 400, 500])

        sp = SectionPlot()
        sp.modeler = md
        sp.setView(ViewEnum.SP_VIEW_MESH)
        sp.plot()
        sp.save(Path(__file__).parent / "test_106_modeler_plot_mesh_slice_yray.png")

        md.meshReset()
        sp.plot()
        sp.save(Path(__file__).parent / "test_106_modeler_plot_mesh_resetted.png")

        md.meshesSliceAtRays(
            [
                [0, 1, -100],
                [0, 1, -200],
                [0, 1, -300],
                [0, 1, -400],
                [0, 1, -500],
            ]
        )

        sp.plot()
        sp.save(Path(__file__).parent / "test_106_modeler_plot_mesh_slice_ray_1.png")

        md.meshReset()
        md.meshesSliceAtRays(
            [
                [-1, 1, -2000],
                [-1, 1, -1500],
                [-1, 1, -1000],
            ]
        )

        sp.plot()
        sp.save(Path(__file__).parent / "test_106_modeler_plot_mesh_slice_ray_2.png")

        md.setLogLevel(1)
        del md

    def test_107_modeler_geometry(self):
        # Build modeler
        md = SectionModeler()

        # Add section and make it current
        md.addSection(1, True)

        # Add node for section
        md.addNode(1, 0, 0)
        md.addNode(2, 300, 0)
        md.addNode(3, 300, 600)
        md.addNode(4, 0, 600)

        md.addTriangle(1, 1, 2, 3)
        md.addTriangle(2, 3, 4, 1)

        # Add node and rebar on bottom
        md.addNode(20, 60, 40)
        md.addNode(21, 120, 40)
        md.addNode(22, 180, 40)
        md.addNode(23, 240, 40)

        diameterBot = 28
        md.addCircle(20, 20, diameterBot / 2)
        md.addCircle(21, 21, diameterBot / 2)
        md.addCircle(22, 22, diameterBot / 2)
        md.addCircle(23, 23, diameterBot / 2)

        # Add node and rebar on top
        md.addNode(10, 60, 560)
        md.addNode(11, 120, 560)
        md.addNode(12, 180, 560)
        md.addNode(13, 240, 560)

        diameterTop = 16
        md.addCircle(10, 10, diameterTop / 2)
        md.addCircle(11, 11, diameterTop / 2)
        md.addCircle(12, 12, diameterTop / 2)
        md.addCircle(13, 13, diameterTop / 2)

        solidBary = md.calcSolidBarycenter()
        print(f"solidBary = {solidBary}")
        self.assertEqual(solidBary.x, 150.0)
        self.assertEqual(solidBary.y, 300.0)

        md.saveGeometry()
        md.moveToSolidBarycenter()
        solidMoved = md.calcSolidBarycenter()
        print(f"solidMoved = {solidMoved}")
        self.assertEqual(solidMoved.x, 0.0)
        self.assertEqual(solidMoved.y, 0.0)

        md.restoreGeometry()
        solidBary = md.calcSolidBarycenter()
        print(f"solidBary restored = {solidBary}")
        self.assertEqual(solidBary.x, 150.0)
        self.assertEqual(solidBary.y, 300.0)

        del md


if __name__ == "__main__":
    unittest.main()
