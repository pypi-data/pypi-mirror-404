#pragma once

#include <cmath>
#include <string>
#include <initializer_list>

#include "IdentityMatrix.h"
#include "ScalingMatrix.h"
#include "Vector.h"
#include "Utilities.h"
#include "TypeAliases.h"

namespace math3d {

    enum class CoordinateSystemHandedness {
        LeftHanded,
        RightHanded
    };

    template <typename T>
    struct Extent {
        T min;
        T max;
        T length() const { return max - min; }
        T center() const { return static_cast<T>(0.5*(max + min)); }
        void scale(T const scale) { min *= scale; max *= scale; }
        [[nodiscard]] std::string asString() const {
            return std::format("[{},{}]", min, max);
        }
        void merge(Extent const& another) {
            min = std::min(min, another.min);
            max = std::max(max, another.max);
        }
    };

    template<typename T>
    struct Bounds3D {
        Extent<T> x;
        Extent<T> y;
        Extent<T> z;

        Bounds3D() {
            reset();
        }

        Bounds3D(Extent<T> const& x, Extent<T> const& y, Extent<T> const& z) : x(x), y(y), z(z) {}

        Bounds3D(std::initializer_list<std::initializer_list<T>> const& initializerList) {
            auto const formatIsCorrect =
                    initializerList.size() == 2 &&
                    (data(initializerList)[0].size() == 2 ||  data(initializerList)[0].size() == 3) &&
                    data(initializerList)[0].size() == data(initializerList)[1].size();
            if (!formatIsCorrect) {
                throw std::runtime_error("Incorrect initializer list. "
                        "Use format:"
                        "{{Minimum X, Minimum Y, Minimum Z}, {Maximum X, Maximum Y, Maximum Z}} "
                        "For 2D bounds, Z extents can be skipped");
            }

            x.min = data(data(initializerList)[0])[0];
            y.min = data(data(initializerList)[0])[1];
            z.min = data(initializerList)[0].size() == 2 ? static_cast<T>(0) : data(data(initializerList)[0])[2];

            x.max = data(data(initializerList)[1])[0];
            y.max = data(data(initializerList)[1])[1];
            z.max = data(initializerList)[0].size() == 2 ? static_cast<T>(0) : data(data(initializerList)[1])[2];
        }

        // Builds a symmetric bounding box where each side is
        // of the specified length
        explicit Bounds3D(T const sideLength) {
            x.min = -0.5f * sideLength;
            x.max = +0.5f * sideLength;
            y.min = -0.5f * sideLength;
            y.max = +0.5f * sideLength;
            z.min = -0.5f * sideLength;
            z.max = +0.5f * sideLength;
        }

        T length() const {
            return sqrt(x.length() * x.length() + y.length() * y.length() + z.length() * z.length());
        }

        [[nodiscard]] Vector3<T> center() const {
            return {x.center(), y.center(), z.center()};
        }

        void reset() {
            x.min = std::numeric_limits<T>::max();
            y.min = std::numeric_limits<T>::max();
            z.min = std::numeric_limits<T>::max();
            x.max = -x.min;
            y.max = -y.min;
            z.max = -z.min;
        }

        bool contains(Vector<T, 3> const& point) const {
            auto const withinXExtent =
                (point.x > x.min && point.x < x.max) ||
                 fabs(point.x - x.min) < constants::tolerance ||
                 fabs(point.x - x.max) < constants::tolerance;

            auto const withinYExtent =
                (point.y > y.min && point.y < y.max) ||
                 fabs(point.y - y.min) < constants::tolerance ||
                 fabs(point.y - y.max) < constants::tolerance;

            auto const withinZExtent =
                (point.z > z.min && point.z < z.max) ||
                 fabs(point.z - z.min) < constants::tolerance ||
                 fabs(point.z - z.max) < constants::tolerance;

            return withinXExtent && withinYExtent && withinZExtent;
        }

        enum class Direction {
            x,
            y,
            z,
            All
        };

        void scale(T const scaleFactor, Direction direction = Direction::All) {
            if (direction == Direction::All || direction == Direction::x)
                x.scale(scaleFactor);
            if (direction == Direction::All || direction == Direction::y)
                y.scale(scaleFactor);
            if (direction == Direction::All || direction == Direction::z)
                z.scale(scaleFactor);
        }

        // Convenience conversion operator to convert string to allow quick-and-easy expressions such as std::puts(Bounds{})
        [[nodiscard]]
        std::string asString() const {
            std::stringstream ss;
            ss << *this;
            return ss.str();
        }

        [[nodiscard]] bool isValid() const {
            return x.min < x.max && y.min < y.max && z.min < z.max;
        }

        void merge(Bounds3D const& another) {
            x.merge(another.x);
            y.merge(another.y);
            z.merge(another.z);
        }

        [[nodiscard]]
        Vector3<T> min() const {
            return {x.min, y.min, z.min};
        }

        [[nodiscard]]
        Vector3<T> max() const {
            return {x.max, y.max, z.max};
        }

