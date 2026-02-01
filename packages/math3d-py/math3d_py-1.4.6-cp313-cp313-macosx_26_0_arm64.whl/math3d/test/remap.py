import os.path
from typing import List, Tuple

from math3d import AABB, Extent, Remap, Vector4

from math3d import Vector3

import pytest

class OBJReader:

    def __init__(self, filename:str):
        self._filename = filename

    @property
    def data(self) -> Tuple[List[Vector3], List[Tuple[int, int, int]]]:
        with open(self._filename, 'r') as obj_file:
            vertices: List[Vector3] = []
            faces: List[Tuple[int, int, int]] = []
            content = obj_file.readlines()
            for line in content:
                if line.startswith('v '):
                    _, x, y, z = line.split()
                    vertices.append(Vector3(float(x), float(y), float(z)))
                elif line.startswith('f '):
                    _, i, j, k = line.split()
                    faces.append((int(i), int(j), int(k)))
            return vertices, faces


class OBJWriter:

    def __init__(self, filename:str):
        self._filename = filename
        self._vertices: List[Vector3] = []
        self._faces: List[Tuple[int, int, int]] = []

    @property
    def vertices(self):
        return self._vertices

    @vertices.setter
    def vertices(self, verts: List[Vector3]):
        self._vertices = verts


    @property
    def faces(self):
        return self._faces

    @faces.setter
    def faces(self, faces: List[Tuple[int, int, int]]):
        self._faces = faces

    def write(self) -> None:
        with open(self._filename, 'w') as obj_file:
            vertices: List[str] = []
            for v in self._vertices:
                vertices.append(f'v {v.x} {v.y} {v.z}\n')
            obj_file.writelines(vertices)
            faces: List[str] = []
            for f in self._faces:
                faces.append(f'f {f[0]} {f[1]} {f[2]}\n')
            obj_file.writelines(faces)


def test_mesh_normalization():

    _TEST_OBJ_FILE = os.path.join(os.path.dirname(__file__), 'suzanne.obj')
    _TEST_OBJ_FILE_OUTPUT = os.path.join(os.path.dirname(__file__), 'suzanne_normalized.obj')
    _TEST_OBJ_FILE_UNMAPPED_OUTPUT = os.path.join(os.path.dirname(__file__), 'suzanne_unmapped.obj')

    reader = OBJReader(_TEST_OBJ_FILE)
    
    vertices, faces = reader.data
    
    extent_x: Extent = Extent()
    extent_y: Extent = Extent()
    extent_z: Extent = Extent()
    for vertex in vertices:
        extent_x.update(vertex.x)
        extent_y.update(vertex.y)
        extent_z.update(vertex.z)
    bounds = AABB(Vector3(extent_x.min, extent_y.min, extent_z.min),
                  Vector3(extent_x.max, extent_y.max, extent_z.max))
    
    normalized_bounds = AABB(Vector3(-1, -1, -1), Vector3(1, 1, 1))
    
    remap: Remap = Remap(bounds, normalized_bounds)
    normalized_vertices = [remap.remap(vertex) for vertex in vertices]

    writer = OBJWriter(_TEST_OBJ_FILE_OUTPUT)
    writer.vertices = normalized_vertices
    writer.faces = faces
    writer.write()

    inverse = remap.decode()
    homogenous_vertices = [inverse * Vector4(vertex) for vertex in normalized_vertices]
    unmapped_vertices = [Vector3(vertex.x, vertex.y, vertex.z) for vertex in homogenous_vertices]

    writer = OBJWriter(_TEST_OBJ_FILE_UNMAPPED_OUTPUT)
    writer.vertices = unmapped_vertices
    writer.faces = faces
    writer.write()




