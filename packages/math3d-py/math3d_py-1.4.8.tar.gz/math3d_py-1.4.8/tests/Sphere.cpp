#include "gtest/gtest.h"
#include "3dmath/Vector.h"
#include "TestSupport.h"
#include "support/PrimitivesTestSupport.h"
#include <algorithm>
#include <vector>

using namespace math3d::test;
using namespace math3d;
using namespace math3d::types;
using namespace math3d::constants;

// This is a hack to get the asString symbol included in the test executable
// Making this symbol available allows lldb to call this function to help in debugging
// asString outputs vector in a format that can be consumed by octave
namespace {
    Vector3D dummyVector;
    auto dummyStr = dummyVector.asString();
}

TEST(Sphere, Getters) {
    Sphere sphere({10.f, 10.f, 10.f}, 10.f);
    ASSERT_FLOAT_EQ(sphere.getRadius(), 10) << "Sphere radius is incorrect";
    ASSERT_FLOAT_EQ(sphere.getCenter().x, 10.f) << "Sphere center is incorrect";
    ASSERT_FLOAT_EQ(sphere.getCenter().y, 10.f) << "Sphere center is incorrect";
    ASSERT_FLOAT_EQ(sphere.getCenter().z, 10.f) << "Sphere center is incorrect";
    ASSERT_FLOAT_EQ(sphere.getResolution(), 16) << "Sphere resolution is wrong";
}


TEST(Sphere, GeometryGenerationVertices) {
    Sphere sphere({0.f, 0.f, 0.f}, 10.f);
    sphere.generateGeometry();
    auto resolution = sphere.getResolution();
    ASSERT_EQ(sphere.getVertices().size(), resolution * (resolution - 1) + 2) << "Number of vertices in the sphere is wrong";
}

TEST(Sphere, GeometryGenerationConnectivity) {
    Sphere sphere({10.f, 10.f, 10.f}, 10.f, 3);
    sphere.generateGeometry();
    auto resolution = sphere.getResolution();
    auto numCircles = resolution - 1;
    auto numQuadsBetweenTwoCircles = resolution;
    auto numTrisPoles = 2 * resolution;
    auto numTris =  numTrisPoles + ((numCircles - 1) * numQuadsBetweenTwoCircles * 2);
    ASSERT_EQ(sphere.getTris().size(), numTris) << "Number of triangles in the sphere is wrong";
    auto vertexPole1 = std::get<0>(sphere.getTris().at(0));
    auto vertexPole2= std::get<2>(sphere.getTris().at(numTris-1));
    std::vector<unsigned> verticesBetweenPole1AndCircle1{0, 1, 2, 3};
    ASSERT_TRUE(std::any_of(verticesBetweenPole1AndCircle1.begin(), verticesBetweenPole1AndCircle1.end(),
                            [vertexPole1](auto elem) { return elem == vertexPole1; })) << "Pole 1 vertex is wrong";
    std::vector<unsigned> verticesBetweenPole2AndCircle2{4, 5, 6, 7};
    ASSERT_TRUE(std::any_of(verticesBetweenPole2AndCircle2.begin(), verticesBetweenPole2AndCircle2.end(),
                            [vertexPole2](auto elem) { return elem == vertexPole2; })) << "Pole 2 vertex is wrong";
    std::remove_reference_t<decltype(sphere.getTris())> trisBetweenCircle1AndCircle2(sphere.getTris().begin() + 3, sphere.getTris().begin() + 9);
    std::vector<unsigned> verticesBetweenCircle1AndCircle2{1, 2, 3, 4, 5, 6};
    for (auto& tri : trisBetweenCircle1AndCircle2) {
        ASSERT_TRUE(std::any_of(verticesBetweenCircle1AndCircle2.begin(), verticesBetweenCircle1AndCircle2.end(),
                                [&tri](auto vertexIndex) { return std::get<0>(tri) == vertexIndex; }));
        ASSERT_TRUE(std::any_of(verticesBetweenCircle1AndCircle2.begin(), verticesBetweenCircle1AndCircle2.end(),
                                [&tri](auto vertexIndex) { return std::get<1>(tri) == vertexIndex; }));
        ASSERT_TRUE(std::any_of(verticesBetweenCircle1AndCircle2.begin(), verticesBetweenCircle1AndCircle2.end(),
                                [&tri](auto vertexIndex) { return std::get<2>(tri) == vertexIndex; }));
    }
}

TEST(Sphere, STLOutput) {
    auto baselinePath = std::filesystem::path(__FILE__).parent_path() / "baseline";
    Sphere {{10, 10, 10}, 10, 16}.writeToFile("Sphere.stl");
    ASSERT_TRUE(
            test::TestSupport::areBinarySTLFilesEqual(
                    "Sphere.stl", baselinePath/"Sphere.stl")) << "Geometry in STL file is different";
}

