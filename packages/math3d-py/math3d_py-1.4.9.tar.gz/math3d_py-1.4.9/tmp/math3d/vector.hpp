#pragma once
#include "pybind11/pybind11.h"
#include "pybind11/operators.h"
#include "pybind11/stl.h"
#include "util.h"
#include "Vector.h"

namespace py = pybind11;

template<typename T, uint32_t Size>
void bind_Vector(py::module_ const& module, char const* className) {
    using vector = math3d::Vector<T, Size>;
    auto pyVecClass =
        py::class_<vector>(module, className)
        // Construction
        .def(py::init())
        .def(py::init([](py::iterable const& list) {
            auto const input = list.cast<std::vector<T>>();
            return vector{input};
        }))
        // Formatted output
        .def("__str__", [](vector const& v) {
            return util::convertSpaceToNewLine(v.asString());
        })
        .def("__repr__", [](vector const& v) {
            return util::convertSpaceToNewLine(v.asString());
        })
        // Operations
        .def(py::self + py::self)
        .def(py::self - py::self)
        .def(py::self * T{})
        .def(py::self / T{})
        .def("dot", &vector::dot)
        .def("normalize", [](vector& v) { v.normalize(); return v; })
        .def("length", [](vector const& v) { return v.length(); })
        .def("length_sqr", [](vector const& v) { return v.lengthSquared(); })
        .def("projection", [](vector const& self, vector const& u) {
            auto vectorProjection = self.getVectorProjection(u);
            return std::pair{vectorProjection.parallel, vectorProjection.perpendicular};
        });
    if constexpr (Size == 3) {
        pyVecClass
        .def(py::init([](T x, T y, T z) {
            return vector({x, y, z});
        }))
        .def(py::self * py::self);
    }
    if constexpr (Size == 4) {
        pyVecClass
        .def(py::init([](T x, T y, T z, T w) {
            return vector({x, y, z, w});
        }))
        .def(py::init([](math3d::Vector3<T> const& vec3) {
            std::vector<T> input {vec3.x, vec3.y, vec3.z, 1.F};
            return vector{input};
        }));
    }

    // Convenience member access (x, y, z, w)
    // .x, .y, .z, .w are Vector<T, N>::Proxy and its conversion operator has to be invoked to get the raw value
    // hence the static cast
    if constexpr (Size >= 2 && Size <= 4) {
        pyVecClass.def_property("x",
            [](vector const& self) {
                    return static_cast<T>(self.x);
                },
            [](vector& self, T value) {
                    self.x = value;
                }
        )
        .def_property("y",
            [](vector const& self) {
                    return static_cast<T>(self.y);
                },
            [](vector& self, T value) {
                    self.y = value;
                }
        );
    }
    if constexpr (Size == 3 || Size == 4 ) {
        pyVecClass.def_property("z",
            [](vector const& self) {
                    return static_cast<T>(self.z);
                },
            [](vector& self, T value) {
                    self.z = value;
                }
        );
    }
    if constexpr (Size == 4) {
        pyVecClass.def_property("w",
            [](vector const& self) {
                    return static_cast<T>(self.w);
                },
            [](vector& self, T value) {
                    self.w = value;
                }
        );
    }

}