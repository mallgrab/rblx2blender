from io import BufferedReader
from array import array

import struct
import ast
import bmesh
import bpy

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
    def __init__(self, vertex_positions: list, vertex_faces: list, vertex_uvs: list, vertex_normals: list, version: str):
        self.vertex_positions = vertex_positions
        self.vertex_faces = vertex_faces
        self.vertex_uvs = vertex_uvs
        self.vertex_normals = vertex_normals
        self.version = version

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
    vertex_list = []
    vertex_positions = []
    vertex_faces = []
    vertex_uvs = []
    vertex_normals = []
    
    if (mesh_version < 2.00):
        num_verts = GetTotalVertices(file) * 3
        
        for _ in range(num_verts):
            position = GetBracketArray(file)
            vertex_positions.append(position)
            
            normals = GetBracketArray(file)
            vertex_normals.append(normals)
            
            uv = GetBracketArray(file)[:-1] # we only need x and y
            vertex_uvs.append(uv)
        
        return MeshData(vertex_positions, vertex_faces, vertex_uvs, vertex_normals, mesh_version)

    if (mesh_version > 3.00):
        print("mesh version above 3 not supported")

    mesh_header = GetHeaderInformation(file)
    
    for _ in range(mesh_header.num_verts):
        position = Vector3Float(file)
        vertex_positions.append([position.x, position.y, position.z])
        
        normals = Vector3Float(file)
        uv_tmp = Vector3Float(file)
        uv = Vector2(uv_tmp.x, uv_tmp.y)
        vertex_uvs.append([uv_tmp.x, uv_tmp.y])
        
        if (mesh_header.vertex_size == 40):
            color_argb = int.from_bytes(file.read(4), "little")
            vertex_color = VertexColor(color_argb)
        else:
            color_white = 4294967295 # ARGB [255 255 255 255]
            vertex_color = color_white

        vertex_list.append(Vertex(position, normals, uv, vertex_color))

    for _ in range(mesh_header.num_faces):
        face_tuple = Vector3Int(file)
        vertex_faces.append([face_tuple.x, face_tuple.y, face_tuple.z])
    
    return MeshData(vertex_positions, vertex_faces, vertex_uvs, vertex_normals, mesh_version)

def OpenMeshFromFile(path: str):
    with open(path, "rb") as file:
        version_string = file.read(7)
        if (version_string.decode("utf-8") == 'version'):
            return MeshReader(file)

def GetMeshFromFile(path: str):
    """
        mesh_uv_layer = mesh_data.uv_layers.new()
        
        #for loop in bpy.context.active_object.data.loops:
        #    mesh_uv_layer.data[loop.index].uv = mesh_vertices[2][loop.index]

        # https://docs.blender.org/api/current/bpy.types.MeshUVLoopLayer.html#bpy.types.MeshUVLoopLayer
    """
    mesh_data = OpenMeshFromFile(path)

    if (mesh_data.version <= 1.99):
        v = 'Mesh_' + str(mesh_data.version)
        mesh = bpy.data.meshes.new('Mesh_' + str(mesh_data.version))
        mesh_uv_layer = mesh.uv_layers.new(name="MeshUV")
        
        basic_brick = bpy.data.objects.new("Part_Mesh", mesh)
        bpy.context.collection.objects.link(basic_brick)
        
        bm = bmesh.new()
        bm.from_mesh(mesh)

        idx = 0
        while idx < int(len(mesh_data.vertex_positions)):
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
        mesh = bpy.data.meshes.new('Mesh_' + str(mesh_data.version))
        
        # replace this where we construct the mesh from the face array information of mesh_data
        # the reason for it is so that we can define normal & uv per vertex since from_pydata doesn't allow it
        mesh.from_pydata(mesh_data.vertex_positions, [], mesh_data.vertex_faces)
        mesh.update()

        basic_brick = bpy.data.objects.new("Part_Mesh", mesh)
        bpy.context.collection.objects.link(basic_brick)

    return mesh