#pragma once
#include "Matrix.h"
#include <filesystem>
#include <fstream>
#include <sstream>

namespace math3d {
    template<typename DataType, unsigned numRows, unsigned numCols>
    void Matrix<DataType, numRows, numCols>::readFromFile(std::filesystem::path const& matrixFile,
                                                          Matrix& matrix,
                                                          char const delimiter) {

        if (!exists(matrixFile)) {
            throw std::runtime_error(matrixFile.string() + " does not exist");
        }

        std::ifstream ifs(matrixFile.string(), std::ios::binary | std::ios::ate);
        if (!ifs) {
            throw std::runtime_error("Error reading " + matrixFile.string());
        }

        auto fileSize = ifs.tellg();
        std::string fileContents(fileSize, ' ');

        ifs.seekg(0, std::ios::beg);
        ifs.read(fileContents.data(), fileSize);


        std::istringstream iss(fileContents, '\n');
        auto nextNumber = [delimiter](std::string const& row, long& delimiterPosition) -> DataType {
            size_t startPosition = delimiterPosition + 1;
            delimiterPosition = row.find_first_of(delimiter, delimiterPosition + 1);
            size_t endPosition = delimiterPosition - 1;
            return static_cast<DataType>(std::atof(row.substr(startPosition, endPosition).c_str()));
        };

        for (unsigned i = 0; i < numRows; ++i) {
            std::string row;
            long delimiterPosition = -1;
            getline(iss, row);
            for (unsigned j = 0; j < numCols; ++j) {
                if (j != 0 && delimiterPosition == std::string::npos) {
                    throw std::runtime_error("Malformed matrix");
                }
                matrix.data[j * numRows + i] = nextNumber(row, delimiterPosition);
            }
        }
    }

}