#include "gtest/gtest.h"
#include "3dmath/Matrix.h"
#include "3dmath/IdentityMatrix.h"
#include <vector>
#include <iostream>
#include <fstream>
#include <regex>
using namespace std;
using namespace math3d;

TEST(Matrix, DefaultConstruction) {
    // Assert all matrix entries are zeroes
    Matrix<float, 10, 10> m; 
    ASSERT_EQ(m.getNumberOfRows(), 10);
    ASSERT_EQ(m.getNumberOfColumns(), 10);
    float const* data = m.getData();
    for (int i = 0; i < 99; ++i) {
        ASSERT_FLOAT_EQ(0, data[i]);
    }
}

TEST(Matrix, Identity) {
    
    // Assert identity matrix is a diagonal matrix
    IdentityMatrix<float, 3, 3> m1; 
    float const* data = m1.getData();
    for (auto i : {0,4,8}) {
        ASSERT_FLOAT_EQ(1, data[i]);
    }
    for (auto i : {1,2,3,5,6,7}) {
        ASSERT_FLOAT_EQ(0, data[i]);
    }
}

TEST(Matrix, CopyConstruction) {
    
    IdentityMatrix<float, 3, 3>m1;
    IdentityMatrix<float, 3, 3>m2(m1);
    float const* data = m2.getData();
    for (auto i : {0,4,8}) {
        ASSERT_FLOAT_EQ(1, data[i]);
    }
    for (auto i : {1,2,3,5,6,7}) {
        ASSERT_FLOAT_EQ(0, data[i]);
    }
}

TEST(Matrix, Initialization) {
    
    // Dimensions don't match: Columns don't match
    EXPECT_THROW(({
        try {
            Matrix<float, 2, 1> m2({{1.f}, {2.f}, {3.f}}, Order::ColumnMajor);
        } catch (std::invalid_argument& ex) {
            EXPECT_STREQ("Incompatible dimensions: Matrix dimensions are [2,1] "
                         "Number of columns in the input is 3", ex.what()); 
            throw;
        }
    }), std::invalid_argument);

    // Dimensions don't match: Rows don't match
    EXPECT_THROW(({
        try {
            Matrix<float, 1, 2> m2({{1.f,2.f}, {2.f}}, Order::ColumnMajor);
        } catch (std::invalid_argument& ex) {
            EXPECT_STREQ("Incompatible dimensions: Matrix dimensions are [1,2] "
                         "Number of rows in column 1 is 2", ex.what()); 
            throw;
        }
    }), std::invalid_argument);
    
    // Assert row major matrix is filled correctly
    Matrix<int, 2, 2> m3 {{1,2},{3,4}};
    int const* data = m3.getData();
    ASSERT_EQ(data[0], 1);
    ASSERT_EQ(data[1], 3);
    ASSERT_EQ(data[2], 2);
    ASSERT_EQ(data[3], 4);
}

TEST(Matrix, CopyAssignment) {
    Matrix<unsigned, 1, 1> m1 {{45U}};
    Matrix<unsigned, 1, 1> m2(m1);
    
    ASSERT_EQ(m2.getData()[0], 45U);
}

TEST(Matrix, MoveConstruction) {
    Matrix<int, 1, 1> m1 {{10}};
    auto p1 = m1.getData();
    Matrix<int, 1, 1> m2(std::move(m1));
    auto p2 = m2.getData();
    ASSERT_EQ(p1, p2);
    ASSERT_EQ(*p1, *p2);
    ASSERT_EQ(*p1, 10);
    ASSERT_EQ(m1.getData(), nullptr);
    Matrix<int, 1, 1> m3 {Matrix<int, 1, 1>{{25}}};
    ASSERT_EQ(m3.getData()[0], 25);
}

TEST(Matrix, MoveAssignment) {
    Matrix<int, 1, 1> m1 = Matrix<int,1,1>{{10}};
    auto p1 = m1.getData();
    ASSERT_EQ(*p1, 10);
}

