from copy import deepcopy
from math import radians, degrees
from typing import NamedTuple
from collections import namedtuple
from io import BytesIO
from xml.etree.ElementTree import Element
from typing import List

from . legacycolors import BrickColor
from . assetreader import MeshAsset
from . assetrequester import AssetRequester
from . types import *
from . mesh import GetMeshFromMeshData

import mathutils
import bmesh
import bpy
import os
import base64
import hashlib
import imghdr
import re
import shutil
import xml.etree.ElementTree as ET

# debug
import timeit

PartsList = []
BrickList = []
CylinderList = []
SphereList = []

RotationMatrix = mathutils.Matrix(([0,0,0],[0,0,0],[0,0,0]))
rbxlx = False

def GetRotationFromMatrix(part: Part, EulerVector3):
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

def CreateMaterialFromBytes(data: MeshAsset, AssetsDir: str):
    open("tmp", 'wb').write(data.texture)
    assetType = imghdr.what('tmp')
    textureName = "tex_" + str(data.texture_id) + "." + str(assetType)

    if (os.path.exists(AssetsDir + "/" + textureName)):
        os.remove(AssetsDir + "/" + textureName)

    os.rename(r'tmp',r'' + textureName)
    shutil.move(textureName, AssetsDir)

    texture_path = os.path.abspath(AssetsDir + "/" + textureName)

    return CreateMaterialWithTexture(texture_path)

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
def GetDataFromPlace(roblox_place_file):
    global PartsList
    global CylinderList
    global BrickList
    global SphereList

    # Clearing lists since if the addon was run once there will be stuff in it.
    PartsList = []
    CylinderList = []
    BrickList = []
    SphereList = []

    context = ET.iterparse(roblox_place_file, events=("start", "end"))
    event: Element
    element: Element
    parent_element: List[Element] = []
    nested_parts: List[Part] = []

    # location_list = [0.0, 0.0, 0.0]
    # part_size = [0.0, 0.0, 0.0]
    # rotation_list = [0,0,0,0,0,0,0,0,0]
    current_part = None

    vector3_index = {
        'X':0,
        'Y':1,
        'Z':2
    }

    rotation_index = {
        'R00':0,
        'R01':1,
        'R02':2,
        'R10':3,
        'R11':4,
        'R12':5,
        'R20':6,
        'R21':7,
        'R22':8,
    }

    TileU = 2
    TileV = 2
    OffsetU = 0 # not used
    OffsetV = 0 # not used
    face_index = 0
    
    for event, element in context:
        # event: start, end
        if element.tag == 'Item':
            class_attrib = element.attrib.get('class')
            if class_attrib == 'Workspace':
                if event == 'end':
                    break

            if class_attrib == 'Part':
                if event == 'start':
                    parent_element.append(element)
                    current_part = Part()
                    nested_parts.append(current_part)
                elif event == 'end':
                    PartsList.append(nested_parts[-1])
                    parent_element.pop()
                    nested_parts.pop()
                    current_part = None

            if class_attrib == 'Decal' or class_attrib == 'Texture':
                if event == 'start':
                    parent_element.append(element)
                elif event == 'end':
                    parent_element.pop()

        if parent_element:
            if parent_element[0].attrib.get('class') == 'Part':
                if element.tag == 'CoordinateFrame':
                    if event == 'start':
                        parent_element.append(element)
                    elif event == 'end':
                        parent_element.pop()
                if element.attrib.get('name') == 'size':
                    if event == 'start':
                        parent_element.append(element)
                    elif event == 'end':
                        parent_element.pop()
                
                if event == 'end':
                    if element.get('name') == 'Color3uint8':
                        nested_parts[-1].brickColor = int(element.text)
                    if element.get('name') == 'BrickColor':
                        nested_parts[-1].brickColor = int(element.text)

                    if element.get('name') == 'shape':
                        nested_parts[-1].brickType = int(element.text)
                
                    if len(parent_element) > 1:
                        if parent_element[-1].attrib.get('name') == 'CFrame':
                            if vector3_index.get(element.tag) == None:
                                pass
                            else:
                                nested_parts[-1].location[vector3_index.get(element.tag)] = float(element.text)

                            if rotation_index.get(element.tag) == None:
                                pass
                            else:
                                nested_parts[-1].rotation_matrix[rotation_index.get(element.tag)] = float(element.text)
                                if element.tag == 'R22':
                                    nested_parts[-1].set_rotation_from_matrix()

                        if parent_element[-1].attrib.get('name') == 'size':
                            if vector3_index.get(element.tag) == None:
                                pass
                            else:
                                nested_parts[-1].scale[vector3_index.get(element.tag)] = float(element.text)

            if len(parent_element) > 1:
                if parent_element[1].attrib.get('class') == 'Decal':
                    if element.tag == 'Content':
                        if event == 'start':
                            parent_element.append(element)
                        elif event == 'end':
                            parent_element.pop()
                    
                    if event == 'end':
                        if element.get('name') == 'Face':
                            face_index = GetFaceIndex(int(element.text))
                        if element.tag == 'hash' or element.tag == 'url':
                            AssetRequester.GetOnlineTexture(element.text, face_index, nested_parts[0], 'Decal', TileUV(None, None))
                        if element.tag == 'binary':
                            AssetRequester.GetLocalTexture(element, face_index, nested_parts[0], 'Decal')

                if parent_element[1].attrib.get('class') == 'Texture':
                    if element.tag == 'Content':
                        if event == 'start':
                            parent_element.append(element)
                        elif event == 'end':
                            parent_element.pop()

                    if event == 'end':
                        if element.get('name') == 'StudsPerTileU':
                            TileU = float(element.text)
                        if element.get('name') == 'StudsPerTileV':
                            TileV = float(element.text)

                        if element.get('name') == 'OffsetStudsU':
                            OffsetU = float(element.text)
                        if element.get('name') == 'OffsetStudsV':
                            OffsetV = float(element.text)

                        if element.get('name') == 'Face':
                            face_index = GetFaceIndex(int(element.text))
                        
                        if element.tag == 'url':
                            AssetRequester.GetOnlineTexture(element.text, face_index, nested_parts[0], 'Texture', TileUV(TileU, TileV))
                        elif element.tag == 'hash':
                            TextureDuplicated(element.text, face_index, nested_parts[0])
                        elif element.tag == 'binary':
                            AssetRequester.GetLocalTexture(element, face_index, nested_parts[0], 'Texture')

