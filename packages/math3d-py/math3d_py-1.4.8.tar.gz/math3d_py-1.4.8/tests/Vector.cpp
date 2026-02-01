#include "gtest/gtest.h"
#include "3dmath/Vector.h"

#include <algorithm>
#include <vector>
using namespace std;
using namespace math3d;

TEST(Vector, DefaultConstruction) {
    // Assert all vector entries are zeroes
    Vector<float, 10> v; 
    float const* data = v.getData();
    for (int i = 0; i < 10; ++i) {
        ASSERT_FLOAT_EQ(0, data[i]);
    }
}

TEST(Vector, InitializerConstruction) {
    Vector<float, 4> v {1.0, 10.0, 20.0, 30.0};
    float const* data = v.getData();
    ASSERT_FLOAT_EQ(1.0, data[0]);
    ASSERT_FLOAT_EQ(10.0, data[1]);
    ASSERT_FLOAT_EQ(20.0, data[2]);
    ASSERT_FLOAT_EQ(30.0, data[3]);
    EXPECT_THROW(({
        try {
            Vector<float, 3> {1.0, 10.0, 20.0, 30.0};
        } catch (std::invalid_argument& ex) {
            EXPECT_STREQ("Dimension mismatch: Vector's dimension is 3 "
                         "Input size is 4", ex.what()); 
            throw;
        }

    }), std::invalid_argument);
}

TEST(Vector, CopyConstruction) {
    Vector<float, 4> v {1.0, 10.0, 20.0, 30.0};
    Vector<float, 4> v2(v);
    float const* data = v2.getData();
    ASSERT_FLOAT_EQ(1.0, data[0]);
    ASSERT_FLOAT_EQ(10.0, data[1]);
    ASSERT_FLOAT_EQ(20.0, data[2]);
    ASSERT_FLOAT_EQ(30.0, data[3]);
    // NOTE: Compiler protects against passing an instance of Vector3D whose
    // dimensions are different to the copy constructor. Same for data type
}

TEST(Vector, CopyAssignment) {
    Vector<float, 4> v {1.0, 10.0, 20.0, 30.0};
    Vector<float, 4> v2;
    v2 = v;
    float const* data = v2.getData();
    ASSERT_FLOAT_EQ(1.0, data[0]);
    ASSERT_FLOAT_EQ(10.0, data[1]);
    ASSERT_FLOAT_EQ(20.0, data[2]);
    ASSERT_FLOAT_EQ(30.0, data[3]);
    float const* data1 = v.getData();
    ASSERT_NE(data1, data) << "Expected copy assignment to do a new allocation";
    ASSERT_FLOAT_EQ(1.0, data1[0]);
    ASSERT_FLOAT_EQ(10.0, data1[1]);
    ASSERT_FLOAT_EQ(20.0, data1[2]);
    ASSERT_FLOAT_EQ(30.0, data1[3]);

}

TEST(Vector, VectorAddition) {
    Vector<float, 3> v1({1,2,3});
    Vector<float, 3> v2({1,2,3});
    Vector<float, 3> v3 = v1 + v2;
    float const* data = v3.getData();
    ASSERT_FLOAT_EQ(2, data[0]);
    ASSERT_FLOAT_EQ(4, data[1]);
    ASSERT_FLOAT_EQ(6, data[2]);
    data = v1.getData();
    ASSERT_FLOAT_EQ(1, data[0]);
    ASSERT_FLOAT_EQ(2, data[1]);
    ASSERT_FLOAT_EQ(3, data[2]);
}

TEST(Vector, ComponentAccess) {
    Vector<float, 3> v1({1,2,3});
    ASSERT_FLOAT_EQ(v1[0],1);
    ASSERT_FLOAT_EQ(v1[1],2);
    ASSERT_FLOAT_EQ(v1[2],3);
    v1[0] = 3;
    v1[1] = 50;
    v1[2] = 1;
    ASSERT_FLOAT_EQ(v1[0],3);
    ASSERT_FLOAT_EQ(v1[1],50);
    ASSERT_FLOAT_EQ(v1[2],1);
}


