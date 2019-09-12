import os

from app.data import stats, terrain, mcost_grid, minimap, data

class Database(object):
    def __init__(self):
        self.levels = data.data()
        self.stats = stats.StatData()
        self.mcost = mcost_grid.McostGrid()
        self.terrain = terrain.TerrainManager()
        self.minimap = minimap.MinimapData()

        self.init_load()

    def init_load(self):
        self.stats.import_xml('./app/data/default_stats.xml')
        self.mcost.import_data('./app/data/default_mcost.txt')
        self.terrain.import_xml('./app/data/default_terrain.xml')

    def get_platform_types(self):
        home = './sprites/platforms/'
        names = list({fn.split('-')[0] for fn in os.listdir(home)})
        sprites = [n + '-Melee' for n in names]
        return zip(names, sprites)

    def restore(self, data):
        self.mcost.restore(data['mcost'])
        self.terrain.restore(data['terrain'])
        self.levels.restore(data['levels'])

    def save(self):
        to_save = {'mcost': self.mcost.serialize(),
                   'terrain': self.terrain.serialize(),
                   'levels': self.levels.serialize(),
                   }
        return to_save

DB = Database()
