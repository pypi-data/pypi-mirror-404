#pragma once
#include <vector>
#include <array>
#include "Vector.h"

namespace math3d::types {
    using Point3D = Vector3<double>;
    using Vector3D = Vector3<double>;
    using Vertex = Vector3<float>;
    using Vertices = std::vector<Vertex>;
    struct Tri : std::array<unsigned, 3> {
        // Emplace support constructor
        Tri(unsigned a, unsigned b, unsigned c)
        : std::array<unsigned, 3>{a, b, c} {
        }
    };
    using Tris = std::vector<Tri>;
}