TEST(Sphere, OBJOutput) {
    auto baselinePath = std::filesystem::path(__FILE__).parent_path() / "baseline";
    Sphere {{10, 10, 10}, 10, 16}.writeToFile("Sphere.obj");
    ASSERT_TRUE(
            test::TestSupport::areFilesEqual(
                    "Sphere.obj",
                    baselinePath/"Sphere.obj")) << "Geometry in OBJ file is different";
}

TEST(Sphere, RayIntersectionRayOriginInsideSphere) {
    auto sphere = Sphere(Utilities::RandomPoint() , fabs(Utilities::RandomNumber()));
    for (auto i = 0; i < test::TestSupport::numberOfSamplesForRobustnessTest; ++i) {
        auto result = sphere.intersectWithRay(
                {PrimitivesTestSupport::getPointRelativeToSphere(sphere, PrimitivesTestSupport::Containment::Inside),
                   Utilities::RandomVector()});
        ASSERT_EQ(result.status, IntersectionStatus::Intersects) << "All rays from within the sphere should intersect the sphere";
        ASSERT_FLOAT_EQ(
                Utilities::distanceBetween(result.intersectionPoint, sphere.getCenter()),
                sphere.getRadius()) << "Intersection point must be on the sphere";
    }
}

TEST(Sphere, RayIntersectionRayOriginOutsideSphereNoIntersection) {
    auto sphereRadius = fabs(Utilities::RandomNumber());
    types::Point3D sphereCenter = Utilities::RandomVector();
    auto sphere = Sphere(sphereCenter, sphereRadius);
    unsigned numValidTests = 0;
    while (numValidTests < TestSupport::numberOfSamplesForRobustnessTest) {
        types::Vector3D randomDirection = Utilities::RandomVector();
        auto ray = Ray{PrimitivesTestSupport::getPointRelativeToSphere(sphere, PrimitivesTestSupport::Containment::Outside),
                       Utilities::RandomVector()};
        auto rayOriginToSphereCenter = (sphereCenter - ray.getOrigin());
        auto proj = rayOriginToSphereCenter.dot(ray.getDirection());
        auto distanceToRaySqr = rayOriginToSphereCenter.lengthSquared() - (proj * proj);
        if (distanceToRaySqr > sphereRadius*sphereRadius) {
            auto result = sphere.intersectWithRay(ray);
            ASSERT_EQ(result.status, IntersectionStatus::NoIntersection) << "Invalid intersection";
            ++numValidTests;
        }
    }
}

TEST(Sphere, RayIntersectionRayOriginOutsideSphereIntersection) {
    auto sphereRadius = fabs(Utilities::RandomNumber());
    Point3D sphereCenter = Utilities::RandomPoint();
    auto sphere = Sphere(sphereCenter, sphereRadius);
    auto numValidTests = 0;
    while (numValidTests < TestSupport::numberOfSamplesForRobustnessTest) {
        auto ray = Ray(PrimitivesTestSupport::getPointRelativeToSphere(sphere, PrimitivesTestSupport::Containment::Outside), Utilities::RandomVector());
        auto projection = ray.getDirection().dot( sphereCenter - ray.getOrigin());
        auto shortestDistance = sqrt((sphereCenter - ray.getOrigin()).lengthSquared() - (projection*projection));
        // If the ray origin is outside the sphere, intersection is only possible when the sphere is in front of the ray
        // origin and the distance between the sphere center and the ray is below the sphere radius
        if (projection > 0 && shortestDistance < sphereRadius) {
            auto result = sphere.intersectWithRay(ray);
            ASSERT_EQ(result.status, IntersectionStatus::Intersects) << "Intersection expected";
            ASSERT_FLOAT_EQ(
                    Utilities::distanceBetween(result.intersectionPoint, sphereCenter),
                    sphereRadius) << "Intersection point has to be on the sphere";
            ++numValidTests;
        }
    }
}

TEST(Sphere, RayIntersectionRayOriginOnSphere) {
    auto sphereRadius = fabs(Utilities::RandomNumber());
    types::Point3D sphereCenter = Utilities::RandomVector();
    auto sphere = Sphere(sphereCenter, sphereRadius);
    for (auto i = 0; i < test::TestSupport::numberOfSamplesForRobustnessTest; ++i) {
        types::Vector3D randomDirection = Utilities::RandomVector();
        auto rayOrigin = PrimitivesTestSupport::getPointRelativeToSphere(sphere, PrimitivesTestSupport::Containment::On);
        auto rayDirection = Utilities::RandomVector();;
        auto result = sphere.intersectWithRay({rayOrigin, rayDirection});
        ASSERT_EQ(result.status, IntersectionStatus::Intersects) << "Intersection expected when ray origin is on the sphere";
        ASSERT_FLOAT_EQ(
                Utilities::distanceBetween(result.intersectionPoint, sphereCenter),
                sphereRadius) << "Intersection point has to be on the sphere";
        ASSERT_FLOAT_EQ(
                Utilities::distanceBetween(result.intersectionPoint, rayOrigin),
                0) << "Intersection point and ray origin have to match";
    }
}
