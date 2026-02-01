from math3d import Vector3, Triangle
import random

NUM_TEST_RUNS = 10
TOLERANCE = 1e-6


def test_distance_to_point():
    for _ in range(NUM_TEST_RUNS):
        a : Vector3 = Vector3([random.random() * 10 for _ in range(3)])
        b : Vector3 = Vector3([random.random() * 10 for _ in range(3)])
        c : Vector3 = Vector3([random.random() * 10 for _ in range(3)])
        # Fix points to z = 10 plane
        a.z = 10
        b.z = 10
        c.z = 10
        # Tri on XY plane
        tri : Triangle = Triangle(a, b, c)

        # Compose a point inside the tri via convex barycentric coordinates
        u = random.random()
        v = (1 - u) * 0.5
        w = 1 - u - v
        assert abs(u + w + v - 1) < TOLERANCE
        assert u >= -TOLERANCE and v >= -TOLERANCE and w >= -TOLERANCE
        pt : Vector3 = u * tri.points[0] + v * tri.points[1] + w * tri.points[2]
        assert tri.distance(pt) < TOLERANCE
        # Point is on the plane of the triangle, distance must be 0
        assert tri.contains(pt)

        # Compose non-convex barycentric combination
        u = random.uniform(TOLERANCE, 1)
        v = u - 1
        w = 1 - u - v
        assert abs(u + w + v - 1) < TOLERANCE
        assert u <= -TOLERANCE or v <= -TOLERANCE or w <= -TOLERANCE

        pt : Vector3 = u * tri.points[0] + v * tri.points[1] + w * tri.points[2]
        assert not tri.contains(pt)
        # Point is still on the plane of the triangle, distance must be 0
        assert tri.distance(pt) < TOLERANCE

        # Move to point to a z = 20 plane from z = 11
        pt.z = 20
        # Perpendicular distance must be 10 since the point is 10 units away along the plane normal
        # NOTE: Distance is signed, +ve values imply
        assert abs(tri.distance(pt) - 10) < TOLERANCE


