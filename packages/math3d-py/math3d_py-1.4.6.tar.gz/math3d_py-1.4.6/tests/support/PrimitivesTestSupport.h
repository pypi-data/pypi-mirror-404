#pragma once

#include "../../include/3dmath/primitives/Sphere.h"
#include "../../include/3dmath/Utilities.h"
#include "../../include/3dmath/TypeAliases.h"

namespace math3d::test {

    class PrimitivesTestSupport {
    public:
        enum class Containment {
            Inside,
            Outside,
            On
        };

        static math3d::types::Point3D getPointRelativeToSphere(math3d::Sphere const& sphere, Containment containment) {
            using namespace math3d::types;
            using namespace math3d;
            Point3D result;
            Vector3D direction = Utilities::RandomVector();
            direction.normalize();
            double distance = 0;
            switch (containment) {
                case Containment::Inside:
                    distance = Utilities::RandomNumber(0.0, sphere.getRadius());
                    break;
                case Containment::Outside:
                    distance = Utilities::RandomNumber(sphere.getRadius() + 1e-3, sphere.getRadius() + 100);
                    break;
                case Containment::On:
                    distance = sphere.getRadius();
                    break;
                default:
                    throw std::runtime_error("Unknown containment relationship");
            }
            return sphere.getCenter() + distance * direction;
        }

    };

}
