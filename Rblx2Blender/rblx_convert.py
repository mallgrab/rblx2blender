from copy import deepcopy
from math import radians, degrees
from typing import NamedTuple
from collections import namedtuple
from . rblx_legacy_color import BrickColor
from . rblx_mesh import GetMeshFromFile

import xml.etree.ElementTree as ET
import mathutils
import bmesh
import bpy
import os
import base64
import hashlib
import requests
import imghdr
import re
import shutil

# debug
import timeit

class Part(object):
    def __init__(self):
        self.location = [0.0, 0.0, 0.0]
        self.rotation = [0.0, 0.0, 0.0]
        self.scale = [0.0, 0.0, 0.0]
        self.brickColor = 0
        self.brickType = 0
        self.textures = []
        self.md5Textures = []
        self.decals = []

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

PartsList = []
BrickList = []
CylinderList = []
SphereList = []

RotationMatrix = mathutils.Matrix(([0,0,0],[0,0,0],[0,0,0]))
localTexId = 0
rbxlx = False

def CalculateRotation(part: Part, EulerVector3):
    part.rotation[0] = EulerVector3[0]
    part.rotation[1] = EulerVector3[1]
    part.rotation[2] = EulerVector3[2]

def srgb2linear(c):
    if c < 0.04045:
        return 0.0 if c < 0.0 else c * (1.0 / 12.92)
    else:
        return ((c + 0.055) * (1.0 / 1.055)) ** 2.4

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def CreateMaterial(r, g, b):
    for i in bpy.data.materials:
        matName = "BrClr" + str(r) + str(g) + str(b)
        if (i.name == matName):
            return i
    
    mat = bpy.data.materials.new(name="BrClr" + str(r) + str(g) + str(b)) #set new material to variable
    mat.diffuse_color=(srgb2linear(r/255), srgb2linear(g/255), srgb2linear(b/255), 1.0)
    return mat

def CreateMaterialWithTexture(dir):
    for material in bpy.data.materials:
        matName = "Tex" + os.path.basename(dir)
        if (material.name == matName):
            return material
    
    mat = bpy.data.materials.new(name="Tex" + os.path.basename(dir))
    mat.use_nodes = True
    mat.diffuse_color=(srgb2linear(255/255), srgb2linear(0/255), srgb2linear(255/255), 1.0)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(dir)
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    
    # Mix base color with texture (mix shader)
        # Check how unity reacts to the model.
    mat.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
    return mat

def CreateMaterialFromBrickColor(colorID):
    if (rbxlx):
        # brickcolor is a 32 integer
        r = (colorID & 0x000000ff)
        g = (colorID & 0x0000ff00) >> 8
        b = (colorID & 0x00ff0000) >> 16
        a = (colorID & 0xff000000) >> 24 # create alpha material(shader) later
        return CreateMaterial(b, g, r)
    
    try:
        return CreateMaterial(BrickColor[colorID][0], BrickColor[colorID][1], BrickColor[colorID][2])
    except:
        print("BrickColor", colorID, "is not defined")
        return CreateMaterial(0, 0, 0)

# Returns material index of material correlating to dir.
def GetMaterialIndex(dir, mesh):
    for idx, i in enumerate(mesh.materials):
        if (i.name == "Tex" + os.path.basename(dir)):
            return idx

    # Material does not exist, append and return last material index.
    mesh.materials.append(CreateMaterialWithTexture(dir))
    return 0

# Local texture which got duplicated from parts. Uses md5 hash of the copied texture for the name.
def TextureDuplicated(md5, faceIdx, part: Part):
    part.md5Textures.append(TextureMd5(md5, faceIdx))

# Convert Roblox face index to Blender.
def GetFaceIndex(FaceIdx):
    switcher = {
        0: 2,
        1: 1,
        2: 5,
        3: 0,
        4: 3,
        5: 4,
    }
    # Return FaceIdx without converting it if its above 5.
    return switcher.get(FaceIdx, FaceIdx)

def GetLocalTexture(TextureXML, FaceIdx, part: Part, Type, AssetsDir):
    global localTexId
    base64buffer = TextureXML.text
    base64buffer = base64buffer.replace('\n', '')
    file_content = base64.b64decode(base64buffer)

    if not (os.path.exists(AssetsDir)):
        os.mkdir(AssetsDir)

    open("tmp", 'wb').write(file_content)
    assetType = imghdr.what('tmp')
    textureName = "tex_" + str(localTexId) + "." + str(assetType)

    if (os.path.exists(AssetsDir + "/" + textureName)):
        os.remove(AssetsDir + "/" + textureName)

    os.rename(r'tmp',r'' + textureName)
    shutil.move(textureName, AssetsDir)

    textureDir = os.path.abspath(AssetsDir + "/" + textureName)
    part.textures.append(Texture(textureDir, FaceIdx, Type, TileUV(None, None)))
    localTexId += 1
    

