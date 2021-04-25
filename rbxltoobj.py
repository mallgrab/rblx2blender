from copy import deepcopy
from math import radians, degrees

import xml.etree.ElementTree as ET
import numpy as np 
import math
import mathutils
import bmesh
import bpy
import signal
import io
import os
import base64
import requests
import imghdr
import re


# debug
import timeit
timer = 0.0
# global timer
start = timeit.default_timer()

# Legacy brick color support
BrickColor = [None] * 2048
BrickColor.insert(1, [242, 243, 243])
BrickColor.insert(2, [161, 165, 162])
BrickColor.insert(3, [249, 233, 153])
BrickColor.insert(5, [215, 197, 154])
BrickColor.insert(6, [194, 218, 184])
BrickColor.insert(9, [232, 186, 200])
BrickColor.insert(11, [128, 187, 219])
BrickColor.insert(12, [203, 132, 66])
BrickColor.insert(18, [204, 142, 105])
BrickColor.insert(21, [196, 40, 28])
BrickColor.insert(22, [196, 112, 160])
BrickColor.insert(23, [13, 105, 172])
BrickColor.insert(24, [245, 205, 48])
BrickColor.insert(25, [98, 71, 50])
BrickColor.insert(26, [27, 42, 53])
BrickColor.insert(27, [109, 110, 108])
BrickColor.insert(28, [40, 127, 71])
BrickColor.insert(29, [161, 196, 140])
BrickColor.insert(36, [243, 207, 155])
BrickColor.insert(37, [75, 151, 75])
BrickColor.insert(38, [160, 95, 53])
BrickColor.insert(39, [193, 202, 222])
BrickColor.insert(40, [236, 236, 236])
BrickColor.insert(41, [205, 84, 75])
BrickColor.insert(42, [193, 223, 240])
BrickColor.insert(43, [123, 182, 232])
BrickColor.insert(44, [247, 241, 141])
BrickColor.insert(45, [180, 210, 228])
BrickColor.insert(47, [217, 133, 108])
BrickColor.insert(48, [132, 182, 141])
BrickColor.insert(49, [248, 241, 132])
BrickColor.insert(50, [236, 232, 222])
BrickColor.insert(100, [238, 196, 182])
BrickColor.insert(101, [218, 134, 122])
BrickColor.insert(102, [110, 153, 202])
BrickColor.insert(103, [199, 193, 183])
BrickColor.insert(104, [107, 50, 124])
BrickColor.insert(105, [226, 155, 64])
BrickColor.insert(106, [218, 133, 65])
BrickColor.insert(107, [0, 143, 156])
BrickColor.insert(108, [104, 92, 67])
BrickColor.insert(110, [67, 84, 147])
BrickColor.insert(111, [191, 183, 177])
BrickColor.insert(112, [104, 116, 172])
BrickColor.insert(113, [228, 173, 200])
BrickColor.insert(115, [199, 210, 60])
BrickColor.insert(116, [85, 165, 175])
BrickColor.insert(118, [183, 215, 213])
BrickColor.insert(119, [164, 189, 71])
BrickColor.insert(120, [217, 228, 167])
BrickColor.insert(121, [231, 172, 88])
BrickColor.insert(123, [211, 111, 76])
BrickColor.insert(124, [146, 57, 120])
BrickColor.insert(125, [234, 184, 146])
BrickColor.insert(126, [165, 165, 203])
BrickColor.insert(127, [220, 188, 129])
BrickColor.insert(128, [174, 122, 89])
BrickColor.insert(131, [156, 163, 168])
BrickColor.insert(133, [213, 115, 61])
BrickColor.insert(134, [216, 221, 86])
BrickColor.insert(135, [116, 134, 157])
BrickColor.insert(136, [135, 124, 144])
BrickColor.insert(137, [224, 152, 100])
BrickColor.insert(138, [149, 138, 115])
BrickColor.insert(140, [32, 58, 86])
BrickColor.insert(141, [39, 70, 45])
BrickColor.insert(143, [207, 226, 247])
BrickColor.insert(145, [121, 136, 161])
BrickColor.insert(146, [149, 142, 163])
BrickColor.insert(147, [147, 135, 103])
BrickColor.insert(148, [87, 88, 87])
BrickColor.insert(149, [22, 29, 50])
BrickColor.insert(150, [171, 173, 172])
BrickColor.insert(151, [120, 144, 130])
BrickColor.insert(153, [149, 121, 119])
BrickColor.insert(154, [123, 46, 47])
BrickColor.insert(157, [255, 246, 123])
BrickColor.insert(158, [225, 164, 194])
BrickColor.insert(168, [117, 108, 98])
BrickColor.insert(176, [151, 105, 91])
BrickColor.insert(178, [180, 132, 85])
BrickColor.insert(179, [137, 135, 136])
BrickColor.insert(180, [215, 169, 75])
BrickColor.insert(190, [249, 214, 46])
BrickColor.insert(191, [232, 171, 45])
BrickColor.insert(192, [105, 64, 40])
BrickColor.insert(193, [207, 96, 36])
BrickColor.insert(194, [163, 162, 165])
BrickColor.insert(195, [70, 103, 164])
BrickColor.insert(196, [35, 71, 139])
BrickColor.insert(198, [142, 66, 133])
BrickColor.insert(199, [99, 95, 98])
BrickColor.insert(200, [130, 138, 93])
BrickColor.insert(208, [229, 228, 223])
BrickColor.insert(209, [176, 142, 68])
BrickColor.insert(210, [112, 149, 120])
BrickColor.insert(211, [121, 181, 181])
BrickColor.insert(212, [159, 195, 233])
BrickColor.insert(213, [108, 129, 183])
BrickColor.insert(216, [143, 76, 42])
BrickColor.insert(217, [124, 92, 70])
BrickColor.insert(218, [150, 112, 159])
BrickColor.insert(219, [107, 98, 155])
BrickColor.insert(220, [167, 169, 206])
BrickColor.insert(221, [205, 98, 152])
BrickColor.insert(222, [228, 173, 200])
BrickColor.insert(223, [220, 144, 149])
BrickColor.insert(224, [240, 213, 160])
BrickColor.insert(225, [235, 184, 127])
BrickColor.insert(226, [253, 234, 141])
BrickColor.insert(232, [125, 187, 221])
BrickColor.insert(268, [52, 43, 117])
BrickColor.insert(1001, [248, 248, 248])
BrickColor.insert(1002, [205, 205, 205])
BrickColor.insert(1003, [17, 17, 17])
BrickColor.insert(1004, [255, 0, 0])
BrickColor.insert(1005, [255, 175, 0])
BrickColor.insert(1006, [180, 128, 255])
BrickColor.insert(1007, [163, 75, 75])
BrickColor.insert(1008, [193, 190, 66])
BrickColor.insert(1009, [255, 255, 0])
BrickColor.insert(1010, [0, 0, 255])
BrickColor.insert(1011, [0, 32, 96])
BrickColor.insert(1012, [33, 84, 185])
BrickColor.insert(1013, [4, 175, 236])
BrickColor.insert(1014, [170, 85, 0])
BrickColor.insert(1015, [170, 0, 170])
BrickColor.insert(1016, [255, 102, 204])
BrickColor.insert(1017, [255, 175, 0])
BrickColor.insert(1018, [18, 238, 212])
BrickColor.insert(1019, [0, 255, 255])
BrickColor.insert(1020, [0, 255, 0])
BrickColor.insert(1021, [58, 125, 21])
BrickColor.insert(1022, [127, 142, 100])
BrickColor.insert(1023, [140, 91, 159])
BrickColor.insert(1024, [175, 221, 255])
BrickColor.insert(1025, [255, 201, 201])
BrickColor.insert(1026, [177, 167, 255])
BrickColor.insert(1027, [159, 243, 233])
BrickColor.insert(1028, [204, 255, 204])
BrickColor.insert(1029, [255, 255, 204])
BrickColor.insert(1030, [255, 204, 153])
BrickColor.insert(1031, [98, 37, 209])
BrickColor.insert(1032, [255, 0, 191])

