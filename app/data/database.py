from app.data import terrain, mcost_grid

class Database(object):
    def __init__(self):
        self.level_list = []
        self.mcost = mcost_grid.McostGrid()
        self.terrain = terrain.TerrainManager()

        self.init_load()

    def init_load(self):
        self.mcost.import_data('./app/data/default_mcost.txt')
        self.terrain.import_xml('./app/data/default_terrain.xml')

DB = Database()
