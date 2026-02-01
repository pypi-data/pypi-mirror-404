#pragma once

#include "Vector.h"
#include "Matrix.h"
#include "MatrixOperations.h"
#include "Constants.h"

namespace math3d {
    // The type is templated to accommodate pybind and enable it to bind unique instances to python typenames, otherwise
    // the sole static member function could be templated instead of the class
    template<typename DataType, unsigned N>
    class LinearSystem {
    public:
        // Solve a linear system with N equations with N unknowns
        static Vector<DataType, N>
        solveLinearSystem(Matrix<DataType, N, N> const& coefficientMatrix,
                          Vector<DataType, N> const& solutionVector) {
            static_assert(std::is_floating_point_v<DataType>, "Data type must be floating point");

            // Use Gaussian elimination to convert to upper triangular
            AugmentedMatrix<DataType, N, N+1> augmentedMatrix(coefficientMatrix, solutionVector);
            Matrix<DataType, N, N+1> upperTriangular;
            augmentedMatrix.convertToUpperTriangular(upperTriangular);

            // Back substitute to solve for unknowns
            Vector<DataType, N> result;
            DataType const* upperTriangularData = upperTriangular;
            for (long rowIndex = N-1; rowIndex >= 0; --rowIndex) {
                Vector<DataType, N+1> row = upperTriangular(rowIndex);
                DataType minuend = row[N];
                DataType subtrahend {};
                for (size_t i = N-1; i > rowIndex ; --i) {
                    subtrahend += result[i] * row[i];
                }
                auto solvedElementIndex = rowIndex * N + rowIndex;
                if (fabs(upperTriangularData[solvedElementIndex]) < constants::tolerance)
                    throw std::runtime_error("System does not have a solution.");
                result[rowIndex] = (minuend - subtrahend) / upperTriangularData[solvedElementIndex];
            }
            return result;
        }
    };

}