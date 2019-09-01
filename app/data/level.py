from app.data import tilemap

class Level(object):
    def __init__(self, nid, title):
        self.nid = nid
        self.title = title
        self.tilemap = tilemap.TileMap.default()
        self.music = {'player_phase': None,
                      'enemy_phase': None,
                      'other_phase': None,
                      'player_battle': None,
                      'enemy_battle': None,
                      'other_battle': None,
                      'prep': None,
                      'base': None}
        self.market_flag = False
        self.objective = {'simple': '',
                          'win': '',
                          'loss': ''}
