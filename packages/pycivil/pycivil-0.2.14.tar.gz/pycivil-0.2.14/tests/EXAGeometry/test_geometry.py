# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

"""
Tests for EXAGeometry.geometry module

@author: lpaone
"""
import copy

import pytest

from pycivil.EXAGeometry.geometry import (
    Edge2d,
    Edge3d,
    Node2d,
    Node3d,
    Point2d,
    Point3d,
    Polyline2d,
    Polyline3d,
    Seg2d,
    Vector2d,
    Vector3d,
    affineSum2d,
    areaFromTria3D,
    twoPointsDivide,
    twoPointsOffset,
)


def test_Points2d_sum() -> None:
    p1 = Point2d(1, 2)
    p2 = Point2d(1, 2)
    p3 = p1 + p2

    assert p3.x == 2
    assert p3.y == 4


def test_Points2d_Coordinates() -> None:
    p1 = Point2d(0, 0)
    p2 = Point2d(1, 2.0 / 3)
    p3 = Point2d(1, 2)

    assert p1.x == 0
    assert p1.y == 0

    assert p2.x == 1
    assert p2.y == 2.0 / 3

    assert p1.x == 0
    assert p1.y == 0

    assert p3.x == 1
    assert p3.y == 2

    p1 = Point2d(coords=(0, 0))
    p2 = Point2d(coords=(1, 2.0 / 3))
    p3 = Point2d(coords=(1, 2))

    assert p1.x == 0
    assert p1.y == 0

    assert p2.x == 1
    assert p2.y == 2.0 / 3

    assert p1.x == 0
    assert p1.y == 0

    assert p3.x == 1
    assert p3.y == 2

    with pytest.raises(ValueError):
        Point2d(None, None)


def test_Polyline3d_properties() -> None:
    nodesLst = [
        Node3d(1, 0.0, 0.0, 0),
        Node3d(2, 300.0, 0.0, 0),
        Node3d(3, 300.0, 500.0, 0),
        Node3d(4, 0.0, 500.0, 0),
    ]
    poly3 = Polyline3d(nodesLst)

    poly3.setClosed()
    assert poly3.isClosed()


def test_Point3d_operations() -> None:
    p1 = Point3d(0.0, 0.0, 1.0)
    p2 = Point3d(1.0, 1.0, 0.0)
    p3 = p1 + p2

    assert p3.x == 1.0
    assert p3.y == 1.0
    assert p3.z == 1.0


def test_Node3d_operations() -> None:
    n1 = Node3d(0.0, 0.0, 1.0)
    n2 = Node3d(1.0, 1.0, 0.0)
    assert n1.x == 0.0
    assert n2.x == 1.0


def test_Vector3d_operations() -> None:
    v1 = Vector3d(0.0, 0.0, 1.0)
    v2 = Vector3d(1.0, 1.0, 0.0)

    # Cross vector for Vector3d
    v1 = Vector3d(1.0, 0.0, 0.0)
    v2 = Vector3d(0.0, 1.0, 0.0)
    v3 = v1.cross(v2)
    assert v3.vz == 1.0

    # Norm of vector for Vector3d
    v1 = Vector3d(5.0, 0.0, 0.0)
    assert v1.norm() == 5.0

    # Normalization of vector for Vector3d
    v1.normalize()
    assert v1.vx == 1.0

    # Vector 3d from two points
    p1 = Point3d(1.0, 0.0, 0.0)
    p2 = Point3d(2.0, 0.0, 0.0)
    v1 = Vector3d(p1, p2)
    assert v1.vx == 1.0


def test_Vector2d_operations() -> None:
    v1 = Vector2d(vx=0.0, vy=0.0)
    v2 = Vector2d(vx=1.0, vy=1.0)

    # Cross vector for Vector2d
    v1 = Vector2d(vx=1.0, vy=0.0)
    v2 = Vector2d(vx=0.0, vy=1.0)
    cross = v1.cross(v2)
    assert cross == 1.0

    # Norm of vector for Vector2d
    v1 = Vector2d(vx=5.0, vy=0.0)
    assert v1.norm() == 5.0

    # Normalization of vector for Vector2d
    v1.normalize()
    assert v1.vx == 1.0

    # Vector 2d from two points
    p1 = Point2d(1.0, 0.0)
    p2 = Point2d(2.0, 0.0)
    v1 = Vector2d(p1, p2)
    assert v1.vx == 1.0


