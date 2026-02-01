#include "gtest/gtest.h"
#include "3dmath/Vector.h"
#include "3dmath/SupportingTypes.h"
#include <vector>
using namespace std;
using namespace math3d;

TEST(Extent, ConstructionAndGetters) {
    Extent<float> extent{10, 10};
    ASSERT_FLOAT_EQ(extent.min, 10);
    ASSERT_FLOAT_EQ(extent.max, 10);
    ASSERT_FLOAT_EQ(extent.length(), 0);
    ASSERT_FLOAT_EQ(extent.center(), 10);
}

TEST(Bounds3D, UninitializedBounds) {
    Bounds3D<float> bounds;
    ASSERT_FLOAT_EQ(bounds.x.min, numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.y.min, numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.y.min, numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.x.max, -numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.y.max, -numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.y.max, -numeric_limits<float>::max());
}

TEST(Bounds3D, InitializedBounds) {
    Bounds3D<float> bounds1{{-1,-1,-1},{+1,+1,+1}};
    ASSERT_FLOAT_EQ(bounds1.x.length(), 2);
    ASSERT_FLOAT_EQ(bounds1.y.length(), 2);
    ASSERT_FLOAT_EQ(bounds1.z.length(), 2);


    Bounds3D<float> bounds2d{{-1,-1},{+1,+1}};
    ASSERT_FLOAT_EQ(bounds2d.x.length(), 2);
    ASSERT_FLOAT_EQ(bounds2d.y.length(), 2);
}

TEST(Bounds3D, Getters) {
    Bounds3D<float> bounds{{-1,-1,-1},{+1,+1,+1}};
    ASSERT_FLOAT_EQ(bounds.center().x, 0.f);
    ASSERT_FLOAT_EQ(bounds.center().y, 0.f);
    ASSERT_FLOAT_EQ(bounds.center().z, 0.f);
    ASSERT_FLOAT_EQ(bounds.length(), 2*sqrt(3));
}

TEST(Bounds3D, SymmetricBounds) {
    Bounds3D<float> bounds(1.f);
    ASSERT_FLOAT_EQ(bounds.center().x, 0.f);
    ASSERT_FLOAT_EQ(bounds.center().y, 0.f);
    ASSERT_FLOAT_EQ(bounds.center().z, 0.f);
    ASSERT_FLOAT_EQ(bounds.x.length(), 1);
    ASSERT_FLOAT_EQ(bounds.y.length(), 1);
    ASSERT_FLOAT_EQ(bounds.z.length(), 1);
    ASSERT_FLOAT_EQ(bounds.x.min, -0.5);
    ASSERT_FLOAT_EQ(bounds.x.max, +0.5);
    ASSERT_FLOAT_EQ(bounds.y.min, -0.5);
    ASSERT_FLOAT_EQ(bounds.y.max, +0.5);
    ASSERT_FLOAT_EQ(bounds.z.min, -0.5);
    ASSERT_FLOAT_EQ(bounds.z.max, +0.5);
}

TEST(Bounds3D, Reset) {
    Bounds3D<float> bounds{{-1,-1,-1},{+1,+1,+1}};
    bounds.reset();
    ASSERT_FLOAT_EQ(bounds.x.min, +std::numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.x.max, -std::numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.y.min, +std::numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.y.max, -std::numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.z.min, +std::numeric_limits<float>::max());
    ASSERT_FLOAT_EQ(bounds.z.max, -std::numeric_limits<float>::max());
}


TEST(Bounds3D, Contains) {
    Bounds3D<float> bounds{{-1,-1,-1},{+1,+1,+1}};
    ASSERT_TRUE(bounds.contains({-1,-1,-1}));
    ASSERT_TRUE(bounds.contains({+1,+1,+1}));
    ASSERT_TRUE(bounds.contains({0,0,0}));
    ASSERT_FALSE(bounds.contains({-5, 0, 0}));
    ASSERT_FALSE(bounds.contains({0, -5, 0}));
    ASSERT_FALSE(bounds.contains({0, 0, -5}));
}

TEST(Bounds3D, ConstructFrom2DBounds) {
    Bounds3D<float> bounds{{-1,-1},{+1,+1}};
    ASSERT_FLOAT_EQ(bounds.z.length(), 0.f);
    ASSERT_FLOAT_EQ(bounds.x.length(), 2.f);
    ASSERT_FLOAT_EQ(bounds.y.length(), 2.f);
}

