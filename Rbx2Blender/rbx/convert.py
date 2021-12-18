from math import radians
from xml.etree.ElementTree import Element
from typing import List

from . legacycolors import BrickColor
from . assetrequester import AssetRequester
from . assetcaching import AssetCaching, Asset
from . types import *

import mathutils
import bmesh
import bpy
import os
import hashlib
import imghdr
import shutil
import glob
import xml.etree.ElementTree as ET

# debug
import cProfile
import pstats

class RbxPartContainer(object):
    PartsList = []
    BrickList = []
    CylinderList = []
    SphereList = []

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

def CreateMaterialFromBytes(data: bytes, texture_name: str):
    file = None

    for directory_file in glob.glob(AssetRequester.asset_dir + "/" + texture_name + ".*"):
        file = directory_file
    
    if not file:
        open("tmp", 'wb').write(data)
        assetType = imghdr.what('tmp')
        texture_name = texture_name + "." + str(assetType)
        os.rename(r'tmp',r'' + texture_name)
        shutil.move(texture_name, AssetRequester.asset_dir)
        texture_path = os.path.abspath(AssetRequester.asset_dir + "/" + texture_name)
    else:
        texture_path = os.path.abspath(file)

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

def CreateMaterialFromBrickColor(colorID, place_file_rbxlx: bool):
    if place_file_rbxlx:
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

def CreatePart(part: Part, place_file_rbxlx: bool):
    if (part.brickType == 2):
        mesh = bpy.data.meshes.new('Part_Cylinder')
        basic_cylinder = bpy.data.objects.new("Part_Cylinder", mesh)
        bpy.context.collection.objects.link(basic_cylinder)
        
        # blender 3.0+ changed diameter1 to radius1
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
        basic_cylinder.data.materials.append(CreateMaterialFromBrickColor(part.brickColor, place_file_rbxlx))
        basic_cylinder.select_set(False)
        
        RbxPartContainer.CylinderList.append(mesh)
               
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
        basic_brick.data.materials.append(CreateMaterialFromBrickColor(part.brickColor, place_file_rbxlx))
        basic_brick.select_set(False)

        RbxPartContainer.BrickList.append(Brick(mesh, part.scale, part.textures))
        
    if (part.brickType == 0):
        mesh = bpy.data.meshes.new('Part_Sphere')
        basic_sphere = bpy.data.objects.new("Part_Sphere", mesh)

        bpy.context.collection.objects.link(basic_sphere)
        bm = bmesh.new()
        
        # blender 3.0+ changed diameter to radius
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
        basic_sphere.data.materials.append(CreateMaterialFromBrickColor(part.brickColor, place_file_rbxlx))
        bpy.ops.object.shade_smooth()

# Rewrite this into a seperate class where we gather everything into Lists.
# Functions that require access to the list do it through the class object.