bpyscene = bpy.context.scene
dobjects = bpy.data.objects
objects = bpy.context.scene.objects
bpy.ops.object.select_all(action='DESELECT')

RobloxPlace = r'C:\Users\win-spike\Desktop\rbxl2obj\Pirate.rbxl'
RobloxInstallLocation = r'C:\Users\win-spike\Documents\CnCRemastered\roblox2008\content'
rbxlx = RobloxPlace.lower().endswith(('rbxlx'))
root = ET.parse(RobloxPlace).getroot()

PartsList = []
BrickList = []
CylinderList = []
SphereList = []
PartIdx = 0

CurrentPart = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0],[0],["",""]]
CurrentDecals = []
RotationMatrix = mathutils.Matrix(([0,0,0],[0,0,0],[0,0,0]))
base64Buffer = ""
texID = 0

# location, rotation, scale, brickcolor, type, surface(TopSurface, BottomSurface), 
class Part(object):
    def __init__(self):
        self.location = [0.0, 0.0, 0.0]
        self.rotation = [0.0, 0.0, 0.0]
        self.scale = [0.0, 0.0, 0.0]
        self.brickColor = 0
        self.brickType = 0
        self.surface = []
        self.texID = 0

# Clear all meshes for performance
for i in bpy.data.meshes:
    bpy.data.meshes.remove(i)

