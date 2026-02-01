import random

import pytest

import math3d
from math3d import Vector3, Vector4, AABB, Extent, Matrix4, Identity4


def test_bounds_transform():
    x: Extent = Extent(-10, 10)
    y: Extent = Extent(-10, 10)
    z: Extent = Extent(-10, 10)
    bounds: AABB = AABB(x, y, z)
    transform: Matrix4 = Identity4()
    transformed_bounds = bounds.transform(transform)
    assert (transformed_bounds.min - bounds.min).length_sqr() == 0
    assert (transformed_bounds.max - bounds.max).length_sqr() == 0

    # a : Vector3 = Vector3(random.random(), random.random(), random.random())
    # a.normalize()
    # another: Vector3 = Vector3(random.random(), random.random(), random.random())
    # b: Vector3 = a * another
    # b.normalize()
    # c: Vector3 = a * b
    # c.normalize()
    # # TODO: Simplify Matrix constructors
    # transform =  Matrix4([a.x, a.y, a.z, 0,
    #                       b.x, b.y, b.z, 0,
    #                       c.x, c.y, c,z, 0,
    #                       10, 10, 10, 1], math3d.col_major)
    # print(f'Transform = {transform}')
    # transformed_bounds = bounds.transform(transform)
