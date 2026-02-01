#include "gtest/gtest.h"
#include "3dmath/ProjectionMatrix.h"
#include "3dmath/OrthographicProjectionMatrix.h"
#include <iostream>
using namespace std;
using namespace math3d;

TEST(OrthographicProjectionMatrix, TransformsCorrectlyToLeftHandedOutputSystem) {
    auto projectionMatrix = OrthographicProjectionMatrix<float, math3d::CoordinateSystemHandedness::LeftHanded>();
    projectionMatrix.update({{-1.f, -1.f, -1.f}, {1.f, 1.f, 1.f}});
    auto data = projectionMatrix.getData();
    // Assert that z is inverted and the rest of the matrix is identity
    ASSERT_FLOAT_EQ(data[0],  1.f);
    ASSERT_FLOAT_EQ(data[5],  1.f);
    ASSERT_FLOAT_EQ(data[10], -1.f);
    ASSERT_FLOAT_EQ(data[15], 1.f);
    for (auto index : {1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14}) {
        ASSERT_FLOAT_EQ(data[index], 0.f);
    }
}

TEST(OrthographicProjectionMatrix, TransformsCorrectlyToRightHandedOutputSystem) {
    auto projectionMatrix = OrthographicProjectionMatrix<float, math3d::CoordinateSystemHandedness::RightHanded>();
    projectionMatrix.update({{-1.f, -1.f, -1.f}, {1.f, 1.f, 1.f}});
    auto data = projectionMatrix.getData();
    // Assert that z is inverted and the rest of the matrix is identity
    ASSERT_FLOAT_EQ(data[0],  1.f);
    ASSERT_FLOAT_EQ(data[5],  1.f);
    ASSERT_FLOAT_EQ(data[10], 1.f);
    ASSERT_FLOAT_EQ(data[15], 1.f);
    for (auto index : {1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14}) {
        ASSERT_FLOAT_EQ(data[index], 0.f);
    }
}

TEST(OrthographicProjectionMatrix, TransformsOffsetBoundingVolumesToLeftHandedSystemCorrectly) {
    Bounds3D<float> offsetBoundingBox {{-5.f, -5.f, 0.f}, {5.f, 5.f, 10.f}};
    auto projectionMatrix =
            OrthographicProjectionMatrix<float, math3d::CoordinateSystemHandedness::LeftHanded>{offsetBoundingBox};
    auto minClip = projectionMatrix * Vector4<float>{-5.f, -5.f, 0.f, 1.f};
    auto maxClip = projectionMatrix * Vector4<float>{5.f, 5.f, 10.f, 1.f};
    // Min eye coordinates of a right-handed system should map the lower left corner of the far plane in the left-handed
    // clip coordinates
    ASSERT_TRUE(Utilities::areEqual(minClip, {-1.f, -1.f, 1.f, 1.f})) << "Expected eye coordinate bounding volume's "
                                                                         "minimum extent to be mapped to lower left far "
                                                                         "corner of the left-handed clip coordinates";

    ASSERT_TRUE(Utilities::areEqual(maxClip, {1.f, 1.f, -1.f, 1.f})) << "Expected eye coordinate bounding volume's "
                                                                        "maximum extent to be mapped to upper right near "
                                                                        "corner of the left-handed clip coordinates";
}

TEST(OrthographicProjectionMatrix, TransformsOffsetBoundingVolumesToRightHandedSystemCorrectly) {
    Bounds3D<float> offsetBoundingBox {{-5.f, -5.f, 0.f}, {5.f, 5.f, 10.f}};
    auto projectionMatrix =
            OrthographicProjectionMatrix<float, math3d::CoordinateSystemHandedness::RightHanded>{offsetBoundingBox};
    auto minClip = projectionMatrix * Vector4<float>{-5.f, -5.f, 0.f, 1.f};
    auto maxClip = projectionMatrix * Vector4<float>{5.f, 5.f, 10.f, 1.f};
    // Min eye coordinates of a right-handed system should map the lower left corner of the far plane in the left-handed
    // clip coordinates
    ASSERT_TRUE(Utilities::areEqual(minClip, {-1.f, -1.f, -1.f, 1.f})) << "Expected eye coordinate bounding volume's "
                                                                         "minimum extent to be mapped to lower left far "
                                                                         "corner of the clip coordinates";

    ASSERT_TRUE(Utilities::areEqual(maxClip, {1.f, 1.f, 1.f, 1.f})) << "Expected eye coordinate bounding volume's "
                                                                        "maximum extent to be mapped to upper right near "
                                                                        "corner of the clip coordinates";
}

TEST(ProjectionMatrix, OrthographicProjectionMatrixWithInvalidBounds) {
    using LeftHandedOrthographicMatrix = OrthographicProjectionMatrix<float, math3d::CoordinateSystemHandedness::LeftHanded>;
    EXPECT_THROW({
         try {
             [[maybe_unused]]
             auto orthoMatrix = LeftHandedOrthographicMatrix ({{0,0}, {0,0}, {0,0}});
         } catch (std::runtime_error &ex) {
             throw;
         }
    }, std::runtime_error) << "Expected a runtime error when invalid bounds are specified";
}