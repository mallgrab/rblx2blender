import requests

def GetAssetFromLink(link: str):
    asset = requests.get(link)
    assetLink = asset.json()['location']
    assetFile = requests.get(assetLink, allow_redirects=True)

    return assetFile

def GetMeshFromAsset(link: str):
    asset = GetAssetFromLink(link)
    
    print(asset)