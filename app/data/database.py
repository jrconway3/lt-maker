import os

from app.data import terrain, mcost_grid, minimap, data

class Database(object):
    def __init__(self):
        self.levels = data.data()
        self.mcost = mcost_grid.McostGrid()
        self.terrain = terrain.TerrainManager()
        self.minimap = minimap.MinimapData()

        self.init_load()

    def init_load(self):
        self.level_list = []
        self.mcost.import_data('./app/data/default_mcost.txt')
        self.terrain.import_xml('./app/data/default_terrain.xml')
        self.minimap = minimap.MinimapData()

    def get_platform_types(self):
        home = './sprites/platforms/'
        names = list({fn.split('-')[0] for fn in os.listdir(home)})
        sprites = [n + '-Melee' for n in names]
        return zip(names, sprites)

    def restore(self, data):
        self.mcost = self.mcost.restore(data['mcost'])
        self.terrain = self.terrain.restore(data['terrain'])
        self.level_list = data['level_list']

    def save(self):
        to_save = {'mcost': self.mcost.serialize(),
                   'terrain': self.terrain.serialize(),
                   'level_list': self.level_list,
                   }
        return to_save

DB = Database()
