from io import BufferedReader, BytesIO
from array import array

import struct
import ast
import bmesh
import bpy

from . assetreader import MeshAsset

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

class MeshData():
    def __init__(self, vertex_positions: list, vertex_faces: list, vertex_uvs: list, vertex_normals: list, vertex_lods: list, version: str):
        self.vertex_positions = vertex_positions
        self.vertex_faces = vertex_faces
        self.vertex_uvs = vertex_uvs
        self.vertex_normals = vertex_normals
        self.vertex_lods = vertex_lods
        self.version = version

class MeshHeader():
    header_size = 0
    vertex_size = 0
    num_lods = 0
    num_faces = 0
    num_verts = 0
    num_meshes = 0
    num_bones = 0

def Vector3Float(file: BufferedReader):
    x = struct.unpack('<f', file.read(4))[0]
    y = struct.unpack('<f', file.read(4))[0]
    z = struct.unpack('<f', file.read(4))[0]

    return [x, y, z]

def Vector3Int(file: BufferedReader):
    x = int.from_bytes(file.read(4), "little")
    y = int.from_bytes(file.read(4), "little")
    z = int.from_bytes(file.read(4), "little")

    return [x, y, z]

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

def GetHeaderInformation(file: BufferedReader, mesh_version: float):
    file.read(1) # Space
    mesh_header = MeshHeader()
    mesh_header.header_size = int.from_bytes(file.read(2), "little")

    if (mesh_version <= 3.00):
        mesh_header.vertex_size = int.from_bytes(file.read(1), "little") 

        file.read(1) # LF
        if (mesh_header.header_size == 16):
            file.read(2) # CR
            mesh_header.num_lods = int.from_bytes(file.read(2), "little")
            mesh_header.num_verts = int.from_bytes(file.read(4), "little")
            mesh_header.num_faces = int.from_bytes(file.read(4), "little")

        if (mesh_header.header_size == 12):
            mesh_header.num_verts = int.from_bytes(file.read(4), "little")
            mesh_header.num_faces = int.from_bytes(file.read(4), "little")

        return mesh_header
   
    elif (mesh_version <= 4.00):
        mesh_header.num_meshes = int.from_bytes(file.read(2), "little") 
        mesh_header.num_verts = int.from_bytes(file.read(4), "little")
        mesh_header.num_faces = int.from_bytes(file.read(4), "little")
        mesh_header.num_lods = int.from_bytes(file.read(2), "little") 
        mesh_header.num_bones = int.from_bytes(file.read(2), "little")
        
        file.read(4) # nameTableSize
        file.read(2) # unknown
        file.read(2) # numSkinData

        return mesh_header


def MeshReader(file: BufferedReader):
    mesh_version = GetMeshVersion(file)
    vertex_positions = []
    vertex_faces = []
    vertex_uvs = []
    vertex_normals = []
    vertex_lods = []
    
    if (mesh_version <= 1.99):
        num_verts = GetTotalVertices(file) * 3
        
        for _ in range(num_verts):
            position = GetBracketArray(file)
            vertex_positions.append(position)
            
            normals = GetBracketArray(file)
            vertex_normals.append(normals)
            
            uv = GetBracketArray(file)[:-1] # we only need x and y
            vertex_uvs.append(uv)
        
        return MeshData(vertex_positions, vertex_faces, vertex_uvs, vertex_normals, vertex_lods, mesh_version)

    mesh_header = GetHeaderInformation(file, mesh_version)
    
    for _ in range(mesh_header.num_verts):
        position = Vector3Float(file)
        vertex_positions.append(position)
        
        normals = Vector3Float(file)
        vertex_normals.append(normals)
        
        uv = Vector3Float(file)[:-1]
        uv = [uv[0], -abs(uv[1])+1.0] # y is upside down
        vertex_uvs.append(uv)
        
        if (mesh_header.vertex_size == 40 or mesh_version <= 4.00):
            color_argb = int.from_bytes(file.read(4), "little")
            vertex_color = VertexColor(color_argb)
        else:
            color_white = 4294967295 # ARGB [255 255 255 255]
            vertex_color = color_white

    if (mesh_header.num_bones > 0):
        for _ in range(mesh_header.num_verts):
            file.read(4) # byte bones[4];
            file.read(4) # byte weights[4];

    for _ in range(mesh_header.num_faces):
        face_tuple = Vector3Int(file)
        vertex_faces.append(face_tuple)

    empty = file.read(4)
    for _ in range(mesh_header.num_lods):
        lod = int.from_bytes(file.read(4), "little")
        vertex_lods.append(lod)
    
    return MeshData(vertex_positions, vertex_faces, vertex_uvs, vertex_normals, vertex_lods, mesh_version)

