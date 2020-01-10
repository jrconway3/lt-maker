from collections import OrderedDict

from app.data import data
from app.data import tilemap

class Level(object):
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

class LevelCatalog(data):
    pass