def GetOnlineTexture(Link, FaceIdx, part: Part, Type, TileUV: TileUV, RobloxInstallLocation, PlaceName, AssetsDir):
    assetID = re.sub(r'[^0-9]+', '', Link.lower())
    localAsset = False

    if not (os.path.exists(PlaceName + "Assets")):
        os.mkdir(PlaceName + "Assets")

    # Get local asset from the roblox content folder.
    # This might not work because of backslash formating, depends on blender.
    if not (assetID):
        if ("rbxasset://" in Link):
            assetID = Link.replace('rbxasset://', RobloxInstallLocation)
            localAsset = True

    if not (localAsset):
        if (os.path.exists(AssetsDir + "/" + assetID + ".png")):
            os.remove(AssetsDir + "/" + assetID + ".png")
        
        if (os.path.exists(AssetsDir + "/" + assetID + ".jpeg")):
            os.remove(AssetsDir + "/" + assetID + ".jpeg")
        
        if not (os.path.exists(assetID + ".png") or os.path.exists(assetID + ".jpeg")):
            asset = requests.get('https://assetdelivery.roblox.com/v1/assetId/' + assetID)
            assetLink = asset.json()['location']

            assetFile = requests.get(assetLink, allow_redirects=True)
            open('tmp', 'wb').write(assetFile.content)
            assetType = imghdr.what('tmp')
            assetFileName = assetID + "." + str(assetType)
            os.rename(r'tmp',r'' + assetFileName)
            shutil.move(assetFileName, AssetsDir)
            textureDir = os.path.abspath(AssetsDir + "/" + assetFileName)
            part.textures.append(Texture(textureDir, FaceIdx, Type, TileUV))

def CreatePart(part: Part):
    if (part.brickType == 2):
        mesh = bpy.data.meshes.new('Part_Cylinder')
        basic_cylinder = bpy.data.objects.new("Part_Cylinder", mesh)
        bpy.context.collection.objects.link(basic_cylinder)
        
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, diameter1=0.5, diameter2=0.5, depth=0.5)
        
        part.scale[2] = part.scale[2] + part.scale[2]
        bmesh.ops.scale(bm, vec=part.scale, verts=bm.verts)
        
        # flip the cylinders
        part.rotation[0] = part.rotation[0] - part.rotation[0]
        part.rotation[1] = part.rotation[1] + radians(90)
        
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(part.rotation, 'XYZ').to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=part.location, verts=bm.verts)
        
        bm.to_mesh(mesh)
        
        # Smooth outside cylinder walls
        bm.faces.ensure_lookup_table()
        for f in mesh.polygons:
            if (f.vertices.__len__() != 12):
                f.use_smooth = True
        
        bm.free()
        
        bpy.context.view_layer.objects.active = basic_cylinder
        basic_cylinder.select_set(True)
        basic_cylinder.data.materials.append(CreateMaterialFromBrickColor(part.brickColor))
        basic_cylinder.select_set(False)
        
        global CylinderList
        CylinderList.append(mesh)
               
    if (part.brickType == 1):
        mesh = bpy.data.meshes.new('Part_Brick')
        basic_brick = bpy.data.objects.new("Part_Brick", mesh)

        bpy.context.collection.objects.link(basic_brick)
        bm = bmesh.new()
    
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=part.scale, verts=bm.verts)
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(part.rotation, 'XYZ').to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=part.location, verts=bm.verts)

        bm.to_mesh(mesh)
        bm.free()
        
        bpy.context.view_layer.objects.active = basic_brick
        basic_brick.select_set(True)
        basic_brick.data.materials.append(CreateMaterialFromBrickColor(part.brickColor))
        basic_brick.select_set(False)

        global BrickList
        BrickList.append(Brick(mesh, part.scale, part.textures))
        
    if (part.brickType == 0):
        mesh = bpy.data.meshes.new('Part_Sphere')
        basic_sphere = bpy.data.objects.new("Part_Sphere", mesh)

        bpy.context.collection.objects.link(basic_sphere)
        bm = bmesh.new()
        
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, diameter=0.5)
        bmesh.ops.scale(bm, vec=part.scale, verts=bm.verts)
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(part.rotation, 'XYZ').to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=part.location, verts=bm.verts)
        
        bm.to_mesh(mesh)
        bm.free()
        
        # add smooth modifier to sphere
        # would be faster if done all at once since it updates the scene per sphere
            # we could add spheres to a list then just select all of them and apply smooth modifier to them.
            # would be one single scene update
        bpy.context.view_layer.objects.active = basic_sphere
        basic_sphere.select_set(True)
        bpy.ops.object.modifier_add(type='SUBSURF')
        basic_sphere.data.materials.append(CreateMaterialFromBrickColor(part.brickColor))
        bpy.ops.object.shade_smooth()