TEST(Matrix, Print) {
    Matrix<int, 3, 2> m1 ({ {10, 11, 12}, {10, 11, 12} }, Order::ColumnMajor);
    ofstream ofs("mat.out");   
    ofs << m1;
    ifstream ifs("mat.out");
    string str;
    bool contentsMatch = false;
    getline(ifs,str);
    regex collapseSpaces (R"(\s+)");
    regex trimLeading (R"(^\s)");
    str = regex_replace(str, collapseSpaces, " ");
    str = regex_replace(str, trimLeading, "");
    contentsMatch = str.substr(0, 2) == "10";
    EXPECT_TRUE(contentsMatch) << "Expecting 10 at 0, 0. Found " << str.substr(0,2) << endl;
    contentsMatch = str.substr(3) == "10";
    EXPECT_TRUE(contentsMatch) << "Expecting 10 at 0, 1. Found " << str.substr(3) << endl;
    getline(ifs, str);
    str = regex_replace(str, collapseSpaces, " ");
    str = regex_replace(str, trimLeading, "");
    contentsMatch = str.substr(0, 2) == "11";
    EXPECT_TRUE(contentsMatch) << "Expecting 11 at 1, 0. Found " << str.substr(0,2) << endl;
    contentsMatch = str.substr(3) == "11";
    EXPECT_TRUE(contentsMatch) << "Expecting 11 at 1, 1. Found " << str.substr(3) << endl;
    getline(ifs, str);
    str = regex_replace(str, collapseSpaces, " ");
    str = regex_replace(str, trimLeading, "");
    contentsMatch = str.substr(0, 2) == "12";
    EXPECT_TRUE(contentsMatch) << "Expecting 12 at 2, 0. Found " << str.substr(0,2) << endl;
    contentsMatch = str.substr(3) == "12";
    EXPECT_TRUE(contentsMatch) << "Expecting 12 at 2, 1. Found " << str.substr(3) << endl;
}

TEST(Matrix, RowMajor) {

    Matrix<int, 3, 2> m1 ({ {10, 12}, {13, 14}, {15, 16} }, Order::RowMajor);
    const int* data = m1.getData();
    EXPECT_EQ(data[0], 10);
    EXPECT_EQ(data[1], 13);
    EXPECT_EQ(data[2], 15);

    EXPECT_EQ(data[3], 12);
    EXPECT_EQ(data[4], 14);
    EXPECT_EQ(data[5], 16);
    
    // Make sure column major internal format is formatted in row major order when printed 
    ofstream ofs("mat1.out");   
    ofs << m1;
    ifstream ifs("mat1.out");
    string str;
    bool contentsMatch = false;
    regex collapseSpaces (R"(\s+)");
    regex trimLeading (R"(^\s)");
    getline(ifs,str);
    str = regex_replace(str, collapseSpaces, " ");
    str = regex_replace(str, trimLeading, "");
    contentsMatch = str.substr(0, 2) == "10";
    EXPECT_TRUE(contentsMatch) << "Expecting 10 at 0, 0. Found " << str.substr(0,2) << endl;
    contentsMatch = str.substr(3) == "12";
    EXPECT_TRUE(contentsMatch) << "Expecting 12 at 0, 1. Found " << str.substr(3) << endl;
    getline(ifs, str);
    str = regex_replace(str, collapseSpaces, " ");
    str = regex_replace(str, trimLeading, "");
    contentsMatch = str.substr(0, 2) == "13";
    EXPECT_TRUE(contentsMatch) << "Expecting 13 at 1, 0. Found " << str.substr(0,2) << endl;
    contentsMatch = str.substr(3) == "14";
    EXPECT_TRUE(contentsMatch) << "Expecting 14 at 1, 1. Found " << str.substr(3) << endl;
    getline(ifs, str);
    str = regex_replace(str, collapseSpaces, " ");
    str = regex_replace(str, trimLeading, "");
    contentsMatch = str.substr(0, 2) == "15";
    EXPECT_TRUE(contentsMatch) << "Expecting 15 at 2, 0. Found " << str.substr(0,2) << endl;
    contentsMatch = str.substr(3) == "16";
    EXPECT_TRUE(contentsMatch) << "Expecting 16 at 2, 1. Found " << str.substr(3) << endl;
}

TEST(Matrix, VectorMultiplicationScaling) {
    Vector4<float> v {10, 10, 10, 1};
    Matrix<float, 4, 4> scalingMatrix {{2, 0, 0, 0}, {0, 2, 0, 0}, {0, 0, 2, 0}, {0, 0, 0, 1}};
    Vector4<float> result = scalingMatrix * v;
    ASSERT_FLOAT_EQ(result.x, 20.f) << "Multiplication results are wrong. Incorrect x coordinate";
    ASSERT_FLOAT_EQ(result.y, 20.f) << "Multiplication results are wrong. Incorrect y coordinate";
    ASSERT_FLOAT_EQ(result.z, 20.f) << "Multiplication results are wrong. Incorrect z coordinate";
    ASSERT_FLOAT_EQ(result.w, 1.f) << "Multiplication results are wrong. Incorrect w coordinate";
}

