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
from . rblx_legacy_color import BrickColor

# debug
import timeit
timer = 0.0
# global timer
start = timeit.default_timer()

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

class StartConverting(bpy.types.Operator):
    bl_idname = "scene.button_operator_convert"
    bl_label = "Start Converting"

    #root = ET.parse(RobloxPlace).getroot()

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

    def execute(self, context):
        bpyscene = context.scene
        dobjects = bpy.data.objects
        objects = context.scene.objects

        RobloxPlace = bpyscene.Place_Path.file_path
        RobloxInstallLocation = bpyscene.Install_Path.file_path
        rbxlx = RobloxPlace.lower().endswith(('rbxlx'))

        # bpy.ops.object.select_all(action='DESELECT')
        for i in context.selectable_objects:
            i.select_set(False)

        print("Pressed button", BrickColor[1], RobloxPlace)
        return {'FINISHED'}