TEST(Vector, CrossProduct) {
    Vector<float, 3> v1({5, 0, 0});
    Vector<float, 3> v2({0, 5, 0});
    Vector<float, 3> v3 = v1 * v2;
    ASSERT_FLOAT_EQ(v3[2], 25);
}

TEST(Vector, Length) {
    Vector<float, 3> v1({5, 0, 0});
    ASSERT_FLOAT_EQ(v1.length(), 5);
    Vector<float, 3> v2({0, 5, 0});
    ASSERT_FLOAT_EQ(v2.length(), 5);
    Vector<float, 3> v3 = v1 * v2;
    ASSERT_FLOAT_EQ(v3.length(), 25);
}

TEST(Vector, Normalize) {
    Vector<float, 3> v1({5, 0, 0});
    const Vector<float, 3> v2({0, 5, 0});
    Vector<float, 3> v3 = v1 * v2;
    v3.normalize();
    ASSERT_FLOAT_EQ(v3.length(), 1);
    auto v4 = v2.normalize();
    ASSERT_FLOAT_EQ(v4.lengthSquared(), 1);
    ASSERT_FLOAT_EQ(v4.dot({0, 1, 0}), 1);
    Vector<float, 3> v5 = {0, 0, 0};
    v5.normalize();
    ASSERT_FALSE(std::ranges::any_of(v5, [](auto const comp) {
        return std::isnan(comp);
    })) << "Normalize did not avoid divide by zero as expected";
    ASSERT_TRUE(std::ranges::all_of(v5, [](auto const comp) {
        return comp < constants::tolerance;
    })) << "Normalizing a zero vector should return yield a zero vector";

}

TEST(Vector, Difference) {
    Vector<float, 3> v2({10, 0, 0});
    Vector<float, 3> v1({5, 0, 0});
    Vector<float, 3> v12v2 = v2 - v1;
    ASSERT_FLOAT_EQ(v12v2[0], 5);
    ASSERT_FLOAT_EQ(v12v2[1], 0);
    ASSERT_FLOAT_EQ(v12v2[2], 0);
}

TEST(Vector, Scale) {
    Vector<float, 3> v1({10, 20, 30});
    v1 /= 10;
    ASSERT_FLOAT_EQ(v1[0], 1);
    ASSERT_FLOAT_EQ(v1[1], 2);
    ASSERT_FLOAT_EQ(v1[2], 3);
}

TEST(Vector, AddToSelf) {
    Vector<float, 3> v1({10, 20, 30});
    Vector<float, 3> v2({10, 20, 30});
    v1 += v2;
    ASSERT_FLOAT_EQ(v1[0], 20);
    ASSERT_FLOAT_EQ(v1[1], 40);
    ASSERT_FLOAT_EQ(v1[2], 60);
    ASSERT_FLOAT_EQ(v2[0], 10);
    ASSERT_FLOAT_EQ(v2[1], 20);
    ASSERT_FLOAT_EQ(v2[2], 30);
}

TEST(Vector, DotProduct) {
    Vector<float, 3> v1({5, 0, 0});
    Vector<float, 3> v2({5, 0, 0});
    ASSERT_FLOAT_EQ(v1.dot(v2), 25);
    Vector<float, 3> v3({0, -5, 0});
    ASSERT_FLOAT_EQ(v1.dot(v3), 0);
}

TEST(Vector, BuildFromSTLVector) {
    std::vector<float> v(5, 8.3f);
    Vector<float, 5> v1(v);
    for(auto i : {0,1,2,3,4})
        ASSERT_FLOAT_EQ(v[i], 8.3f);
}


TEST(Vector, WriteData) {
    Vector3<float> v3;
    v3.getData()[0] = 5.f;
    v3.getData()[1] = 50.f;
    v3.getData()[2] = 500.f;
    ASSERT_FLOAT_EQ(v3.x, 5.f);
    ASSERT_FLOAT_EQ(v3.y, 50.f);
    ASSERT_FLOAT_EQ(v3.z, 500.f);
}

