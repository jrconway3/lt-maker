import os

from app.data import data
from app.data import stats, equations, weapons, factions, terrain, mcost_grid, \
    minimap, items, klass, units, ai

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
        self.tags = []
        self.classes = klass.ClassCatalog()
        self.units = units.UnitCatalog()
        self.ai = ai.AICatalog()

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
        self.tags = ['Lord', 'Boss', 'Armor', 'Horse', 'Mounted', 'Dragon']
        self.classes.import_xml('./app/default_data/default_classes.xml', self.stats, self.weapons, self.weapon_ranks)
        self.units.import_xml('./app/default_data/default_units.xml', self.stats, self.weapons, self.weapon_ranks, self.items)
        self.ai.import_data('./app/default_data/default_ai.txt')

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
        self.tags = data['tags']
        self.classes.restore(data['classes'])
        self.units.restore(data['units'])
        self.ai.restore(data['ai'])

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
                   'tags': self.tags,  # Just a list
                   'classes': self.classes.serialize(),
                   'units': self.units.serialize(),
                   'ai': self.ai.serialize(),
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

    def create_new_class(self, nid, name):
        num_stats = len(self.stats)
        bases = [10] + [0] * (num_stats - 2) + [5]
        growths = [0] * num_stats
        promotion = [0] * num_stats
        max_stats = [30] * num_stats
        wexp_gain = [0] * len(self.weapon_ranks)
        new_class = klass.Klass(nid, name, name, '', 1, 0, None, [], [], 20, 
                                bases, growths, promotion, max_stats, [], wexp_gain)
        return new_class

    def create_new_unit(self, nid, name):
        num_stats = len(self.stats)
        bases = [10] + [0] * (num_stats - 2) + [5]
        growths = [0] * num_stats
        wexp_gain = [0] * len(self.weapon_ranks)
        new_unit = units.Unit(nid, name, '', 0, 1, 'Citizen', [], bases, growths, [], [], wexp_gain)
        return new_unit

    def create_new_ai(self, nid, name=None):
        new_ai = ai.AIPreset(nid, 20)
        return new_ai

DB = Database()

# Testing
# Run "python -m app.data.database" from main directory
