from io import BufferedReader
from array import array

path = "/home/user/Desktop/RobloxMeshLoader/RobloxMeshLoader/MeshTesting_V3"

def MeshReader(file: BufferedReader):
    file.read(7)

with open(path, "rb") as f:
    version_string = f.read(7)

    if (version_string.decode("utf-8") == 'version'):
        MeshReader(f)