def test_Seg2d_properties() -> None:
    p1 = Point2d(1.0, 0.0)
    p2 = Point2d(2.0, 0.0)
    Seg2d(p1, p2)
    assert p1.distance(p2) == 1.0


def test_Points2d_scalarVector() -> None:
    p1 = Point2d(1, 2)
    p2 = 2 * p1
    assert p2.x == 2
    assert p2.y == 4

    p3 = p2 * 2
    assert p3.x == 4
    assert p3.y == 8


def test_Node2d_properties() -> None:
    node = Node2d(101, 2.3, 4)

    assert node.x == 101
    assert node.y == 2.3
    assert node.idn == 4

    node.x = 1
    node.y = 2
    node.idn = 1

    assert node.x == 1
    assert node.y == 2
    assert node.idn == 1

    node = Node2d()
    assert node.x == 0.0
    assert node.y == 0.0
    assert node.idn == -1


def test_Polyline2d_properties() -> None:
    n1 = Node2d(0.0, 0.0, 1)
    n2 = Node2d(300.0, 0.0, 2)
    n3 = Node2d(300.0, 500.0, 3)
    n4 = Node2d(0.0, 500.0, 4)

    with pytest.raises(TypeError):
        Polyline2d([n1, n2], 2, 3)

    Polyline2d([n1, n2, n3, n4])


def test_Polyline2d_methods() -> None:
    nodesLst = [
        Node2d(0.0, 0.0, 1),
        Node2d(300.0, 0.0, 2),
        Node2d(300.0, 500.0, 3),
        Node2d(0.0, 500.0, 4),
    ]
    poly2 = Polyline2d(nodesLst)

    assert poly2.size() == 4
    assert not poly2.isClosed()

    poly2.setClosed()
    assert poly2.size() == 5
    assert poly2.isClosed()


def test_Edge2d_properties() -> None:
    n1 = Node2d(0.0, 0.0, 1)
    n2 = Node2d(300.0, 0.0, 2)

    with pytest.raises(TypeError):
        Edge2d(n1)

    with pytest.raises(TypeError):
        Edge2d(n1, 1)

    edge1 = Edge2d(n1, n2)

    ni = edge1.nodeI()
    nj = edge1.nodeJ()

    assert ni.x == 0.0
    assert ni.y == 0.0
    assert ni.idn == 1

    assert nj.x == 300.0
    assert nj.y == 0.0
    assert nj.idn == 2


def test_Node3d_properties() -> None:
    node = Node3d(1, 2, 3, 4)

    assert node.x == 1
    assert node.y == 2
    assert node.z == 3
    assert node.idn == 4

    node = Node3d()

    assert node.x == 0.0
    assert node.y == 0.0
    assert node.z == 0.0
    assert node.idn == -1


def test_Edge3d_properties() -> None:
    edge1 = Edge3d(Node3d(1, 1, 1, 1), Node3d(2, 3, 3, 3))
    edge2 = Edge3d(Node3d(1, 3, 3, 3), Node3d(2, 3, 3, 0))

    assert edge1.nodeI().x == 1
    assert edge1.nodeI().y == 1
    assert edge1.nodeI().z == 1
    assert edge1.nodeI().idn == 1

    assert edge1.nodeJ().x == 2
    assert edge1.nodeJ().y == 3
    assert edge1.nodeJ().z == 3
    assert edge1.nodeJ().idn == 3

    assert edge2.nodeI().x == 1
    assert edge2.nodeI().y == 3
    assert edge2.nodeI().z == 3
    assert edge2.nodeI().idn == 3

    assert edge2.nodeJ().x == 2
    assert edge2.nodeJ().y == 3
    assert edge2.nodeJ().z == 3
    assert edge2.nodeJ().idn == 0


def test_Vector2d_properties() -> None:
    v = Vector2d(vx=1.0, vy=2.0)
    assert v.vx == 1.0
    assert v.vy == 2.0

    v = Vector2d(vx=1, vy=2)
    assert v.vx == 1
    assert v.vy == 2

    v = Vector2d(vx=1, vy=2.0)
    assert v.vx == 1
    assert v.vy == 2

    p1 = Point2d(1, 1)
    p2 = Point2d(2, 3)
    v = Vector2d(p1, p2)
    assert v.vx == 1
    assert v.vy == 2

    v = Vector2d()
    assert v.vx == 0.0
    assert v.vy == 0.0

    with pytest.raises(TypeError):
        Vector2d(1, 2, 3)

    with pytest.raises(TypeError):
        Vector2d(1)

    with pytest.raises(TypeError):
        Vector2d(1, Point2d())


