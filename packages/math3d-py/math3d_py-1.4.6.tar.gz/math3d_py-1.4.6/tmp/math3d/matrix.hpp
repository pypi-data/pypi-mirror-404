#pragma once
#include "pybind11/pybind11.h"
#include "pybind11/operators.h"

#include "MatrixOperations.h"

namespace py = pybind11;

template<typename T, uint32_t Rows, uint32_t Cols>
void bind_Matrix(py::module_ const& module, char const* className) {

    using matrix = math3d::Matrix<T, Rows, Cols>;
    using vector = math3d::Vector<T, Cols>;

    py::class_<matrix>(module, className)
    .def(py::init())
    .def(py::init([](py::iterable const& data, math3d::Order const order) {
        std::vector<std::vector<T>> dataAsVec;
        for (auto outer : data) {
            std::vector<T> inner = outer.cast<std::vector<T>>();
            dataAsVec.push_back(std::move(inner));
        }
        return matrix{dataAsVec, order};
    }))
    .def("__getitem__", [](matrix const& matrix, uint32_t const index) {
        return matrix.operator[](index);
    })
    .def("__getitem__", [](matrix const& matrix, std::pair<uint32_t, uint32_t> const& index_pair) {
        return matrix.operator()(index_pair.first, index_pair.second);
    })
    .def("row", [](matrix const& matrix, uint32_t row) {
        return matrix.operator()(row);
    })
    .def(py::self * py::self)
    .def(py::self * vector{})
    .def("__str__", &matrix::asString)
    .def("__repr__", &matrix::asString)

    // Operations
    .def("transpose", &matrix::transpose)
    .def("upper_triangular", [](matrix const& input) {
        matrix output;
        input.convertToUpperTriangular(output);
        return output;
    })
    .def("determinant", &matrix::determinant)
    .def("inverse", &matrix::inverse)
    ;
}

template<typename T, uint32_t Rows, uint32_t Cols>
void bind_identityMatrix(py::module_ const& module, char const* className) {
    using identityMatrix = math3d::IdentityMatrix<T, Rows, Cols>;
    using matrix = math3d::Matrix<T, Rows, Cols>;
    py::class_<identityMatrix, matrix>(module, className)
    .def(py::init());
}