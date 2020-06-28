import os

from app.data import data
from app import sprites

from app.resources.fonts import FontCatalog
from app.resources.icons import IconCatalog
from app.resources.portraits import PortraitCatalog
from app.resources.animations import AnimationCatalog
from app.resources.panoramas import PanoramaCatalog
from app.resources.map_sprites import MapSpriteCatalog
from app.resources.tiles import TileSetCatalog, TileMapCatalog
from app.resources.sounds import SFXCatalog, MusicCatalog
from app.resources.combat_anims import CombatCatalog

class Resources():
    def __init__(self):
        self.main_folder = None

        # Modifiable Resources
        self.clear()

        # Standardized, Locked resources
        self.load_standard_resources()

    def load_standard_resources(self):
        self.platforms = self.get_sprites('resources', 'platforms')
        self.fonts = FontCatalog.load('resources', 'fonts')

    def get_sprites(self, home, sub):
        s = {}
        loc = os.path.join(home, sub)
        for root, dirs, files in os.walk(loc):
            for name in files:
                if name.endswith('.png'):
                    full_name = os.path.join(root, name)
                    s[name[:-4]] = full_name
        return s

    def clear(self):
        self.icons16 = IconCatalog()
        self.icons32 = IconCatalog()
        self.icons80 = IconCatalog()

        self.portraits = PortraitCatalog()
        self.animations = AnimationCatalog()

        self.panoramas = PanoramaCatalog()
        self.map_sprites = MapSpriteCatalog()
        self.combat_anims = CombatCatalog()
        self.combat_effects = data.Data()

        self.tilesets = TileSetCatalog()
        self.tilemaps = TileMapCatalog()

        self.music = MusicCatalog()
        self.sfx = SFXCatalog()

    def load(self, proj_dir):
        self.main_folder = os.path.join(proj_dir, 'resources')

        # Load custom sprites for the UI
        sprites.load_sprites(os.path.join(self.main_folder, 'custom_sprites'))

        self.icons16.load(os.path.join(self.main_folder, 'icons/icons_16x16'))
        self.icons32.load(os.path.join(self.main_folder, 'icons/icons_32x32'))
        self.icons80.load(os.path.join(self.main_folder, 'icons/icons_80x72'))

        self.portraits.load(os.path.join(self.main_folder, 'portraits'))
        self.animations.load(os.path.join(self.main_folder, 'animations'))
        self.map_sprites.load(os.path.join(self.main_folder, 'map_sprites'))
        self.panoramas.load(os.path.join(self.main_folder, 'panoramas'))

        self.tilesets.load(os.path.join(self.main_folder, 'tilesets'))
        self.tilemaps.load(os.path.join(self.main_folder, 'tilesets'))

        self.combat_anims.load(os.path.join(self.main_folder, 'combat_anims'))

        self.sfx.load(os.path.join(self.main_folder, 'sfx'))
        self.music.load(os.path.join(self.main_folder, 'music'))

    def reload(self, proj_dir):
        self.clear()
        self.load(proj_dir)

    def save(self, proj_dir):
        print("Starting Resource Serialization...")
        # Make the directory to save this resource pack in
        if not os.path.exists(proj_dir):
            os.mkdir(proj_dir)
        resource_dir = os.path.join(proj_dir, 'resources')
        if not os.path.exists(resource_dir):
            os.mkdir(resource_dir)

        # Save Icons
        icons_dir = os.path.join(resource_dir, 'icons')
        if not os.path.exists(icons_dir):
            os.mkdir(icons_dir)
        # Save Icons16
        subicons_dir = os.path.join(icons_dir, 'icons_16x16')
        if not os.path.exists(subicons_dir):
            os.mkdir(subicons_dir)
        self.icons16.save(subicons_dir)
        # Save Icons32
        subicons_dir = os.path.join(icons_dir, 'icons_32x32')
        if not os.path.exists(subicons_dir):
            os.mkdir(subicons_dir)
        self.icons32.save(subicons_dir)
        # Save Icons80
        subicons_dir = os.path.join(icons_dir, 'icons_80x72')
        if not os.path.exists(subicons_dir):
            os.mkdir(subicons_dir)
        self.icons80.save(subicons_dir)
        
        # Save Portraits
        portraits_dir = os.path.join(resource_dir, 'portraits')
        if not os.path.exists(portraits_dir):
            os.mkdir(portraits_dir)
        self.portraits.save(portraits_dir)
        
        # Save Panoramas
        panoramas_dir = os.path.join(resource_dir, 'panoramas')
        if not os.path.exists(panoramas_dir):
            os.mkdir(panoramas_dir)
        self.panoramas.save(panoramas_dir)

        # Save Map Sprites
        map_sprites_dir = os.path.join(resource_dir, 'map_sprites')
        if not os.path.exists(map_sprites_dir):
            os.mkdir(map_sprites_dir)
        self.map_sprites.save(map_sprites_dir)

        # Save Animations
        animation_dir = os.path.join(resource_dir, 'animations')
        if not os.path.exists(animation_dir):
            os.mkdir(animation_dir)
        self.animations.save(animation_dir)

        # Save TileSets & TileMaps 
        tileset_dir = os.path.join(resource_dir, 'tilesets')
        if not os.path.exists(tileset_dir):
            os.mkdir(tileset_dir)
        self.tilesets.save(tileset_dir)
        self.tilemaps.save(tileset_dir)

        # Save Combat Animations
        combat_anim_dir = os.path.join(resource_dir, 'combat_anims')
        if not os.path.exists(combat_anim_dir):
            os.mkdir(combat_anim_dir)
        self.combat_anims.save(combat_anim_dir)

        # === Save SFX ===
        sfx_dir = os.path.join(resource_dir, 'sfx')
        if not os.path.exists(sfx_dir):
            os.mkdir(sfx_dir)
        self.sfx.save(sfx_dir)

        # === Save Music ===
        music_dir = os.path.join(resource_dir, 'music')
        if not os.path.exists(music_dir):
            os.mkdir(music_dir)
        self.music.save(music_dir)

        print('Done Resource Serializing!')

RESOURCES = Resources()
