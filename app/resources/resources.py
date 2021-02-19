import os

from app import sprites

from app.resources.fonts import FontCatalog
from app.resources.icons import IconCatalog
from app.resources.portraits import PortraitCatalog
from app.resources.animations import AnimationCatalog
from app.resources.panoramas import PanoramaCatalog
from app.resources.map_sprites import MapSpriteCatalog
from app.resources.tiles import TileSetCatalog, TileMapCatalog
from app.resources.sounds import SFXCatalog, MusicCatalog
from app.resources.combat_anims import CombatCatalog, CombatEffectCatalog

import logging

class Resources():
    save_data_types = ("icons16", "icons32", "icons80", "portraits", "animations", "panoramas",
                       "map_sprites", "combat_anims", "combat_effects", "music", "sfx", 
                       "tilesets", "tilemaps")

    def __init__(self):
        self.main_folder = None

        # Modifiable Resources
        self.clear()

        # Standardized, Locked resources
        self.load_standard_resources()

    def load_standard_resources(self):
        self.platforms = self.get_sprites('resources', 'platforms')
        self.fonts = FontCatalog()
        self.fonts.load('resources/fonts')

    def get_sprites(self, home, sub):
        s = {}
        loc = os.path.join(home, sub)
        for root, dirs, files in os.walk(loc):
            for name in files:
                if name.endswith('.png'):
                    full_name = os.path.join(root, name)
                    s[name[:-4]] = full_name
        return s

    def get_platform_types(self):
        names = list(sorted({fn.split('-')[0] for fn in self.platforms.keys()}))
        sprites = [n + '-Melee' for n in names]
        return list(zip(names, sprites))

    def clear(self):
        self.icons16 = IconCatalog()
        self.icons32 = IconCatalog()
        self.icons80 = IconCatalog()

        self.portraits = PortraitCatalog()
        self.animations = AnimationCatalog()

        self.panoramas = PanoramaCatalog()
        self.map_sprites = MapSpriteCatalog()
        self.combat_anims = CombatCatalog()
        self.combat_effects = CombatEffectCatalog()

        self.tilesets = TileSetCatalog()
        self.tilemaps = TileMapCatalog()

        self.music = MusicCatalog()
        self.sfx = SFXCatalog()

    def load(self, proj_dir, specific=None):
        self.main_folder = os.path.join(proj_dir, 'resources')

        # Load custom sprites for the UI
        # This should overwrite the regular sprites in the "/sprites" folder
        sprites.load_sprites(os.path.join(self.main_folder, 'custom_sprites'))

        if specific:
            save_data_types = specific
        else:
            save_data_types = self.save_data_types
        for data_type in save_data_types:
            logging.info("Loading %s from %s..." % (data_type, self.main_folder))
            getattr(self, data_type).clear()  # Now always clears first
            getattr(self, data_type).load(os.path.join(self.main_folder, data_type))

    def save(self, proj_dir, specific=None):
        logging.info("Starting Resource Serialization...")
        import time
        start = time.time_ns()/1e6
        # Make the directory to save this resource pack in
        if not os.path.exists(proj_dir):
            os.mkdir(proj_dir)
        resource_dir = os.path.join(proj_dir, 'resources')
        if not os.path.exists(resource_dir):
            os.mkdir(resource_dir)

        if specific:
            save_data_types = specific
        else:
            save_data_types = self.save_data_types
        for data_type in save_data_types:
            data_dir = os.path.join(resource_dir, data_type)
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)
            getattr(self, data_type).save(data_dir)

        end = time.time_ns()/1e6
        logging.info("Total Time Taken for Resources: %s ms" % (end - start))
        logging.info('Done Resource Serializing!')

RESOURCES = Resources()

# Testing
# Run "python -m app.resources.resources" from main directory
