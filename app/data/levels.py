from collections import OrderedDict

from app.data.data import data, serial_obj
from app.data import tilemap
from app.data.units import UnitPrefab

class Level(serial_obj):
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

        self.units = []

    def check_position(self, pos):
        for unit in self.units:
            if unit.position == pos:
                return unit
        return None

    def serialize_attr(self, name, value):
        if name == 'tilemap':
            value = value
        elif name == 'units':
            value = [unit_prefab.serialize() for unit_prefab in value]
        else:
            value = super().serialize_attr(name, value)
        return value

    def deserialize_attr(self, name, value):
        if name == 'tilemap':
            value = value
        elif name == 'units':
            value = [UnitPrefab.deserialize(unit_data) for unit_data in value]
        else:
            value = super().deserialize_attr(name, value)
        return value

class LevelCatalog(data):
    def save(self):
        return [level.serialize() for level in self._list]

    def restore(self, serialized_data):
        self.clear()
        for s_dict in serialized_data:
            new_level = Level.deserialize(s_dict)
            self.append(new_level)
