from collections import OrderedDict

from app.data import terrain

class Database(object):
    def __init__(self):
        self.level_list = []
        self.mcost = OrderedDict()
        self.terrain = terrain.TerrainManager()

        self.init_load()

    def init_load(self):
        self.mcost = self.create_mcost_dict('./app/data/default_mcost.txt')
        self.terrain.import_xml('./app/data/default_terrain.xml')

    def create_mcost_dict(self, fn):
        mcost_dict = OrderedDict()
        with open(fn) as mcost_data:
            mcost_dict.column_headers = [l.strip() for l in mcost_data.readline().split('-')[1:]]
            for line in mcost_data.readlines()[1:]:
                s_line = line.strip().split()
                mcost_dict[s_line[0]] = [int(s) if s != '-' else 99 for s in s_line[1:]]
        return mcost_dict

DB = Database()
