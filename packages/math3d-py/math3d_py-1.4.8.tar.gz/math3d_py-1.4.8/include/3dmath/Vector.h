#pragma once
#include <ostream>
#include <string>
#include <initializer_list>
#include <memory>
#include <cmath>
#include <array>
#include <iostream>
#include <vector>

#include "Constants.h"

namespace math3d {

    // A vector whose elements are stored in contiguous memory
    template<typename T, unsigned Size>
    class Vector {
        // Proxy to an element in the vector
        struct Proxy;
    public:
        // Vector data accessors that allow 1,2,3 and 4D vectors to be used in semantically meaningful fashion.
        // For example:
        //      using Point2D = Vector<float, 2>
        //      Point2D origin{10, 10};
        //      origin.x += 10
        //      origin.y += 10;
        // or
        //      using RGBColor = Vector<float,3>
        //      RGBColor color{RED, GREEN, BLUE}
        //      glClearColor(color.r, color.g, color.b);
        union {Proxy x{}; Proxy r;};
        union {Proxy y{}; Proxy g;};
        union {Proxy z{}; Proxy b;};
        union {Proxy w{}; Proxy a;};

    private:
        // Definition of element proxy. Proxy is defined private so clients of vector cannot create proxies external to a vector
        struct Proxy {
            // Update element pointed to by the proxy to T. value is const T& to accept both l and rvalues
            // e.g.
            // using Point3D = Vector<float,3>;
            // Point3D p1, p2;
            // p1.x = 100.f
            // or
            // p2.x = p1.x;
            void operator=(T const& value) { // NOLINT: We are intentionally using a different signature for = operator
                if (!data) {
                    throw std::runtime_error("Invalid access!");
                }
                *data = value;
            }
            // Convert to T so a proxy can be used in expressions that involve T
            // e.g.
            // void someFunction(float val);
            // using Point3D = Vector<float,3>;
            // Point3D p1;
            // someFunction(p1.x);
            operator T() {          // NOLINT: Supress implicit conversion clang-tidy warning since we want Proxy to be
                                    //         converted to T implicitly without client calling Proxy.operator T() or
                                    //         doing an ugly cast
                return *data;
            }
            operator T() const {    // NOLINT
                return *data;
            }

            // Convert the address of the proxy to the address of the object
            // Allows conversions of this form:
            // Point2D windowSize;
            // getWindowSize(..., &windowSize.x, &windowSize.y);
            T* operator&() {        // NOLINT
                return data;
            }

            // Convenience functions for using vector's convenience members in shorthand expressions
            void operator+=(T const& another) {
                *data += another;
            }
            void operator-=(T const& another) {
                *data -= another;
            }
            void operator*=(T const& another) {
                *data *= another;
            }
            void operator/=(T const& another) {
                *data /= another;
            }
            void operator+=(Proxy const& another) {
                *data += *(another.data);
            }
            void operator-=(Proxy const& another) {
                *data -= *(another.data);
            }
            void operator*=(Proxy const& another) {
                *data *= *(another.data);
            }
            void operator/=(Proxy const& another) {
                *data /= *(another.data);
            }

        private:
            // Clear the proxy. Permits a Vector to be moved meaningfully by allowing the r-value that's moved to have its proxies
            // null-ed out. Defined private to prevent clients of vector from clobbering the internal state of a vector
            void reset() {
                data = nullptr;
            }

            void bind(T& element) {
                if(!data) {
                    data = &element;
                } else {
                    throw std::runtime_error("Proxy already bound");
                }
            }

            T* data {};

            // Allow the outer class Vector to call reset() to facilitate move operations
            friend Vector;
        };

        // These macros prevent code duplication in vector's constructors and operators
        #define SET_CONVENIENCE_MEMBERS           \
            switch (Size) {                       \
            case 4:                               \
                w.bind(data[3]);                  \
            case 3:                               \
                z.bind(data[2]);                  \
            case 2:                               \
                y.bind(data[1]);                  \
            case 1:                               \
                x.bind(data[0]);                  \
            default:                              \
                break;                            \
            }

        #define RESET_CONVENIENCE_MEMBERS(Vector) \
            Vector.x.reset();                     \
            Vector.y.reset();                     \
            Vector.z.reset();                     \
            Vector.w.reset();

        public:
            Vector() {
                SET_CONVENIENCE_MEMBERS
            }

            Vector(std::initializer_list<T> const& vals) {
                if (vals.size() != Size) {
                    throw std::invalid_argument("Dimension mismatch: Vector's dimension is " +
                                                std::to_string(Size) + " Input size is " +
                                                std::to_string(vals.size()));
                }
                for (size_t i = 0; i < vals.size(); ++i) {
                    data[i] = std::data(vals)[i];
                }
                SET_CONVENIENCE_MEMBERS
            }

            // Convenience constructor to build a vector with a different last component
            Vector(Vector<T, Size-1> const& another, T const val) {
                for (auto i = 0u; i < Size-1; ++i) {
                    data[i] = another[i];
                }
                data[Size-1] = val;
                SET_CONVENIENCE_MEMBERS
            }

            Vector(Vector const& other) {
               this->operator=(other);
               SET_CONVENIENCE_MEMBERS
            }

            Vector& operator=(Vector const& rhs) {
                if (&rhs != this) {
                    for (unsigned i = 0; i < Size; ++i) {
                        data[i] = rhs.data[i];
                    }
                }
                return *this;
            }

            Vector(Vector&& other) noexcept {
                data = std::move(other.data);
                SET_CONVENIENCE_MEMBERS
                RESET_CONVENIENCE_MEMBERS(other)
            }

            Vector& operator=(Vector&& other) noexcept {
                if (&other != this) {
                    data = std::move(other.data);
                    RESET_CONVENIENCE_MEMBERS(other)
                }
                return *this;
            }

