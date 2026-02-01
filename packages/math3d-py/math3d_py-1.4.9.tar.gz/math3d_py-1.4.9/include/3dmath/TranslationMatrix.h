#pragma once
#include "IdentityMatrix.h"
#include "Utilities.h"
namespace math3d {

// 4x4 column-major translation matrix
template<typename DataType>
class TranslationMatrix : public IdentityMatrix<DataType, 4, 4> {

public:
    // Allow creation of an identity rotation matrix
    TranslationMatrix() = default;

    // Set 4th column to [tx, ty, tz, 1]
    TranslationMatrix(Vector3<DataType> const& translation) {
        this->operator[](3) = Vector<DataType, 4>(translation, static_cast<DataType>(1));
    }

};

}