TEST(Matrix, VectorMultiplicationTranslation) {
    Vector4<float> v {10, 10, 10, 1};
    Matrix<float, 4, 4> translationMatrix {{1, 0, 0, 10}, {0, 1, 0, 10}, {0, 0, 1, 10}, {0, 0, 0, 1}};
    Vector4<float> result = translationMatrix * v;
    ASSERT_FLOAT_EQ(result.x, 20.f) << "Multiplication results are wrong. Incorrect x coordinate";
    ASSERT_FLOAT_EQ(result.y, 20.f) << "Multiplication results are wrong. Incorrect y coordinate";
    ASSERT_FLOAT_EQ(result.z, 20.f) << "Multiplication results are wrong. Incorrect z coordinate";
    ASSERT_FLOAT_EQ(result.w, 1.f) << "Multiplication results are wrong. Incorrect w coordinate";
}

TEST(Matrix, ConversionToPointer) {
    IdentityMatrix<float, 3, 3> identityMatrix;
    float const* matrixData = identityMatrix;
    ASSERT_FLOAT_EQ(matrixData[0], 1.);
    ASSERT_FLOAT_EQ(matrixData[4], 1.);
    ASSERT_FLOAT_EQ(matrixData[8], 1.);
    for (auto i : {1,2,3,5,6,7}) {
        ASSERT_FLOAT_EQ(matrixData[i], 0.);
    }
}

TEST(Matrix, ColumnExtraction) {
    Matrix<float, 3, 3> matrix { {1, 2, 3}, {4, 5, 6}, {7, 8, 9} };
    Vector<float, 3> column0 = matrix[0];
    ASSERT_FLOAT_EQ(column0[0], 1);
    ASSERT_FLOAT_EQ(column0[1], 4);
    ASSERT_FLOAT_EQ(column0[2], 7);

    Vector<float, 3> column1 = matrix[1];
    ASSERT_FLOAT_EQ(column1[0], 2);
    ASSERT_FLOAT_EQ(column1[1], 5);
    ASSERT_FLOAT_EQ(column1[2], 8);

    Vector<float, 3> column2 = matrix[2];
    ASSERT_FLOAT_EQ(column2[0], 3);
    ASSERT_FLOAT_EQ(column2[1], 6);
    ASSERT_FLOAT_EQ(column2[2], 9);
}

TEST(Matrix, RowExtraction) {
    Matrix<float, 3, 3> matrix { {1, 2, 3}, {4, 5, 6}, {7, 8, 9} };
    Vector<float, 3> row0 = matrix(0);
    ASSERT_FLOAT_EQ(row0[0], 1);
    ASSERT_FLOAT_EQ(row0[1], 2);
    ASSERT_FLOAT_EQ(row0[2], 3);

    Vector<float, 3> row1 = matrix(1);
    ASSERT_FLOAT_EQ(row1[0], 4);
    ASSERT_FLOAT_EQ(row1[1], 5);
    ASSERT_FLOAT_EQ(row1[2], 6);

    Vector<float, 3> row2 = matrix(2);
    ASSERT_FLOAT_EQ(row2[0], 7);
    ASSERT_FLOAT_EQ(row2[1], 8);
    ASSERT_FLOAT_EQ(row2[2], 9);
}

TEST(Matrix, ColumnAssignment) {
   IdentityMatrix<float, 3, 3> m;
   m[2] = {10, 12, 5};
   Vector<float, 3> thirdCol = m[2];
   ASSERT_FLOAT_EQ(thirdCol[0], 10);
   ASSERT_FLOAT_EQ(thirdCol[1], 12);
   ASSERT_FLOAT_EQ(thirdCol[2], 5);
}

TEST(Matrix, ColumnAccessBadCall) {
    IdentityMatrix<float, 3, 3> m;
    m[2] = {10, 12, 5};

    //TODO: ASSERT_THROW and EXCEPT_THROW appear broken. Investigate...
    bool exceptionThrown = false;
    try {
        m.operator[](0);
        m.operator[](1);
    } catch (std::runtime_error &ex) {
        exceptionThrown = true;
        ASSERT_STREQ(ex.what(), "Matrix::operator[]() : Invalid access. Previous column access operation is still in progress");
    }
    ASSERT_TRUE(exceptionThrown) << "Expected an exception to be thrown when subscript operator is abused";
}