            // Conversion constructor to build from an STL vector
            explicit Vector(std::vector<T> const& v) {
                if (Size != v.size()) {
                    throw std::invalid_argument("Dimension mismatch: Vector's dimension is " +
                                                std::to_string(Size) + " Input size is " +
                                                std::to_string(v.size()));
                }
                for (size_t i = 0; i < v.size(); ++i) {
                    data[i] = v[i];
                }
                SET_CONVENIENCE_MEMBERS
            }

            // Add this vector to another and return the sum
            Vector operator+(Vector const& another) const {
                Vector result;
                for (unsigned i = 0; i < Size; ++i) {
                    result.data[i] = this->data[i] + another.data[i];
                }
                return result;
            } 

            // Subtract this vector from another and return the difference
            Vector operator-(Vector const& another) const {
                Vector result;
                for (unsigned i = 0; i < Size; ++i) {
                    result.data[i] = this->data[i] - another.data[i];
                }
                return result;
            }

            T const& operator[](const unsigned index) const {
                if (index >= Size)
                    throw std::invalid_argument(std::to_string(index) + " is out of bounds."
                                                " Vector dimension is " + std::to_string(Size));
                return data[index];
            }

            T& operator[](const unsigned index) {
                if (index >= Size)
                    throw std::invalid_argument(std::to_string(index) + " is out of bounds."
                                                " Vector dimension is " + std::to_string(Size));
                return data[index];
            }
            
            // Compute cross product of this vector and another and return the mutually orthonormal vector
            Vector operator*(Vector const& another) const {
                static_assert(Size == 3, "Cross product can only be computed for 3D vectors");
                Vector result;
                auto* v1 = getData();
                auto* v2 = another.getData();
                result[0] = v1[1]*v2[2] - v1[2]*v2[1];
                result[1] = v2[0]*v1[2] - v1[0]*v2[2];
                result[2] = v1[0]*v2[1] - v1[1]*v2[0];
                return result; 
            }

            Vector operator*(T const scalar) const {
                Vector result;
                for(auto i = 0; i < Size; ++i) {
                    result[i] = scalar * data[i];
                }
                return result;
            }

            Vector operator-() const {
                Vector result;
                for(auto i = 0; i < Size; ++i) {
                    result[i] = -data[i];
                }
                return result;
            }

            Vector& normalize() {
                T norm = length();
                if (norm > constants::tolerance) {
                    for (size_t i = 0; i < Size; ++i) {
                        data[i] /= norm;
                    }
                }
                return *this;
            }

            Vector normalize() const {
                T norm = length();
                Vector result{*this};
                for (size_t i = 0; i < Size; ++i) {
                    result.data[i] /= norm;
                }
                return result;
            }

            T length() const {
                return static_cast<T> (sqrt(lengthSquared()));
            }

            T lengthSquared() const {
                T result = 0;
                for (size_t i = 0; i < Size; ++i) {
                    result += (data[i] * data[i]);
                }
                return result;
            }

            Vector operator/(const T scalar) const {
                Vector result;
                for (size_t i = 0; i < Size; ++i) {
                    result.data[i] = data[i]/scalar;
                }
                return result;
            }

            void operator/=(const T scalar) {
                for (size_t i = 0; i < Size; ++i) {
                    data[i] /= scalar;
                }
            }

            void operator+=(Vector const& another) {
                for (size_t i = 0; i < Size; ++i) {
                    data[i] += another[i];
                }
            }

            T dot(Vector const& another) const {
                T proj {};
                for (size_t i = 0; i < Size; ++i)
                    proj += this->operator[](i) * another[i];
                return proj;
            }

            template<typename AnotherType>
            operator Vector<AnotherType, Size>() const { // NOLINT
                static_assert(std::is_floating_point<AnotherType>::value, "Cannot convert vector to non-floating point types");
                Vector<AnotherType, Size> result;
                for (unsigned i = 0; i < Size; ++i) {
                    result[i] = data[i];
                }
                return result;
            }

            struct VectorProjection {
                Vector parallel;
                Vector perpendicular;
            };

            // TODO: Add derivation for this
            [[nodiscard]]
            VectorProjection getVectorProjection(Vector const& u) const {
                VectorProjection result;
                auto uNormalized = u / u.length();
                result.parallel = uNormalized * this->dot(uNormalized);
                result.perpendicular = *this - result.parallel;
                return result;
            }

            T const* getData() const { return data.data(); }
            T* getData() { return data.data(); }

            [[nodiscard]]
            std::string asString() const {
                std::string result{'['};
                for (auto i = 0; i < Size; ++i) {
                    result += std::to_string((*this)[i]) + ' ';
                }
                result.erase(result.size() - 1);
                result += ']';
                return result;
            }

            void print(std::ostream& os) const {
                os << '[';
                for (auto i = 0; i < Size; ++i) {
                    os << (*this)[i];
                    os << ((i == Size - 1) ? ']' : ',');
                }
            }

            void print() const {
                print(std::cout);
            }

            T* begin() {
                return data.begin();
            }

            T* end() {
                return data.end();
            }

        protected:
            std::array<T, Size> data{};
    };

    template<typename DataType, unsigned numRows>
    std::ostream& operator << (std::ostream& os, Vector<DataType, numRows> const& v) {
        v.print(os);
        return os;
    }

    template <typename DataType, unsigned numRows>
    Vector<DataType, numRows> operator*(DataType scalar, Vector<DataType, numRows> const& vector) {
        return vector * scalar;
    }

    template<typename T>
    using Vector2 = Vector<T,2>;

    template<typename T>
    using Vector3 = Vector<T,3>;

    template<typename T>
    using Vector4 = Vector<T,4>;

}
