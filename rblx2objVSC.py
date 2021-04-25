import xml.etree.ElementTree as ET
import math
from copy import deepcopy
from math import radians
from math import degrees
from math import (
    asin, pi, atan2, cos 
)

# location, rotation, scale, brickcolor
PartsList = []
CurrentPart = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0.0, 0.0, 0.0],[0]]
R = [[[0.0, 0.0, 0.0],
      [0.0, 0.0, 0.0],
      [0.0, 0.0, 0.0]]]

def InsertPartIntoList():
    temp = deepcopy(CurrentPart)
    PartsList.append(temp)

def CalculateRotation():
    # blender has rotation matrix so this might be useless
    theta = math.acos(((R[0][0][0] + R[0][1][1] + R[0][2][2]) - 1) / 2)
    if (theta == 0.0):  # do nothing if no rotation was applied
        CurrentPart[1][0] = 0.0
        CurrentPart[1][1] = 0.0
        CurrentPart[1][2] = 0.0
        return

    if R[0][2][0] == -1.0:
        rx = math.pi/2.0
        ry = 0.0
        rz = -math.atan2(R[0][0][1],R[0][0][2])
    elif R[0][2][0] == 1.0:
        rx = -math.pi/2.0
        ry = 0.0
        rz = math.atan2(-R[0][0][1],-R[0][0][2])
    else:
        multi = 1 / (2 * math.sin(theta))

        rx = multi * (R[0][2][1] - R[0][1][2]) * theta
        ry = multi * (R[0][0][2] - R[0][2][0]) * theta
        rz = multi * (R[0][1][0] - R[0][0][1]) * theta

    # rx = degrees(rx)
    # ry = degrees(ry)
    # rz = degrees(rz)

    CurrentPart[1][0] = rx
    CurrentPart[1][1] = ry
    CurrentPart[1][2] = rz

#root = ET.parse('Place1.rbxl').getroot()
root = ET.parse('C:/Users/win-spike/Desktop/rbxl2obj/cannon.rbxl').getroot()

for DataModel in root:
    if (DataModel.get('class') == 'Workspace'):
        for Workspace in DataModel.iter('Item'):
            if (Workspace.get('class') == 'Part'):
                for Parts in Workspace.iter('Properties'):
                    for Properties in Parts.iter():
                        if (Properties.tag == 'int'):
                            if (Properties.attrib.get('name') == 'BrickColor'):
                                CurrentPart[3] = int(Properties.text)
                                
                        if (Properties.tag == 'CoordinateFrame'):
                            if (Properties.attrib.get('name') == 'CFrame'):
                                for Pos in Properties.iter():
                                    if (Pos.tag == 'X'): CurrentPart[0][0] = float(Pos.text)
                                    if (Pos.tag == 'Y'): CurrentPart[0][1] = float(Pos.text)
                                    if (Pos.tag == 'Z'): CurrentPart[0][2] = float(Pos.text)
                                    if (Pos.tag == 'R00'): R[0][0][0] = float(Pos.text)
                                    if (Pos.tag == 'R01'): R[0][0][1] = float(Pos.text)
                                    if (Pos.tag == 'R02'): R[0][0][2] = float(Pos.text)
                                    if (Pos.tag == 'R10'): R[0][1][0] = float(Pos.text)
                                    if (Pos.tag == 'R11'): R[0][1][1] = float(Pos.text)
                                    if (Pos.tag == 'R12'): R[0][1][2] = float(Pos.text)
                                    if (Pos.tag == 'R20'): R[0][2][0] = float(Pos.text)
                                    if (Pos.tag == 'R21'): R[0][2][1] = float(Pos.text)
                                    if (Pos.tag == 'R22'): R[0][2][2] = float(Pos.text)

                        if (Properties.tag == 'Vector3'):
                            if (Properties.attrib.get('name') == 'size'):
                                for Pos in Properties.iter():
                                    if (Pos.tag == 'X'): CurrentPart[2][0] = float(Pos.text)
                                    if (Pos.tag == 'Y'): CurrentPart[2][1] = float(Pos.text)
                                    if (Pos.tag == 'Z'): 
                                        CurrentPart[2][2] = float(Pos.text)
                                        CalculateRotation()
                                        InsertPartIntoList()

print("done")