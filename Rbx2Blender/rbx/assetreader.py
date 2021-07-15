import requests
import io
import xml.etree.ElementTree as ET

class MeshAsset(object):
    def __init__(self, mesh, texture, mesh_id, texture_id):
        self.mesh = mesh
        self.texture = texture
        self.mesh_id = mesh_id
        self.texture_id = texture_id

def GetAssetFromLink(link: str):
    asset = requests.get(link)
    assetLink = asset.json()['location']
    assetFile = requests.get(assetLink, allow_redirects=True)

    return assetFile

def XMLAssetReader(file: str):
    root = ET.parse(io.StringIO(file)).getroot()
    mesh_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='MeshId']/url")[0].text
    texture_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='TextureId']/url")[0].text

    # unsure how it would handle url's that are malformed.
    mesh_id = mesh_url[mesh_url.find('='):][1:]
    texture_id = texture_url[texture_url.find('='):][1:]

    mesh = io.BytesIO(GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + mesh_id).content)
    texture = GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + texture_id).content

    mesh_asset = MeshAsset(mesh, texture, mesh_id, texture_id)
    
    return mesh_asset

def BinaryAssetReader(file: bytes):
    _ = file[file.find(b"MeshId"):][24:]
    mesh_id = _[:_.find(b"PROP")].decode("ascii")
    
    _ = file[file.find(b"TextureId"):][27:]
    texture_id = _[:_.find(b"PROP")].decode("ascii")

    mesh = io.BytesIO(GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + mesh_id).content)
    texture = GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + texture_id).content

    mesh_asset = MeshAsset(mesh, texture, mesh_id, texture_id)

    return mesh_asset

def GetMeshFromAsset(link: str):
    asset = GetAssetFromLink(link)

    if(asset.content.find(b'roblox xmlns') > -1):   
        mesh_asset = XMLAssetReader(asset.content.decode('ascii').replace("\n", "").replace("\t", ""))
        return mesh_asset

    if(asset.content.find(b'roblox!') > -1):
        mesh_asset = BinaryAssetReader(asset.content)
        return mesh_asset