def CalculateRotation(PartIdx):
    EulerVector3 = RotationMatrix.to_euler("XYZ")

    PartsList[PartIdx].rotation[0] = EulerVector3[0]
    PartsList[PartIdx].rotation[1] = EulerVector3[1]
    PartsList[PartIdx].rotation[2] = EulerVector3[2]
    
def srgb2linear(c):
    if c < 0.04045:
        return 0.0 if c < 0.0 else c * (1.0 / 12.92)
    else:
        return ((c + 0.055) * (1.0 / 1.055)) ** 2.4

def CreateMaterial(r, g, b):
    for i in bpy.data.materials:
        matName = "BrClr" + str(r) + str(g) + str(b)
        if (i.name == matName):
            return i
    
    mat = bpy.data.materials.new(name="BrClr" + str(r) + str(g) + str(b)) #set new material to variable
    mat.diffuse_color=(srgb2linear(r/255), srgb2linear(g/255), srgb2linear(b/255), 1.0)
    return mat

# On both functions return file location and face direction
def GetLocalTexture(TextureXML):
    global texID
    base64buffer = TextureXML.text
    base64buffer = base64buffer.replace('\n', '')
    file_content = base64.b64decode(base64buffer)

    open("tmp", 'wb').write(file_content)
    assetType = imghdr.what('tmp')
    textureName = "tex_" + str(texID) + "." + str(assetType)

    if (os.path.exists(textureName)):
        os.remove(textureName)
    os.rename(r'tmp',r'' + textureName)

    texID += 1

def GetOnlineTexture(Link):
    assetID = re.sub(r'[^0-9]+', '', Link.lower())
    localAsset = False

    # Check if what we return would even work as a file link for blender
    # Might have to reformat it a little bit so it works cause of backslashes
    if not (assetID):
        if ("rbxasset://" in Link):
            assetID = Link.replace('rbxasset://', RobloxInstallLocation)
            localAsset = True

    if not (localAsset):
        if (os.path.exists(assetID + ".png")):
            os.remove(assetID + ".png")
        elif (os.path.exists(assetID + ".jpeg")):
            os.remove(assetID + ".jpeg")
        
        if not (os.path.exists(assetID + ".png") or os.path.exists(assetID + ".jpeg")):
            asset = requests.get('https://assetdelivery.roblox.com/v1/assetId/' + assetID)
            assetLink = asset.json()['location']

            assetFile = requests.get(assetLink, allow_redirects=True)
            open('tmp', 'wb').write(assetFile.content)
            assetType = imghdr.what('tmp')
            os.rename(r'tmp',r'' + assetID + "." + str(assetType))

# Group stuff later on depending on if they are inside models.
# Check also if fbx supports exporting groups so that in unity you can move stuff easier

