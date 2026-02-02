# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import random
import unittest
from pathlib import Path

from pycivil.EXAGeometry.clouds import PointCloud2d
from pycivil.EXAGeometry.geometry import Point2d
from pycivil.EXAStructural.plot import Geometry2DPlot
from pycivil.EXAStructural.templateRCRect import RCTemplRectEC2


class Test(unittest.TestCase):
    def test_001_addPoint(self):
        gp = Geometry2DPlot()

        nb = 12
        ray = 1

        for _i in range(nb):
            gp.addPoint(
                Point2d(
                    random.uniform(-ray / 2, ray / 2), random.uniform(-ray / 2, ray / 2)
                )
            )

        gp.plot()
        gp.save(Path(__file__).parent / "test_001_addPoint.png")

    def test_002_addPointCloud(self):
        gp = Geometry2DPlot()

        nb = 12
        ray = 1

        points = []
        for _i in range(nb):
            points.append(
                Point2d(
                    random.uniform(-ray / 2, ray / 2), random.uniform(-ray / 2, ray / 2)
                )
            )
        pc = PointCloud2d(points)
        assert pc.isConvex() is False
        gp.addPointCloud(pc)

        points = []
        for _i in range(nb):
            points.append(
                Point2d(
                    random.uniform(-ray / 2 + 2, ray / 2 + 2),
                    random.uniform(-ray / 2 + 2, ray / 2 + 2),
                )
            )
        pc = PointCloud2d(points)
        gp.addPointCloud(pc)

        gp.plot()
        gp.save(Path(__file__).parent / "test_002_addPointCloud.png")

    def test_003_savePointCloud(self):

        points = []
        points.append(Point2d(-0.33155, -0.23683))
        points.append(Point2d(-0.34277, -0.35870))
        points.append(Point2d(0.31207, -0.21037))
        points.append(Point2d(-0.06377, -0.38116))
        points.append(Point2d(0.02957, 0.06710))
        points.append(Point2d(-0.25647, 0.36642))
        points.append(Point2d(0.33481, -0.13742))
        points.append(Point2d(-0.01376, -0.32877))
        points.append(Point2d(0.05573, 0.24965))
        points.append(Point2d(0.42329, -0.33455))
        points.append(Point2d(-0.14461, -0.39083))
        points.append(Point2d(-0.06779, -0.09793))

        pc = PointCloud2d(points)

        pc.save(Path(__file__).parent / "test_003_savePointCloud.pkl")

    def test_004_openPointCloud(self):
        points = []
        points.append(Point2d(-0.33155, -0.23683))
        points.append(Point2d(-0.34277, -0.35870))
        points.append(Point2d(0.31207, -0.21037))
        points.append(Point2d(-0.06377, -0.38116))
        points.append(Point2d(0.02957, 0.06710))
        points.append(Point2d(-0.25647, 0.36642))
        points.append(Point2d(0.33481, -0.13742))
        points.append(Point2d(-0.01376, -0.32877))
        points.append(Point2d(0.05573, 0.24965))
        points.append(Point2d(0.42329, -0.33455))
        points.append(Point2d(-0.14461, -0.39083))
        points.append(Point2d(-0.06779, -0.09793))

        pc0 = PointCloud2d(points)
        pc1 = PointCloud2d()
        pc1.open(Path(__file__).parent / "test_003_savePointCloud.pkl")

        self.assertEqual(pc0, pc1)

    def test_005_domain_01(self):
        section = RCTemplRectEC2(1, "First Section")
        section.setDimH(500.0)
        section.setDimW(300.0)
        section.addSteelArea("MB", 40.0, 600.0)
        section.addSteelArea("MT", 40.0, 600.0)
        section.setMaterials("C32/40", "B450C")
        pc = section.interactionDomainBuild2d(nbPoints=24)
        assert isinstance(pc, PointCloud2d)

        pc.save(Path(__file__).parent / "test_005_domain_01.pkl")
        pcFromFile = PointCloud2d()
        pcFromFile.open(Path(__file__).parent / "test_005_domain_01.pkl")

        self.assertEqual(pc, pcFromFile)
        self.assertTrue(isinstance(pc, PointCloud2d))

        print(f"Convexity: --> {pc.isConvex()}")
        gp = Geometry2DPlot()
        gp.addPointCloud(pc)
        gp.pointSize = 10
        gp.textSize = 10
        gp.showItems(True, False, True)
        gp.plot()
        gp.save(Path(__file__).parent / "test_005_domain_01.png")


if __name__ == "__main__":
    unittest.main()
