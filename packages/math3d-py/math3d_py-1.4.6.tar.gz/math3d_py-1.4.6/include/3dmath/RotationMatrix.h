#pragma once
#include "Matrix.h"
#include "IdentityMatrix.h"
#include "Utilities.h"
namespace math3d {

// 4x4 column-major rotation matrix
template<typename DataType>
class RotationMatrix : public Matrix<DataType, 4, 4> {

public:

    RotationMatrix()
    : Matrix<DataType, 4, 4>(IdentityMatrix<DataType, 4, 4>{}) {

    }

    // Conversion constructor to build a RotationMatrix from Matrix to support the following expression forms
    // RotationMatrix r1, r2;
    // ...
    // r1 = r1 * r2
    // Matrix::operator* returns a Matrix, so assigning that to a rotation matrix is an invalid operation without
    // this conversion constructor that aids in building a temporary RotationMatrix from the result of Matrix::operator*
    RotationMatrix(Matrix<DataType, 4, 4>&& matrix)
    :   Matrix<DataType, 4, 4>(matrix) {}

    // Multiplication assignment operator to enable expressions of the form
    // RotationMatrix r1, r2;
    // ...
    // r1 *= r2;
    RotationMatrix& operator*=(RotationMatrix const& another) {
        *this = *this * another;
        return *this;
    }

    RotationMatrix(Vector3<DataType> const& rotationAxis,
                   DataType const rotationInDegrees)
    : Matrix<DataType, 4, 4>(IdentityMatrix<DataType, 4, 4>{}) {

        auto cosTheta = static_cast<DataType>(cos(Utilities::asRadians(rotationInDegrees)));
        auto oneMinusCosTheta = 1 - cosTheta;
        auto sinTheta = static_cast<DataType>(sin(Utilities::asRadians(rotationInDegrees)));

        // TODO: Add a specialization that allows assigning a vec3 to a vec4 with w set to 0 automatically
        this->operator[](0) =
            {((rotationAxis.x * rotationAxis.x) * oneMinusCosTheta) + cosTheta,
             ((rotationAxis.x * rotationAxis.y) * oneMinusCosTheta) + (rotationAxis.z * sinTheta),
             ((rotationAxis.x * rotationAxis.z) * oneMinusCosTheta) - (rotationAxis.y * sinTheta),
             0};

        this->operator[](1) =
             {((rotationAxis.x * rotationAxis.y) * oneMinusCosTheta) - (rotationAxis.z * sinTheta),
              ((rotationAxis.y * rotationAxis.y) * oneMinusCosTheta) + cosTheta,
              ((rotationAxis.z * rotationAxis.y) * oneMinusCosTheta) + (rotationAxis.x * sinTheta),
              0};

        this->operator[](2) =
            {((rotationAxis.x * rotationAxis.z) * oneMinusCosTheta) + (rotationAxis.y * sinTheta),
             ((rotationAxis.y * rotationAxis.z) * oneMinusCosTheta) - (rotationAxis.x * sinTheta),
             ((rotationAxis.z * rotationAxis.z) * oneMinusCosTheta) + cosTheta,
             0};
    }

    // See https://github.com/mdh81/3dmath/blob/master/derivations/Rotation_About_X.jpg
    static RotationMatrix rotateAboutX(DataType const rotationInDegrees) {
        return RotationMatrix({1, 0, 0}, rotationInDegrees);
    }

    // See https://github.com/mdh81/3dmath/blob/master/derivations/Rotation_About_Y.jpg
    static RotationMatrix rotateAboutY(DataType const rotationInDegrees) {
        return RotationMatrix({0, 1, 0}, rotationInDegrees);
    }

    // See https://github.com/mdh81/3dmath/blob/master/derivations/Rotation_About_Z.jpg
    static RotationMatrix rotateAboutZ(DataType const rotationInDegrees) {
       return RotationMatrix({0, 0, 1}, rotationInDegrees);
    }

};

}
