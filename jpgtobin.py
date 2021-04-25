import xml.etree.ElementTree as ET
import io
import base64
import os
import requests
import imghdr
import math
import signal
import re

from PIL import Image
from copy import deepcopy
from math import radians, degrees

RobloxPlace = r'C:\Users\win-spike\Desktop\rbxl2obj\UV.rbxl'
RobloxInstallLocation = r'C:\Users\win-spike\Documents\CnCRemastered\roblox2008\content'
rbxlx = RobloxPlace.lower().endswith(('rbxlx'))
root = ET.parse(RobloxPlace).getroot()

PartsList = []

BrickList = []
CylinderList = []
SphereList = []

class Part:
    location = [0.0, 0.0, 0.0]
    rotation = [0.0, 0.0, 0.0]
    scale = [0.0, 0.0, 0.0]
    brickType = 0
    surface = []
    texID = 0

# location, rotation, scale, brickcolor, type, surface, texID, 
CurrentPart = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0],[0]]
CurrentDecals = []
RotationMatrix = [[0,0,0],[0,0,0],[0,0,0]]

def InsertPartIntoList():
    temp = deepcopy(CurrentPart)
    PartsList.append(temp)

base64Buffer = ""
texID = 0

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

for DataModel in root:
    if (DataModel.get('class') == 'Workspace'):
        for Workspace in DataModel.iter('Item'):
            if (Workspace.get('class') == 'Part'):
                for Parts in Workspace.iter('Properties'):
                    for Properties in Parts.iter():
                        if (rbxlx):
                            if (Properties.tag == 'Color3uint8'):
                                if (Properties.attrib.get('name') == 'Color3uint8'):
                                    CurrentPart[3] = int(Properties.text)
                        else:
                            if (Properties.tag == 'int'):
                                if (Properties.attrib.get('name') == 'BrickColor'):
                                    CurrentPart[3] = int(Properties.text)
                        if (Properties.tag == 'token'):
                            if (Properties.attrib.get('name') == 'shape'):
                                CurrentPart[4] = int(Properties.text)
                                
                        if (Properties.tag == 'CoordinateFrame'):
                            if (Properties.attrib.get('name') == 'CFrame'):
                                for Pos in Properties.iter():
                                    if (Pos.tag == 'X'): CurrentPart[0][0] = float(Pos.text)
                                    if (Pos.tag == 'Y'): CurrentPart[0][1] = float(Pos.text)
                                    if (Pos.tag == 'Z'): CurrentPart[0][2] = float(Pos.text)
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
                                    if (Pos.tag == 'X'): CurrentPart[2][0] = float(Pos.text)
                                    if (Pos.tag == 'Y'): CurrentPart[2][1] = float(Pos.text)
                                    if (Pos.tag == 'Z'): 
                                        CurrentPart[2][2] = float(Pos.text)
                                        InsertPartIntoList()
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
print("done")