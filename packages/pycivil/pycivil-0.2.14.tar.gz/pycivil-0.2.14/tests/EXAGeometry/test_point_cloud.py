# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

"""
Created on Sun Nov 19 11:02:00 2023

@author: lpaone
"""
import math
import unittest
from typing import List

from pycivil.EXAGeometry.clouds import PointCloud2d
from pycivil.EXAGeometry.geometry import Point2d, Seg2d


class Test(unittest.TestCase):
    def test_001_constructor(self):
        PointCloud2d([[1, 2], [2, 3]])

        self.assertRaises(ValueError, PointCloud2d, [2, 3])

    def test_002_inspect(self):
        pc = PointCloud2d([[1, 2], [2, 3]])
        self.assertEqual(pc[0], Point2d(1, 2))
        self.assertEqual(pc[1], Point2d(2, 3))
        self.assertRaises(IndexError, pc.__getitem__, 2)

        for i, e in enumerate(pc):
            print(f"At {i} item is {e}")
            self.assertEqual(e, pc[i])

        self.assertEqual(len(pc), 2)

        print(pc.getPoints())

    def test_003_intersect(self):
        p1 = Point2d(-1.0, -1.0)
        p2 = Point2d(+1.0, -1.0)
        p3 = Point2d(+1.0, +1.0)
        p4 = Point2d(-1.0, +1.0)
        seg1 = Seg2d(p1, p2)
        seg2 = Seg2d(p2, p3)
        seg3 = Seg2d(p3, p4)
        seg4 = Seg2d(p4, p1)

        self.assertTrue(seg1.p0 == p1 and seg1.p1 == p2)
        self.assertTrue(seg2.p0 == p2 and seg2.p1 == p3)
        self.assertTrue(seg3.p0 == p3 and seg3.p1 == p4)
        self.assertTrue(seg4.p0 == p4 and seg4.p1 == p1)

        pint = seg1.intersect(seg2)
        self.assertTrue(pint == p2)
        self.assertFalse(pint.isNull())

        pint = seg2.intersect(seg3)
        self.assertFalse(pint.isNull())
        self.assertTrue(pint == p3)

        pint = seg3.intersect(seg4)
        self.assertFalse(pint.isNull())
        self.assertTrue(pint == p4)

        pint = seg1.intersect(seg3)
        self.assertTrue(pint.isNull())

        pint = seg2.intersect(seg4)
        self.assertTrue(pint.isNull())

        pint = seg1.intersect(Seg2d(p2, p4))
        self.assertFalse(pint.isNull())
        self.assertTrue(pint == p2)

        pint = seg1.intersect(Seg2d(p1, p3))
        self.assertFalse(pint.isNull())
        self.assertTrue(pint == p1)

    def test_004_convexity(self):
        nbAngle = 90
        ray = 1.0
        points = []
        for i in range(nbAngle):
            p = Point2d(
                ray * math.cos(math.pi / nbAngle * i),
                ray * math.sin(math.pi / nbAngle * i),
            )
            points.append(p)
        pc = PointCloud2d(points)
        self.assertTrue(pc.isConvex())

    def test_005_contained_false(self):
        nbAngle = 4
        ray = 1.0
        points: List[Point2d] = []
        for i in range(nbAngle):
            p = Point2d(
                ray * math.cos(2 * math.pi / nbAngle * i),
                ray * math.sin(2 * math.pi / nbAngle * i),
            )
            points.append(p)
        pc = PointCloud2d(points)

        self.assertTrue(pc.isConvex())

        bb = pc.boundingBox()
        ro = (bb[1] - bb[0], bb[3] - bb[2])

        res = pc.contains(1.0, 1.0, ro=ro)
        contained = res[0]
        val = res[1]
        if isinstance(val, list):
            points = val
        factor = res[2]
        indexes = res[3]
        assert isinstance(points, list)
        assert isinstance(factor, float)
        assert isinstance(indexes, tuple)

        self.assertEqual(contained, False)
        self.assertEqual(len(points), 2)
        p0 = Point2d(0.5, 0.5)
        p1 = Point2d(-0.5, -0.5)
        self.assertAlmostEqual(points[0].x, p0.x, delta=1e-16)
        self.assertAlmostEqual(points[0].y, p0.y, delta=1e-16)
        self.assertAlmostEqual(points[1].x, p1.x, delta=1e-16)
        self.assertAlmostEqual(points[1].y, p1.y, delta=1e-16)

    def test_006_contained_true(self):
        nbAngle = 4
        ray = 1.0
        points = []
        for i in range(nbAngle):
            p = Point2d(
                ray * math.cos(2 * math.pi / nbAngle * i),
                ray * math.sin(2 * math.pi / nbAngle * i),
            )
            points.append(p)
        pc = PointCloud2d(points)

        self.assertTrue(pc.isConvex())

        bb = pc.boundingBox()
        ro = (bb[1] - bb[0], bb[3] - bb[2])

        res = pc.contains(0.25, 0.25, ro=ro)

        contained = res[0]
        val = res[1]
        if isinstance(val, list):
            points = val
        factor = res[2]
        indexes = res[3]
        assert isinstance(points, list)
        assert isinstance(factor, float)
        assert isinstance(indexes, tuple)

        self.assertEqual(contained, True)
        self.assertEqual(len(points), 2)
        p0 = Point2d(0.5, 0.5)
        p1 = Point2d(-0.5, -0.5)
        self.assertAlmostEqual(points[0].x, p0.x, delta=1e-16)
        self.assertAlmostEqual(points[0].y, p0.y, delta=1e-16)
        self.assertAlmostEqual(points[1].x, p1.x, delta=1e-16)
        self.assertAlmostEqual(points[1].y, p1.y, delta=1e-16)

    def test_007_contained_horizontal(self):
        nbAngle = 4
        ray = 1.0
        points = []
        for i in range(nbAngle):
            p = Point2d(
                ray * math.cos(2 * math.pi / nbAngle * i),
                ray * math.sin(2 * math.pi / nbAngle * i),
            )
            points.append(p)
        pc = PointCloud2d(points)

        self.assertTrue(pc.isConvex())

        bb = pc.boundingBox()
        ro = (bb[1] - bb[0], bb[3] - bb[2])

        res = pc.contains(0.25, 0.0, ro=ro)
        contained = res[0]
        val = res[1]
        if isinstance(val, list):
            points = val
        factor = res[2]
        indexes = res[3]
        assert isinstance(points, list)
        assert isinstance(factor, float)
        assert isinstance(indexes, tuple)

        self.assertEqual(contained, True)
        self.assertEqual(len(points), 2)
        p0 = Point2d(+1.0, 0.0)
        p1 = Point2d(-1.0, 0.0)
        self.assertAlmostEqual(points[0].x, p0.x, delta=1e-15)
        self.assertAlmostEqual(points[0].y, p0.y, delta=1e-15)
        self.assertAlmostEqual(points[1].x, p1.x, delta=1e-15)
        self.assertAlmostEqual(points[1].y, p1.y, delta=1e-15)

    def test_008_contained_vertical(self):
        nbAngle = 4
        ray = 1.0
        points = []
        for i in range(nbAngle):
            p = Point2d(
                ray * math.cos(2 * math.pi / nbAngle * i),
                ray * math.sin(2 * math.pi / nbAngle * i),
            )
            points.append(p)
        pc = PointCloud2d(points)

        self.assertTrue(pc.isConvex())

        bb = pc.boundingBox()
        ro = (bb[1] - bb[0], bb[3] - bb[2])

        res = pc.contains(0.0, 0.25, ro=ro)
        contained = res[0]
        val = res[1]
        if isinstance(val, list):
            points = val
        factor = res[2]
        indexes = res[3]
        assert isinstance(points, list)
        assert isinstance(factor, float)
        assert isinstance(indexes, tuple)

        self.assertEqual(contained, True)
        self.assertEqual(len(points), 2)
        p0 = Point2d(0.0, +1.0)
        p1 = Point2d(0.0, -1.0)
        self.assertAlmostEqual(points[0].x, p0.x, delta=1e-15)
        self.assertAlmostEqual(points[0].y, p0.y, delta=1e-15)
        self.assertAlmostEqual(points[1].x, p1.x, delta=1e-15)
        self.assertAlmostEqual(points[1].y, p1.y, delta=1e-15)


if __name__ == "__main__":
    unittest.main()
