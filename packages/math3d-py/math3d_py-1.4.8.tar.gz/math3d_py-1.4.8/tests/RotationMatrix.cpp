#include "gtest/gtest.h"
#include "3dmath/RotationMatrix.h"
#include "3dmath/Utilities.h"
#include <iostream>
using namespace std;
using namespace math3d;

TEST(RotationMatrix, RotateAboutX) {
    auto rotateAboutXBy90 =
            RotationMatrix<float>::rotateAboutX(90);
    // ugh! c++ doesn't allow initializer list to be an argument to overloaded operators
    auto xAxisAfterRotation = rotateAboutXBy90.operator*({1, 0, 0, 0});
    ASSERT_TRUE(Utilities::areEqual(xAxisAfterRotation.dot({1, 0, 0, 0}), 1.f));

    auto yAxisAfterRotation = rotateAboutXBy90 * Vector<float, 4>{0, 1, 0, 0};
    ASSERT_TRUE(Utilities::areEqual(yAxisAfterRotation.dot({0, 0, 1, 0}), 1.f));

    auto zAxisAfterRotation = rotateAboutXBy90 * Vector<float, 4>{0, 0, 1, 0};
    ASSERT_TRUE(Utilities::areEqual(zAxisAfterRotation.dot({0, -1, 0, 0}), 1.f));

}

TEST(RotationMatrix, RotateAboutY) {
    auto rotateAboutYBy90 =
            RotationMatrix<float>::rotateAboutY(90);
    // ugh! c++ doesn't allow initializer list to be an argument to overloaded operators
    auto xAxisAfterRotation = rotateAboutYBy90.operator*({1, 0, 0, 0});
    ASSERT_TRUE(Utilities::areEqual(xAxisAfterRotation.dot({0, 0, -1, 0}), 1.f));

    auto yAxisAfterRotation = rotateAboutYBy90 * Vector<float, 4>{0, 1, 0, 0};
    ASSERT_TRUE(Utilities::areEqual(yAxisAfterRotation.dot({0, 1, 0, 0}), 1.f));

    auto zAxisAfterRotation = rotateAboutYBy90 * Vector<float, 4>{0, 0, 1, 0};
    ASSERT_TRUE(Utilities::areEqual(zAxisAfterRotation.dot({1, 0, 0, 0}), 1.f));
}

TEST(RotationMatrix, RotateAboutZ) {
    auto rotateAboutZBy90 =
            RotationMatrix<float>::rotateAboutZ(90);
    // ugh! c++ doesn't allow initializer list to be an argument to overloaded operators
    auto xAxisAfterRotation = rotateAboutZBy90.operator*({1, 0, 0, 0});
    ASSERT_TRUE(Utilities::areEqual(xAxisAfterRotation.dot({0, 1, 0, 0}), 1.f));

    auto yAxisAfterRotation = rotateAboutZBy90 * Vector<float, 4>{0, 1, 0, 0};
    ASSERT_TRUE(Utilities::areEqual(yAxisAfterRotation.dot({-1, 0, 0, 0}), 1.f));

    auto zAxisAfterRotation = rotateAboutZBy90 * Vector<float, 4>{0, 0, 1, 0};
    ASSERT_TRUE(Utilities::areEqual(zAxisAfterRotation.dot({0, 0, 1, 0}), 1.f));
}

TEST(RotationMatrix, RotateAboutArbitraryAxis) {

    Vector<double, 3>arbitraryAxis = Utilities::RandomVector();
    arbitraryAxis.normalize();

    Vector<double, 4> axis {{arbitraryAxis.x, arbitraryAxis.y, arbitraryAxis.z}, 0};

    RotationMatrix<double> rotateAboutArbitraryVector(arbitraryAxis, Utilities::RandomNumber());

    auto axisAfterRotation = rotateAboutArbitraryVector * axis;
    ASSERT_TRUE(Utilities::areEqual(axisAfterRotation.dot(axis), 1.0));

}

TEST(RotationMatrix, MatrixStructure) {
    // Rotation matrix used to inherit from identity, but to allow
    // matrix multiplication-assignment, its base type was changed to
    // Matrix. This test asserts that the matrix constructed via all
    // constructors have the right structure i.e. are identity by default
    // and when built via the axis angle constructor the 4th column is
    // {0, 0, 0, 1}
    RotationMatrix<double> r1;
    Vector4<double> column1 = r1[0];
    Vector4<double> column2 = r1[1];
    Vector4<double> column3 = r1[2];
    Vector4<double> column4 = r1[3];
    ASSERT_TRUE(Utilities::areEqual(column1, Vector4<double>{1, 0, 0, 0}));
    ASSERT_TRUE(Utilities::areEqual(column2, Vector4<double>{0, 1, 0, 0}));
    ASSERT_TRUE(Utilities::areEqual(column3, Vector4<double>{0, 0, 1, 0}));
    ASSERT_TRUE(Utilities::areEqual(column4, Vector4<double>{0, 0, 0, 1}));

    RotationMatrix<double> rotateAboutArbitraryVector({1, 0, 0}, 0);
    column4 = rotateAboutArbitraryVector[3];
    ASSERT_TRUE(Utilities::areEqual(column4, Vector4<double>{0, 0, 0, 1}));
}

TEST(RotationMatrix, Multiplication) {

    // The reason this test exists is that matrix multiplication is implemented in base class Matrix. The result of
    // the multiplication is a base class instance and therefore, the result cannot be assigned
    // to a derived instance without special logic even though idiomatically speaking, multiplying two rotation matrices
    // and assigning their results to another rotation matrix is very natural.
    // To satisfy such expressions, the RotationMatrix class has a converting constructor that takes a 4x4 Matrix and
    // passes that to the copy-constructor of the Matrix class and builds a rotation matrix and then invokes
    // RotationMatrix::operator= to complete the assignment. The sequence of steps are
    // r1 = r1 * r2
    // step 1: Matrix::operator*() -> Matrix
    // step 2: RotationMatrix::RotationMatrix(Matrix const&)
    // step 3: RotationMatrix::operator=(RotationMatrix const&)
    RotationMatrix<float> r1, r2;
    auto str = r1.asString();
    r1 = r1 * r2;
    Vector<float, 4> testVec {10, 10, 10, 1};
    ASSERT_TRUE(Utilities::areEqual(r1 * testVec, testVec))
    << "Rotation matrix multiplication/conversion logic is incorrect";

    // Sequence of steps for expression r1 *= r2
    // step 1: RotationMatrix::operator*=() -> RotationMatrix
    // step 2: step 1 invokes Matrix::operator*() -> Matrix
    // step 3: RotationMatrix::RotationMatrix(Matrix const&) is invoked
    //         to convert result from step 2 into a rotation matrix
    // step 4: Matrix::operator=(Matrix const&) is invoked to assign the
    //         result of multiplication to r1
    r1 *= r2;
    ASSERT_TRUE(Utilities::areEqual(r1 * testVec, testVec))
    << "Rotation matrix multiplication/conversion logic is incorrect";
}

TEST(RotationMatrix, Concatenation) {

    RotationMatrix<float> r1 = RotationMatrix<float>::rotateAboutX(90);
    RotationMatrix<float> r2 = RotationMatrix<float>::rotateAboutZ(90);
    cout << r1 << endl;
    cout << r2 << endl;
    r1 *= r2;
    cout << r1 << endl;
}