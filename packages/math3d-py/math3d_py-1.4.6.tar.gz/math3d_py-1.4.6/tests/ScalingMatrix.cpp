#include "gtest/gtest.h"
#include "3dmath/ScalingMatrix.h"
#include "3dmath/Utilities.h"
#include <iostream>
using namespace std;
using namespace math3d;

TEST(ScalingMatrix, ScaleXYZ) {
    ScalingMatrix<float> scaleMatrix {5, 10, 15};
    ASSERT_FLOAT_EQ(scaleMatrix(0,0), 5);
    ASSERT_FLOAT_EQ(scaleMatrix(1,1), 10);
    ASSERT_FLOAT_EQ(scaleMatrix(2,2), 15);
    for (auto i = 0u; i < 4; ++i) {
        for (auto j = 0u; j < 4; ++j) {
            if (i != j) {
                ASSERT_FLOAT_EQ(scaleMatrix(i,j), i==3 && j == 3 ? 1.f : 0.f);
            }
        }
    }
}