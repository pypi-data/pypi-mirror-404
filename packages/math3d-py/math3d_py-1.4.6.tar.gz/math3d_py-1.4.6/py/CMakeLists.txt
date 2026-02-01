cmake_minimum_required(VERSION 3.24.2)

project(3dmath_python VERSION 1.3.0)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED True)
include(FetchContent)
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG        v2.13.6
)
set(PYBIND11_FINDPYTHON ON)
find_package(Python 3.13 EXACT REQUIRED COMPONENTS Interpreter Development.Module)
FetchContent_MakeAvailable(pybind11)
message(STATUS "Using python ${Python_EXECUTABLE}")

include_directories(
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/../include/3dmath
)

if (NOT MAX_DIMENSIONS)
    set(MAX_DIMENSIONS 4)
endif()
message(STATUS "Generating vector and matrices of size ${MAX_DIMENSIONS}")
add_compile_definitions(MAX_DIMENSIONS=${MAX_DIMENSIONS})

file(GLOB bindingSrcs "./math3d/*.cpp")
pybind11_add_module(math3d MODULE ${bindingSrcs})
set_target_properties(math3d PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/math3d)
install(
    TARGETS math3d
    LIBRARY DESTINATION math3d
    RUNTIME DESTINATION math3d
    ARCHIVE DESTINATION math3d
)