# Also use https://docs.python.org/3/library/xml.etree.elementtree.html#example (XPath, findall, etc)
def GetDataFromPlace(roblox_place_file):
    # Clearing lists since if the addon was run once there will be stuff in it.
    RbxPartContainer.PartsList = []
    RbxPartContainer.CylinderList = []
    RbxPartContainer.BrickList = []
    RbxPartContainer.SphereList = []

    context = ET.iterparse(roblox_place_file, events=("start", "end"))
    event: Element
    element: Element
    parent_element: List[Element] = []
    nested_parts: List[Part] = []
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
                    RbxPartContainer.PartsList.append(nested_parts[-1])
                    parent_element.pop()
                    nested_parts.pop()
                    current_part = None

            if (class_attrib == 'Decal' or 
                class_attrib == 'Texture' or 
                class_attrib == 'SpecialMesh'):
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
                if parent_element[1].attrib.get('class') == 'SpecialMesh':
                    if (element.attrib.get('name') == 'MeshId' or
                        element.attrib.get('name') == 'TextureId' or
                        element.attrib.get('name') == 'Scale'):
                        if event == 'start':
                            parent_element.append(element)
                        elif event == 'end':
                            parent_element.pop()
                    
                    if event == 'end':
                        if parent_element[-1].attrib.get('name') == 'Scale':
                            nested_parts[-1].scale[vector3_index.get(element.tag)] = float(element.text)
                        
                        if element.tag == 'url':
                            if parent_element[-1].attrib.get('name') == 'MeshId':
                                mesh_id = AssetRequester.GetAssetId(element.text)
                                AssetCaching.assets.append(Asset(mesh_id, "mesh"))
                                nested_parts[-1].meshes.append(mesh_id)
                                
                            elif parent_element[-1].attrib.get('name') == 'TextureId':
                                texture_id = AssetRequester.GetAssetId(element.text)
                                AssetCaching.assets.append(Asset(texture_id, "texture"))
                                nested_parts[-1].mesh_textures.append(texture_id)

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
                            texture_id = AssetRequester.GetAssetId(element.text)
                            AssetCaching.assets.append(Asset(texture_id, "texture"))
                            texture_directory = AssetRequester.GetOnlineTexture(element.text)
                            texture = Texture(texture_directory, face_index, 'Decal', TileUV(None, None))
                            nested_parts[0].textures.append(texture)

                        if element.tag == 'binary':
                            AssetRequester.GetLocalTexture(element.text, face_index, nested_parts[0], 'Decal')

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
                            texture_id = AssetRequester.GetAssetId(element.text)
                            AssetCaching.assets.append(Asset(texture_id, "texture"))
                            texture_directory = AssetRequester.GetOnlineTexture(element.text)
                            texture = Texture(texture_directory, face_index, 'Texture', TileUV(TileU, TileV))
                            nested_parts[0].textures.append(texture)
                            
                        elif element.tag == 'hash':
                            TextureDuplicated(element.text, face_index, nested_parts[0])
                        elif element.tag == 'binary':
                            AssetRequester.GetLocalTexture(element.text, face_index, nested_parts[0], 'Texture')

