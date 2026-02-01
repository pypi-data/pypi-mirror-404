# get gtest
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG v1.17.0
)
FetchContent_MakeAvailable(googletest)
include(GoogleTest)

# Build tests in debug mode
add_compile_options(-g -DLLDB)

# All c++ sources in the test directory are considered to be tests
file(GLOB allTestSources *.cpp)

# Convenience target to build and run all tests
add_custom_target(3dmathTests COMMAND ctest --output-on-failure ${CMAKE_BINARY_DIR})

# Build all tests. Create a separate build target for each test and enable google test discovery
foreach(test ${allTestSources})
    get_filename_component(testTarget ${test} NAME_WE)
    add_executable(${testTarget} ${test})
    target_include_directories(${testTarget} PRIVATE ../include)
    target_link_libraries(${testTarget} gtest_main gmock_main)
    gtest_discover_tests(${testTarget})
    add_dependencies(3dmathTests ${testTarget})
endforeach()
