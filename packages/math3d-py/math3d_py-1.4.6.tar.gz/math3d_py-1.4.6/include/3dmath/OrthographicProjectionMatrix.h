#pragma once

#include "ProjectionMatrix.h"
namespace math3d {

template<typename DataType, CoordinateSystemHandedness OutputSystemHandedness>
class OrthographicProjectionMatrix : public ProjectionMatrix<DataType> {

public:
    // Allow users to create an empty matrix and then call update when the projection needs to be recomputed
    OrthographicProjectionMatrix() = default;

    explicit OrthographicProjectionMatrix(Bounds3D<DataType> const& bounds3D)
    : ProjectionMatrix<DataType>() {
        update(bounds3D);
    }

    void update(Bounds3D<DataType> const& bounds3D) override {

        auto& data = Matrix<DataType, 4u, 4u>::data;

        // Bounding box has to have valid extents
        if (isZero(bounds3D.x) || isZero(bounds3D.y) || isZero(bounds3D.z)) {
            throw std::runtime_error("Unable to compute orthographic projection: Invalid bounds!");
        }

        // See https://mdh81.github.io/3dmath/orthographicProjection/ for a derivation for this matrix
        data[0]  = 2 / bounds3D.x.length();
        data[5]  = 2 / bounds3D.y.length();
        data[10] = 2 / bounds3D.z.length();
        data[12] = -(bounds3D.x.min + bounds3D.x.max) / bounds3D.x.length();
        data[13] = -(bounds3D.y.min + bounds3D.y.max) / bounds3D.y.length();
        data[14] = -(bounds3D.z.min + bounds3D.z.max) / bounds3D.z.length();

        // This library uses a right-handed coordinate system, but a graphics system like OpenGL might require projection
        // matrices set up so that the clip coordinates are in a left-handed system. In that case, z-coordinates have to
        // be inverted
        if (OutputSystemHandedness == CoordinateSystemHandedness::LeftHanded) {
            data[10] *= -1;
            data[14] *= -1;
        }
    }

};

}