        /// @brief Gets the corner vertices of this bounding box
        ///
        /// The corners are returned lower back to front with the bottom corners appearing before the top ones
        [[nodiscard]]
        std::array<Vector3<T>, 8> corners() const {
            using Vec3 = Vector3<T>;

            auto lower_left_back = min();
            auto lower_right_back = lower_left_back + Vec3{x.length(), 0, 0};
            auto upper_right_back= lower_right_back + Vec3{0, y.length(), 0};
            auto upper_left_back = upper_right_back - Vec3{x.length(), 0, 0};

            auto upper_right_front = max();
            auto upper_left_front = upper_right_front - Vec3{x.length(), 0, 0};
            auto lower_left_front  = upper_left_front - Vec3{0, y.length(), 0};
            auto lower_right_front = lower_left_front + Vec3{x.length(), 0, 0};

            return {lower_left_back, lower_right_back, upper_right_back, upper_left_back,
                    lower_left_front, lower_right_front, upper_right_front, upper_left_front};
        }

        /// @brief Gets vertex indices of the quadrilateral faces of this bounding box
        ///
        /// Edges are returned in the following face order: front, right, back, left, bottom, and top
        [[nodiscard]]
        static constexpr std::array<std::array<uint8_t , 4>, 6> edges() {

            using Face = std::array<uint8_t, 4>;

            return {
                    Face{4, 5, 6, 7},
                    Face{5, 1, 2, 6},
                    Face{0, 1, 2, 3},
                    Face{0, 4, 7, 3},
                    Face{0, 1, 5, 4},
                    Face{6, 2, 3, 7}
                };
        }

        [[nodiscard]]
        Extent<T> extent(Direction dir) const {
            if (dir == Direction::x) {
                return x;
            }
            if (dir == Direction::y) {
                return y;
            }
            if (dir == Direction::z) {
                return z;
            }
            throw std::runtime_error(
                std::format("Direction {} is not supported in the extent accessor",
                            std::underlying_type_t<Direction>(dir))
            );
        }
    };

    template<typename T>
    class Remapper final {
    public:
        Remapper(Bounds3D<T> const& source, Bounds3D<T> const& destination)
            : source{source}
            , destination{destination}
            , remapTransform(std::nullopt) {
        }

        Vector3<T> operator()(Vector3<T> const& sourcePoint) const {
            if (!remapTransform) {
                computeRemapTransform();
            }
            auto remappedPoint = *remapTransform * Vector4<T>(sourcePoint, T{1});
            return {remappedPoint.x, remappedPoint.y, remappedPoint.z};
        }

        Matrix<T, 4, 4> getInverseTransform() {
            if (!remapTransform) {
                computeRemapTransform();
            }
            return remapTransform->inverse();
        }

        Bounds3D<T> const& getSource() const {
            return source;
        }

        Bounds3D<T> const& getDestination() const {
            return destination;
        }

    private:
        void computeRemapTransform() const {
            // For each source extent map [min, max] to [0, 1]
            // Then map [0, 1] to destination extent [min, max]
            Mat4 normalize = Identity4{};
            Mat4 remap = Identity4{};
            auto sourceExtentX = source.extent(Bounds3D<T>::Direction::x);
            auto sourceExtentY = source.extent(Bounds3D<T>::Direction::y);
            auto sourceExtentZ = source.extent(Bounds3D<T>::Direction::z);

            normalize(0, 0) = T{1} / sourceExtentX.length();
            normalize(1, 1) = T{1} / sourceExtentY.length();
            normalize(2, 2) = T{1} / sourceExtentZ.length();
            normalize(0, 3) = -sourceExtentX.min / sourceExtentX.length();
            normalize(1, 3) = -sourceExtentY.min / sourceExtentY.length();
            normalize(2, 3) = -sourceExtentZ.min / sourceExtentZ.length();
            auto destinationExtentX = destination.extent(Bounds3D<T>::Direction::x);
            auto destinationExtentY = destination.extent(Bounds3D<T>::Direction::y);
            auto destinationExtentZ = destination.extent(Bounds3D<T>::Direction::z);
            remap(0, 0) = destinationExtentX.length();
            remap(1 ,1) = destinationExtentY.length();
            remap(2, 2) = destinationExtentZ.length();
            remap(0, 3) = destinationExtentX.min;
            remap(1, 3) = destinationExtentY.min;
            remap(2, 3) = destinationExtentZ.min;
            remapTransform = std::make_optional(remap * normalize);
        }

        Bounds3D<T> const& source;
        Bounds3D<T> const& destination;
        using Mat4 = Matrix<T, 4, 4>;
        using Identity4 = IdentityMatrix<T, 4, 4>;
        using Scale4 = ScalingMatrix<T>;
        mutable std::optional<Mat4> remapTransform;
    };

    template<typename T>
    std::ostream& operator<<(std::ostream& os, Bounds3D<T> const& bounds3D) {
        os << "Min:[" << bounds3D.x.min << "," << bounds3D.y.min << "," << bounds3D.z.min << "] ";
        os << "Max:[" << bounds3D.x.max << "," << bounds3D.y.max << "," << bounds3D.z.max << "]";
        return os;
    }

    template<typename T>
    bool isZero(Extent<T> const extent) {
        return Utilities::isZero(std::fabs(extent.max - extent.min));
    }

    enum class IntersectionStatus {
        Intersects,
        NoIntersection,
        Skew
    };
    struct IntersectionResult {
        IntersectionStatus status;
        types::Vector3D intersectionPoint;
    };

}
