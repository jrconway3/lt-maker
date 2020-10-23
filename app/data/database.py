import os
import json

from app.data import constants, stats, equations, tags, weapons, factions, terrain, mcost, \
    minimap, items, klass, units, parties, ai, translations, skills, levels
from app.events import event_prefab

class Database(object):
    save_data_types = ("constants", "stats", "equations", "mcost", "terrain", "weapon_ranks",
                       "weapons", "factions", "items", "skills", "tags", "classes", 
                       "units", "ai", "parties", "translations", "levels", "events")

    def __init__(self):
        self.constants = constants.constants
        self.teams = ["player", "enemy", "enemy2", "other"]  # Order determine phase order
        self.stats = stats.StatCatalog()
        self.equations = equations.EquationCatalog()
        self.mcost = mcost.McostGrid()
        self.terrain = terrain.TerrainCatalog()
        self.minimap = minimap.MinimapCatalog()
        self.weapon_ranks = weapons.RankCatalog()
        self.weapons = weapons.WeaponCatalog()
        self.factions = factions.FactionCatalog()
        self.items = items.ItemCatalog()
        self.skills = skills.SkillCatalog()
        self.tags = tags.TagCatalog(['Lord', 'Boss', 'Armor', 'Horse', 'Mounted', 'Dragon', 'ZeroMove', 'AutoPromote', 'NoAutoPromote'])
        self.classes = klass.ClassCatalog()
        self.units = units.UnitCatalog()
        self.parties = parties.PartyCatalog()
        self.ai = ai.AICatalog()

        self.levels = levels.LevelCatalog()
        self.events = event_prefab.EventCatalog()

        self.translations = translations.TranslationCatalog()

    # === Saving and loading important data functions ===
    def restore(self, save_obj):
        for data_type in self.save_data_types:
            print("Database: Restoring %s..." % data_type)
            getattr(self, data_type).restore(save_obj[data_type])

    def save(self):
        to_save = {}
        for data_type in self.save_data_types:
            to_save[data_type] = getattr(self, data_type).save()
        return to_save

    def serialize(self, proj_dir):
        data_dir = os.path.join(proj_dir, 'game_data')
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        print("Serializing data in %s..." % data_dir)

        to_save = self.save()
        for key, value in to_save.items():
            save_loc = os.path.join(data_dir, key + '.json')
            print("Serializing %s to %s" % (key, save_loc))
            with open(save_loc, 'w') as serialize_file:
                json.dump(value, serialize_file, indent=4)

        print("Done serializing!")

    def load(self, proj_dir):
        data_dir = os.path.join(proj_dir, 'game_data')
        print("Deserializing data from %s..." % data_dir)

        save_obj = {}
        for key in self.save_data_types:
            save_loc = os.path.join(data_dir, key + '.json')
            if os.path.exists(save_loc):
                print("Deserializing %s from %s" % (key, save_loc))
                with open(save_loc) as load_file:
                    save_obj[key] = json.load(load_file)
            else:
                print("%s does not exist!" % save_loc)
                save_obj[key] = []

        self.restore(save_obj)
        print("Done deserializing!")

DB = Database()

# Testing
# Run "python -m app.data.database" from main directory
