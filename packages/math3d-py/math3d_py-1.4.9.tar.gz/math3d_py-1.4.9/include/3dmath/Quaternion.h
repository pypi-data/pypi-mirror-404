#pragma once

#include "Vector.h"
#include "Utilities.h"
#include <cmath>

namespace math3d {

    template<typename T>
    class Quaternion {
        public:
            Quaternion(T angle, Vector<T, 3> axis)
            : theta(angle)
            , axisVector(std::move(axis)) {
                axisVector.normalize();
                w();
                v();
            }

            T angle() const {
                return theta;
            }

            Vector<T, 3> axis() const {
                return axisVector;
            }

            T magnitude() const {
            	return std::sqrt(wSqr() + vSqr());
           	}

            Quaternion conjugate() const {
                return Quaternion{theta,  static_cast<T>(-1) * axisVector };
            }

            Quaternion inverse() const {
                return conjugate() * (1/magnitude());
            }

            Quaternion operator*(T scalar) const {
                return Quaternion{scalar * theta, scalar * axisVector};
            }

        private:
            void w() {
                wComponent = static_cast<T>(std::cos(Utilities::asRadians(theta * 0.5)));
            }

            [[nodiscard]] T w() const {
            	return wComponent;
            }

            [[nodiscard]] T wSqr() const {
                return wComponent * wComponent;
            }

            void v() {
                auto n = axisVector.normalize();
                auto sinThetaByTwo = static_cast<T>(std::sin(Utilities::asRadians(theta * 0.5)));
                vComponent = sinThetaByTwo * n;
            }

            [[nodiscard]] Vector<T, 3> v() const {
                return vComponent;
            }

            [[nodiscard]] T vSqr() const {
                return v().lengthSquared();
            }

            T theta{};
            Vector<T, 3> axisVector{};
            T wComponent;
            Vector<T,3> vComponent;
    };

    // Post multiply
    template<typename T>
    Quaternion<T> operator*(T const scalar, Quaternion<T> const& quaternion) {
        return quaternion * scalar;
    }
}