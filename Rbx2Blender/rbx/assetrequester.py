import requests
import os
import base64
import imghdr
import re
import shutil

from . types import TileUV, Part

class AssetRequester(object):
    place_name = ""
    asset_dir = ""
    roblox_install_directory = ""
    local_texture_id = 0

    @staticmethod
    def GetAssetFromLink(link: str):
        asset = requests.get(link)
        assetLink = asset.json()['location']
        headers = {
            'User-Agent': 'Roblox/WinInet',
            'From': 'youremail@domain.com'  # Check with postman later regarding the header roblox studio uses.
        }

        assetFile = requests.get(assetLink, allow_redirects=True, headers=headers)

        return assetFile

    @staticmethod
    def GetMeshFromAsset(link: str):
        from . assetreader import XMLAssetReader, BinaryAssetReader
        asset = AssetRequester.GetAssetFromLink(link)

        if(asset.content.find(b'roblox xmlns') > -1):   
            mesh_asset = XMLAssetReader(asset.content.decode('ascii').replace("\n", "").replace("\t", ""))
            return mesh_asset

        if(asset.content.find(b'roblox!') > -1):
            mesh_asset = BinaryAssetReader(asset.content)
            return mesh_asset
    
    @staticmethod
    def GetLocalTexture(TextureXML, FaceIdx, part, Type):
        from . convert import Texture, TileUV, Part
        base64buffer = TextureXML.text
        base64buffer = base64buffer.replace('\n', '')
        file_content = base64.b64decode(base64buffer)

        if not (os.path.exists(AssetRequester.asset_dir)):
            os.mkdir(AssetRequester.asset_dir)

        open("tmp", 'wb').write(file_content)
        assetType = imghdr.what('tmp')
        textureName = "tex_" + str(AssetRequester.local_texture_id) + "." + str(assetType)
        AssetRequester.local_texture_id += 1

        if (os.path.exists(AssetRequester.asset_dir + "/" + textureName)):
            os.remove(AssetRequester.asset_dir + "/" + textureName)

        os.rename(r'tmp',r'' + textureName)
        shutil.move(textureName, AssetRequester.asset_dir)

        textureDir = os.path.abspath(AssetRequester.asset_dir + "/" + textureName)
        part.textures.append(Texture(textureDir, FaceIdx, Type, TileUV(None, None)))

    @staticmethod
    def GetOnlineTexture(Link, FaceIdx, part: Part, Type, TileUV: TileUV):
        from . convert import Texture
        assetID = re.sub(r'[^0-9]+', '', Link.lower())
        localAsset = False

        if not (os.path.exists(AssetRequester.place_name + "Assets")):
            os.mkdir(AssetRequester.place_name + "Assets")

        # Get local asset from the roblox content folder.
        # This might not work because of backslash formating, depends on blender.
        if not (assetID):
            if ("rbxasset://" in Link):
                assetID = Link.replace('rbxasset://', AssetRequester.roblox_install_directory)
                localAsset = True

        if not (localAsset):
            if (os.path.exists(AssetRequester.asset_dir + "/" + assetID + ".png")):
                os.remove(AssetRequester.asset_dir + "/" + assetID + ".png")

            if (os.path.exists(AssetRequester.asset_dir + "/" + assetID + ".jpeg")):
                os.remove(AssetRequester.asset_dir + "/" + assetID + ".jpeg")

            if not (os.path.exists(assetID + ".png") or os.path.exists(assetID + ".jpeg")):
                assetFile = AssetRequester.GetAssetFromLink('https://assetdelivery.roblox.com/v1/assetId/' + assetID)

                open('tmp', 'wb').write(assetFile.content)
                assetType = imghdr.what('tmp')
                assetFileName = assetID + "." + str(assetType)
                os.rename(r'tmp',r'' + assetFileName)
                shutil.move(assetFileName, AssetRequester.asset_dir)
                textureDir = os.path.abspath(AssetRequester.asset_dir + "/" + assetFileName)
                part.textures.append(Texture(textureDir, FaceIdx, Type, TileUV))