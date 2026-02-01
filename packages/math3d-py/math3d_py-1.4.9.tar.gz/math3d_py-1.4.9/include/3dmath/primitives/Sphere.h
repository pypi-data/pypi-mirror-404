#pragma once

#include "ConvexPrimitive.h"
#include "../PolarCoordinates.h"
#include "Ray.h"
#include "../TypeAliases.h"
#include <tuple>
#include <numbers>

namespace math3d {

    class Sphere : public ConvexPrimitive {

    public:
        Sphere(types::Point3D const& center, float radius, unsigned resolution = 16)
        : ConvexPrimitive(center)
        , radius(radius)
        , resolution(resolution) {

        }

        [[nodiscard]]
        types::Point3D getCenter() const {
            return origin;
        }

        [[nodiscard]]
        double getRadius() const {
            return radius;
        }

        [[nodiscard]]
        unsigned getResolution() const {
            return resolution;
        }

        // Refer to https://github.com/mdh81/3dmath/blob/master/derivations/Spherical_to_Cartesian.jpg
        void generateGeometry() override {
            if (!vertices.empty()) {
                std::cerr << "Warning: Skipping geometry generation. Geometry was already generated" << std::endl;
            }

            unsigned numCircles = resolution - 1;
            unsigned numCircleVertices = resolution;

            vertices.reserve((numCircleVertices * numCircles) + 2); // +2 for poles

            // Every pair of circles in the sphere will have resolution number of
            // quads in them. The two circles that join the poles will have resolution
            // number of triangles in them. Since we split quads into triangles we count
            // two faces for each quad
            unsigned numberOfQuads = resolution * numCircles - 1;
            unsigned numberOfTris = resolution * 2;
            tris.reserve((numberOfQuads * 2) + numberOfTris);

            // Generate vertices
            // We generate resolution number of circles in theta and phi directions. The first and last circles in the phi
            // direction are poles where the radius is zero. Phi will go from zero to 180 degrees, and theta will be a full
            // circle

            // Pole 1: At distance of radius from the center along +z
            vertices.emplace_back(Utilities::asFloat(origin +
                                  SphericalCoordinates{radius, 0., 0.}.getCartesianCoordinates()));

            // Circles between the two poles
            // In spherical coordinate system, phi = zero is a singularity, where theta has no influence on
            // the resulting coordinate. To prevent this, we start with phi at a sensible value given our resolution
            // constraint.
            float phiIncrement = constants::oneEightyDegreesInRadians / static_cast<float>(resolution);
            float thetaIncrement = constants::threeSixtyDegreesInRadians / static_cast<float>(resolution);
            float phi = phiIncrement, theta = 0.f;

            // Rotation by theta in spherical by convention rotates about the +z-axis. When theta is zero, the projection
            // of the spherical coordinate on the xy plane is on the +x-axis.
            // This coordinate (r, 0, phi) is our starting point for each circle. Each value of phi provides a new circle
            // and as theta varies from 0 to 360 we have new points on the chosen circle. All our circles are parallel
            // to the xy plane
            for (unsigned yzCircle = 1; yzCircle <= numCircles; ++yzCircle) {
                for (unsigned xyCircle = 1; xyCircle <= numCircleVertices; ++xyCircle) {
                    vertices.emplace_back(Utilities::asFloat(origin +
                                          SphericalCoordinates{radius, theta, phi}.getCartesianCoordinates()));
                    theta += thetaIncrement;
                }
                theta = 0.f;
                phi += phiIncrement;
            }

            // Pole 2: At distance of radius from the center along -z
            vertices.emplace_back(Utilities::asFloat(origin +
                                  SphericalCoordinates{radius, 0.f, constants::oneEightyDegreesInRadians}.getCartesianCoordinates()));

            // Generate faces
            // NOTE: In the two lambdas below, indices are vertex indices
            // quadNumber is [1, resolution] and it identifies the quadrilateral formed between corresponding segments of
            // two circles
            // circle1Index is the vertex index of the vertex on circle 1. circleIndex and circleIndex+1 define a segment on circle 1
            // circle2Index is the same as circle1Index but for circle 2
            auto createSplitQuad = [this](unsigned quadNumber, unsigned circle1Index, unsigned circle2Index) {
                // The quad is created between the pairs (circle1Index, circle1Index+1) and (circle2Index, circle2Index+1)
                // with consideration for the last segment in the circle, in which case, the second index in these two pairs
                // is subtracted from resolution to loop back to the first vertex in their respective circles
                bool isLastSegment = quadNumber == resolution;
                unsigned a = circle1Index;
                unsigned b = isLastSegment ? a + 1 - resolution : a + 1;
                unsigned c = circle2Index;
                unsigned d = isLastSegment ? c + 1 - resolution : c + 1;
                this->tris.emplace_back(orientTriangleNormalOutside({a, b, c}));
                this->tris.emplace_back(orientTriangleNormalOutside({b, c, d}));
            };

            // triangleNumber is [1...resolution], and it identifies the triangle that's constructed
            // poleIndex is the vertex index of the vertex at the poles, and it is either 0 or Number of Vertices-1
            // circleIndex is the vertex index of the vertex on the circle that is being joined with the pole
            auto createTri = [this](unsigned triangleNumber, unsigned poleIndex, unsigned circleIndex) {
                bool isLastSegment = triangleNumber == resolution;
                unsigned a = poleIndex;
                unsigned b = circleIndex;
                unsigned c = isLastSegment ? b + 1 - resolution : b + 1;
                this->tris.emplace_back(orientTriangleNormalOutside({a, b, c}));
            };

            // Faces between the first pole and circle
            unsigned nextIndex = 1;
            for (unsigned triangleNumber = 1; triangleNumber <= resolution; ++triangleNumber, ++nextIndex) {
                createTri(triangleNumber, 0, nextIndex);
            }

            // Faces between circles
            unsigned circle1VertexIndex = 1;
            unsigned circle2VertexIndex = circle1VertexIndex + resolution;
            for (unsigned circleNumber = 1; circleNumber < resolution - 1; ++circleNumber) {
                // Join corresponding edges to form a quad and then split that quad into two triangles
                for (unsigned quadNumber = 1; quadNumber <= resolution; ++quadNumber, ++circle1VertexIndex, ++circle2VertexIndex) {
                    createSplitQuad(quadNumber, circle1VertexIndex, circle2VertexIndex);
                }
            }

            // Faces between the second pole and final circle
            nextIndex = static_cast<unsigned>(vertices.size() - 1 - resolution);
            for (unsigned triangleNumber = 1; triangleNumber <= resolution; ++triangleNumber, ++nextIndex) {
                createTri(triangleNumber, vertices.size() - 1, nextIndex);
            }
        }