TEST(Bounds3D, UniformScaling) {
    Bounds3D<float> bounds{{-1, -1, -1},
                           {+1, +1, +1}};
    auto oldLength = bounds.length();
    bounds.scale(1.5f);
    ASSERT_FLOAT_EQ(bounds.length(), oldLength * 1.5f);
}

TEST(Bounds3D, NonUniformScaling) {
    Bounds3D<float> bounds{{-1, -1, -1},
                           {+1, +1, +1}};
    auto xLen = bounds.x.length();
    auto yLen = bounds.y.length();
    auto zLen = bounds.z.length();
    bounds.scale(1.5f, Bounds3D<float>::Direction::y);
    ASSERT_FLOAT_EQ(bounds.x.length(), xLen);
    ASSERT_FLOAT_EQ(bounds.y.length(), yLen*1.5f);
    ASSERT_FLOAT_EQ(bounds.z.length(), zLen);
    bounds.scale(1.5f, Bounds3D<float>::Direction::x);
    ASSERT_FLOAT_EQ(bounds.x.length(), xLen*1.5f);
    ASSERT_FLOAT_EQ(bounds.y.length(), yLen*1.5f);
    ASSERT_FLOAT_EQ(bounds.z.length(), zLen);
    bounds.scale(1.5f, Bounds3D<float>::Direction::z);
    ASSERT_FLOAT_EQ(bounds.x.length(), xLen*1.5f);
    ASSERT_FLOAT_EQ(bounds.y.length(), yLen*1.5f);
    ASSERT_FLOAT_EQ(bounds.z.length(), zLen*1.5f);
}

TEST(Bounds3D, Validity) {
    ASSERT_FALSE(Bounds3D<float>{}.isValid()) << "Uninitialized bounds should have been classified as invalid";
    Bounds3D<float> bounds{{-0.5, -0.5, -0.5},
                           {+0.5, +0.5, +0.5}};
    ASSERT_TRUE(bounds.isValid()) << "Bounds initialized with a unit cube must have been classified as valid";
}

TEST(Extent, Merging) {
    Extent e1 {-10.F, 0.F};
    Extent constexpr e2 {5.F, 10.F};
    e1.merge(e2);
    ASSERT_EQ(e1.min, -10.F);
    ASSERT_EQ(e1.max, 10.F);
}

TEST(Bounds, Merging) {
    Bounds3D smallerBounds {{-10, -10, -10}, {10, 10, 10}};
    Bounds3D const biggerBounds {{-100, -100, -100}, {100, 100, 100}};
    ASSERT_FALSE(smallerBounds.contains({-100, -100, -100}));
    smallerBounds.merge(biggerBounds);
    ASSERT_TRUE(smallerBounds.contains({-100, -100, -100}));
    ASSERT_TRUE(smallerBounds.contains({100, 100, 100}));

    Bounds3D boundsA {{-10, -10, -10}, { 10,  10,  10}};
    Bounds3D const boundsB {{-100,  -1,  -2}, {  5, 200,   3}};
    boundsA.merge(boundsB);
    ASSERT_NEAR((boundsA.min() - Vector3{-100, -10, -10}).lengthSquared(), 0, 1e-6);
    ASSERT_NEAR((boundsA.max() - Vector3{10, 200, 10}).lengthSquared(), 0, 1e-6);
}

TEST(Bounds, Corners) {
    Bounds3D const bounds {{-10, -10, -10}, { 10,  10,  10}};
    auto const corners = bounds.corners();
    ASSERT_EQ((bounds.min() - corners.at(0)).lengthSquared(), 0);
    ASSERT_EQ(((bounds.min() + Vector3{bounds.x.length(), bounds.y.length(), 0}) - corners.at(2)).lengthSquared(), 0);
    ASSERT_EQ((bounds.max() - corners.at(6)).lengthSquared(), 0);
    ASSERT_EQ(((bounds.max() - Vector3{bounds.x.length(), bounds.y.length(), 0}) - corners.at(4)).lengthSquared(), 0);
}

TEST(Bounds, Remap) {
    Bounds3D<float> const boundsA {{-10, -10, -10}, { 10,  10,  10}};
    Bounds3D<float> const boundsB {{-1, -1, -1}, { 1,  1,  1}};
    Remapper const remapper {boundsA, boundsB};
    ASSERT_TRUE(Utilities::areEqual(remapper({-10, -10, -10}), {-1, -1, -1}));
    ASSERT_TRUE(Utilities::areEqual(remapper({10, 10, 10}), {1, 1, 1}));
}