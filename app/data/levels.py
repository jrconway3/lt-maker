from collections import OrderedDict

from app.utilities.data import Data, Prefab
from app.data.level_units import UniqueUnit, GenericUnit, UnitGroup
from app.events.regions import Region

class LevelPrefab(Prefab):
    def __init__(self, nid, name):
        self.nid = nid
        self.name = name
        self.tilemap = None  # Tilemap Nid
        self.party = None  # Party Prefab Nid
        self.music = OrderedDict()
        music_keys = ['player_phase', 'enemy_phase', 'other_phase',
                      'player_battle', 'enemy_battle', 'other_battle',
                      'base']
        for key in music_keys:
            self.music[key] = None
        self.objective = {'simple': '',
                          'win': '',
                          'loss': ''}

        self.units = Data()
        self.regions = Data()
        self.unit_groups = Data()

        # self.fog_of_war = 0  # Range units can default see in fog of war

    def save_attr(self, name, value):
        if name == 'units':
            value = [unit.save() for unit in value]
        elif name == 'unit_groups':
            value = [unit_group.save() for unit_group in value]
        elif name == 'regions':
            value = [region.save() for region in value]
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'units':
            value = Data([GenericUnit.restore(unit_data) if unit_data['generic'] 
                          else UniqueUnit.restore(unit_data) for unit_data in value])
        elif name == 'unit_groups':
            value = Data([UnitGroup.restore(val, self.units) for val in value])
        elif name == 'regions':
            value = Data([Region.restore(val) for val in value])
        else:
            value = super().restore_attr(name, value)
        return value

    @classmethod
    def default(cls):
        return cls('0', 'Prologue')

class LevelCatalog(Data):
    datatype = LevelPrefab