# Rewrite this into a seperate class where we gather everything into Lists.
# Functions that require access to the list do it through the class object.

# Also use https://docs.python.org/3/library/xml.etree.elementtree.html#example (XPath, findall, etc)
def GetDataFromPlace(root, RobloxInstallLocation, PlaceName, AssetsDir):
    global PartsList
    global CylinderList
    global BrickList
    global SphereList

    PartsList = []
    CylinderList = []
    BrickList = []
    SphereList = []

    for DataModel in root:
        if (DataModel.get('class') == 'Workspace'):
            for Workspace in DataModel.iter('Item'):
                if (Workspace.get('class') == 'Part'):
                    CurrentPart = Part()
                    PartsList.append(CurrentPart)

                    for Parts in Workspace.iter('Properties'):
                        for Properties in Parts.iter():
                            if (rbxlx):
                                if (Properties.tag == 'Color3uint8'):
                                    if (Properties.attrib.get('name') == 'Color3uint8'):
                                        CurrentPart.brickColor = int(Properties.text)
                            else:
                                if (Properties.tag == 'int'):
                                    if (Properties.attrib.get('name') == 'BrickColor'):
                                        CurrentPart.brickColor = int(Properties.text)

                            if (Properties.tag == 'token'):
                                if (Properties.attrib.get('name') == 'shape'):
                                    CurrentPart.brickType = int(Properties.text)

                            if (Properties.tag == 'CoordinateFrame'):
                                if (Properties.attrib.get('name') == 'CFrame'):
                                    for Pos in Properties.iter():

                                        if (Pos.tag == 'X'): CurrentPart.location[0] = float(Pos.text)
                                        if (Pos.tag == 'Y'): CurrentPart.location[1] = float(Pos.text)
                                        if (Pos.tag == 'Z'): CurrentPart.location[2] = float(Pos.text)

                                        if (Pos.tag == 'R00'): 
                                            RotationMatrix[0][0] = float(Pos.text)
                                        if (Pos.tag == 'R01'): 
                                            RotationMatrix[0][1] = float(Pos.text)
                                        if (Pos.tag == 'R02'): 
                                            RotationMatrix[0][2] = float(Pos.text)
                                        if (Pos.tag == 'R10'): 
                                            RotationMatrix[1][0] = float(Pos.text)
                                        if (Pos.tag == 'R11'): 
                                            RotationMatrix[1][1] = float(Pos.text)
                                        if (Pos.tag == 'R12'): 
                                            RotationMatrix[1][2] = float(Pos.text)
                                        if (Pos.tag == 'R20'): 
                                            RotationMatrix[2][0] = float(Pos.text)
                                        if (Pos.tag == 'R21'): 
                                            RotationMatrix[2][1] = float(Pos.text)
                                        if (Pos.tag == 'R22'): 
                                            RotationMatrix[2][2] = float(Pos.text)

                            if (Properties.tag == 'Vector3'):
                                if (Properties.attrib.get('name') == 'size'):
                                    for Pos in Properties.iter():
                                        if (Pos.tag == 'X'): 
                                            CurrentPart.scale[0] = float(Pos.text)
                                        if (Pos.tag == 'Y'): 
                                            CurrentPart.scale[1] = float(Pos.text)
                                        if (Pos.tag == 'Z'): 
                                            CurrentPart.scale[2] = float(Pos.text)
                                            CalculateRotation(CurrentPart, RotationMatrix.to_euler("XYZ"))
         
                    for Items in Workspace.iter('Item'):
                        if (Items.get('class') == 'Decal'):
                            if (Workspace.attrib.get('class') == 'Part'):
                                for Decal in Items.iter():   
                                    if (Decal.tag == 'token'):
                                        if (Decal.attrib.get('name') == 'Face'):
                                            FaceIdx = GetFaceIndex(int(Decal.text))  
                                    if (Decal.tag == 'hash' or Decal.tag == 'url'):
                                        GetOnlineTexture(Decal.text, FaceIdx, CurrentPart, 'Decal', TileUV(None, None), RobloxInstallLocation, PlaceName, AssetsDir)            
                                    if (Decal.tag == 'binary'):
                                        GetLocalTexture(Decal, FaceIdx, CurrentPart, 'Decal', AssetsDir)

                        if (Items.get('class') == 'Texture'):
                            if (Workspace.attrib.get('class') == 'Part'):
                                TileU = 2
                                TileV = 2
                                for Texture in Items.iter():
                                    if (Texture.tag == 'float'):
                                        if (Texture.attrib.get('name') == 'StudsPerTileU'):
                                            TileU = float(Texture.text)
                                        if (Texture.attrib.get('name') == 'StudsPerTileV'):
                                            TileV = float(Texture.text)

                                    if (Texture.tag == 'token'):
                                        if (Texture.attrib.get('name') == 'Face'):
                                            FaceIdx = GetFaceIndex(int(Texture.text))
                                    if (Texture.tag == 'url'):
                                        GetOnlineTexture(Texture.text, FaceIdx, CurrentPart, 'Texture', TileUV(TileU, TileV), RobloxInstallLocation, PlaceName, AssetsDir)
                                    
                                    if (Texture.tag == 'hash'):
                                        TextureDuplicated(Texture.text, FaceIdx, CurrentPart)                                  

                                    if (Texture.tag == 'binary'):
                                        GetLocalTexture(Texture, FaceIdx, CurrentPart, 'Texture', AssetsDir)

