import glob
import os

from functools import reduce
from . assetrequester import AssetRequester

class AssetCaching(object):
    asset_ids = []

    @staticmethod
    def PrefetchAssets():
        AssetCaching.asset_ids = list(set(AssetCaching.asset_ids))
        local_assets = glob.glob(os.path.abspath(AssetRequester.asset_dir + "/*"))
        
        # Remove assets that we already have locally
        for index, file in enumerate(local_assets):
            local_assets[index] = os.path.basename(file)

        # Return assets that don't exist in both local_assets and asset_ids
        request_assets = list(reduce(lambda x,y : filter(lambda z: z!=y,x), AssetCaching.asset_ids, local_assets))