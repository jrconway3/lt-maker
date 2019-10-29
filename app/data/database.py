import os

from app.data import data
from app.data import stats, equations, weapons, factions, terrain, mcost_grid, minimap, items 

class Database(object):
    def __init__(self):
        self.levels = data.data()
        self.stats = stats.StatCatalog()
        self.equations = equations.EquationCatalog()
        self.mcost = mcost_grid.McostGrid()
        self.terrain = terrain.TerrainCatalog()
        self.minimap = minimap.MinimapCatalog()
        self.weapon_ranks = weapons.RankCatalog()
        self.weapons = weapons.WeaponCatalog()
        self.factions = factions.FactionCatalog()
        self.items = items.ItemCatalog()

        self.init_load()

    def init_load(self):
        self.stats.import_xml('./app/default_data/default_stats.xml')
        self.equations.import_data('./app/default_data/default_equations.txt')
        self.mcost.import_data('./app/default_data/default_mcost.txt')
        self.terrain.import_xml('./app/default_data/default_terrain.xml')
        self.weapon_ranks.import_data('./app/default_data/default_weapon_ranks.txt')
        self.weapons.import_xml('./app/default_data/default_weapons.xml')
        self.factions.import_xml('./app/default_data/default_factions.xml')
        self.items.import_xml('./app/default_data/default_items.xml')

    def get_platform_types(self):
        home = './sprites/platforms/'
        names = list({fn.split('-')[0] for fn in os.listdir(home)})
        sprites = [n + '-Melee' for n in names]
        return list(zip(names, sprites))

    # === Serialization function ===
    def restore(self, data):
        self.stats.restore(data['stats'])
        self.equations.restore(data['equations'])
        self.mcost.restore(data['mcost'])
        self.terrain.restore(data['terrain'])
        self.weapon_ranks.restore(data['weapon_ranks'])
        self.weapons.restore(data['weapons'])
        self.factions.restore(data['factions'])
        self.items.restore(data['items'])

        self.levels.restore(data['levels'])

    def save(self):
        to_save = {'stats': self.stats.serialize(),
                   'equations': self.equations.serialize(),
                   'mcost': self.mcost.serialize(),
                   'terrain': self.terrain.serialize(),
                   'weapon_ranks': self.weapon_ranks.serialize(),
                   'weapons': self.weapons.serialize(),
                   'factions': self.factions.serialize(),
                   'items': self.items.serialize(),
                   'levels': self.levels.serialize(),
                   }
        return to_save

    # === Creation functions ===
    def create_new_terrain(self, nid, name):
        new_terrain = terrain.Terrain(nid, name, (0, 0, 0), 'Grass', self.get_platform_types()[0][0], self.mcost.row_headers[0])
        self.terrain.append(new_terrain)

    def create_new_weapon_type(self, nid, name):
        new_weapon_type = weapons.WeaponType(nid, name, False, [], [])
        self.weapons.append(new_weapon_type)

    def create_new_faction(self, nid, name):
        new_faction_type = factions.Faction(nid, name, "")
        self.factions.append(new_faction_type)

    def create_new_item(self, nid, name):
        new_item = items.Item(nid, name, "", 1, 1, 0)
        self.items.append(new_item)

DB = Database()

# Testing
# Run "python -m app.data.database" from main directory
