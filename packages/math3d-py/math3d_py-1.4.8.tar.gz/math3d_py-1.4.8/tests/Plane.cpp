#include "gtest/gtest.h"
#include "3dmath/primitives/Plane.h"
#include "TestSupport.h"

constexpr unsigned robustnessTestSampleCount = 100;

TEST(Plane, Getters) {
    math3d::types::Point3D origin  = math3d::Utilities::RandomPoint();
    math3d::types::Vector3D normal = math3d::Utilities::RandomVector();
    math3d::Plane p{origin, normal};
    ASSERT_FLOAT_EQ(p.getOrigin().x, origin.x);
    ASSERT_FLOAT_EQ(p.getOrigin().y, origin.y);
    ASSERT_FLOAT_EQ(p.getOrigin().z, origin.z);
    // Normal should be normalized by the constructor
    ASSERT_FLOAT_EQ(p.getNormal().x, normal.normalize().x);
    ASSERT_FLOAT_EQ(p.getNormal().y, normal.normalize().y);
    ASSERT_FLOAT_EQ(p.getNormal().z, normal.normalize().z);

}

TEST(Plane, GeometryGeneration) {
    math3d::Plane {math3d::constants::origin,
                   math3d::constants::xAxis}.writeToFile("Yz.stl");
    math3d::Plane {math3d::constants::origin,
                   math3d::constants::yAxis}.writeToFile("Xz.stl");
    math3d::Plane {math3d::constants::origin,
                   math3d::constants::zAxis}.writeToFile("Xy.stl");
    auto baselinePath = std::filesystem::path(__FILE__).parent_path() / "baseline";
    for (auto& fileName : { "Xy.stl", "Xz.stl", "Yz.stl"}) {
        ASSERT_TRUE(
                math3d::test::TestSupport::areBinarySTLFilesEqual(
                        fileName, baselinePath / fileName)) << "Geometry in STL file is different";
    }
}

TEST(Plane, PointProjection) {
    for (auto sample = 1u; sample <= robustnessTestSampleCount; ++sample) {
        math3d::types::Point3D pointInSpace = math3d::Utilities::RandomPoint();
        math3d::types::Point3D planeOrigin = math3d::Utilities::RandomPoint();
        math3d::types::Vector3D planeNormal = math3d::Utilities::RandomVector();
        auto plane = math3d::Plane{planeOrigin, planeNormal};
        auto projectedPoint = plane.getProjection(pointInSpace);
        auto planeVector = projectedPoint - planeOrigin;
        if (!math3d::Utilities::isZero(planeVector.dot(planeNormal))) {
            std::cerr << "Plane " << plane << " point " << pointInSpace << std::endl;
            std::cerr << "Projected point " << projectedPoint << std::endl;
            std::cerr << "Dot product = " << planeVector.dot(planeNormal) << std::endl;
            ASSERT_TRUE(false) << "Projection failure";
        }
    }
}

TEST(Plane, RayIntersection) {
    for (auto sample = 1u; sample <= robustnessTestSampleCount; ++sample) {
        math3d::Ray ray {math3d::Utilities::RandomPoint(), math3d::Utilities::RandomVector()};
        math3d::Plane plane {math3d::Utilities::RandomPoint(), math3d::Utilities::RandomVector()};
        auto result = plane.intersectWithRay(ray);
        if (result.status == math3d::IntersectionStatus::Intersects) {
            auto planeVector = result.intersectionPoint - plane.getOrigin();
            if (!math3d::Utilities::isZero(planeVector.dot(plane.getNormal()))) {
                std::cerr << "Plane: " << plane << " Ray: " << ray << std::endl;
                ASSERT_TRUE(false) << "Ray plane intersection failure";
            }
        }
    }
}

TEST(Plane, RayIntersectionEdgeCases) {
    // Ray is parallel and ray origin is not on the plane
    math3d::Plane plane1 {math3d::constants::origin, math3d::constants::yAxis};
    math3d::Ray ray1 {math3d::types::Vector3D{math3d::constants::origin} + math3d::types::Point3D{0, 5, 0},
                      math3d::constants::xAxis};
    ASSERT_EQ(plane1.intersectWithRay(ray1).status, math3d::IntersectionStatus::NoIntersection);

    // Ray is parallel and ray origin is on the plane
    math3d::Ray ray2 {math3d::types::Vector3D{math3d::constants::origin},
                      math3d::constants::xAxis};
    auto result1 = plane1.intersectWithRay(ray2);
    ASSERT_EQ(result1.status, math3d::IntersectionStatus::Intersects);
    ASSERT_FLOAT_EQ(result1.intersectionPoint.x, 0);
    ASSERT_FLOAT_EQ(result1.intersectionPoint.y, 0);
    ASSERT_FLOAT_EQ(result1.intersectionPoint.z, 0);

    // Ray is not parallel and the ray origin is on the plane
    math3d::Plane plane2 {math3d::Utilities::RandomPoint(), math3d::Utilities::RandomVector()};
    math3d::Ray ray3 {plane2.getOrigin(), math3d::Utilities::RandomVector()};

    auto result2 = plane2.intersectWithRay(ray3);
    ASSERT_EQ(result2.status, math3d::IntersectionStatus::Intersects);
    ASSERT_FLOAT_EQ(result2.intersectionPoint.x, ray3.getOrigin().x);
    ASSERT_FLOAT_EQ(result2.intersectionPoint.y, ray3.getOrigin().y);
    ASSERT_FLOAT_EQ(result2.intersectionPoint.z, ray3.getOrigin().z);
}

TEST(Plane, DistanceToPoint) {
    using namespace math3d;
    auto constexpr numTestRuns{10U};
    auto plane = Plane(Utilities::RandomPoint{}, Utilities::RandomVector{});
    auto planeAxisX = Utilities::getPerpendicular(plane.getNormal());
    auto planeAxisY = planeAxisX * plane.getNormal();
    planeAxisX.normalize();
    planeAxisY.normalize();
    for (size_t i = 0; i < numTestRuns; ++i) {
        double xLength = Utilities::RandomNumber{}, yLength = Utilities::RandomNumber{};
        auto planePoint = plane.getOrigin() + xLength * planeAxisX + yLength * planeAxisY;
        ASSERT_NEAR(0, plane.getDistanceToPoint(planePoint), math3d::constants::tolerance);
    }
}