def test_Vector3d_properties() -> None:
    v = Vector3d(1.0, 2.0, 3.0)
    assert v.vx == 1.0
    assert v.vy == 2.0
    assert v.vz == 3.0

    v = Vector3d(1, 2, 3)
    assert v.vx == 1
    assert v.vy == 2
    assert v.vz == 3

    p1 = Point3d(1, 1, 1)
    p2 = Point3d(2, 3, 4)
    v = Vector3d(p1, p2)
    assert v.vx == 1
    assert v.vy == 2
    assert v.vz == 3

    v = Vector3d()
    assert v.vx == 0.0
    assert v.vy == 0.0
    assert v.vz == 0.0


def test_MidPoint_2D() -> None:
    v0 = Point2d(0.0, 0.0)
    v1 = Point2d(1.0, 0.0)
    assert v0.midpoint(v1).x == 0.5
    assert v0.midpoint(v1).y == 0.0


def test_AreaFromTria_2D() -> None:
    v0 = Point2d(0.0, 0.0)
    v1 = Point2d(1.0, 0.0)
    v2 = Point2d(0.5, 1.0)
    assert Point2d.areaFromTria(v0, v1, v2) == v0.distance(v1) * v0.midpoint(v1).distance(v2) / 2


def test_AreaFromTria_3D() -> None:
    v0 = Point2d(0.0, 0.0)
    v1 = Point2d(1.0, 0.0)
    v2 = Point2d(0.5, 1.0)
    area2D = Point2d.areaFromTria(v0, v1, v2)

    p0 = Point3d(0.0, 0.0, 2.0)
    p1 = Point3d(1.0, 0.0, 2.0)
    p2 = Point3d(0.5, 1.0, 2.0)
    area3D_1 = areaFromTria3D(p0, p1, p2)

    assert area2D == area3D_1

    p0 = Point3d(0.0, 2.0, 0.0)
    p1 = Point3d(1.0, 2.0, 0.0)
    p2 = Point3d(0.5, 2.0, 1.0)
    area3D_2 = areaFromTria3D(p0, p1, p2)

    assert area2D == area3D_2


def test_vector_rotate() -> None:
    v1 = Vector2d(Point2d(0, 0), Point2d(5, 5))
    v2 = copy.deepcopy(v1).rotate(90)
    assert v2.vx == pytest.approx(-5)
    assert v2.vy == pytest.approx(+5)

    assert v1.normalize().cross(v2.normalize()) == pytest.approx(1)


def test_sum_affine() -> None:
    p = Point2d(1, 1)
    v = Vector2d(vx=2, vy=3)
    psum = affineSum2d(p, v)
    assert psum.x == 3
    assert psum.y == 4


def test_points_divide() -> None:
    p0 = Point2d(1, 1)
    p1 = Point2d(2, 2)

    with pytest.raises(ValueError):
        twoPointsDivide(p0, p1, 0)

    arr1 = twoPointsDivide(p0, p1, 1)
    assert len(arr1) == 2
    assert arr1[0] == p0
    assert arr1[1] == p1

    arr2 = twoPointsDivide(p0, p1, 4)
    assert len(arr2) == 5
    assert arr2[0] == p0
    assert arr2[1] == Point2d(1.25, 1.25)
    assert arr2[2] == Point2d(1.50, 1.50)
    assert arr2[3] == Point2d(1.75, 1.75)
    assert arr2[4] == p1


def test_points_offset() -> None:
    p0 = Point2d(1, 1)
    p1 = Point2d(1, 2)
    pp0, pp1 = twoPointsOffset(p0, p1, 10)
    assert pp0.x == pytest.approx(Point2d(-9, 1).x)
    assert pp0.y == pytest.approx(Point2d(-9, 1).y)
    assert pp1.x == pytest.approx(Point2d(-9, 2).x)
    assert pp1.y == pytest.approx(Point2d(-9, 2).y)
