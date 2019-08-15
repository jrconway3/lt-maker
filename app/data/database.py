from app.data import terrain

class Database(object):
    def __init__(self):
        self.level_list = []
        self.terrain = terrain.TerrainManager()

        self.init_load()

    def init_load(self):
        self.terrain.import_xml('./app/data/default_terrain.xml')

DB = Database()