        // Refer to
        // 1. https://github.com/mdh81/3dmath/raw/master/derivations/RaySphereIntersection_1.jpg
        // 2. https://github.com/mdh81/3dmath/raw/master/derivations/RaySphereIntersection_2.jpg
        // to see the derivation of the formula used in this method
        IntersectionResult intersectWithRay(Ray const& ray) override {
            IntersectionResult result;

            auto radiusSqr = radius * radius;
            types::Vector3D rayOriginToCenter = getOrigin() - ray.getOrigin();
            auto rayOriginToCenterLengthSqr = rayOriginToCenter.lengthSquared();

            // Special case: If the ray origin is on the sphere, just return the ray origin as the intersection point
            // ray direction does not matter in this case
            if (Utilities::areEqual(rayOriginToCenterLengthSqr, radiusSqr)) {
                result.status = IntersectionStatus::Intersects;
                result.intersectionPoint = ray.getOrigin();
                return result;
            }

            // Compute projection of the vector from ray origin to sphere center on the ray
            auto projection = rayOriginToCenter.dot(ray.getDirection());
            auto projectionSqr = projection * projection;

            // Compute the shortest distance between sphere center and the ray
            auto perpendicularDistanceSqr = rayOriginToCenterLengthSqr - projectionSqr;

            bool intersects =
                    (projection > 0 && Utilities::isLessThanOrEqual(perpendicularDistanceSqr, radiusSqr)) ||
                    (projection < 0 && Utilities::isLessThanOrEqual(rayOriginToCenterLengthSqr, radiusSqr));

            if (intersects) {
                // return the first intersection point in the direction of the ray
                result.status = IntersectionStatus::Intersects;

                // Compute distance between intersection point and projected sphere center
                auto beta = sqrt(radiusSqr - perpendicularDistanceSqr);

                // Compute distance between ray origin and intersection point
                bool sphereCenterIsBehindRayOrigin = projection < 0;
                bool rayOriginIsInsideSphere = rayOriginToCenterLengthSqr < radiusSqr;
                auto alpha = 1.0;

                // There are three possible relationships between the ray origin and the sphere center when there is an intersection
                if (rayOriginIsInsideSphere && sphereCenterIsBehindRayOrigin) {
                    alpha = beta - fabs(projection);
                } else if (rayOriginIsInsideSphere && !sphereCenterIsBehindRayOrigin) {
                    alpha = projection + beta;
                } else if (!rayOriginIsInsideSphere && !sphereCenterIsBehindRayOrigin) {
                    alpha = projection - beta;
                }

                // Compute the intersection point using distance from ray origin
                result.intersectionPoint = ray.getOrigin() + alpha * ray.getDirection();
            } else {
                result.status = IntersectionStatus::NoIntersection;
            }

            return result;
        }

    protected:
        double const radius;
        unsigned const resolution;

    friend std::ostream& operator<<(std::ostream& os, Sphere const&);
    };

    inline std::ostream& operator<<(std::ostream& os, Sphere const& sphere) {
        os << "Radius " << sphere.getRadius() << " Center " << sphere.getCenter();
        return os;
    }
}