class StartConverting(bpy.types.Operator):
    bl_idname = "scene.button_operator_convert"
    bl_label = "Start Converting"

    def execute(self, context: bpy.types.Context):
        cProfile.runctx("self.ConvertProcess(context)", globals(), locals(), "rbx_performance.prof")
        p = pstats.Stats("rbx_performance.prof")
        p.sort_stats("tottime").print_stats(10)
        return {'FINISHED'}

    def ConvertProcess(self, context: bpy.types.Context):
        bpyscene = context.scene

        # https://docs.blender.org/api/current/bpy.types.WindowManager.html?highlight=progress_begin#bpy.types.WindowManager.progress_begin
        context.window_manager.progress_begin(0, 10)

        roblox_place_file = bpyscene.Place_Path.file_path
        roblox_install_directory = bpyscene.Install_Path.file_path
        place_name = os.path.splitext(os.path.basename(roblox_place_file))[0]

        asset_dir = "placeassets" + "/" + place_name + "_assets"
        TextureList = []

        place_file_rbxlx = roblox_place_file.lower().endswith(('rbxlx'))

        for i in context.selectable_objects:
            i.select_set(False)

        for i in bpy.data.meshes:
            bpy.data.meshes.remove(i)

        for i in bpy.data.materials:
            bpy.data.materials.remove(i)

        if not os.path.exists("placeassets"):
            os.mkdir("placeassets")

        if not os.path.exists(asset_dir):
            os.mkdir(asset_dir)

        AssetRequester.asset_dir = asset_dir
        AssetRequester.place_name = place_name
        AssetRequester.roblox_install_directory = roblox_install_directory
        AssetRequester.local_texture_id = 0
        AssetCaching.assets = []

        GetDataFromPlace(roblox_place_file)

        # GetAssetFromId the list
        # When it all works use worker threads to speed stuff up because ssl read is slow
        AssetCaching.PrefetchAssets()

        # If place has textures fill up TextureList.
        if os.path.exists(asset_dir):
            for i in os.listdir(asset_dir):
                TextureList.append(os.path.abspath(asset_dir + "/" + i))

        # Convert md5 hash to the texture path
        part: Part
        for part in RbxPartContainer.PartsList:
            textureMd5: TextureMd5
            for textureMd5 in part.md5Textures:
                for TexturePath in TextureList:
                    if (md5(TexturePath) == textureMd5.md5):
                        # Change md5 hash to texture path
                        # Should probably just add texture path as a variable within TextureMd5
                        textureMd5.md5 = TexturePath
                        part.textures.append(textureMd5)


        for part in RbxPartContainer.PartsList:
            if part.meshes:
                mesh = AssetRequester.GetMeshFromId(part.meshes[0], part)
                if part.mesh_textures:
                    mesh_texture_path = AssetRequester.GetOnlineTexture(part.mesh_textures[0])
                    mesh_material = CreateMaterialWithTexture(mesh_texture_path)
                    mesh.materials.append(mesh_material)
                continue
            CreatePart(part, place_file_rbxlx)


        # Rotate place properly
        for obj in bpy.context.scene.objects:
            obj.select_set(True)

        for obj_selected in bpy.context.selected_objects:
            obj_selected.rotation_euler.x = radians(90.0)

        # Seperate top and bottom part of cylinder so smoothing looks good
        if RbxPartContainer.CylinderList:
            for i in RbxPartContainer.CylinderList:
                for v in i.polygons:
                    if (v.vertices.__len__() == 12):
                        v.select = True
            
            bpy.context.tool_settings.mesh_select_mode = [False, False, True]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')

        for obj_scene in bpy.context.scene.objects:
            obj_scene.select_set(False)

        # Complains for some reason on some places, bad if we disable it?
        # bpy.ops.object.mode_set(mode='OBJECT')

        if RbxPartContainer.BrickList:
            brick: Brick
            for brick in RbxPartContainer.BrickList:
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
                                            loop_uv.uv = [1.0, 0.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [1.0, 1.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, 1.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [0.0, 0.0]
                                    if (idxFace == 0 or idxFace == 2):
                                        if (idxLoop == 0):
                                            loop_uv.uv = [0.0, 0.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [1.0, 0.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [1.0, 1.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [0.0, 1.0]
                                    if (idxFace == 5 or idxFace == 4):    
                                        if (idxLoop == 0):
                                            loop_uv.uv = [1.0, 1.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [0.0, 1.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, 0.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [1.0, 0.0]                               
                                    else:
                                        continue

                            if (texture.faceIdx == idxFace):
                                if (texture.type == 'Texture'):
                                    if texture.tileUV.TileU == None:
                                        continue
                                    loop_uv = loop[uv_layer]
                                    if (idxFace == 1 or idxFace == 3):
                                        if (idxLoop == 0):
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, (-brick.scale[2]/texture.tileUV.TileV) + 1.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [brick.scale[0]/texture.tileUV.TileU, 1.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [0.0, 1.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [0.0, (-brick.scale[2]/texture.tileUV.TileV) + 1.0]
                                    if (idxFace == 0):
                                        if (idxLoop == 0):
                                            loop_uv.uv = [0.0, (-brick.scale[1]/texture.tileUV.TileV) + 1.0]
                                        if (idxLoop == 1):
                                            loop_uv.uv = [(brick.scale[0]/texture.tileUV.TileU), (-brick.scale[1]/texture.tileUV.TileV) + 1.0]
                                        if (idxLoop == 2):
                                            loop_uv.uv = [(brick.scale[0]/texture.tileUV.TileU), 1.0]
                                        if (idxLoop == 3):
                                            loop_uv.uv = [0.0, 1.0]
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
