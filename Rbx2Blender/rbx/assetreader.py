import io
import xml.etree.ElementTree as ET

class MeshAssetIds(object):
    def __init__(self, mesh, texture):
        self.mesh = mesh
        self.texture = texture

class MeshAssetContent(object):
    def __init__(self, mesh, texture):
        self.mesh = mesh
        self.texture = texture

class MeshAsset(object):
    def __init__(self, content: MeshAssetContent, ids: MeshAssetIds):
        self.content = content
        self.ids = ids

def XMLAssetReader(file: str):
    root = ET.parse(io.StringIO(file)).getroot()
    mesh_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='MeshId']/url")[0].text
    texture_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='TextureId']/url")[0].text

    # unsure how it would handle url's that are malformed.
    mesh_id = mesh_url[mesh_url.find('='):][1:]
    texture_id = texture_url[texture_url.find('='):][1:]

    mesh_asset_ids = MeshAssetIds(mesh_id, texture_id)
    return mesh_asset_ids

def BinaryAssetReader(file: bytes):
    _ = file[file.find(b"MeshId"):][24:]
    mesh_id = _[:_.find(b"PROP")].decode("ascii")

    _ = file[file.find(b"TextureId"):][27:]
    texture_id = _[:_.find(b"PROP")].decode("ascii")

    mesh_asset_ids = MeshAssetIds(mesh_id, texture_id)
    return mesh_asset_ids