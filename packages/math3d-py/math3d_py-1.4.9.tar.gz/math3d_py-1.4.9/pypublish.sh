#!/bin/bash

set -e

isPoetryInstalled=$(which poetry > /dev/null && echo $?)

if [[ $isPoetryInstalled -eq 1 ]]; then
  echo "poetry is not installed, cannot run python build"
  exit 1
fi


if [[ $# -eq 1 ]]; then

    if [[ "$1" == "patch_ver" ]]; then
        echo "Upgrading patch version"
        poetry version patch
    elif [[ "$1" == "minor_ver" ]]; then
        echo "Upgrading minor version"
        poetry version minor
    elif [[ "$1" == "major_ver" ]]; then
        echo "Upgrading major version"
        poetry version major
    else
        echo "Error: Unknown argument $1"
        exit 1
    fi
fi

# Ensure build is clean
cmake -S . -B build/
cmake --build build --parallel
ctest --test-dir build/
pushd py/math3d || exit
pytest
popd || exit

rm -rf dist/*
touch py/math3d/py.typed
poetry run pybind11-stubgen math3d -o py
CMAKE_BUILD_PARALLEL_LEVEL="$(sysctl -n hw.ncpu)" \
CMAKE_ARGS="-DenableTesting=OFF" poetry run python -m build
poetry run twine upload dist/*
