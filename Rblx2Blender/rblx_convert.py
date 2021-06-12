from copy import deepcopy
from math import radians, degrees

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
from . rblx_legacy_color import BrickColor

# debug
import timeit

# location, rotation, scale, brickcolor, type, surface(TopSurface, BottomSurface), 
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

PartsList = []
BrickList = []
CylinderList = []
SphereList = []

# Contains path of all textures
TextureList = []

CurrentPart = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0],[0],["",""]]
RotationMatrix = mathutils.Matrix(([0,0,0],[0,0,0],[0,0,0]))
base64Buffer = ""
localTexId = 0
rbxlx = False

bpyscene = ""
dobjects = ""
objects = ""

RobloxPlace = ""
RobloxInstallLocation = ""
PlaceName = ""
AssetsDir = ""

def CalculateRotation(CurrentPart):
    EulerVector3 = RotationMatrix.to_euler("XYZ")

    CurrentPart.rotation[0] = EulerVector3[0]
    CurrentPart.rotation[1] = EulerVector3[1]
    CurrentPart.rotation[2] = EulerVector3[2]

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

# Local texture which got duplicated. Uses md5 hash for the texture.
def TextureDuplicated(TextureMd5, FaceIdx, Part):
    Part.md5Textures.append([TextureMd5, FaceIdx])

# On both functions return file location and face direction
def GetLocalTexture(TextureXML, FaceIdx, Part, Type):
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
    Part.textures.append([textureDir, FaceIdx, Type])
    localTexId += 1
    

def GetOnlineTexture(Link, FaceIdx, Part, Type):
    assetID = re.sub(r'[^0-9]+', '', Link.lower())
    localAsset = False

    if not (os.path.exists(PlaceName + "Assets")):
        os.mkdir(PlaceName + "Assets")

    # Check if what we return would even work as a file link for blender
    # Might have to reformat it a little bit so it works cause of backslashes
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
            Part.textures.append([textureDir, FaceIdx, Type])

def CreatePart(scale, rotation, translate, brickcolor, type, textures):
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

        bpy.context.collection.objects.link(basic_brick)
        bm = bmesh.new()
    
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(rotation, 'XYZ').to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=translate, verts=bm.verts)

        bm.to_mesh(mesh)
        bm.free()
        
        bpy.context.view_layer.objects.active = basic_brick
        basic_brick.select_set(True)
        basic_brick.data.materials.append(CreateMaterialFromBrickColor(brickcolor))
        basic_brick.select_set(False)

        global BrickList
        BrickList.append([mesh, scale, textures])
        
    if (type == 0):
        mesh = bpy.data.meshes.new('Part_Sphere')
        basic_sphere = bpy.data.objects.new("Part_Sphere", mesh)

        bpy.context.collection.objects.link(basic_sphere)
        bm = bmesh.new()
        
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, diameter=0.5)
        bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
        bmesh.ops.rotate(bm, matrix=mathutils.Euler(rotation, 'XYZ').to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=translate, verts=bm.verts)
        
        bm.to_mesh(mesh)
        bm.free()
        
        # add smooth modifier to sphere
        # would be faster if done all at once since it updates the scene per sphere
            # we could add spheres to a list then just select all of them and apply smooth modifier to them.
            # would be one single scene update
        bpy.context.view_layer.objects.active = basic_sphere
        basic_sphere.select_set(True)
        bpy.ops.object.modifier_add(type='SUBSURF')
        basic_sphere.data.materials.append(CreateMaterialFromBrickColor(brickcolor))
        bpy.ops.object.shade_smooth()

