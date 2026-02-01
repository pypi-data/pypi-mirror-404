#include "gtest/gtest.h"
#include "3dmath/Vector.h"
#include "3dmath/TranslationMatrix.h"
#include "3dmath/Utilities.h"
#include "3dmath/TypeAliases.h"
#include <iostream>
using namespace std;
using namespace math3d;

TEST(TranslationMatrix, DefaultConstruction) {

    TranslationMatrix<double> t;
    std::vector<Vector<double, 4>> columns;
    for (auto i : {0, 1, 2, 3}) {
        columns.push_back(t[i]);
    }
    ASSERT_FLOAT_EQ(columns[0].dot(Vector<double, 4>(constants::xAxis, 0.f)), 1.f);
    ASSERT_FLOAT_EQ(columns[1].dot(Vector<double, 4>(constants::yAxis, 0.f)), 1.f);
    ASSERT_FLOAT_EQ(columns[2].dot(Vector<double, 4>(constants::zAxis, 0.f)), 1.f);
    ASSERT_FLOAT_EQ(columns[3].dot(Vector<double, 4>{0, 0, 0, 1}), 1.f);
}

TEST(TranslationMatrix, ConstructionWithTranslation) {
    TranslationMatrix<double> t({100, 200, 300});
    Vector<double, 4> lastColumn = t[3];
    ASSERT_FLOAT_EQ(lastColumn[0], 100.f);
    ASSERT_FLOAT_EQ(lastColumn[1], 200.f);
    ASSERT_FLOAT_EQ(lastColumn[2], 300.f);
    ASSERT_FLOAT_EQ(lastColumn[3], 1.f);
}