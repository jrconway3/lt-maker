from app.data.data import Data, Prefab

from app.data.unit_object import UnitObject

# Main Level Object used by engine
class LevelObject(Prefab):
    def __init__(self):
        self.nid = None
        self.title = None
        self.tilemap = None

        self.music = {}
        self.market_flag = False
        self.objective = {}

        self.units = Data()

    @classmethod
    def from_prefab(cls, prefab, tilemap):
        level = cls()
        level.nid = prefab.nid
        level.title = prefab.title
        level.tilemap = tilemap

        level.music = {k: v for k, v in prefab.music.items()}
        level.market_flag = prefab.market_flag
        level.objective = {k: v for k, v in prefab.objective.items()}

        level.units = Data([UnitObject.from_prefab(prefab) for prefab in prefab.units])
        return level

    def serialize(self):
        s_dict = {'nid': self.nid,
                  'title': self.title,
                  'tilemap': self.tilemap.serialize(),
                  'music': self.music,
                  'market_flag': self.market_flag,
                  'objective': self.objective,
                  'units': [unit.nid for unit in self.units],
                  }
        return s_dict

    def deserialize(cls, s_dict, tilemap, game):
        level = cls()
        level.nid = s_dict['nid']
        level.title = s_dict['title']
        level.tilemap = tilemap

        level.music = s_dict['music']
        level.market_flag = s_dict['market_flag']
        level.objective = s_dict['objective']

        level.units = Data(game.get_unit(unit_nid) for unit_nid in s_dict['units'])
        return level
