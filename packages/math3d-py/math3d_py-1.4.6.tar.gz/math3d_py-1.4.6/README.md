# 3dmath

A header-only 3D math library used for building apps like [MeshViewer](https://github.com/mdh81/meshviewer)

[![Quality](https://github.com/mdh81/3dmath/actions/workflows/cmake-single-platform.yml/badge.svg)](https://github.com/mdh81/3dmath/actions/workflows/cmake-single-platform.yml)

## Build and Test

```bash
$ cd <path to 3dmath> && mkdir <build dir>
$ cmake -S . -B <build dir>
$ cmake --build <build dir>/ --parallel
$ ctest --test-dir <build dir>
```


## Python Bindings

Python bindings are generated using the excellent [pybind11](https://github.com/pybind/pybind11) library

### Building and testing python bindings
1. Python 3.13 is prerequisite. Install it via pyenv or uv
2. Poetry is a prerequisite. Install it via usual channels (e.g. `brew install poetry`). 

```bash
$ poetry use python 3.13
$ source .venv/bin/activate
$ cd <path to 3dmath> && mkdir <build dir>
$ cmake -S . -B <build dir> -DenableTesting=OFF
$ cmake --build <build dir>/ --parallel --target math3d
$ poetry install 
$ python
> import math3d
```

Any changes to python bindings or to the core C++ code requires a rebuild of the pybind11 target `math3d` before python
will see those changes. Rebuild with `cmake --build build/ --parallel --target math3d`