def IsValidMeshFile(file: BufferedReader):
    version_string = file.read(7)
    if (version_string.decode("utf-8") == 'version'):
        return True

def OpenMeshFromFile(path: str):
    with open(path, "rb") as file:
        if IsValidMeshFile(path):
            return MeshReader(file)

def OpenMeshFromAsset(file: BytesIO):
    if IsValidMeshFile(file):
        return MeshReader(file)

def GetMeshData(data):
    if (type(data) == BytesIO):
        return OpenMeshFromAsset(data)
    elif (type(data) == str):
        return OpenMeshFromFile(data)
    else:
        print("Faulty mesh data")
        return None

def GetMeshFromMeshData(data: MeshAsset):
    mesh_data = GetMeshData(data.content.mesh)
    mesh_name = 'Mesh_' + str(mesh_data.version)
    mesh = bpy.data.meshes.new('mesh')
    
    basic_brick = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(basic_brick)
    
    bm = bmesh.new()
    bm.from_mesh(mesh)

    if (mesh_data.version <= 1.99):
        idx = 0
        while idx < len(mesh_data.vertex_positions):
            t_v1 = bm.verts.new(mesh_data.vertex_positions[idx])
            t_v2 = bm.verts.new(mesh_data.vertex_positions[idx+1])
            t_v3 = bm.verts.new(mesh_data.vertex_positions[idx+2])
            bm.faces.new([t_v1, t_v2, t_v3])
            idx += 3
        
        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.ensure_lookup_table()

        idx = 0
        for face in bm.faces:
            face.normal = mesh_data.vertex_normals[idx]
            for loop in face.loops:
                loop_uv = loop[uv_layer]
                loop_uv.uv = mesh_data.vertex_uvs[idx]
                idx += 1

        bm.to_mesh(mesh)
        bm.free()
    
    elif (mesh_data.version >= 2.00): 
        for idx, face in enumerate(mesh_data.vertex_faces):
            t_v1 = bm.verts.new(mesh_data.vertex_positions[face[0]])
            t_v2 = bm.verts.new(mesh_data.vertex_positions[face[1]])
            t_v3 = bm.verts.new(mesh_data.vertex_positions[face[2]])
            
            t_v1.normal = mesh_data.vertex_normals[face[0]]
            t_v2.normal = mesh_data.vertex_normals[face[1]]
            t_v3.normal = mesh_data.vertex_normals[face[2]]
            
            bm.faces.new([t_v1, t_v2, t_v3])
            if idx == mesh_data.vertex_lods[0]-1: # skip remaining faces, get highest lod mesh
                break
        
        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.ensure_lookup_table()

        for idx, face in enumerate(bm.faces):
            face_data = mesh_data.vertex_faces[idx]
            for vertex_idx, loop in enumerate(face.loops):
                current_vertex_uv = mesh_data.vertex_uvs[face_data[vertex_idx]]
                loop_uv = loop[uv_layer]
                loop_uv.uv = current_vertex_uv

        bm.to_mesh(mesh)
        bm.free()

    return mesh