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

class Vertex():
    def __init__(self, position: Vector3, normals: Vector3, uv: Vector2, vertex_color: int):
        self.position = position
        self.normals = normals
        self.uv = uv
        self.vertex_color = vertex_color

def Vector3Float(file: BufferedReader):
    x = struct.unpack('<f', file.read(4))
    y = struct.unpack('<f', file.read(4))
    z = struct.unpack('<f', file.read(4))

    return Vector3(x, y, z)

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

    position = Vector3Float(file)
    normals = Vector3Float(file)
    
    uv_tmp = Vector3Float(file)
    uv = Vector2(uv_tmp.x, uv_tmp.y)

    print(position.x, position.y, position.z)
    print(normals.x, normals.y, normals.z)
    print(uv.x, uv.y)

def OpenMeshFile(path):
    with open(path, "rb") as file:
        version_string = file.read(7)
        if (version_string.decode("utf-8") == 'version'):
            MeshReader(file)

OpenMeshFile(path)