class StartConverting(bpy.types.Operator):
    bl_idname = "scene.button_operator_convert"
    bl_label = "Start Converting"

    def execute(self, context):
        global rbxlx
        bpyscene = context.scene

        roblox_place_file = bpyscene.Place_Path.file_path
        roblox_install_directory = bpyscene.Install_Path.file_path
        place_name = os.path.splitext(os.path.basename(roblox_place_file))[0]
        
        asset_dir = place_name + "Assets"
        TextureList = []

        rbxlx = roblox_place_file.lower().endswith(('rbxlx'))

        timer = 0.0
        start = timeit.default_timer()

        for i in context.selectable_objects:
            i.select_set(False)

        for i in bpy.data.meshes:
            bpy.data.meshes.remove(i)

        for i in bpy.data.materials:
            bpy.data.materials.remove(i)

        timer_data = 0.0
        timer_data_start = timeit.default_timer()
        
        AssetRequester.asset_dir = asset_dir
        AssetRequester.place_name = place_name
        AssetRequester.roblox_install_directory = roblox_install_directory
        AssetRequester.local_texture_id = 0
        
        GetDataFromPlace(roblox_place_file)
        
        timer_data += (timeit.default_timer() - timer_data_start)
        print("data done:", timer_data)

        if not os.path.exists(asset_dir):
            os.mkdir(asset_dir)

        # If place has textures fill up TextureList.
        if (os.path.exists(asset_dir)):
            for i in os.listdir(asset_dir):
                TextureList.append(os.path.abspath(asset_dir + "/" + i))

        # Convert md5 hash to the texture path
        part: Part
        
        for part in PartsList:
            textureMd5: TextureMd5
            for textureMd5 in part.md5Textures:
                for TexturePath in TextureList:
                    if (md5(TexturePath) == textureMd5.md5):
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
                                        if (idxLoop == 0): # 1
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, (-brick.scale[2]/texture.tileUV.TileV) + 1.0]
                                        if (idxLoop == 1): # 4
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, 1.0]
                                        if (idxLoop == 2): # 3
                                            loop_uv.uv = [0.0, 1.0]
                                        if (idxLoop == 3): # 2
                                            loop_uv.uv = [0.0, (-brick.scale[2]/texture.tileUV.TileV) + 1.0]
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
        
        asset_mesh = AssetRequester.GetMeshFromAsset("https://assetdelivery.roblox.com/v1/assetId/1091572")
        mesh = GetMeshFromMeshData(asset_mesh)
        mesh.materials.append(CreateMaterialFromBytes(asset_mesh, asset_dir))
        
        timer += (timeit.default_timer() - start)
        print("done", timer)
        return {'FINISHED'}

