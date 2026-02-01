#pragma once

#include <numbers>

// List of constants used in this library
// NOTE: Don't include any constant here that is dependent on this
// library's data-structures to avoid circular dependencies
namespace math3d::constants {
    constexpr auto threeSixtyDegreesInRadians= 2 * std::numbers::pi;
    constexpr auto oneEightyDegreesInRadians = std::numbers::pi;
    constexpr auto radiansToDegrees = 180 / std::numbers::pi;
    constexpr auto tolerance = 1e-6;
    constexpr std::initializer_list<double> xAxis = {1, 0, 0};
    constexpr std::initializer_list<double> yAxis = {0, 1, 0};
    constexpr std::initializer_list<double> zAxis = {0, 0, 1};
    constexpr std::initializer_list<double> origin = {0, 0, 0};
}