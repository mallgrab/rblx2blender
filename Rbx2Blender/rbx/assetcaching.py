class AssetCaching(object):
    asset_ids = []

    @staticmethod
    def PrefetchAssets():
        AssetCaching.asset_ids = list(set(AssetCaching.asset_ids))
        _v = AssetCaching.asset_ids