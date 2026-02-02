# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import unittest
from pathlib import Path

from pycivil.EXAGeometry.geometry import Point2d
from pycivil.EXAStructural.modeler import SectionModeler
from pycivil.EXAStructural.plot import Geometry2DPlot, SectionPlot


class Test(unittest.TestCase):
    def test_101_modeler(self):
        # Build modeler
        md = SectionModeler()
        md.setLogLevel(0)

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

        diameterTop = 8
        md.addCircle(10, 10, diameterTop / 2)
        md.addCircle(11, 11, diameterTop / 2)
        md.addCircle(12, 12, diameterTop / 2)
        md.addCircle(13, 13, diameterTop / 2)

        # md.rotate(90, Point2d(150, 300))

        sp = SectionPlot()
        sp.modeler = md
        # sp.setView(SectionPlotView_Enum.SP_VIEW_MESH)

        self.assertTrue(md.buildDomain(15, 30))
        sp.plot()
        sp.save(Path(__file__).parent / "test_101_modeler_section.png")
        bbox = md.domainBounding()

        print(f"bounding Fz: ({bbox[0]},{bbox[1]})")
        print(f"bounding Mx: ({bbox[2]},{bbox[3]})")
        print(f"bounding My: ({bbox[4]},{bbox[5]})")
        # My = const -> (N,Mx)
        intersectionsMy = md.intersectAtMy(0, 1e-3, 1e-6)
        # N = const  -> (Mx, My)
        intersectionsN = md.intersectAtN(0, 1e-6, 1e-6)
        # Mx = const -> (N,My)
        intersectionsMx = md.intersectAtMx(0, 1e-3, 1e-6)

        print(f"Intersections vec lenght {len(intersectionsMy)}")

        gpMy = Geometry2DPlot(figsize=(7, 7))
        gpMy.addPointCloud(intersectionsMy)
        gpMy.showItems(True, False, True)
        gpMy.setTitles(
            [
                "Domain N-Mx in KNm",
            ]
        )
        gpMy.setXLabel(
            [
                "N [KN]",
            ]
        )
        gpMy.setYLabel(
            [
                "Mx [KNm]",
            ]
        )
        gpMy.plot()
        gpMy.save(Path(__file__).parent / "test_101_modeler_domain_01.png")

        gpN = Geometry2DPlot(figsize=(7, 7))
        gpN.addPointCloud(intersectionsN)
        gpN.showItems(False, False, True)
        gpN.setTitles(
            [
                "Domain Mx-My in KNm",
            ]
        )
        gpN.plot()
        gpN.save(Path(__file__).parent / "test_101_modeler_domain_02.png")

        gpMx = Geometry2DPlot(figsize=(7, 7))
        gpMx.addPointCloud(intersectionsMx)
        gpMx.showItems(False, False, True)
        gpMx.setTitles(
            [
                "Domain N,My in KNm",
            ]
        )
        gpMx.plot()
        gpMx.save(Path(__file__).parent / "test_101_modeler_domain_03.png")

        gpArray = Geometry2DPlot(3, 1, figsize=(7, 14))
        gpArray.addPointCloud(intersectionsMy)
        gpArray.addPointCloud(intersectionsN)
        gpArray.addPointCloud(intersectionsMx)
        pointArrayMy = [Point2d(0, 0), Point2d(100, -100)]
        pointArrayN = [Point2d(0, 0), Point2d(10, 100)]
        pointArrayMx = [Point2d(0, 0), Point2d(100, 200)]
        gpArray.addPointArray(pointArrayMy, ["green", "green"])
        gpArray.addPointArray(pointArrayN, ["green", "green"])
        gpArray.addPointArray(pointArrayMx, ["green", "red"])
        gpArray.showItems(False, False, True)
        gpArray.setTitles(
            [
                "Domain N-Mx in KNm",
                "Domain Mx-My in KNm",
                "Domain N,My in KNm",
            ]
        )
        gpArray.setXLabel(
            [
                "N [KN]",
                "Mx [KNm]",
                "N [KNm]",
            ]
        )
        gpArray.setYLabel(
            [
                "Mx [KN]",
                "My [KNm]",
                "My [KNm]",
            ]
        )
        gpArray.plot()
        gpArray.save(Path(__file__).parent / "test_101_modeler_domain_04.png")
        md.setLogLevel(1)
        md.printInfo()

    def test_102_modeler(self):
        # Build modeler
        md = SectionModeler()
        md.setLogLevel(0)

        # Add section and make it current
        md.addSection(1, True)

        # Add node for section
        md.addNode(1, 0, 0)
        md.addNode(2, 600, 0)
        md.addNode(3, 600, 300)
        md.addNode(4, 0, 300)

        md.addTriangle(1, 1, 2, 3)
        md.addTriangle(2, 3, 4, 1)

        # Add node and rebar on bottom
        md.addNode(20, 560, 60)
        md.addNode(21, 560, 120)
        md.addNode(22, 560, 180)
        md.addNode(23, 560, 240)

        diameterBot = 28
        md.addCircle(20, 20, diameterBot / 2)
        md.addCircle(21, 21, diameterBot / 2)
        md.addCircle(22, 22, diameterBot / 2)
        md.addCircle(23, 23, diameterBot / 2)

        # Add node and rebar on top
        md.addNode(10, 40, 60)
        md.addNode(11, 40, 120)
        md.addNode(12, 40, 180)
        md.addNode(13, 40, 240)

        diameterTop = 16
        md.addCircle(10, 10, diameterTop / 2)
        md.addCircle(11, 11, diameterTop / 2)
        md.addCircle(12, 12, diameterTop / 2)
        md.addCircle(13, 13, diameterTop / 2)

        sp = SectionPlot()
        sp.modeler = md
        # sp.setView(ViewEnum.SP_VIEW_TRIANGLES)
        sp.plot()
        sp.save(Path(__file__).parent / "test_102_modeler_section.png")

        self.assertTrue(md.buildDomain(15, 30))

        bbox = md.domainBounding()
        print(f"bounding Fz: ({bbox[0]},{bbox[1]})")
        print(f"bounding Mx: ({bbox[2]},{bbox[3]})")
        print(f"bounding My: ({bbox[4]},{bbox[5]})")
        # My = const -> (N,Mx)
        intersectionsMy = md.intersectAtMy(0, 1e-3, 1e-6)
        # N = const  -> (Mx, My)
        intersectionsN = md.intersectAtN(0, 1e-6, 1e-6)
        # Mx = const -> (N,My)
        intersectionsMx = md.intersectAtMx(0, 1e-3, 1e-6)

        print(f"Intersections vec lenght {len(intersectionsMy)}")

        gpMy = Geometry2DPlot(figsize=(7, 7))
        gpMy.addPointCloud(intersectionsMy)
        gpMy.showItems(False, False, True)
        gpMy.setTitles(
            [
                "Domain N-Mx in KNm",
            ]
        )
        gpMy.setXLabel(
            [
                "N [KN]",
            ]
        )
        gpMy.setYLabel(
            [
                "Mx [KNm]",
            ]
        )
        gpMy.plot()
        gpMy.save(Path(__file__).parent / "test_102_modeler_domain_01.png")

        gpN = Geometry2DPlot(figsize=(7, 7))
        gpN.addPointCloud(intersectionsN)
        gpN.showItems(False, False, True)
        gpN.setTitles(
            [
                "Domain Mx-My in KNm",
            ]
        )
        gpN.plot()
        gpN.save(Path(__file__).parent / "test_102_modeler_domain_02.png")

        gpMx = Geometry2DPlot(figsize=(7, 7))
        gpMx.addPointCloud(intersectionsMx)
        gpMx.showItems(False, False, True)
        gpMx.setTitles(
            [
                "Domain N,My in KNm",
            ]
        )
        gpMx.plot()
        gpMx.save(Path(__file__).parent / "test_102_modeler_domain_03.png")

        gpArray = Geometry2DPlot(3, 1, figsize=(7, 14))
        gpArray.addPointCloud(intersectionsMy)
        gpArray.addPointCloud(intersectionsN)
        gpArray.addPointCloud(intersectionsMx)
        pointArrayMy = [Point2d(0, 0), Point2d(100, -100)]
        pointArrayN = [Point2d(0, 0), Point2d(10, 100)]
        pointArrayMx = [Point2d(0, 0), Point2d(100, 200)]
        gpArray.addPointArray(pointArrayMy, ["green", "green"])
        gpArray.addPointArray(pointArrayN, ["green", "green"])
        gpArray.addPointArray(pointArrayMx, ["green", "red"])
        gpArray.showItems(False, False, True)
        gpArray.setTitles(
            [
                "Domain N-Mx in KNm",
                "Domain Mx-My in KNm",
                "Domain N,My in KNm",
            ]
        )
        gpArray.setXLabel(
            [
                "N [KN]",
                "Mx [KNm]",
                "N [KNm]",
            ]
        )
        gpArray.setYLabel(
            [
                "Mx [KN]",
                "My [KNm]",
                "My [KNm]",
            ]
        )
        gpArray.plot()
        gpArray.save(Path(__file__).parent / "test_102_modeler_domain_04.png")
        md.setLogLevel(1)
        md.printInfo()


if __name__ == "__main__":
    unittest.main()
