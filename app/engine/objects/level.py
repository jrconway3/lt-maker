from app.utilities.data import Data

from app.engine.objects.unit import UnitObject
from app.engine.objects.tilemap import TileMapObject
from app.event.region import Region
from app.data.level_units import UnitGroup

# Main Level Object used by engine
class LevelObject():
    def __init__(self):
        self.nid: str = None
        self.name: str = None
        self.tilemap: TileMapObject = None  # Actually the tilemap, not a nid

        self.music = {}
        self.objective = {}

        self.units = Data()
        self.regions = Data()
        self.unit_groups = Data()

        self.fog_of_war = 0

    @classmethod
    def from_prefab(cls, prefab, tilemap):
        level = cls()
        level.nid = prefab.nid
        level.name = prefab.name
        level.tilemap = tilemap

        level.music = {k: v for k, v in prefab.music.items()}
        level.objective = {k: v for k, v in prefab.objective.items()}

        level.units = Data([UnitObject.from_prefab(p) for p in prefab.units])
        level.regions = Data([Region.from_prefab(p) for p in prefab.regions])
        level.unit_groups = Data([UnitGroup.from_prefab(p) for p in prefab.regions])

        return level

    def save(self):
        s_dict = {'nid': self.nid,
                  'name': self.name,
                  'tilemap': self.tilemap.save(),
                  'music': self.music,
                  'objective': self.objective,
                  'units': [unit.nid for unit in self.units],
                  'regions': [region.save() for region in self.regions],
                  'unit_groups': [unit_group.save() for unit_group in self.unit_groups],
                  }
        return s_dict

    @classmethod
    def restore(cls, s_dict, game):
        level = cls()
        level.nid = s_dict['nid']
        level.name = s_dict['name']
        level.tilemap = TileMapObject.restore(s_dict['tilemap'])

        level.music = s_dict['music']
        level.objective = s_dict['objective']

        level.units = Data([game.get_unit(unit_nid) for unit_nid in s_dict['units']])
        level.regions = Data([Region.restore(region) for region in s_dict['regions']])
        level.unit_groups = Data([UnitGroup.restore(unit_group) for unit_group in s_dict['unit_groups']])

        return level
