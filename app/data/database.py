import os, shutil

try:
    import cPickle as pickle
except ImportError:
    import pickle

import json

from app.data import stats, equations, weapons, factions, terrain, mcost_grid, \
    minimap, items, klass, units, ai, levels

from app.data.resources import RESOURCES

class Database(object):
    def __init__(self):
        self.levels = levels.LevelCatalog()
        self.teams = ["player", "enemy", "other", "enemy2"]
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

        # self.init_load()
        # self.deserialize()

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
        p = RESOURCES.platforms
        names = list({fn.split('-')[0] for fn in p.keys()})
        sprites = [n + '-Melee' for n in names]
        return list(zip(names, sprites))

    # === Saving and loading important data functions ===
    def restore(self, data):
        # print(data['stats'])
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
        to_save = {'stats': self.stats.save(),
                   'equations': self.equations.save(),
                   'mcost': self.mcost.save(),
                   'terrain': self.terrain.save(),
                   'weapon_ranks': self.weapon_ranks.save(),
                   'weapons': self.weapons.save(),
                   'factions': self.factions.save(),
                   'items': self.items.save(),
                   'tags': self.tags,  # Just a list
                   'classes': self.classes.save(),
                   'units': self.units.save(),
                   'ai': self.ai.save(),
                   'levels': self.levels.save(),
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
        new_item = items.Item(nid, name, "", "1", "1", 0)
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

    def serialize(self, proj_dir='./default', title="default"):
        save_loc = os.path.join(proj_dir, title + ".ltdata")
        print("Serializing data as %s..." % save_loc)

        # Place level image maps in correct place
        # This is how it works for now -- maybe in the future 
        # I will incorporate maps as a resource so it works the same
        # as other resources -- but we need to see how layering and tilemaps
        # will work before I decide
        for idx, level in enumerate(self.levels):
            if level.tilemap.base_image:
                map_dir = os.path.join(proj_dir, 'maps')
                if not os.path.exists(map_dir):
                    os.mkdir(map_dir)
                new_loc = os.path.join(map_dir, 'map%d.png' % idx)
                if os.path.abspath(level.tilemap.base_image) != os.path.abspath(new_loc):
                    shutil.copy(level.tilemap.base_image, new_loc)
                    level.tilemap.base_image = new_loc

        to_save = self.save()

        with open(save_loc, 'w') as serialize_file:
            # Remove the -1 here if you want to interrogate the pickled save file
            # pickle.dump(to_save, serialize_file, -1)
            # pickle.dump(to_save, serialize_file)
            json.dump(to_save, serialize_file)

        print("Done serializing!")

    def deserialize(self, proj_dir='./default', title="default"):
        save_loc = os.path.join(proj_dir, title + ".ltdata")
        print("Deserializing data as %s..." % save_loc)

        with open(save_loc, 'rb') as load_file:
            save_obj = pickle.load(load_file)

        self.restore(save_obj)
        print("Done deserializing!")

DB = Database()

# Testing
# Run "python -m app.data.database" from main directory
