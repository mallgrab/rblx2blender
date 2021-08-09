import glob
import os

from functools import reduce
from . assetrequester import AssetRequester

class Asset(object):
    def __init__(self, asset_id: int, asset_type: str):
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
        local_assets = glob.glob(os.path.abspath(AssetRequester.asset_dir + "/*"))
        
        # Remove assets that we already have locally
        for index, file in enumerate(local_assets):
            local_assets[index] = os.path.basename(file)

        # Return assets that don't exist in both local_assets and asset_ids
        request_assets = list(reduce(lambda x,y : filter(lambda z: z!=y,x), AssetCaching.assets, local_assets))