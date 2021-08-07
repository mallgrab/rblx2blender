class AssetCaching(object):
    asset_ids = []

    @staticmethod
    def PrefetchAssets():
        for asset_id in AssetCaching.asset_ids:
            print(asset_id)