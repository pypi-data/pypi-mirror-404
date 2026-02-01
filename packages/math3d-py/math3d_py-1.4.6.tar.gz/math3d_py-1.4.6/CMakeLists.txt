cmake_minimum_required(VERSION 3.24.2)

project(3dmath VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED True)

set(INSTALL_GTEST OFF)

add_library(3dmath INTERFACE)
target_include_directories(
    3dmath INTERFACE
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
    "$<INSTALL_INTERFACE:include/3dmath>")

# This allows testing to be skipped by root modules by setting enableTesting to OFF
if (NOT DEFINED enableTesting)
    message(STATUS "Enabling tests")
    set(enableTesting ON)
endif()

if (enableTesting)
    enable_testing()
    add_subdirectory(tests)
endif()

add_subdirectory(py)
