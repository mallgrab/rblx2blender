import requests
import io
import xml.etree.ElementTree as ET

class MeshAsset(object):
    def __init__(self, mesh, texture):
        self.mesh = mesh
        self.texture = texture

def GetAssetFromLink(link: str):
    asset = requests.get(link)
    assetLink = asset.json()['location']
    assetFile = requests.get(assetLink, allow_redirects=True)

    return assetFile

def XMLAssetReader(file: str):
    root = ET.parse(io.StringIO(file)).getroot()
    mesh_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='MeshId']/url")[0].text
    texture_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='TextureId']/url")[0].text

    mesh_id = mesh_url[mesh_url.find('='):][1:]
    texture_id = texture_url[texture_url.find('='):][1:]

    mesh = GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + mesh_id)
    texture = GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + texture_id)

    return MeshAsset(mesh, texture)

def GetMeshFromAsset(link: str):
    asset = GetAssetFromLink(link)

    if(asset.content.find(b'roblox xmlns') > -1):   
        mesh_asset = XMLAssetReader(asset.content.decode('ascii').replace("\n", "").replace("\t", ""))
        return mesh_asset

    if(asset.content.find(b'roblox!') > -1):
        print("binary")