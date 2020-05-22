from app.data.data import Data, Prefab

class TileMapObject(Prefab):
    @classmethod
    def from_prefab(cls, prefab):
        self.nid = prefab.nid
        self.width = prefab.width
        self.height = prefab.height
        self.layers = Data()

        # Stitch together image layers
        for layer in prefab.layers:
