#pragma once
#include "pybind11/pybind11.h"
#include "LinearSystem.h"

namespace py = pybind11;

template<typename T, uint32_t Size>
void bind_linearSystem(py::module_ const& module, char const* className) {

    using linear_system = math3d::LinearSystem<T, Size>;

    py::class_<linear_system>(module, className)
    .def_static("solve", &linear_system::solveLinearSystem);

}