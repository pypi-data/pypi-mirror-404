#include "gtest/gtest.h"
#include "3dmath/LinearSystem.h"
#include "3dmath/Vector.h"
#include <chrono>
#include "3dmath/MatrixUtil.h"
using namespace std;
using namespace math3d;

TEST(LinearSystem, Identity) {
    Matrix<float, 3, 3> A {
        {1.f, 0.f, 0.f},
        {0.f, 1.f, 0.f},
        {0.f, 0.f, 1.f}
    };

    Vector<float, 3> b {21.f, 67.f, 16.f};

    Vector<float, 3> x = LinearSystem<float, 3>::solveLinearSystem(A, b);

    ASSERT_FLOAT_EQ(x[0], 21.f);
    ASSERT_FLOAT_EQ(x[1], 67.f);
    ASSERT_FLOAT_EQ(x[2], 16.f);
}

TEST(LinearSystem, UpperTriangular) {
    Matrix<float, 3, 3> A {
       {4.f, 5.f, 2.f},
       {0.f, 3.f, 8.f},
       {0.f, 0.f, 2.f}
    };

    Vector<float, 3> b {21.f, 67.f, 16.f};

    Vector<float, 3> x = LinearSystem<float, 3>::solveLinearSystem(A, b);

    ASSERT_FLOAT_EQ(x[0], 0.f);
    ASSERT_FLOAT_EQ(x[1], 1.f);
    ASSERT_FLOAT_EQ(x[2], 8.f);
}

TEST(LinearSystem, ThreeByThree) {
    Matrix<float, 3, 3> A {
        {0.4165,   0.9501,   0.1960},
        {0.2203,   0.4414,   0.6924},
        {0.9187,   0.4295,   0.6804}
    };

    Vector<float, 3> b {
        0.151307,
        0.073879,
        0.788695
    };

    Vector<float, 3> x = LinearSystem<float, 3>::solveLinearSystem(A, b);

    ASSERT_NEAR(x[0], +1.01808, 1e-4);
    ASSERT_NEAR(x[1], -0.278914, 1e-4);
    ASSERT_NEAR(x[2], -0.0394141, 1e-4);
}

TEST(LinearSystem, TenByTen) {
    Matrix<float, 10, 10> A {
        {83.9175, 2.1504, 44.7749, 97.7076, 38.5932, 54.4315, 34.3065, 14.5406, 40.2962, 14.1848},
        {41.8232, 48.6340, 64.1426, 89.6907, 14.3528, 80.3592, 14.8258, 41.3537, 72.4550, 42.1148},
        {40.1245, 26.5755, 29.3335, 32.8500, 49.9322, 74.2766, 3.3788, 20.5299, 85.6952, 31.9631},
        {51.7892, 40.3369, 60.9213, 34.9505, 57.1583, 94.8142, 2.3201, 75.2189, 69.3947, 93.7239},
        {93.2734, 26.1540, 44.1576, 21.1109, 67.7192, 20.2526, 41.0352, 61.9952, 58.6687, 45.1568},
        {81.5093, 97.6149, 15.9276, 61.1556, 13.9408, 41.4103, 33.0514, 75.2911, 5.3577, 39.2399},
        {80.3327, 88.8009, 49.8528, 92.4116, 77.2082, 34.8903, 65.0150, 21.7885, 22.8921, 5.1787},
        {99.9551, 7.5151, 47.3456, 97.2556, 55.9180, 5.8396, 8.2286, 24.5699, 65.5308, 55.9558},
        {83.4886, 29.0333, 77.2853, 39.1374, 32.8153, 67.5385, 11.4714, 58.2570, 27.6533, 62.1352},
        {57.3050, 94.9192, 13.2074, 19.5097, 25.4907, 5.3738, 32.9132, 49.3600, 79.1654, 32.0221}
    };
    Vector<float, 10> b {
       65.6284, 12.8682, 76.4991, 66.2634, 58.2422, 40.7078, 74.4473, 44.3651, 2.7081, 93.1322
    };

    Vector<float, 10> x = LinearSystem<float, 10>::solveLinearSystem(A, b);

    std::array<float, 10> expectedResult = {
        0.5709, 0.1570, -1.8675, -0.5550, -0.5475, 0.9204, 3.2058, -2.9134, 0.3467, 3.1498
    };
    for (int i = 0; i < 10; ++i) {
        ASSERT_NEAR(x[i], expectedResult[i], 1e-4);
    }
}
