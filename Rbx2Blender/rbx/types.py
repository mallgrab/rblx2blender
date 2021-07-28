import mathutils

class TileUV(object):
    def __init__(self, U, V):
        self.TileU = U
        self.TileV = V

class Texture(object):
    def __init__(self, textureDir, faceIndex, textureType, tileUV):
        self.textureDir = textureDir
        self.faceIdx = faceIndex
        self.type = textureType
        self.tileUV = tileUV

class TextureMd5(object):
    def __init__(self, md5, faceIdx):
        self.md5 = md5
        self.faceIdx = faceIdx

class Brick(object):
    def __init__(self, mesh, scale, textures):
        self.mesh = mesh
        self.scale = scale
        self.textures = textures

class Part(object):
    def __init__(self):
        self.location = [0.0, 0.0, 0.0]
        self.rotation = [0.0, 0.0, 0.0]
        self.rotation_matrix = [0,0,0,0,0,0,0,0,0]
        self.scale = [0.0, 0.0, 0.0]
        self.brickColor = 0
        self.brickType = 0
        self.textures = []
        self.md5Textures = []
        self.decals = []
        self.meshes = []

    def apply_euler_to_rotation(self, EulerVector3):
        self.rotation[0] = EulerVector3[0]
        self.rotation[1] = EulerVector3[1]
        self.rotation[2] = EulerVector3[2]
    
    def set_rotation_from_matrix(self):
        matrix = mathutils.Matrix(([0,0,0],[0,0,0],[0,0,0]))
        matrix[0][0] = self.rotation_matrix[0]
        matrix[0][1] = self.rotation_matrix[1]
        matrix[0][2] = self.rotation_matrix[2]
        matrix[1][0] = self.rotation_matrix[3]
        matrix[1][1] = self.rotation_matrix[4]
        matrix[1][2] = self.rotation_matrix[5]
        matrix[2][0] = self.rotation_matrix[6]
        matrix[2][1] = self.rotation_matrix[7]
        matrix[2][2] = self.rotation_matrix[8]
        
        self.apply_euler_to_rotation(matrix.to_euler("XYZ"))