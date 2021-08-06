import requests
import os
import base64
import imghdr
import re
import shutil
import io
import glob
import xml.etree.ElementTree as ET

from . types import TileUV, Part, Texture
from . assetreader import HatXMLAssetReader, HatBinaryAssetReader, HatAssetContent, HatAsset, HatAssetIds, MeshAsset
from . mesh import GetMeshFromMeshData

class AssetRequester(object):
    place_name = ""
    asset_dir = ""
    roblox_install_directory = ""
    local_texture_id = 0
    roblox_asset_api_url = "https://assetdelivery.roblox.com/v1/assetId/"

    # multithread this since we can gather a whole list of asset id's then use worker threads
    @staticmethod
    def GetAssetFromLink(link: str):
        asset = requests.get(link)
        asset_link = asset.json()['location']
        headers = {
            'User-Agent': 'Roblox/WinInet',
            'From': 'youremail@domain.com'  # Check with postman later regarding the header roblox studio uses.
        }

        asset_file = requests.get(asset_link, allow_redirects=True, headers=headers)

        return asset_file

    @staticmethod
    def GetAssetFromId(asset_id: str):
        link = AssetRequester.roblox_asset_api_url + asset_id
        asset = AssetRequester.GetAssetFromLink(link)
        return asset.content

    @staticmethod
    def GetAssetId(id: str):
        if id.find('rbxassetid://') > -1:
            asset_id = id.replace('rbxassetid://', '')
        elif id.find('http://www.roblox.com/asset/?id=') > -1:
            asset_id = id.replace('http://www.roblox.com/asset/?id=', '')
        else:
            asset_id = None
        return asset_id

    @staticmethod
    def GetMeshFromHat(link: str):
        asset = AssetRequester.GetAssetFromLink(link)

        if (asset.content.find(b'roblox xmlns') > -1):   
            mesh_asset_ids = HatXMLAssetReader(asset.content.decode('ascii').replace("\n", "").replace("\t", ""))
            
            mesh = io.BytesIO(AssetRequester.GetAssetFromLink(AssetRequester.roblox_asset_api_url + mesh_asset_ids.mesh).content)
            texture = AssetRequester.GetAssetFromLink(AssetRequester.roblox_asset_api_url + mesh_asset_ids.texture).content
            mesh_content = HatAssetContent(mesh, texture)
            
            return HatAsset(mesh_content, mesh_asset_ids)
        elif (asset.content.find(b'roblox!') > -1):
            mesh_asset_ids = HatBinaryAssetReader(asset.content)
            
            mesh = io.BytesIO(AssetRequester.GetAssetFromLink(AssetRequester.roblox_asset_api_url + mesh_asset_ids.mesh).content)
            texture = AssetRequester.GetAssetFromLink(AssetRequester.roblox_asset_api_url + mesh_asset_ids.texture).content
            mesh_content = HatAssetContent(mesh, texture)
            
            return HatAsset(mesh_content, mesh_asset_ids)
        else:
            print("Not a valid hat link")
            return None
    
    @staticmethod
    # add extra arguments to create a blender mesh at xyz pos and hw scale
    def GetMeshFromId(id: str, part: Part):
        asset = AssetRequester.GetAssetFromId(id)
        mesh_id = AssetRequester.GetAssetId(id)
        mesh_content = io.BytesIO(asset)
        
        mesh_asset = MeshAsset(mesh_content, mesh_id)
        mesh = GetMeshFromMeshData(mesh_asset, part)
        return mesh
    
    @staticmethod
    def GetLocalTexture(texture_base64: str, face_index: int, part: Part, type: str):
        texture_base64 = texture_base64.replace('\n', '')
        file_content = base64.b64decode(texture_base64)

        open("tmp", 'wb').write(file_content)
        asset_type = imghdr.what('tmp')
        texture_name = "tex_" + str(AssetRequester.local_texture_id) + "." + str(asset_type)
        AssetRequester.local_texture_id += 1

        if (os.path.exists(AssetRequester.asset_dir + "/" + texture_name)):
            os.remove(AssetRequester.asset_dir + "/" + texture_name)

        os.rename(r'tmp',r'' + texture_name)
        shutil.move(texture_name, AssetRequester.asset_dir)

        texture_directory = os.path.abspath(AssetRequester.asset_dir + "/" + texture_name)
        part.textures.append(Texture(texture_directory, face_index, type, TileUV(None, None)))

    @staticmethod
    def GetOnlineTexture(link: str, face_index: int, part: Part, type: str, tile_uv: TileUV):
        asset_id = re.sub(r'[^0-9]+', '', link.lower())
        local_asset = False

        # Get local asset from the roblox content folder.
        # This might not work because of backslash formating, depends on blender.
        if not asset_id:
            if ("rbxasset://" in link):
                asset_id = link.replace('rbxasset://', AssetRequester.roblox_install_directory)
                local_asset = True

        if not local_asset:
            file = ""
            for directory_file in glob.glob(AssetRequester.asset_dir + "/" + asset_id + ".*"):
                file = directory_file
            
            # Don't download the same asset again if we already have it locally.
            if not os.path.exists(file):
                asset_file = AssetRequester.GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + asset_id)
                open('tmp', 'wb').write(asset_file.content)
                asset_type = imghdr.what('tmp')
                asset_filename = asset_id + "." + str(asset_type)
                os.rename(r'tmp',r'' + asset_filename)
                shutil.move(asset_filename, AssetRequester.asset_dir)
            else:
                asset_filename = os.path.basename(file)
            
            texture_directory = os.path.abspath(AssetRequester.asset_dir + "/" + asset_filename)
            part.textures.append(Texture(texture_directory, face_index, type, tile_uv))