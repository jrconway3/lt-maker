from collections import OrderedDict

from app.utilities.data import Data, Prefab
from app.data.level_units import UniqueUnit, GenericUnit

class LevelPrefab(Prefab):
    def __init__(self, nid, name):
        self.nid = nid
        self.name = name
        self.tilemap = None  # Tilemap Nid
        self.party = None  # Party Prefab Nid
        self.music = OrderedDict()
        music_keys = ['player_phase', 'enemy_phase', 'other_phase',
                      'player_battle', 'enemy_battle', 'other_battle',
                      'prep', 'base']
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
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'units':
            value = Data([GenericUnit.restore(unit_data) if unit_data['generic'] 
                          else UniqueUnit.restore(unit_data) for unit_data in value])
        else:
            value = super().restore_attr(name, value)
        return value

    @classmethod
    def default(cls):
        return cls('0', 'Prologue')

class LevelCatalog(Data):
    datatype = LevelPrefab
