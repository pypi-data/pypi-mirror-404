#pragma once
#include <memory>
#include <vector>
#include <filesystem>
#include "../Vector.h"
#include "../TypeAliases.h"
#include "../SupportingTypes.h"

namespace math3d {

    class Ray;

    class Primitive {

    public:
        Primitive() = default;
        virtual ~Primitive() = default;
        virtual void generateGeometry() = 0;
        virtual IntersectionResult intersectWithRay(Ray const& ray) = 0;
        [[nodiscard]]
        std::vector<types::Vertex> const& getVertices() {
            return vertices;
        }
        virtual void writeToFile(std::filesystem::path const& outputFile) = 0;

    protected:
       types::Vertices vertices;
    };

}
