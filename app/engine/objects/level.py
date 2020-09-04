from app.utilities.data import Data

from app.engine.objects.unit import UnitObject
from app.engine.objects.tilemap import TileMapObject

# Main Level Object used by engine
class LevelObject():
    def __init__(self):
        self.nid: str = None
        self.name: str = None
        self.tilemap: TileMapObject = None  # Actually the tilemap, not a nid

        self.music = {}
        self.objective = {}

        self.units = Data()

        self.fog_of_war = 0

    @classmethod
    def from_prefab(cls, prefab, tilemap):
        level = cls()
        level.nid = prefab.nid
        level.name = prefab.name
        level.tilemap = tilemap

        level.music = {k: v for k, v in prefab.music.items()}
        level.objective = {k: v for k, v in prefab.objective.items()}

        level.units = Data([UnitObject.from_prefab(prefab) for prefab in prefab.units])
        
        level.fog_of_war = prefab.fog_of_war

        return level

    def save(self):
        s_dict = {'nid': self.nid,
                  'title': self.title,
                  'tilemap': self.tilemap.save(),
                  'music': self.music,
                  'objective': self.objective,
                  'units': [unit.nid for unit in self.units],
                  'fog_of_war': self.fog_of_war,
                  }
        return s_dict

    @classmethod
    def restore(cls, s_dict, game):
        level = cls()
        level.nid = s_dict['nid']
        level.title = s_dict['title']
        level.tilemap = TileMapObject.restore(s_dict['tilemap'])

        level.music = s_dict['music']
        level.objective = s_dict['objective']

        level.units = Data([game.get_unit(unit_nid) for unit_nid in s_dict['units']])

        level.fog_of_war = s_dict['fog_of_war']

        return level
