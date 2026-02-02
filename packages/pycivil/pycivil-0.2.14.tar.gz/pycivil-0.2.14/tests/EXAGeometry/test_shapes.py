# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

"""
Tests for EXAGeometry.shapes module

@author: lpaone
"""
import pytest

from pycivil.EXAGeometry.geometry import (
    Edge3d,
    Node2d,
    Node3d,
    Point2d,
    Point3d,
    Polyline2d,
)
from pycivil.EXAGeometry.shapes import Frame, ShapeCircle, ShapePoly


def test_Frame_with_ShapePoly() -> None:
    nodesLst = [
        Node2d(0.0, 0.0, 1),
        Node2d(300.0, 0.0, 2),
        Node2d(300.0, 500.0, 3),
        Node2d(0.0, 500.0, 4),
    ]
    poly = Polyline2d(nodesLst)
    shape = ShapePoly(poly)

    edge1 = Edge3d(Node3d(1, 1, 1, 1), Node3d(2, 3, 3, 3))
    frame1 = Frame(edge1)

    frame1.setShape(shape)

    # Build a normal frame
    n1 = Node3d(1.0, 1.0, 1.0, 1)
    n2 = Node3d(6.0, 6.0, 6.0, 2)

    axis = Edge3d(n1, n2)

    frame_typical = Frame(axis)

    frame_typical.setReference(Point3d(1.0, 1.0, 0.0))
    frame_typical.setReference(1.0, 1.0, 0.0)

    # Polygonar
    secPoly = ShapePoly(0.0, 0.0, 1, 300.0, 0.0, 2, 300.0, 500.0, 3, 0.0, 500.0, 4)

    frame_typical.setShape(secPoly)

    secPoly.translate(Point2d(150.0, 250.0), Point2d(0.0, 0.0))

    axis = Edge3d(1.0, 1.0, 1.0, 1, 6.0, 6.0, 6.0, 2)

    frame_typical = Frame(100.0, 100.0, 100.0, 1, 600.0, 600.0, 600.0, 2)
    frame_typical.setReference(100.0, 100.0, 0.0)
    frame_typical.setShape(secPoly)

    frame_typical2 = Frame(15.0, 25.0, 35.0, 1, 60.0, 70.0, 90.0, 2)
    frame_typical2.setReference(15.0, 25.0, 10.0)
    frame_typical2.setShape(secPoly)


def test_Frame_properties() -> None:
    edge1 = Edge3d(Node3d(1, 1, 1, 1), Node3d(2, 3, 3, 3))
    edge2 = Edge3d(Node3d(1, 3, 3, 3), Node3d(2, 3, 3, 0))

    Frame(edge1)
    Frame(edge2)

    with pytest.raises(TypeError):
        Frame(1)

    with pytest.raises(TypeError):
        Frame(1, 1)


def test_ShapePoly_properties() -> None:
    nodesLst = [
        Node2d(0.0, 0.0, 1),
        Node2d(300.0, 0.0, 2),
        Node2d(300.0, 500.0, 3),
        Node2d(0.0, 500.0, 4),
    ]
    poly = Polyline2d(nodesLst)

    ShapePoly(poly)


def test_ShapeCircle_properties() -> None:
    # First constructor
    shape1 = ShapeCircle(20, 100, 200)
    assert shape1.getRadius() == 20
    assert shape1.getShapePoint("O").x == 100
    assert shape1.getShapePoint("O").y == 200

    # Second constructor
    shape2 = ShapeCircle(20, center=Point2d(101, 201))
    assert shape2.getRadius() == 20
    assert shape2.getShapePoint("O").x == 101
    assert shape2.getShapePoint("O").y == 201
