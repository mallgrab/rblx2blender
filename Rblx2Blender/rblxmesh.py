from io import BufferedReader
from array import array
import struct

path = "./meshes/MeshTesting_V3"

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

    pos_x = struct.unpack('<f', file.read(4))
    pos_y = struct.unpack('<f', file.read(4))
    pos_z = struct.unpack('<f', file.read(4))
    print(pos_x, pos_y, pos_z)

def OpenMeshFile(path):
    with open(path, "rb") as file:
        version_string = file.read(7)
        if (version_string.decode("utf-8") == 'version'):
            MeshReader(file)

OpenMeshFile(path)