# We also not checking for transparency which we should do later.
# Check also if unity will transparent the object if the material is transparent.
for DataModel in root:
    if (DataModel.get('class') == 'Workspace'):
        for Workspace in DataModel.iter('Item'):
            if (Workspace.get('class') == 'Part'):
                PartsList.append(Part())
                
                for Parts in Workspace.iter('Properties'):
                    for Properties in Parts.iter():
                        if (rbxlx):
                            if (Properties.tag == 'Color3uint8'):
                                if (Properties.attrib.get('name') == 'Color3uint8'):
                                    # CurrentPart[3] = int(Properties.text)
                                    PartsList[PartIdx].brickColor = int(Properties.text)
                        else:
                            if (Properties.tag == 'int'):
                                if (Properties.attrib.get('name') == 'BrickColor'):
                                    # CurrentPart[3] = int(Properties.text)
                                    PartsList[PartIdx].brickColor = int(Properties.text)
                                    
                        if (Properties.tag == 'token'):
                            if (Properties.attrib.get('name') == 'shape'):
                                # CurrentPart[4] = int(Properties.text)
                                PartsList[PartIdx].brickType = int(Properties.text)
                                
                        if (Properties.tag == 'CoordinateFrame'):
                            if (Properties.attrib.get('name') == 'CFrame'):
                                for Pos in Properties.iter():
                                    if (Pos.tag == 'X'): PartsList[PartIdx].location[0] = float(Pos.text)
                                    if (Pos.tag == 'Y'): PartsList[PartIdx].location[1] = float(Pos.text)
                                    if (Pos.tag == 'Z'): PartsList[PartIdx].location[2] = float(Pos.text)

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
                                        PartsList[PartIdx].scale[0] = float(Pos.text)
                                    if (Pos.tag == 'Y'): 
                                        PartsList[PartIdx].scale[1] = float(Pos.text)
                                    if (Pos.tag == 'Z'): 
                                        PartsList[PartIdx].scale[2] = float(Pos.text)
                                        CalculateRotation(PartIdx)
                                        PartIdx += 1            
                for Items in Workspace.iter('Item'):
                    if (Items.get('class') == 'Decal'):
                        if (Workspace.attrib.get('class') == 'Part'):
                            for Decal in Items.iter():      
                                if (Decal.tag == 'hash' or Decal.tag == 'url'):
                                    GetOnlineTexture(Decal.text)            
                                if (Decal.tag == 'binary'):
                                    GetLocalTexture(Decal)

                    if (Items.get('class') == 'Texture'):
                        if (Workspace.attrib.get('class') == 'Part'):
                            for Texture in Items.iter():
                                if (Texture.tag == 'float'):
                                    if (Texture.attrib.get('name') == 'StudsPerTileU'):
                                        print("StudsPerTileU: " + Texture.text)
                                    if (Texture.attrib.get('name') == 'StudsPerTileV'):
                                        print("StudsPerTileV: " + Texture.text)
                                if (Texture.tag == 'binary'):
                                    GetLocalTexture(Texture)

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


def CreatePart(scale, rotation, translate, brickcolor, type):
    if (type == 2):
        mesh = bpy.data.meshes.new('Part_Cylinder')
        basic_cylinder = bpy.data.objects.new("Part_Cylinder", mesh)
        bpy.context.collection.objects.link(basic_cylinder)
        
        bm = bmesh.new()
        
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, diameter1=0.5, diameter2=0.5, depth=0.5)
        
        scale[2] = scale[2] + scale[2]
        bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
        
        # flip the cylinders
        rotation[0] = rotation[0] - rotation[0]
        rotation[1] = rotation[1] + radians(90)
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(rotation, 'XYZ').to_matrix(), verts=bm.verts)
        
        bmesh.ops.translate(bm, vec=translate, verts=bm.verts)
        
        bm.to_mesh(mesh)
        
        # Smooth outside cylinder walls
        bm.faces.ensure_lookup_table()
        for f in mesh.polygons:
            if (f.vertices.__len__() != 12):
                f.use_smooth = True
        
        bm.free()
        
        bpy.context.view_layer.objects.active = basic_cylinder
        basic_cylinder.select_set(True)
        basic_cylinder.data.materials.append(CreateMaterialFromBrickColor(brickcolor))
        basic_cylinder.select_set(False)
        
        global CylinderList
        CylinderList.append(mesh)
        
        # Later to apply top/bottom texture for the parts
        # https://blender.stackexchange.com/questions/149956/python-to-select-and-delete-multiple-faces
        #for f in mesh.polygons:
            #f.material_index
               
    if (type == 1):
        mesh = bpy.data.meshes.new('Part_Brick')
        basic_brick = bpy.data.objects.new("Part_Brick", mesh)

        bpyscene.collection.objects.link(basic_brick)
        bm = bmesh.new()
    
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(rotation, 'XYZ').to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=translate, verts=bm.verts)

        bm.to_mesh(mesh)
        
        
        bpy.context.view_layer.objects.active = basic_brick
        basic_brick.select_set(True)
        
        basic_brick.data.materials.append(CreateMaterialFromBrickColor(brickcolor))
        
        basic_brick.select_set(False)
        bm.free()
        
        global BrickList
        BrickList.append([mesh, scale])
        
    if (type == 0):
        mesh = bpy.data.meshes.new('Part_Sphere')
        basic_sphere = bpy.data.objects.new("Part_Sphere", mesh)

        bpy.context.collection.objects.link(basic_sphere)
        bm = bmesh.new()
        
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=0.5)
        bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(rotation, 'XYZ').to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=translate, verts=bm.verts)
        
        bm.to_mesh(mesh)
        bm.free()
        
        # add smooth modifier to sphere
        # would be faster if done all at once since it updates the scene per sphere
        bpy.context.view_layer.objects.active = basic_sphere
        basic_sphere.select_set(True)
        bpy.ops.object.modifier_add(type='SUBSURF')
        basic_sphere.data.materials.append(CreateMaterialFromBrickColor(brickcolor))
        bpy.ops.object.shade_smooth()

