from io import BufferedReader
from array import array
import struct

path = "./meshes/MeshTesting_V3"

class Vector3():
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

class Vector2():
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class Color_ARGB():
    def __init__(self, A: int, R: int, G: int, B: int):
        self.A = A
        self.R = R
        self.G = G
        self.B = B

class Vertex():
    def __init__(self, position: Vector3, normals: Vector3, uv: Vector2, vertex_color: Color_ARGB):
        self.position = position
        self.normals = normals
        self.uv = uv
        self.vertex_color = vertex_color


def Vector3Float(file: BufferedReader):
    x = struct.unpack('<f', file.read(4))
    y = struct.unpack('<f', file.read(4))
    z = struct.unpack('<f', file.read(4))

    return Vector3(x, y, z)

def VertexColor(vertex_color: int):
    vertex_bytes = vertex_color.to_bytes(4, 'little')

    a = vertex_bytes[0]
    r = vertex_bytes[1]
    g = vertex_bytes[2]
    b = vertex_bytes[3]
    return Color_ARGB(a, r, g, b)

def MeshReader(file: BufferedReader):
    file.read(1)
    mesh_version = float(file.read(4))
    file.read(1)
    file.read(2) # padding?
    vertex_size = int.from_bytes(file.read(1), "little") 
    file.read(1) # padding?
    file.read(2) # padding?
    num_lods = int.from_bytes(file.read(2), "little")
    num_verts = int.from_bytes(file.read(4), "little")
    num_faces = int.from_bytes(file.read(4), "little")

    vertex_list = []
    for i in range(num_verts):
        position = Vector3Float(file)
        normals = Vector3Float(file)

        uv_tmp = Vector3Float(file)
        uv = Vector2(uv_tmp.x, uv_tmp.y)

        color_argb = int.from_bytes(file.read(4), "little")
        vertex_color = VertexColor(color_argb)

        vertex_list.append(Vertex(position, normals, uv, vertex_color))

    print("done")

def OpenMeshFile(path):
    with open(path, "rb") as file:
        version_string = file.read(7)
        if (version_string.decode("utf-8") == 'version'):
            MeshReader(file)

OpenMeshFile(path)