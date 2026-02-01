#include "gtest/gtest.h"
#include "3dmath/MatrixOperations.h"
#include <vector>
using namespace std;
using namespace math3d;

namespace math3d {
    // Friend class of matrix to get results of private methods
    template<typename T, unsigned M, unsigned N>
    class MatrixTestWrapper {
    public:
        explicit MatrixTestWrapper(Matrix<T,M,N> const& testMatrix) : testMatrix(testMatrix) {}

        auto swapRows(unsigned i, unsigned j) {
            testMatrix.swapRows(i, j);
            return decltype(testMatrix)(testMatrix);
        }

    private:
        Matrix<T, M, N> testMatrix;
    };

}

TEST(MatrixOperations, Transpose) {
    // Inner init list is a row since the default order is row major
    Matrix<int, 3, 3> matrix {
            {1, 4, 7},
            {2, 5, 8},
            {3, 6, 9} };
    auto transposedMatrix = matrix.transpose();
    using Column = Vector<int, 3>;
    Column column0 = transposedMatrix[0];
    ASSERT_EQ(column0[0], 1);
    ASSERT_EQ(column0[1], 4);
    ASSERT_EQ(column0[2], 7);

    Column column1 = transposedMatrix[1];
    ASSERT_EQ(column1[0], 2);
    ASSERT_EQ(column1[1], 5);
    ASSERT_EQ(column1[2], 8);

    Column column2 = transposedMatrix[2];
    ASSERT_EQ(column2[0], 3);
    ASSERT_EQ(column2[1], 6);
    ASSERT_EQ(column2[2], 9);
}

TEST(MatrixOperations, SwapRows) {
    Matrix<int, 3, 3> testMatrix {
        {2, 1, 3},
        {-3, -1, 2},
        {1, 2, 4}
    };
    MatrixTestWrapper<int, 3, 3> matrixTestWrapper(testMatrix);
    auto result = matrixTestWrapper.swapRows(0, 1);
    ASSERT_EQ(result(0, 0), -3);
    ASSERT_EQ(result(0, 1), -1);
    ASSERT_EQ(result(0, 2), +2);
    ASSERT_EQ(result(1, 0), +2);
    ASSERT_EQ(result(1, 1), +1);
    ASSERT_EQ(result(1, 2), +3);
}

TEST(MatrixOperations, DeterminantOfValidMatrices) {
    Matrix<float, 3, 3> testMatrix {{2.f, 1.f, 3.f},
                                    {-3.f, -1.f, 2.f},
                                    {1.f, 2.f, 4.f}};
    auto result = testMatrix.determinant();
    ASSERT_TRUE(Utilities::areEqual(-17.000001f, result));

    auto identityMatrix = IdentityMatrix<float, 3, 3>{};
    result = identityMatrix.determinant();
    ASSERT_TRUE(Utilities::areEqual(1.f, result));

    Matrix<float, 2, 2> testMatrix2 {{
        {15,5},
        {2,10}
    }};
    result = testMatrix2.determinant();
    ASSERT_TRUE(Utilities::areEqual(15.f*10 - 2*5, result)) << "2x2 determinant is not the difference between product of diagonal elements";
}

TEST(MatrixOperations, DeterminantOfMatrixWithZerosInLastColumn) {
    Matrix<float, 2, 2> testMatrix {{
        {1,0},
        {2,0}
    }};
    ASSERT_FLOAT_EQ(0, testMatrix.determinant());
}

TEST(MatrixOperations, DeterminantOfMatrixWithAllZerosInColumns) {
    Matrix<float, 3, 3> testMatrix {{
        {1,0,4},
        {2,0,5},
        {3,0,6}
    }};
    ASSERT_TRUE(Utilities::areEqual(0.f, testMatrix.determinant()));
}

TEST(MatrixOperations, InverseOfNonInvertibleMatrix) {
    Matrix<float, 3, 3> testMatrix {{
        {1,0,4},
        {2,0,5},
        {3,0,6}
    }};

    std::string errorMessage;
    try {
        testMatrix.inverse();
    } catch(std::exception& ex) {
        errorMessage = ex.what();
    }
    ASSERT_EQ(errorMessage, "Matrix is not invertible");
}

TEST(MatrixOperations, Inverse) {
    Matrix<float, 3, 3> testMatrix {{
        {1,4,7},
        {2,5,8},
        {3,6,11}
    }};

    Matrix<float, 3, 3> inverseExpectedResult = {
            {-1.166667,   0.333333,        0.5},
            {-0.333333,   1.666667,         -1},
            {0.5,         -1,             0.5},
    };

    auto inverse = testMatrix.inverse();

    for (auto i = 0u; i < 3u; ++i) {
        for (auto j = 0u; j < 3u; ++j) {
            float expectedVal = inverseExpectedResult(i, j);
            float actualVal = inverse(i, j);
            ASSERT_NEAR(expectedVal, actualVal, 1e-6);
        }
    }
}

TEST(MatrixOperations, InverseOfMatrixWithZeroNonPivots) {
    Matrix<float, 4, 4> testMatrix {{
        {5,4,3,2},
        {0,4,2,0},
        {0,0,8,0},
        {0,0,0,10}
    }};

    Matrix<float, 4, 4> inverseExpectedResult = {
        {0.2000,  -0.2000,  -0.0250,  -0.0400},
        {0,        0.2500,  -0.0625,        0},
        {0,        0,        0.1250,        0},
        {0,        0,        0,         0.1000}
    };

    auto inverse = testMatrix.inverse();

    for (auto i = 0u; i < 4u; ++i) {
        for (auto j = 0u; j < 4u; ++j) {
            float expectedVal = inverseExpectedResult(i, j);
            float actualVal = inverse(i, j);
            ASSERT_NEAR(expectedVal, actualVal, 1e-6);
        }
    }
}