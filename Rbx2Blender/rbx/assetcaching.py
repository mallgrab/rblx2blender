import glob
import os

from functools import reduce
from . assetrequester import AssetRequester

class Asset(object):
    def __init__(self, asset_id: str, asset_type: str):
        self.asset_id = asset_id
        self.asset_type = asset_type
    
    def __hash__(self):
        return hash(self.asset_id)

    def __eq__(self, other):
        return self.asset_id == other.asset_id

class AssetCaching(object):
    assets = []

    @staticmethod
    def PrefetchAssets():
        asset_set = list(set(AssetCaching.assets))

        AssetCaching.assets = list(set(AssetCaching.assets))
        cached_asset_ids = [os.path.basename(asset) for asset in glob.glob(AssetRequester.asset_dir + "/*")]

        # remove binary textures
        for index, asset_id in enumerate(cached_asset_ids):
            if asset_id.find("tex_") > -1:
                cached_asset_ids.pop(index)

        # remove extension of local asset
        for index, asset_id in enumerate(cached_asset_ids):
            asset_id_split = asset_id.split(".")
            if asset_id_split:
                cached_asset_ids[index] = asset_id_split[0]


        cached_asset_set = []
        for asset in asset_set:
            for asset_id in cached_asset_ids:
                if asset.asset_id == asset_id:
                    cached_asset_set.append(asset)
        
        uncached_assets = list(reduce(lambda x,y : filter(lambda z: z!=y,x), cached_asset_set, asset_set))