TEST(Vector, ScalarMultiplication) {
    Vector3<float> v1({1, 2, 3});
    Vector3<float> v2 = v1 * 1.5f;
    ASSERT_FLOAT_EQ(v2.x, 1.5f);
    ASSERT_FLOAT_EQ(v2.y, 3.0f);
    ASSERT_FLOAT_EQ(v2.z, 4.5f);
}

TEST(Vector, ScalarPreMultiplication) {
    Vector3<float> v1({1, 2, 3});
    Vector3<float> v2 = 1.5f * v1;
    ASSERT_FLOAT_EQ(v2.x, 1.5f);
    ASSERT_FLOAT_EQ(v2.y, 3.0f);
    ASSERT_FLOAT_EQ(v2.z, 4.5f);
}

TEST(Vector, Negation) {
    Vector3<float> v{1, 2, 3};
    ASSERT_FLOAT_EQ(-v.x, -1.f);
    ASSERT_FLOAT_EQ(-v.y, -2.f);
    ASSERT_FLOAT_EQ(-v.z, -3.f);
}

TEST(Vector, AsString) {
    Vector3<int> v{1, 2, 3};
    ASSERT_STREQ(v.asString().c_str(), "[1 2 3]");
}

TEST(Vector, SelfAssignment) {
    Vector3<float> v{1,2,3};
    v = v;
    ASSERT_FLOAT_EQ(v.x, 1);
    ASSERT_FLOAT_EQ(v.y, 2);
    ASSERT_FLOAT_EQ(v.z, 3);
    v = std::move(v);
    ASSERT_FLOAT_EQ(v.x, 1);
    ASSERT_FLOAT_EQ(v.y, 2);
    ASSERT_FLOAT_EQ(v.z, 3);
}

TEST(Vector, VectorProjection) {
    Vector3<float> v{5, 5, 0};
    Vector3<float> u{1, 0, 0};
    auto result = v.getVectorProjection(u);
    ASSERT_FLOAT_EQ((u * result.parallel).lengthSquared(), 0.f);
    ASSERT_FLOAT_EQ(u.dot(result.perpendicular), 0.f);
}

TEST(Vector, PrintingToStandardOutput) {
    testing::internal::CaptureStdout();
    Vector3<int> v{5, 5, 0};
    v.print();
    ASSERT_STREQ("[5,5,0]", testing::internal::GetCapturedStdout().c_str());
}

TEST(Vector, BuildAsCopyWithAnAdditionalElement) {
    Vector3<float> v{5, 5, 0};
    Vector4<float> v1(v, 45);
    ASSERT_FLOAT_EQ(v1.w, 45);
    ASSERT_FLOAT_EQ(v1.x, 5);
    ASSERT_FLOAT_EQ(v1.y, 5);
    ASSERT_FLOAT_EQ(v1.z, 0);
}

TEST(Vector, TypeConversion) {
    Vector3<float> v{5.5, 10.5, 15.5};
    Vector3<double> v_double = static_cast<Vector3<float>>(v);
    auto v_float = static_cast<Vector3<float>>(v_double);
    for(auto i = 0u; i < 3; ++i) {
        ASSERT_FLOAT_EQ(v_float[i], v[i]);
        ASSERT_FLOAT_EQ(v_double[i], v[i]);
    }
}

TEST(Vector, AddressOfProxies) {
    Vector3<float> v{5.5, 10.5, 15.5};
    ASSERT_EQ(&v.x, &v[0]);
    ASSERT_EQ(&v.y, &v[1]);
    ASSERT_EQ(&v.z, &v[2]);

    Vector3<int> v1;
    auto l = [](int* a, int* b, int* c) {
        *a = 10; *b = 20; *c = 30;
    };
    l(&v1.x, &v1.y, &v1.z);
    ASSERT_TRUE(v1.x == 10);
    ASSERT_TRUE(v1.y == 20);
    ASSERT_TRUE(v1.z == 30);

}