#include "gtest/gtest.h"
#include "3dmath/Vector.h"
#include <vector>
using namespace std;
using namespace math3d;

TEST(VectorConvenienceMembers, Construction) {
    Vector3<float> v1;
    ASSERT_FLOAT_EQ(v1.x, 0);
    ASSERT_FLOAT_EQ(v1.y, 0);
    ASSERT_FLOAT_EQ(v1.z, 0);
    Vector3<float> v2({10.f, 20.f, 30.f});
    ASSERT_FLOAT_EQ(v2.x, 10.f);
    ASSERT_FLOAT_EQ(v2.y, 20.f);
    ASSERT_FLOAT_EQ(v2.z, 30.f);
}

TEST(VectorConvenienceMembers, CopyAssignment) {
    Vector3<float> v1({1, 0, 0});
    Vector3<float> v2({0, 1, 0});
    v2 = v1;
    ASSERT_FLOAT_EQ(v2.x, 1);
    ASSERT_FLOAT_EQ(v2.y, 0);
    ASSERT_FLOAT_EQ(v2.z, 0);
}

TEST(VectorConvenienceMembers, CopyConstruction) {
    Vector3<float> v1({1, 0, 0});
    Vector3<float> v2(v1);
    ASSERT_FLOAT_EQ(v2.x, 1);
    ASSERT_FLOAT_EQ(v2.y, 0);
    ASSERT_FLOAT_EQ(v2.z, 0);
}

TEST(VectorConvenienceMembers, MoveConstruction) {
    auto v =  Vector3<float>{10, 20, 30};
    Vector3<float> v1(std::move(v));
    ASSERT_FLOAT_EQ(v1.x, 10);
    ASSERT_FLOAT_EQ(v1.y, 20);
    ASSERT_FLOAT_EQ(v1.z, 30);
    std::string exceptionMessage;
    ASSERT_THROW({
                     try {
                         v.x = 100.f;
                     } catch(std::runtime_error& ex) {
                         exceptionMessage = ex.what();
                         throw ex;
                     }
                 }, std::runtime_error) << "Expected an invalid access exception";
    ASSERT_EQ(exceptionMessage, "Invalid access!");
}

TEST(VectorConvenienceMembers, MoveAssignment) {
    auto v =  Vector3<float>{10, 20, 30};
    Vector3<float> v1;
    v1 = std::move(v);
    ASSERT_FLOAT_EQ(v1.x, 10);
    ASSERT_FLOAT_EQ(v1.y, 20);
    ASSERT_FLOAT_EQ(v1.z, 30);
    std::string exceptionMessage;
    ASSERT_THROW({
                     try {
                         v.x = 100.f;
                     } catch(std::runtime_error& ex) {
                         exceptionMessage = ex.what();
                         throw ex;
                     }
                 }, std::runtime_error) << "Expected an invalid access exception";
    ASSERT_EQ(exceptionMessage, "Invalid access!");
}

TEST(VectorConvenienceMembers, AddAssignmentOperator) {
    auto v =  Vector3<float>{10, 20, 30};
    v.x += 45.f;
    ASSERT_FLOAT_EQ(v.x, 55);
    Vector3<float> v1;
    v1.x += v.x;
    ASSERT_FLOAT_EQ(v1.x, 55);
}

TEST(VectorConvenienceMembers, SubtractAssignmentOperator) {
    auto v =  Vector3<float>{10, 20, 30};
    v.x -= 45.f;
    ASSERT_FLOAT_EQ(v.x, -35);
    Vector3<float> v1;
    v1.x -= v.x;
    ASSERT_FLOAT_EQ(v1.x, 35);
}

TEST(VectorConvenienceMembers, MultiplyAssignmentOperator) {
    auto v =  Vector3<float>{10, 20, 30};
    v.x *= 45.f;
    ASSERT_FLOAT_EQ(v.x, 450);
    Vector3<float> v1;
    v.x *= v1.x;
    ASSERT_FLOAT_EQ(v1.x, 0);
}

TEST(VectorConvenienceMembers, DivideAssignmentOperator) {
    auto v =  Vector3<float>{10, 20, 30};
    v.x /= 45.f;
    ASSERT_FLOAT_EQ(v.x, 1/4.5);
    Vector3<float> v1;
    v1.x /= v.x;
    ASSERT_FLOAT_EQ(v1.x, 0);
}