#pragma once

#include <array>
#include <fstream>
#include "Primitive.h"
#include "../SupportingTypes.h"
#include "../Utilities.h"

namespace math3d {
    // Ray has an origin and a direction. The direction is normalized and the ray is
    // assumed to extend to infinity from the origin
    class Ray : public Primitive {
    public:
        Ray(types::Point3D const& origin, types::Vector3D const& direction, float geometryLength = 1)
        : origin(origin)
        , direction(direction)
        , geometryLength(geometryLength) {
            this->direction.normalize();
        }

        ~Ray() = default;

        // See https://github.com/mdh81/3dmath/blob/master/derivations/PointDistanceToRay.jpg
        [[nodiscard]]
        auto distanceToPoint(types::Point3D const& point) const {
            auto v = point - origin;
            auto lengthOfV = v.length();
            auto angle = acos(v.dot(direction) / lengthOfV);
            return lengthOfV * sin(angle) ;
        }

        // Please refer to
        // https://github.com/mdh81/3dmath/raw/master/derivations/RayRayIntersection.jpg
        IntersectionResult intersectWithRay(Ray const& ray) override {
            // Initialize result
            IntersectionResult result;
            result.status = IntersectionStatus::NoIntersection;

            // No intersection if rays are parallel
            auto d1xd2 = this->direction * ray.direction;
            if (!Utilities::isZero(d1xd2.length())) {

                // Parametric distance along ray to the intersection point
                auto d1xd2Length = d1xd2.length();
                auto t = ((ray.getOrigin() - origin) * ray.getDirection()).dot(d1xd2) / (d1xd2Length * d1xd2Length);

                // Intersection that occurs behind the ray origin is not a valid intersection
                if (t > 0 || Utilities::isZero(t)) {

                    result.intersectionPoint = origin + (t * direction);

                    // For the intersection to be valid, the intersection point should be on the ray, otherwise
                    // the two rays are on parallel planes. Use the second ray for this calculation since
                    // the intersection point was computed using the first ray
                    if (Utilities::isZero(ray.distanceToPoint(result.intersectionPoint))) {
                        result.status = IntersectionStatus::Intersects;
                    } else {
                        result.status = IntersectionStatus::Skew;
                    }
                }
            }

            return result;
        }

        [[nodiscard]]
        types::Vector3D getDirection() const {
            return direction;
        }

        [[nodiscard]]
        types::Point3D getOrigin() const {
            return origin;
        }

        void generateGeometry() override {
            // Line
            vertices.push_back(origin);

            auto endPoint = origin + static_cast<double>(geometryLength) * direction;
            vertices.push_back(endPoint);
            // Arrow
            auto perpendicular = Utilities::getPerpendicular(direction);
            // leg 1 is halfway vector between the ray direction and its normal
            auto leg1= (perpendicular + direction) * 0.5;
            // leg 2 is halfway vector between the ray direction and the negative of its normal
            auto leg2 = (-perpendicular + direction) * 0.5;
            // To orient the arrow facing away from the ray origin, negate the halfway vectors
            vertices.push_back(endPoint + ((0.02 * geometryLength) * -leg1));
            vertices.push_back(endPoint + ((0.02 * geometryLength) * -leg2));
        }

        void writeToFile(const std::filesystem::path &outputFile) override {
            auto extension = outputFile.extension().string().substr(1);
            if (extension == "OBJ" || extension == "obj") {
                if (vertices.empty()) {
                    generateGeometry();
                }
                std::ofstream ofs(outputFile.string());
                for (auto& vertex : vertices) {
                    ofs << "v " << vertex.x << ' ' << vertex.y << ' ' << vertex.z << std::endl;
                }
                ofs << "f 1 2" << std::endl;
                ofs << "f 2 3" << std::endl;
                ofs << "f 2 4" << std::endl;

                ofs.close();
            } else {
                throw std::runtime_error("Only OBJ output is supported for rays");
            }
        }

    private:
        types::Point3D origin;
        types::Vector3D direction;
        float const geometryLength;

    friend std::ostream& operator<<(std::ostream& os, Ray const& ray);
    };


    inline std::ostream& operator<<(std::ostream& os, Ray const& ray) {
        os << "Origin " << ray.getOrigin() << " Direction " << ray.getDirection();
        return os;
    }
}