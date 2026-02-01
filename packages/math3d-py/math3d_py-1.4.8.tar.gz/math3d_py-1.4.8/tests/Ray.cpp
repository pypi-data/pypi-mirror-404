#include "gtest/gtest.h"
#include "3dmath/primitives/Ray.h"
#include "TestSupport.h"

TEST(Ray, PerpendicularDistanceToPoint) {
    // Same direction
    math3d::Ray r({0,0,0}, {1,0,0});
    ASSERT_FLOAT_EQ(10, r.distanceToPoint({10, 10, 0}));

    // Different direction
    ASSERT_FLOAT_EQ(10, r.distanceToPoint({-10, -10, 0}));

    // Special cases:
}

TEST(Ray, DistanceToPointOnDifferentPlane) {

}

TEST(Ray, RayIntersectionParallel) {
    math3d::Ray r1(math3d::constants::origin, math3d::constants::xAxis);
    math3d::Ray r2({-5, 0, 0},math3d::constants::xAxis);
    ASSERT_TRUE(r1.intersectWithRay(r2).status == math3d::IntersectionStatus::NoIntersection);
}

TEST(Ray, RayIntersectionBehindOrigin) {
    math3d::Ray r1(math3d::constants::origin, math3d::constants::xAxis);
    math3d::Ray r2({-5, -5, 0},math3d::constants::yAxis);
    ASSERT_TRUE(r1.intersectWithRay(r2).status == math3d::IntersectionStatus::NoIntersection);
}

TEST(Ray, RayIntersectionForSkewRays) {
    math3d::types::Point3D origin{math3d::constants::origin};
    math3d::Ray r1(origin, {0.707, 0.707, 0});
    math3d::Ray r2(origin + math3d::types::Point3D{10, 0, 10}, {-0.707, 0.707, 0});
    ASSERT_TRUE(r1.intersectWithRay(r2).status == math3d::IntersectionStatus::Skew);
}

TEST(Ray, RayGeometry) {
    auto baselinePath = std::filesystem::path(__FILE__).parent_path() / "baseline";
    math3d::Ray r1(math3d::constants::origin, {0.707, 0.707, 0});
    r1.writeToFile("Ray.obj");
    ASSERT_TRUE(
            math3d::test::TestSupport::areFilesEqual(
                    "Ray.obj",
                    baselinePath/"Ray.obj")) << "Geometry in OBJ file is different";
}
