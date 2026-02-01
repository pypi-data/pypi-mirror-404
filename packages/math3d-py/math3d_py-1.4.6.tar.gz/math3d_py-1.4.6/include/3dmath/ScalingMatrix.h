#pragma once

#include "IdentityMatrix.h"

namespace math3d {
    template<typename T>
    class ScalingMatrix : public IdentityMatrix<T, 4, 4> {
    public:
        ScalingMatrix(T const scaleFactorX, T const scaleFactorY, T const scaleFactorZ) {
            Matrix<T, 4, 4>::data[0] = scaleFactorX;
            Matrix<T, 4, 4>::data[5] = scaleFactorY;
            Matrix<T, 4, 4>::data[10] = scaleFactorZ;
        }
    };
}