class StartConverting(bpy.types.Operator):
    bl_idname = "scene.button_operator_convert"
    bl_label = "Start Converting"

    def execute(self, context):
        global rbxlx
        global localTexId

        bpyscene = context.scene

        RobloxPlace = bpyscene.Place_Path.file_path
        RobloxInstallLocation = bpyscene.Install_Path.file_path
        PlaceName = os.path.splitext(os.path.basename(RobloxPlace))[0]
        
        AssetsDir = PlaceName + "Assets"
        TextureList = []
        localTexId = 0
        
        rbxlx = RobloxPlace.lower().endswith(('rbxlx'))
        root = ET.parse(RobloxPlace).getroot()

        timer = 0.0
        start = timeit.default_timer()

        for i in context.selectable_objects:
            i.select_set(False)

        for i in bpy.data.meshes:
            bpy.data.meshes.remove(i)

        for i in bpy.data.materials:
            bpy.data.materials.remove(i)

        GetDataFromPlace(root, RobloxInstallLocation, PlaceName, AssetsDir)

        # If place has textures fill up TextureList.
        if (os.path.exists(AssetsDir)):
            for i in os.listdir(AssetsDir):
                TextureList.append(os.path.abspath(AssetsDir + "/" + i))

        # Convert md5 hash to the texture path
        part: Part
        for part in PartsList:
            textureMd5: TextureMd5
            for textureMd5 in part.md5Textures:
                for TexturePath in TextureList:
                    if(md5(TexturePath) == textureMd5.md5):
                        # Change md5 hash to texture path
                        # Should probably just add texture path as a variable within TextureMd5
                        textureMd5.md5 = TexturePath
                        part.textures.append(textureMd5)

        for part in PartsList:
            CreatePart(part)

        # Rotate place properly
        for obj in bpy.context.scene.objects:
            obj.select_set(True)

        for obj_selected in bpy.context.selected_objects:
            obj_selected.rotation_euler.x = radians(90.0)

        # Seperate top and bottom part of cylinder so smoothing looks good
        if CylinderList:
            for i in CylinderList:
                for v in i.polygons:
                    if (v.vertices.__len__() == 12):
                        v.select = True
            
            bpy.context.tool_settings.mesh_select_mode = [False, False, True]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')

        for obj_scene in bpy.context.scene.objects:
            obj_scene.select_set(False)

        bpy.ops.object.mode_set(mode='OBJECT')

        if BrickList:
            brick: Brick
            for brick in BrickList:
                bm = bmesh.new()
                bm.from_mesh(brick.mesh)
                uv_layer = bm.loops.layers.uv.verify()
                bm.faces.ensure_lookup_table()

                for idxFace, face in enumerate(bm.faces):                    
                    for idxLoop, loop in enumerate(bm.faces[idxFace].loops):
                        loop_uv = loop[uv_layer]
                        """
                        # top and bottom of brick gets their UV stretched, creates tiling for the studs.
                        if (idxFace == 1 or idxFace == 3):
                            if (idxLoop == 0):
                                loop_uv.uv = [scale[2]/2, scale[0]/4]       # top right
                            if (idxLoop == 1):
                                loop_uv.uv = [0.0, scale[0]/4]              # top left
                            if (idxLoop == 2):
                                loop_uv.uv = [0.0, 0.0]                     # bottom left
                            if (idxLoop == 3):
                                loop_uv.uv = [(scale[2]/2), 0.0]            # bottom right
                        """

                        texture: Texture
                        for texture in brick.textures:
                            if (texture.faceIdx == idxFace):
                                face.material_index = GetMaterialIndex(texture.textureDir, brick.mesh)

                            if (texture.faceIdx == idxFace):
                                if (texture.type == 'Decal'):
                                    loop_uv = loop[uv_layer]
                                    if (idxFace == 1 or idxFace == 3):
                                        if (idxLoop == 0):
                                            loop_uv.uv = [1.0, 0.0]       # bottom left
                                        if (idxLoop == 1):
                                            loop_uv.uv = [1.0, 1.0]       # top left
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, 1.0]       # top right
                                        if (idxLoop == 3):
                                            loop_uv.uv = [0.0, 0.0]       # bottom right
                                    if (idxFace == 0 or idxFace == 2):
                                        if (idxLoop == 0):
                                            loop_uv.uv = [0.0, 0.0]       # bottom right
                                        if (idxLoop == 1):
                                            loop_uv.uv = [1.0, 0.0]       # bottom left
                                        if (idxLoop == 2):
                                            loop_uv.uv = [1.0, 1.0]       # top left
                                        if (idxLoop == 3):
                                            loop_uv.uv = [0.0, 1.0]       # top right
                                    if (idxFace == 5 or idxFace == 4):    
                                        if (idxLoop == 0):
                                            loop_uv.uv = [1.0, 1.0]       # top left
                                        if (idxLoop == 1):
                                            loop_uv.uv = [0.0, 1.0]       # top right
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, 0.0]       # bottom right
                                        if (idxLoop == 3):
                                            loop_uv.uv = [1.0, 0.0]       # bottom left                                    
                                    else:
                                        continue

                            if (texture.faceIdx == idxFace):
                                if (texture.type == 'Texture'):
                                    if texture.tileUV.TileU == None:
                                        continue
                                    loop_uv = loop[uv_layer]
                                    if (idxFace == 1 or idxFace == 3):
                                        if (idxLoop == 0):
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, 1.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [0.0, 1.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, (-brick.scale[2]/texture.tileUV.TileV) + 1.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, (-brick.scale[2]/texture.tileUV.TileV) + 1.0]
                                    if (idxFace == 0): # flip uv transforms on idxFace 2 if idxFace is 1
                                        if (idxLoop == 0):
                                            loop_uv.uv = [0.0, (-brick.scale[1]/texture.tileUV.TileV) + 1.0] # bottom left
                                        if (idxLoop == 1):
                                            loop_uv.uv = [(brick.scale[0]/texture.tileUV.TileU), (-brick.scale[1]/texture.tileUV.TileV) + 1.0] # bottom right
                                        if (idxLoop == 2):
                                            loop_uv.uv = [(brick.scale[0]/texture.tileUV.TileU), 1.0] # top right
                                        if (idxLoop == 3):
                                            loop_uv.uv = [0.0, 1.0] # top left
                                    if (idxFace == 2):
                                        if (idxLoop == 0):
                                            loop_uv.uv = [(brick.scale[0]/texture.tileUV.TileU), 1.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [0.0, 1.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, (-brick.scale[1]/texture.tileUV.TileV) + 1.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [(brick.scale[0]/texture.tileUV.TileU), (-brick.scale[1]/texture.tileUV.TileV) + 1.0]
                                    if (idxFace == 5 or idxFace == 4):    
                                        if (idxLoop == 0):
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, 1.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [0.0, 1.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, (-brick.scale[1]/texture.tileUV.TileV) + 1.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, (-brick.scale[1]/texture.tileUV.TileV) + 1.0]                                  
                                    else:
                                        continue
                bm.to_mesh(brick.mesh)
        
        #GetMeshFromFile("./meshes/MeshTesting_V1_00")
        GetMeshFromFile("./meshes/MeshTesting_V3")
        
        timer += (timeit.default_timer() - start)
        print("done", timer)
        return {'FINISHED'}

