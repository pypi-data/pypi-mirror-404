#pragma once

#include "IdentityMatrix.h"
#include "SupportingTypes.h"

namespace math3d {

    template<typename DataType>
    class ProjectionMatrix : public IdentityMatrix<DataType, 4u, 4u> {
        static_assert(std::is_same<float, DataType>() ||
                      std::is_same<double, DataType>(), "Float and double are the only allowed types");
    public:
        // Allow users to create an empty matrix and then call update when the projection needs to be recomputed
        ProjectionMatrix() = default;
        virtual void update(Bounds3D<DataType> const& bounds3D) = 0;
    };

}