TEST(Matrix, ColumnAssignmentSubscriptOutOfBounds) {
    IdentityMatrix<float, 3, 3> m;
    //TODO: ASSERT_THROW and EXCEPT_THROW appear broken. Investigate...
    bool exceptionThrown = false;
    try {
        m[10] = {10, 10, 10};
    } catch (std::runtime_error &ex) {
        exceptionThrown = true;
        ASSERT_STREQ(ex.what(), "Matrix::operator[]() : Invalid access. 10 is not a valid column index for a 3x3 matrix");
    }
    ASSERT_TRUE(exceptionThrown) << "Expected an exception to be thrown when subscript operator is abused";
}

TEST(Matrix, ElementAccess) {
    IdentityMatrix<float, 3, 3> m;
    m(2, 2) = 4;
    ASSERT_FLOAT_EQ(m.getData()[8], 4);
    m(2,2) = 40;
    ASSERT_FLOAT_EQ(m.getData()[8], 40);
    m[0] = {100, 100, 100};
    m(1,0) = 200;
    Vector<float, 3> col0 = m[0];
    ASSERT_FLOAT_EQ(col0[1], 200);
}

TEST(Matrix, ColumnRowIndexOutOfBounds) {
    std::string errorMessage;
    IdentityMatrix<float, 3, 3> m1;
    ASSERT_THROW(
    {
        try {
            m1(2,3) = 10.f;
        } catch(std::exception& ex) {
            errorMessage = ex.what();
            throw;
        }
    }, std::runtime_error);
    ASSERT_EQ(errorMessage, "Invalid access: 3 is not a valid column index for a 3x3 matrix\n");

    ASSERT_THROW(
        try {
            m1(5, 1) = 10.f;
        } catch(std::exception& ex) {
            errorMessage = ex.what();
            throw;
        }, std::runtime_error);
    ASSERT_EQ(errorMessage, "Invalid access: 5 is not a valid row index for a 3x3 matrix\n");

    ASSERT_THROW(
            try {
                m1(5, 5) = 10.f;
            } catch(std::exception& ex) {
                errorMessage = ex.what();
                throw;
            }, std::runtime_error);
    ASSERT_EQ(errorMessage, "Invalid access: 5 is not a valid row index for a 3x3 matrix\n"
                            "5 is not a valid column index for a 3x3 matrix\n");
}

TEST(Matrix, ElementAccessWithConstObject) {
    IdentityMatrix<float, 3, 3> const m;
    // Call float Matrix::operator(r, c) const
    ASSERT_TRUE(m(2,2) == m(1,1));
}

TEST(Matrix, ElementAccessWithNonConstObject) {
    Matrix<float, 4, 6> m2;
    // Call non-const function Matrix& operator(r, c)
    m2(3,5) = 10.f;
    // call function DataType operator() const with a non-const object
    ASSERT_FLOAT_EQ(m2(3,5), 10.f);
}

TEST(Matrix, ConversionOperatorAbuse) {
    Matrix<float, 5, 2> m;
    std::string errorMessage;
    ASSERT_THROW(
        try {
            float val = m;
        } catch(std::exception& ex) {
            errorMessage = ex.what();
            throw;
        }, std::runtime_error);
    ASSERT_EQ(errorMessage, "Invalid conversion. Check element access expressions");

    m.operator[](0);
    ASSERT_THROW(
            try {
                float val = m;
            } catch(std::exception& ex) {
                errorMessage = ex.what();
                throw;
            }, std::runtime_error);
    ASSERT_EQ(errorMessage, "Invalid conversion. Check element access expressions");
}

TEST(Matrix, BuildFromVector) {
    std::vector<int> vec;
    for (auto i = 0; i < 10; i++) {
        vec.push_back(i);
    }
    Matrix<int, 3, 3> m(vec);
    ASSERT_EQ(m(0, 0), 0);
    ASSERT_EQ(m(0, 1), 1);
    ASSERT_EQ(m(0, 2), 2);

    ASSERT_EQ(m(1, 0), 3);
    ASSERT_EQ(m(1, 1), 4);
    ASSERT_EQ(m(1, 2), 5);

    ASSERT_EQ(m(2, 0), 6);
    ASSERT_EQ(m(2, 1), 7);
    ASSERT_EQ(m(2, 2), 8);

    Matrix<int, 3, 3> m1(vec, Order::ColumnMajor);
    ASSERT_EQ(m1(0, 0), 0);
    ASSERT_EQ(m1(1, 0), 1);
    ASSERT_EQ(m1(2, 0), 2);

    ASSERT_EQ(m1(0, 1), 3);
    ASSERT_EQ(m1(1, 1), 4);
    ASSERT_EQ(m1(2, 1), 5);

    ASSERT_EQ(m1(0, 2), 6);
    ASSERT_EQ(m1(1, 2), 7);
    ASSERT_EQ(m1(2, 2), 8);
}

