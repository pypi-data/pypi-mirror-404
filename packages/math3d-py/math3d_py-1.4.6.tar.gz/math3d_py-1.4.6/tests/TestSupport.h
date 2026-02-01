#pragma once
#include <iostream>
#include <fstream>
#include <exception>
#include <filesystem>
#include <memory>
#include "3dmath/Constants.h"
#include "3dmath/Matrix.h"

// TODO: Move to support directory

namespace math3d::test {

    class TestSupport {
    public:
        static constexpr unsigned numberOfSamplesForRobustnessTest = 100;

        static bool areFilesEqual(std::filesystem::path const& file1,
                                  std::filesystem::path const& file2) {

            std::ifstream ifs1(file1.string(), std::ios::binary | std::ios::ate);
            std::ifstream ifs2(file2.string(), std::ios::binary | std::ios::ate);
            if (!ifs1 || !ifs2) {
                throw std::runtime_error("Unable to open input files");
            }

            auto size1 = ifs1.tellg();
            auto size2 = ifs2.tellg();
            if (size1 != size2) {
                std::cerr << "File sizes don't match" << std::endl;
                return false;
            }

            ifs1.seekg(0, std::ios::beg);
            ifs2.seekg(0,std::ios::beg);

            auto buffer1 = std::unique_ptr<char[]>(new char[size1]);
            auto buffer2 = std::unique_ptr<char[]>(new char[size2]);

            ifs1.read(buffer1.get(), size1);
            ifs2.read(buffer2.get(), size1);

            for (size_t i = 0; i < size1; ++i) {
                if (buffer1[i] != buffer2[i]) {
                    std::cerr << "File contents are different" << std::endl;
                    return false;
                }
            }

            return true;
        }

        static bool areBinarySTLFilesEqual(std::filesystem::path const& file1,
                                           std::filesystem::path const& file2) {

            auto file1Name = file1.string();
            auto file2Name = file2.string();

            std::ifstream ifs1(file1Name, std::ios::binary | std::ios::ate);
            std::ifstream ifs2(file2Name, std::ios::binary | std::ios::ate);
            if (!ifs1 || !ifs2) {
                throw std::runtime_error("Unable to open input files");
            }

            auto size1 = ifs1.tellg();
            auto size2 = ifs2.tellg();
            if (size1 != size2) {
                std::cerr << "File sizes don't match" << std::endl;
                return false;
            }

            ifs1.seekg(0, std::ios::beg);
            ifs2.seekg(0,std::ios::beg);

            auto buffer1 = std::unique_ptr<char[]>(new char[size1]);
            auto buffer2 = std::unique_ptr<char[]>(new char[size2]);

            ifs1.read(buffer1.get(), size1);
            ifs2.read(buffer2.get(), size1);

            // Compare 80 byte header
            auto offset = 0;
            for (auto i = offset; i < 80; ++i) {
                if (buffer1.get()[i] != buffer2.get()[i]) {
                    std::cerr << "STL headers are different" << std::endl;
                    char header1[80], header2[80];
                    memcpy(header1, buffer1.get(), 80);
                    memcpy(header2, buffer2.get(), 80);
                    std::cerr << file1Name << ':' << header1 << std::endl;
                    std::cerr << file2Name << ':' << header2 << std::endl;
                    return false;
                } else if (buffer1.get()[i] == '\0') {
                    // If the characters are eol, the end of the comment string has been reached
                    break;
                }
            }
            offset += 80;

            // Compare 4-byte num triangles
            unsigned numTris1 = *reinterpret_cast<unsigned*>(buffer1.get() + offset);
            unsigned numTris2 = *reinterpret_cast<unsigned*>(buffer2.get() + offset);
            if (numTris1 != numTris2) {
                std::cerr << file1Name << ':' << numTris1 << std::endl;
                std::cerr << file2Name << ':' << numTris2 << std::endl;
                return false;
            }
            offset += 4;

            // Compare triangles
            auto areXYZsEqual = [](float* data1, float* data2) {
                return fabs(data1[0] - data2[0]) < math3d::constants::tolerance &&
                       fabs(data1[1] - data2[1]) < math3d::constants::tolerance &&
                       fabs(data1[2] - data2[2]) < math3d::constants::tolerance;
            };
            for (auto triNum = 1; triNum <= numTris1; ++triNum) {
                float *tri1Normal, *tri2Normal;
                tri1Normal = reinterpret_cast<float*>(buffer1.get() + offset);
                tri2Normal = reinterpret_cast<float*>(buffer2.get() + offset);
                if (!areXYZsEqual(tri1Normal, tri2Normal)) {
                    std::cerr << "Normals are different for triangle " << triNum << std::endl;
                    std::cerr << file1Name << ':' << tri1Normal[0] << "," << tri1Normal[1] << "," << tri1Normal[2]   << std::endl;
                    std::cerr << file2Name << ':' << tri2Normal[0] << "," << tri2Normal[1] << "," << tri2Normal[2]   << std::endl;
                    return false;
                }

                float *vertex11, *vertex12;
                vertex11 = reinterpret_cast<float*>(buffer1.get() + offset + 12);
                vertex12 = reinterpret_cast<float*>(buffer2.get() + offset + 12);
                if (!areXYZsEqual(vertex11, vertex12)) {
                    std::cerr << "Vertex 1 is different for triangle " << triNum << std::endl;
                    std::cerr << file1Name << ':' << vertex11[0] << "," << vertex11[1] << "," << vertex11[2]   << std::endl;
                    std::cerr << file2Name << ':' << vertex12[0] << "," << vertex12[1] << "," << vertex12[2]   << std::endl;
                    return false;
                }

                float *vertex21, *vertex22;
                vertex21 = reinterpret_cast<float*>(buffer1.get() + offset + 24);
                vertex22 = reinterpret_cast<float*>(buffer2.get() + offset + 24);
                if (!areXYZsEqual(vertex21, vertex22)) {
                    std::cerr << "Vertex 2 is different for triangle " << triNum << std::endl;
                    std::cerr << file1Name << ':' << vertex21[0] << "," << vertex21[1] << "," << vertex21[2]   << std::endl;
                    std::cerr << file2Name << ':' << vertex22[0] << "," << vertex22[1] << "," << vertex22[2]   << std::endl;
                    return false;
                }

                float *vertex31, *vertex32;
                vertex31 = reinterpret_cast<float*>(buffer1.get() + offset + 36);
                vertex32 = reinterpret_cast<float*>(buffer2.get() + offset + 36);
                if (!areXYZsEqual(vertex31, vertex32)) {
                    std::cerr << "Vertex 3 is different for triangle " << triNum << std::endl;
                    std::cerr << file1Name << ':' << vertex31[0] << "," << vertex31[1] << "," << vertex31[2]   << std::endl;
                    std::cerr << file2Name << ':' << vertex32[0] << "," << vertex32[1] << "," << vertex32[2]   << std::endl;
                    return false;
                }

                unsigned short dummy1, dummy2;
                dummy1 = *reinterpret_cast<unsigned short*>(buffer1.get() + offset + 48);
                dummy2 = *reinterpret_cast<unsigned short*>(buffer2.get() + offset + 48);
                if (dummy1 != dummy2) {
                    std::cerr << "Dummy attribute count is different for triangle " << triNum << std::endl;
                    std::cerr << file1Name << dummy1 << std::endl;
                    std::cerr << file2Name << dummy2 << std::endl;
                    return false;
                }
                offset += 50;
            }

            return true;
        }
    };

}
