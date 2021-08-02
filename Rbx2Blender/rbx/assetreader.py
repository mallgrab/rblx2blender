import io
import xml.etree.ElementTree as ET

class HatAssetIds(object):
    def __init__(self, mesh, texture):
        self.mesh = mesh
        self.texture = texture

class HatAssetContent(object):
    def __init__(self, mesh, texture):
        self.mesh = mesh
        self.texture = texture

class HatAsset(object):
    def __init__(self, content: HatAssetContent, ids: HatAssetIds):
        self.content = content
        self.ids = ids

class MeshAsset(object):
    def __init__(self, mesh_content, mesh_id):
        self.mesh_content = mesh_content
        self.mesh_id = mesh_id

def HatXMLAssetReader(file: str):
    root = ET.parse(io.StringIO(file)).getroot()
    mesh_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='MeshId']/url")[0].text
    texture_url = root.findall(".//*[@class='SpecialMesh']/Properties/Content[@name='TextureId']/url")[0].text

    # unsure how it would handle url's that are malformed.
    mesh_id = mesh_url[mesh_url.find('='):][1:]
    texture_id = texture_url[texture_url.find('='):][1:]

    mesh_asset_ids = HatAssetIds(mesh_id, texture_id)
    return mesh_asset_ids

def HatBinaryAssetReader(file: bytes):
    _ = file[file.find(b"MeshId"):][24:]
    mesh_id = _[:_.find(b"PROP")].decode("ascii")

    _ = file[file.find(b"TextureId"):][27:]
    texture_id = _[:_.find(b"PROP")].decode("ascii")

    mesh_asset_ids = HatAssetIds(mesh_id, texture_id)
    return mesh_asset_ids