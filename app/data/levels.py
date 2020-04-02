from collections import OrderedDict

from app.data.data import Data, Prefab
from app.data import tilemap
from app.data.units import UniqueUnit, GenericUnit

class Level(Prefab):
    def __init__(self, nid, title):
        self.nid = nid
        self.title = title
        self.tilemap = tilemap.TileMap.default()
        self.music = OrderedDict()
        music_keys = ['player_phase', 'enemy_phase', 'other_phase',
                      'player_battle', 'enemy_battle', 'other_battle',
                      'prep', 'base']
        for key in music_keys:
            self.music[key] = None
        self.market_flag = False
        self.objective = {'simple': '',
                          'win': '',
                          'loss': ''}

        self.units = Data()

    def check_position(self, pos):
        for unit in self.units:
            if unit.starting_position == pos:
                return unit
        return None

    def serialize_attr(self, name, value):
        if name == 'tilemap':
            value = value.serialize()
        elif name == 'units':
            value = [unit.serialize() for unit in value]
        else:
            value = super().serialize_attr(name, value)
        return value

    def deserialize_attr(self, name, value):
        if name == 'tilemap':
            value = tilemap.TileMap.deserialize(value)
        elif name == 'units':
            value = Data([GenericUnit.deserialize(unit_data) if unit_data['generic'] 
                          else UniqueUnit.deserialize(unit_data) for unit_data in value])
        else:
            value = super().deserialize_attr(name, value)
        return value

    @classmethod
    def default(cls):
        return cls('0', 'Prologue')

class LevelCatalog(Data):
    datatype = Level
    
    def save(self):
        return [level.serialize() for level in self._list]

    def restore(self, serialized_data):
        self.clear()
        for s_dict in serialized_data:
            new_level = Level.deserialize(s_dict)
            self.append(new_level)
