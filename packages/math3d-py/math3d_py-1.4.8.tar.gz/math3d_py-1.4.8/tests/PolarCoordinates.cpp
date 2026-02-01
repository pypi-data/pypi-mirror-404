#include "gtest/gtest.h"
#include "3dmath/PolarCoordinates.h"
#include "3dmath/Constants.h"
#include <vector>
#include <numbers>
#include <random>

class SphericalCoordinatesFixture : public ::testing::Test {
public:
    SphericalCoordinatesFixture()
    : gen(rd())
    , dis(0.f, 2*std::numbers::pi) {

    }
    float getRandomAngle() {
        return dis(gen);
    }

private:
    std::random_device rd;
    std::mt19937 gen;
    std::uniform_real_distribution<float> dis;

};

TEST(PolarCoordinates, ToCartesian) {
    ASSERT_FLOAT_EQ(
            (math3d::PolarCoordinates{1.f, 0.f}.getCartesianCoordinates())
                    .dot({1.f,0.f,0.f}), 1.f);

    ASSERT_FLOAT_EQ(
            (math3d::PolarCoordinates{1.f, 2.f*std::numbers::pi}.getCartesianCoordinates())
            .dot({1.f, 0.f, 0.f}), 1.f);

    ASSERT_FLOAT_EQ(
        (math3d::PolarCoordinates{1, std::numbers::pi/2}.getCartesianCoordinates())
        .dot({0.f,1.f,0.f}), 1.f);
}

TEST(PolarCoordinates, FromCartesian) {
    auto polarCoordinates =
            math3d::PolarCoordinates::convertCartesianCoordinates({10, 0});
    ASSERT_FLOAT_EQ(polarCoordinates.getRadius(), 10);
    ASSERT_FLOAT_EQ(polarCoordinates.getTheta(), 0);

    auto polarCoordinates1 =
            math3d::PolarCoordinates::convertCartesianCoordinates({10, 10});
    ASSERT_FLOAT_EQ(polarCoordinates1.getRadius(), sqrt(2)*10);
    ASSERT_FLOAT_EQ(polarCoordinates1.getTheta(), std::numbers::pi/4);

    auto polarCoordinates2 =
            math3d::PolarCoordinates::convertCartesianCoordinates({0, 0});
    ASSERT_FLOAT_EQ(polarCoordinates2.getRadius(), 0);
    ASSERT_FLOAT_EQ(polarCoordinates2.getTheta(), 0);
}

TEST_F(SphericalCoordinatesFixture, ToCartesian) {
    // When both theta and phi are zero, we should be at pole 1, which is at a distance or radius from the
    // origin in the +z direction
    auto cartesianCoordinates =
            math3d::SphericalCoordinates({1, 0, 0}).getCartesianCoordinates();
    ASSERT_FLOAT_EQ(cartesianCoordinates.dot({0, 0, 1}), 1);

    // When phi is 90, we should be in the xy plane
    auto cartesianCoordinates1 =
            math3d::SphericalCoordinates({1, getRandomAngle(), std::numbers::pi/2}).getCartesianCoordinates();
    ASSERT_NEAR(cartesianCoordinates1.dot({0, 0, 1}), 0, math3d::constants::tolerance);

    // When phi is 180 and theta is 0, we should be at pole 2, which is at a distance of radius from the origin
    // along -z direction
    auto cartesianCoordinates2 =
            math3d::SphericalCoordinates({5, 0, std::numbers::pi}).getCartesianCoordinates();
    ASSERT_NEAR(cartesianCoordinates2.dot({0, 0, -1}), 5, math3d::constants::tolerance);
}
