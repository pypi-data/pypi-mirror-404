#include "pybind11/pybind11.h"
#include "vector.hpp"
#include "matrix.hpp"
#include "linear_system.hpp"
#include "types.hpp"

#include <unordered_map>
#include <format>

namespace {

#ifdef MAX_DIMENSIONS
    auto constexpr MaxDimension {MAX_DIMENSIONS};
#else
    auto constexpr MaxDimension {4};
#endif

    enum class Type : uint8_t {
        Vector,
        Matrix,
        LinearSystem,
        IdentityMatrix,
        Extent,
        Bounds,
        Remapper,
    };
    std::unordered_map<Type, char const*> TypePrefixMap {
        {Type::Vector, "Vector"},
        {Type::Matrix, "Matrix"},
        {Type::LinearSystem, "LinearSystem"},
        {Type::IdentityMatrix, "Identity"},
        {Type::Bounds, "AABB"},
        {Type::Extent, "Extent"},
        {Type::Remapper, "Remap"}
    };

    template<typename Type, Type Start, Type End>
    class TypeIterator {
    public:
        TypeIterator() = default;

        TypeIterator begin() {
            return *this;
        }

        TypeIterator end() {
            return TypeIterator{End + 1};
        }

        bool operator==(TypeIterator const& another) {
            return value == another.value;
        }

    private:
        std::underlying_type_t<Type> value {Start};
    };

    auto pyCompositeTypeCreator = [](Type const type, pybind11::module_ const& pythonModule, auto const integerConstant) {
        constexpr uint8_t dimension = integerConstant + 2;
        auto const typeName = TypePrefixMap[type] + std::to_string(dimension);
        if (typeName.empty()) {
            throw std::runtime_error{std::format("Unknown type {}", std::to_underlying(type))};
        }
        switch (type) {
            case Type::Vector:
                bind_Vector<double, dimension>(pythonModule, typeName.c_str());
                break;
            case Type::Matrix:
                bind_Matrix<double, dimension, dimension>(pythonModule, typeName.c_str());
                break;
            case Type::LinearSystem:
                bind_linearSystem<double, dimension>(pythonModule, typeName.c_str());
                break;
            case Type::IdentityMatrix:
                bind_identityMatrix<double, dimension, dimension>(pythonModule, typeName.c_str());
                break;
            default:
                break;
        }
    };

    void createSimpleType(Type const type, pybind11::module_ const& module) {
        auto const typeName = TypePrefixMap.at(type);
        switch (type) {
            case Type::Extent:
                bind_Extent<double>(module, typeName);
                break;
            case Type::Bounds:
                bind_Bounds<double>(module, typeName);
                break;
            case Type::Remapper:
                bind_Remapper<double>(module, typeName);
                break;
            default:
                throw std::runtime_error(std::format("Unknown simple type {}", std::to_underlying(type)));
        }

    }

    template <uint8_t... integers>
    void createCompositeType(Type const type, pybind11::module_& module, std::integer_sequence<uint8_t, integers...>) {
        (pyCompositeTypeCreator(type, module, std::integral_constant<uint8_t, integers>{}), ...);
    }
}

PYBIND11_MODULE(math3d, module) {
    // NOTE: std::make_integer_sequence returns integer_sequence<unsigned, 0, 1, ... , N-1>
    // Therefore, when MaxDimension is 4, the integer sequence is 0, 1, 2 (range [0, 3)), which gets is translated to
    // types with suffix 2, 3, 4 e.g. vec2, vec3, and vec4
    auto constexpr intSeq  = std::make_integer_sequence<uint8_t, MaxDimension-1>{};
    createCompositeType(Type::Vector, module, intSeq);
    py::enum_<math3d::Order>(module, "order")
        .value("row_major", math3d::Order::RowMajor)
        .value("col_major", math3d::Order::ColumnMajor)
        .export_values();
    createCompositeType(Type::Matrix, module, intSeq);
    createCompositeType(Type::LinearSystem, module, intSeq);
    createCompositeType(Type::IdentityMatrix, module, intSeq);
    createSimpleType(Type::Extent, module);
    createSimpleType(Type::Bounds, module);
    createSimpleType(Type::Remapper, module);
}
