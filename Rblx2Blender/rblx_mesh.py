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
    x = struct.unpack('<f', file.read(4))[0]
    y = struct.unpack('<f', file.read(4))[0]
    z = struct.unpack('<f', file.read(4))[0]

    return Vector3(x, y, z)

def Vector3Int(file: BufferedReader):
    x = int.from_bytes(file.read(4), "little")
    y = int.from_bytes(file.read(4), "little")
    z = int.from_bytes(file.read(4), "little")

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
    if (mesh_version < 3.00):
        print("mesh version above 3 not supported")

    file.read(1)
    
    header_size = int.from_bytes(file.read(2), "little")
    vertex_size = int.from_bytes(file.read(1), "little") 
    
    if (header_size == 16):
        file.read(1)
        file.read(2)
        num_lods = int.from_bytes(file.read(2), "little") # lods could be implemented later for example for unity.
        num_verts = int.from_bytes(file.read(4), "little")
        num_faces = int.from_bytes(file.read(4), "little")
    
    if (header_size == 12):
        file.read(1)
        num_verts = int.from_bytes(file.read(4), "little")
        num_faces = int.from_bytes(file.read(4), "little")


    vertex_list = []
    vertex_position_list = []
    for _ in range(num_verts):
        position = Vector3Float(file)
        vertex_position_list.append([position.x, position.y, position.z])
        
        normals = Vector3Float(file)
        uv_tmp = Vector3Float(file)
        uv = Vector2(uv_tmp.x, uv_tmp.y)
        
        if (vertex_size == 16):
            color_argb = int.from_bytes(file.read(4), "little")
            vertex_color = VertexColor(color_argb)
        else:
            color_white = 4294967295 # 255 255 255 255
            vertex_color = color_white

        vertex_list.append(Vertex(position, normals, uv, vertex_color))

    vertex_face_list = []
    for _ in range(num_faces):
        face_tuple = Vector3Int(file)
        vertex_face_list.append([face_tuple.x, face_tuple.y, face_tuple.z])
    
    return [vertex_position_list, vertex_face_list]

def OpenMeshFile(path: str):
    with open(path, "rb") as file:
        version_string = file.read(7)
        if (version_string.decode("utf-8") == 'version'):
            return MeshReader(file)