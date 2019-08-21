import os

from app.data import terrain, mcost_grid, minimap

class Database(object):
    def __init__(self):
        self.level_list = []
        self.mcost = mcost_grid.McostGrid()
        self.terrain = terrain.TerrainManager()
        self.minimap = minimap.MinimapData()

        self.init_load()

    def init_load(self):
        self.mcost.import_data('./app/data/default_mcost.txt')
        self.terrain.import_xml('./app/data/default_terrain.xml')

    def get_platform_types(self):
        home = './sprites/platforms/'
        names = list({fn.split('-')[0] for fn in os.listdir(home)})
        sprites = [n + '-Melee' for n in names]
        return zip(names, sprites)

DB = Database()
