from app.data.data import Data, Prefab

from app.data.unit_object import UnitObject

# Main Level Object used by engine
class LevelObject(Prefab):
    def __init__(self, prefab, tilemap):
        self.nid = prefab.nid
        self.title = prefab.title
        self.tilemap = tilemap

        self.music = {k: v for k, v in prefab.music.items()}
        self.market_flag = prefab.market_flag
        self.objective = {k: v for k, v in prefab.objective.items()}

        self.units = Data([UnitObject(prefab) for prefab in prefab.units])
