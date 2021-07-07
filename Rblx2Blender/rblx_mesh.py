from io import BufferedReader
from array import array

import struct
import ast

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

class Mesh():
    def __init__(self, vertex_positions: list, vertex_faces: list, vertex_uvs: list, version: str):
        self.vertex_positions = vertex_positions
        self.vertex_faces = vertex_faces
        self.vertex_uvs = vertex_uvs
        self.version = "0.0"

class MeshHeader():
    header_size = 0
    vertex_size = 0
    num_lods = 0
    num_faces = 0
    num_verts = 0

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

def GetTotalVertices(file: BufferedReader):
    tmp_byte = file.read(1)
    if (tmp_byte.decode() == "\n"):
        pass
    else:
        file.read(1) # CR LF
    byte_array = bytearray()
    while True:
        tmp_byte = file.read(1)
        if (tmp_byte.decode() == "\r"): # CR LF
            file.read(1)
            break
        elif (tmp_byte.decode() == "\n"):
            break
        else:
            byte_array.extend(tmp_byte)
    num_verts = int(byte_array.decode('ascii'))
    return(num_verts)

def GetBracketArray(file: BufferedReader):
    byte_array = bytearray()
    while True:
        tmp_byte = file.read(1)
        if (tmp_byte.decode() == "]"):
            byte_array.extend(tmp_byte)
            break
        else:
            byte_array.extend(tmp_byte)
    bracket_array = ast.literal_eval(byte_array.decode('ascii'))
    return(bracket_array)

def GetMeshVersion(file: BufferedReader):
    file.read(1) # Space
    mesh_version = float(file.read(4))
    return mesh_version

def GetHeaderInformation(file: BufferedReader):
    file.read(1) # Space

    mesh_header = MeshHeader()
    
    mesh_header.header_size = int.from_bytes(file.read(2), "little")
    mesh_header.vertex_size = int.from_bytes(file.read(1), "little") 
    
    file.read(1) # LF
    if (mesh_header.header_size == 16):
        file.read(2) # CR
        mesh_header.num_lods = int.from_bytes(file.read(2), "little") # lods could be implemented later.
        mesh_header.num_verts = int.from_bytes(file.read(4), "little")
        mesh_header.num_faces = int.from_bytes(file.read(4), "little")
    
    if (mesh_header.header_size == 12):
        mesh_header.num_verts = int.from_bytes(file.read(4), "little")
        mesh_header.num_faces = int.from_bytes(file.read(4), "little")

    return mesh_header

def MeshReader(file: BufferedReader):
    mesh_version = GetMeshVersion(file)
    
    if (mesh_version < 2.00):
        vertex_position_list = []
        vertex_face_list = []
        num_verts = GetTotalVertices(file) * 3
        
        for _ in range(num_verts):
            position = GetBracketArray(file)
            vertex_position_list.append(position)
            normals = GetBracketArray(file)
            uv = GetBracketArray(file)[:-1]
        
        return [vertex_position_list, vertex_face_list]

    if (mesh_version > 3.00):
        print("mesh version above 3 not supported")

    mesh_header = GetHeaderInformation(file)

    vertex_list = []
    vertex_position_list = []
    vertex_uv_list = []
    vertex_face_list = []
    
    for _ in range(mesh_header.num_verts):
        position = Vector3Float(file)
        vertex_position_list.append([position.x, position.y, position.z])
        
        normals = Vector3Float(file)
        uv_tmp = Vector3Float(file)
        uv = Vector2(uv_tmp.x, uv_tmp.y)
        vertex_uv_list.append([uv_tmp.x, uv_tmp.y])
        
        if (mesh_header.vertex_size == 40):
            color_argb = int.from_bytes(file.read(4), "little")
            vertex_color = VertexColor(color_argb)
        else:
            color_white = 4294967295 # 255 255 255 255
            vertex_color = color_white

        vertex_list.append(Vertex(position, normals, uv, vertex_color))

    for _ in range(mesh_header.num_faces):
        face_tuple = Vector3Int(file)
        vertex_face_list.append([face_tuple.x, face_tuple.y, face_tuple.z])
    
    return [vertex_position_list, vertex_face_list, vertex_uv_list]

def OpenMeshFile(path: str):
    with open(path, "rb") as file:
        version_string = file.read(7)
        if (version_string.decode("utf-8") == 'version'):
            return MeshReader(file)

def GetMeshFile(path: str):
    mesh_data = OpenMeshFile(path)