print("\nCollected all parts")

for i in PartsList:
    CreatePart(i.scale, i.rotation, i.location, i.brickColor, i.brickType)

ob = bpy.data.objects
for obj in bpy.context.scene.objects:
    obj.select_set(True)

# Rotate place properly
for i in  bpy.context.selected_objects:
    i.rotation_euler.x = radians(90.0)

# Seperate top and bottom part of cylinder so smoothing looks good
if CylinderList:
    for i in CylinderList:
        for v in i.polygons:
            if (v.vertices.__len__() == 12):
                v.select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')

for obj in bpy.context.scene.objects:
    obj.select_set(False)

"""
    UV:
    By default set vertex to each corner after cube_project().

    If a decal is placed on a specific surface on the brick.
    Do not do anything on that particular surface.

    If theres no decal on a specific surface.
    Increase UV width/height by surface size.
    This will repeat the stud pattern.
"""

bpy.ops.object.mode_set(mode='OBJECT')

if BrickList:
    for mesh in BrickList:
        bm = bmesh.new()
        bm.from_mesh(mesh[0])
        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.ensure_lookup_table()
        
        _mesh = mesh[0]
        scale = mesh[1]
    
        # top and bottom of brick gets their UV stretched, creates tiling for the studs.
        # mesh[0] is the blender mesh
        # mesh[1] is the scale from roblox
        for idxFace, face in enumerate(bm.faces):
            for idxLoop, loop in enumerate(bm.faces[idxFace].loops):
                loop_uv = loop[uv_layer]
                if (idxFace == 1 or idxFace == 3):
                    if (idxLoop == 0):
                        loop_uv.uv = [scale[2]/2, scale[0]/4]       # top right
                    if (idxLoop == 1):
                        loop_uv.uv = [0.0, scale[0]/4]              # top left
                    if (idxLoop == 2):
                        loop_uv.uv = [0.0, 0.0]                     # bottom left
                    if (idxLoop == 3):
                        loop_uv.uv = [(scale[2]/2), 0.0]            # bottom right
        bm.to_mesh(_mesh)
  
  
""" Roblox does some funny shit to the UV's on the sides, this looks 'ok' but its not the same as it does in Roblox.
        if (idxFace == 4 or idxFace == 5):
            if (idxLoop == 0):
                loop_uv.uv = [scale[0]/2, scale[1]/4]   # top right
            if (idxLoop == 1):
                loop_uv.uv = [0.0, scale[1]/4]              # top left
            if (idxLoop == 2):
                loop_uv.uv = [0.0, 0.0]                         # bottom left
            if (idxLoop == 3):
                loop_uv.uv = [scale[0]/2, 0.0]              # bottom right
        
        if (idxFace == 2 or idxFace == 0):
            if (idxLoop == 0):
                loop_uv.uv = [scale[2]/2, scale[1]/4]   # top right
            if (idxLoop == 1):
                loop_uv.uv = [0.0, scale[1]/4]              # top left
            if (idxLoop == 2):
                loop_uv.uv = [0.0, 0.0]                         # bottom left
            if (idxLoop == 3):
                loop_uv.uv = [scale[2]/2, 0.0]              # bottom right
"""

timer += (timeit.default_timer() - start)
print("done", timer)