def GetDataFromPlace(root):
    global PartsList
    global CylinderList
    global BrickList
    global SphereList
    global TextureList

    PartsList = []
    CylinderList = []
    BrickList = []
    SphereList = []
    TextureList = []

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
                                            CalculateRotation(CurrentPart)
         
                    for Items in Workspace.iter('Item'):
                        if (Items.get('class') == 'Decal'):
                            if (Workspace.attrib.get('class') == 'Part'):
                                for Decal in Items.iter():   
                                    if (Decal.tag == 'token'):
                                        if (Decal.attrib.get('name') == 'Face'):
                                            FaceIdx = int(Decal.text)   
                                    if (Decal.tag == 'hash' or Decal.tag == 'url'):
                                        GetOnlineTexture(Decal.text, FaceIdx, CurrentPart, 'Decal')            
                                    if (Decal.tag == 'binary'):
                                        GetLocalTexture(Decal, FaceIdx, CurrentPart, 'Decal')

                        if (Items.get('class') == 'Texture'):
                            if (Workspace.attrib.get('class') == 'Part'):
                                for Texture in Items.iter():
                                    if (Texture.tag == 'token'):
                                        if (Texture.attrib.get('name') == 'Face'):
                                            FaceIdx = int(Texture.text)
                                    if (Texture.tag == 'hash'):
                                        TextureDuplicated(Texture.text, FaceIdx, CurrentPart)
                                    # We will use this later for now we assume every texture uses default values.                                    
                                    """
                                    if (Texture.tag == 'float'):
                                        if (Texture.attrib.get('name') == 'StudsPerTileU'):
                                            print("StudsPerTileU: " + Texture.text)
                                        if (Texture.attrib.get('name') == 'StudsPerTileV'):
                                            print("StudsPerTileV: " + Texture.text)
                                    """
                                    if (Texture.tag == 'binary'):
                                        GetLocalTexture(Texture, FaceIdx, CurrentPart, 'Texture')

class StartConverting(bpy.types.Operator):
    bl_idname = "scene.button_operator_convert"
    bl_label = "Start Converting"

    def execute(self, context):
        global bpyscene
        global dobjects
        global objects
        global rbxlx
        global RobloxPlace
        global RobloxInstallLocation
        global PlaceName
        global AssetsDir
        global localTexId

        bpyscene = context.scene
        dobjects = bpy.data.objects
        objects = context.scene.objects

        RobloxPlace = bpyscene.Place_Path.file_path
        RobloxInstallLocation = bpyscene.Install_Path.file_path
        PlaceName = os.path.splitext(os.path.basename(RobloxPlace))[0]
        AssetsDir = PlaceName + "Assets"
        localTexId = 0
        
        rbxlx = RobloxPlace.lower().endswith(('rbxlx'))
        root = ET.parse(RobloxPlace).getroot()

        timer = 0.0
        start = timeit.default_timer()

        # bpy.ops.object.select_all(action='DESELECT')
        for i in context.selectable_objects:
            i.select_set(False)

        for i in bpy.data.meshes:
            bpy.data.meshes.remove(i)

        for i in bpy.data.materials:
            bpy.data.materials.remove(i)

        GetDataFromPlace(root)

        # If place has textures fill up TextureList.
        if (os.path.exists(AssetsDir)):
            for i in os.listdir(AssetsDir):
                TextureList.append(os.path.abspath(AssetsDir + "/" + i))
                TextureList.append(CreateMaterialWithTexture(AssetsDir + "/" + i))

        # Convert md5 hash to the texture path
        for i in PartsList:
            for v in i.md5Textures:
                md5Texture = v[0]
                for TexturePath in TextureList:
                    if(md5(TexturePath) == md5Texture):
                        # Change md5 hash to texture path
                        v[0] = TexturePath
                        i.textures.append(v)

        for Part in PartsList:
            CreatePart(Part.scale, Part.rotation, Part.location, Part.brickColor, Part.brickType, Part.textures)

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
            
            bpy.context.tool_settings.mesh_select_mode = [False, False, True]
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
            for brick in BrickList:
                mesh = brick[0]
                scale = brick[1]

                bm = bmesh.new()
                bm.from_mesh(mesh)
                uv_layer = bm.loops.layers.uv.verify()
                bm.faces.ensure_lookup_table()


                # top and bottom of brick gets their UV stretched, creates tiling for the studs.
                for idxFace, face in enumerate(bm.faces):
                    # Check if part contains textures
                    # If true select face
                        # Apply material to face
                        # Deselect
                    
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
                bm.to_mesh(mesh)


        """ Roblox does some funny shit to the UV's on the sides, this looks 'ok' but its not the same as in Roblox.
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
        return {'FINISHED'}