TEST(Matrix, RowAccess) {
    Matrix<int, 3, 2> m{{1,2},{3,4},{5,6}};
    auto row0 = m(0);
    ASSERT_EQ(row0[0], 1);
    ASSERT_EQ(row0[1], 2);
    auto row1 = m(1);
    ASSERT_EQ(row1[0], 3);
    ASSERT_EQ(row1[1], 4);
    auto row2 = m(2);
    ASSERT_EQ(row2[0], 5);
    ASSERT_EQ(row2[1], 6);
}

TEST(Matrix, ColumnAccess) {
    Matrix<int, 3, 2> m{{1,2},{3,4},{5,6}};
    Vector<int, 3> col0 = m[0];
    ASSERT_EQ(col0[0], 1);
    ASSERT_EQ(col0[1], 3);
    ASSERT_EQ(col0[2], 5);
    Vector<int, 3> col1 = m[1];
    ASSERT_EQ(col1[0], 2);
    ASSERT_EQ(col1[1], 4);
    ASSERT_EQ(col1[2], 6);
}

TEST(Matrix, AugmentedMatrixFromMatrix) {
    Matrix<int, 3, 2> m{
        {1, 2},
        {4, 5},
        {7, 8}
    };

    Matrix<int, 3, 4> m1{
        {10, 11, 12, 13},
        {14, 15, 16, 17},
        {18, 19, 20, 21}
    };

    AugmentedMatrix<int, 3, 6> augmentedMatrix(m, m1);
    ASSERT_EQ(augmentedMatrix(2, 5), 21);
    ASSERT_EQ(augmentedMatrix(1, 5), 17);
    ASSERT_EQ(augmentedMatrix(0, 5), 13);

    ASSERT_EQ(augmentedMatrix(0, 3), 11);
    ASSERT_EQ(augmentedMatrix(1, 3), 15);
    ASSERT_EQ(augmentedMatrix(2, 3), 19);
}

TEST(Matrix, AugmentedMatrixFromVector) {
    Matrix<int, 3, 2> m{
            {1, 2},
            {4, 5},
            {7, 8}
    };

    Vector3<int> v{9, 10, 11};

    AugmentedMatrix<int, 3, 3> augmentedMatrix(m, v);
    ASSERT_EQ(augmentedMatrix(2, 2), 11);
    ASSERT_EQ(augmentedMatrix(1, 2), 10);
    ASSERT_EQ(augmentedMatrix(0, 2), 9);

    ASSERT_EQ(augmentedMatrix(0, 0), 1);
    ASSERT_EQ(augmentedMatrix(1, 0), 4);
    ASSERT_EQ(augmentedMatrix(2, 0), 7);
}

TEST(Matrix, asString) {
    Matrix<int, 3, 2> m{
            {1, 2},
            {4, 5},
            {7, 8}
    };

    ASSERT_EQ(m.asString(),
              "         1          2\n"
              "         4          5\n"
              "         7          8\n");
}

TEST(Matrix, PrintingToStandardOutput) {
    testing::internal::CaptureStdout();
    Matrix<int, 3, 2> m{
            {1, 2},
            {4, 5},
            {7, 8}
    };
    m.print();
    ASSERT_STREQ("         1          2\n"
                 "         4          5\n"
                 "         7          8\n",
                 testing::internal::GetCapturedStdout().c_str());
}

TEST(Matrix, MultiplicationWithMatrix) {
    Matrix<int, 4, 2> m1{
        {1, 2},
        {3, 4},
        {5, 6},
        {7, 8}
    };

    Matrix<int, 2, 4> m2{
        {1, 2, 3, 4},
        {7, 8, 9, 10}
    };

    Matrix <int, 4, 4> expectedResult {
        {15,    18,    21,    24},
        {31,    38,    45,    52},
        {47,    58,    69,    80},
        {63,    78,    93,   108}
    };

    auto result = m1 * m2;

    std::cout << result << std::endl;

    int const* actualData = result;
    int const* expectedData = expectedResult;

    for (auto i = 0u; i < 16; ++i) {
        ASSERT_EQ(actualData[i], expectedData[i]);
    }

}