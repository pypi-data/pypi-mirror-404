#include "3dmath/primitives/Triangle.h"

#include <algorithm>

#include "gtest/gtest.h"
#include "3dmath/Utilities.h"
#include <ranges>

using namespace math3d;

TEST(Triangle, CrossProductBasedArea) {
    Triangle tri { Utilities::RandomPoint{}, Utilities::RandomPoint{}, Utilities::RandomPoint{} };
    auto [a, b, c] = tri.getPoints();
    auto ab = b - a;
    auto ac = c - a;
    auto theta = atan2((ab * ac).length(), ab.dot(ac));
    auto base = ab.length();
    auto height = ac.length() * sin(theta);
    ASSERT_NEAR(0.5 * base * height, tri.getArea(), constants::tolerance);
    ASSERT_NEAR(0.5 * (ab * ac).length(), tri.getArea(), constants::tolerance);
}

TEST(Triangle, PointContainment) {
    size_t constexpr numTestRuns {10};
    for (size_t i = 0; i < numTestRuns; ++i) {
        Triangle tri { Utilities::RandomPoint{}, Utilities::RandomPoint{}, Utilities::RandomPoint{} };
        auto [a, b, c] = tri.getPoints();
        ASSERT_TRUE(
            tri.isPointInTriangle(a) &&
            tri.isPointInTriangle(b) &&
            tri.isPointInTriangle(c)) << "Triangle vertex incorrectly classified as outside the triangle";
    }
    for (size_t i = 0; i < numTestRuns; ++i) {
        Vector3<double> weights {Utilities::RandomVector{/*positiveComponents=*/true} };
        double sum{};
        std::ranges::for_each(weights, [&](double const weight) {
            sum += weight;
        });
        std::ranges::for_each(weights, [&](double& weight) {
            weight /= sum;
        });
        Triangle tri { Utilities::RandomPoint{}, Utilities::RandomPoint{}, Utilities::RandomPoint{} };
        Vector3<double> pointInTri;
        for (auto index = 0; index < 3; ++index) {
            pointInTri += tri.getPoints()[index] * weights[index];
        }
        ASSERT_TRUE(tri.isPointInTriangle(pointInTri))
            << "Convex barycentric combination of triangle vertices cannot be outside the triangle";
    }
    for (size_t i = 0; i < numTestRuns; ++i) {
        Vector3<double> pointOutsideTri;
        double u = Utilities::RandomNumber{0.0, 1.0 - constants::tolerance};
        double v = u - 1;
        double w = 1 - u - v;
        Vector3 nonConvexWeights {u, v, w};
        Triangle tri { Utilities::RandomPoint{}, Utilities::RandomPoint{}, Utilities::RandomPoint{} };
        for (auto index = 0; index < 3; ++index) {
            pointOutsideTri += nonConvexWeights[index] * tri.getPoints()[index];
        }
        ASSERT_NEAR(tri.getDistanceToPoint(pointOutsideTri), 0, constants::tolerance)
            << "Sanity check failed. Point weights are not barycentric";
        ASSERT_FALSE(tri.isPointInTriangle(pointOutsideTri))
            << "Only convex barycentric combinations of triangle vertices can be inside the triangle";
    }
}

TEST(Triangle, BaryCentricCoordinates) {
    for (int i = 0; i < 10; ++i) {
        Triangle tri { Utilities::RandomPoint{}, Utilities::RandomPoint{}, Utilities::RandomPoint{} };
        auto [a, b, c] = tri.getPoints();
        auto barycentricCoordinates = tri.getBarycentricCoordinates(a);
        ASSERT_NEAR(0, barycentricCoordinates.x, constants::tolerance);
        barycentricCoordinates = tri.getBarycentricCoordinates(b);
        ASSERT_NEAR(0, barycentricCoordinates.y, constants::tolerance);
        barycentricCoordinates = tri.getBarycentricCoordinates(c);
        ASSERT_NEAR(0, barycentricCoordinates.z, constants::tolerance);
    }
}