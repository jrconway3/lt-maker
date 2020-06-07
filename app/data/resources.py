import os, glob, shutil

import xml.etree.ElementTree as ET
import json

from app.data import data
import app.utilities as utilities

from app.data.tilemap_prefab import TileSet, TileMapPrefab

class Resources():
    def __init__(self):
        self.main_folder = None

        # Modifiable Resources
        self.clear()

        # Standardized, Locked resources
        self.platforms = {}
        self.fonts = {}
        
        self.init_load()

    def init_load(self):
        # Grab project resources
        # self.load()

        # Standard locked resources
        self.platforms = self.get_sprites("resources", 'platforms')
        self.fonts = self.get_fonts("resources", 'fonts')

    def populate_database(self, d, folder, ftype, obj):
        for root, dirs, files in os.walk(os.path.join(self.main_folder, folder)):
            for name in files:
                if name.endswith(ftype):
                    full_path = os.path.join(root, name)
                    if ftype == '.png':
                        new_resource = obj(name[:-4], full_path)
                    elif ftype == '.ogg':
                        new_resource = obj(name[:-4], full_path)
                    d.append(new_resource)

    def populate_database_with_tags(self, d, folder, ftype, obj):
        base = os.path.join(self.main_folder, folder)
        temp_list = []
        for root, dirs, files in os.walk(base):
            tag = os.path.relpath(root, base)
            # print(tag, files, flush=True)
            for name in files:
                if name.endswith(ftype):
                    full_path = os.path.join(root, name)
                    if ftype == '.png':
                        new_resource = obj(name[:-4], full_path)
                    elif ftype == '.ogg':
                        new_resource = obj(name[:-4], full_path)
                    if tag != '.':
                        new_resource.tag = tag
                    temp_list.append(new_resource)
        temp_list = sorted(temp_list, key=lambda x: x.tag if x.tag else '____')
        for l in temp_list:
            d.append(l)

    def populate_music(self, d, folder, fn):
        loc = os.path.join(self.main_folder, fn)
        data = ET.parse(loc)
        music_dict = {}
        for music in data.getroot().findall('song'):
            music_dict[music.get('nid')] = {'full_path': music.find('full_path').text,
                                            'battle_path': music.find('battle_path').text,
                                            'intro_path': music.find('intro_path').text}
        for song_nid, paths in music_dict.items():
            new_song = Song(song_nid, os.path.join(self.main_folder, folder, paths['full_path']))
            if paths['battle_path']:
                new_song.set_battle_full_path(os.path.join(self.main_folder, folder, paths['battle_path']))
            if paths['intro_path']:
                new_song.set_intro_full_path(os.path.join(self.main_folder, folder, paths['intro_path']))
            d.append(new_song)

    def set_up_portrait_coords(self, fn):
        loc = os.path.join(self.main_folder, fn)
        if not os.path.exists(loc):
            return
        data = ET.parse(loc)
        portrait_dict = {}
        for portrait in data.getroot().findall('portrait'):
            portrait_dict[portrait.get('name')] = {'mouth': [int(coord) for coord in portrait.find('mouth').text.split(',')],
                                                   'blink': [int(coord) for coord in portrait.find('blink').text.split(',')]}
        for portrait in self.portraits:
            offsets = portrait_dict.get(portrait.nid)
            if offsets:
                portrait.blinking_offset = offsets['blink']
                portrait.smiling_offset = offsets['mouth']

    def set_up_animations(self, fn):
        loc = os.path.join(self.main_folder, fn)
        if not os.path.exists(loc):
            return
        data = ET.parse(loc)
        anim_dict = {}
        for anim in data.getroot().findall('animation'):
            anim_dict[anim.get('nid')] = {'frame_x': int(anim.find('frame_x').text),
                                          'frame_y': int(anim.find('frame_y').text),
                                          'num_frames': int(anim.find('num_frames').text),
                                          'speed': anim.find('speed').text}
        for anim in self.animations:
            stats = anim_dict.get(anim.nid)
            if stats:
                anim.frame_x = stats['frame_x']
                anim.frame_y = stats['frame_y']
                anim.num_frames = stats['num_frames']
                if utilities.is_int(stats['speed']):
                    anim.speed = int(stats['speed'])
                else:
                    anim.speed = [int(_) for _ in stats['speed'].split(',')]

    def create_map_sprite(self, folder, fn):
        save_loc = os.path.join(self.main_folder, folder, fn)
        print("Save Loc %s" % save_loc)
        map_sprite_dict = {}
        if os.path.exists(save_loc):
            print("Deserializing map sprites from %s" % save_loc)
            with open(save_loc) as load_file:
                map_sprite_dict = json.load(load_file)
        for s_dict in map_sprite_dict:
            new_map_sprite = MapSprite.deserialize(s_dict)
            for variant in new_map_sprite.variants:
                variant.set_standing_full_path(os.path.join(self.main_folder, folder, variant.standing_full_path))
                variant.set_moving_full_path(os.path.join(self.main_folder, folder, variant.moving_full_path))
            self.map_sprites.append(new_map_sprite)

    def populate_panoramas(self, folder):
        for root, dirs, files in os.walk(os.path.join(self.main_folder, folder)):
            for name in files:
                if name.endswith('.png'):
                    nid = name[:-4]
                    last_number = utilities.find_last_number(nid)
                    if last_number == 0:
                        movie_prefix = name[:-5]
                        full_path = os.path.join(root, movie_prefix + '.png')
                        num_frames = len(glob.glob(os.path.join(root, movie_prefix + '*' + '.png')))
                    elif last_number is None:
                        movie_prefix = nid
                        full_path = os.path.join(root, name)
                        num_frames = 1
                    else:
                        continue
                    new_panorama = Panorama(movie_prefix, full_path, num_frames=num_frames)
                    self.panoramas.append(new_panorama)

    def get_sprites(self, home, sub):
        s = {}
        for root, dirs, files in os.walk(os.path.join(home, sub)):
            for name in files:
                if name.endswith('.png'):
                    full_name = os.path.join(root, name)
                    s[name[:-4]] = full_name
        return s

    def get_fonts(self, home, sub):
        s = {}
        for root, dirs, files in os.walk(os.path.join(home, sub)):
            for name in files:
                if name.endswith('.png'):
                    full_name = os.path.join(root, name)
                    nid = name[:-4]
                    idx_name = nid.split('_')[0] + '.idx'
                    idx_full_name = os.path.join(root, idx_name)
                    s[name[:-4]] = Font(nid, full_name, idx_full_name)
        return s

    def create_tilesets(self, folder, fn):
        save_loc = os.path.join(self.main_folder, folder, fn)
        print("Save Loc %s" % save_loc)
        tileset_dict = {}
        if os.path.exists(save_loc):
            print("Deserializing tilesets from %s" % save_loc)
            with open(save_loc) as load_file:
                tileset_dict = json.load(load_file)
        for s_dict in tileset_dict:
            full_path = os.path.join(self.main_folder, folder, s_dict['nid'] + '.png')
            new_tileset = TileSet.deserialize(s_dict, full_path)
            self.tilesets.append(new_tileset)

    def create_tilemaps(self, folder, fn):
        save_loc = os.path.join(self.main_folder, folder, fn)
        tilemap_dict = {}
        if os.path.exists(save_loc):
            print("Deserializing tilemaps from %s" % save_loc)
            with open(save_loc) as load_file:
                tilemap_dict = json.load(load_file)
        for s_dict in tilemap_dict:
            new_tilemap = TileMapPrefab.deserialize(s_dict)
            self.tilemaps.append(new_tilemap)

    def clear(self):
        self.icons16 = data.Data()
        self.icons32 = data.Data()
        self.icons80 = data.Data()
        self.portraits = data.Data()
        self.panoramas = data.Data()
        self.map_sprites = data.Data()
        self.combat_anims = data.Data()
        self.combat_effects = data.Data()
        self.animations = data.Data()

        self.tilesets = data.Data()
        self.tilemaps = data.Data()

        self.music = data.Data()
        self.sfx = data.Data()

    def load(self, proj_dir):
        self.main_folder = os.path.join(proj_dir, 'resources')
        self.populate_database(self.icons16, 'icons/icons_16x16', '.png', ImageResource)
        self.populate_database(self.icons32, 'icons/icons_32x32', '.png', ImageResource)
        self.populate_database(self.icons80, 'icons/icons_80x72', '.png', ImageResource)
        self.populate_database(self.portraits, 'portraits', '.png', Portrait)
        self.set_up_portrait_coords('portraits/portrait_coords.xml')

        self.populate_database(self.animations, 'animations', '.png', Animation)
        self.set_up_animations('animations/animation_manifest.xml')

        self.create_map_sprites('map_sprites', 'map_sprites.json')
        self.populate_panoramas('panoramas')

        self.create_tilesets('tilesets', 'tilesets.json')
        self.create_tilemaps('tilesets', 'tilemaps.json')

        self.populate_database_with_tags(self.sfx, 'sfx', '.ogg', SFX)
        self.populate_music(self.music, 'music', 'music/music_manifest.xml')

    def reload(self, proj_dir):
        self.clear()
        self.load(proj_dir)

    def serialize(self, proj_dir):
        print("Starting Resource Serialization...")

        def move_image(image, parent_dir):
            new_full_path = os.path.join(parent_dir, image.nid + '.png')
            if os.path.abspath(image.full_path) != os.path.abspath(new_full_path):
                shutil.copy(image.full_path, new_full_path)
                image.set_full_path(new_full_path)

        def save_icons(icons_dir, new_icon_dirname, database):
            subicons_dir = os.path.join(icons_dir, new_icon_dirname)
            if not os.path.exists(subicons_dir):
                os.mkdir(subicons_dir)
            for icon in database:
                move_image(icon, subicons_dir)

        def delete_unused_icons(icons_dir, icon_dirname, database):
            subicons_dir = os.path.join(icons_dir, icon_dirname)
            nids = set(d.nid for d in database)
            for fn in os.listdir(subicons_dir):
                if not fn.endswith('.png') or fn[:-4] not in nids:
                    full_path = os.path.join(subicons_dir, fn)
                    print("Deleting %s" % full_path)
                    os.remove(full_path)

        def delete_unused_images(direc, database):
            nids = set(d.nid for d in database)
            for fn in os.listdir(direc):
                if fn.endswith('.png') and fn[:-4] not in nids:
                    full_path = os.path.join(direc, fn)
                    print("Deleting %s" % full_path)
                    os.remove(full_path)

        # Make the directory to save this resource pack in
        if not os.path.exists(proj_dir):
            os.mkdir(proj_dir)
        resource_dir = os.path.join(proj_dir, 'resources')
        if not os.path.exists(resource_dir):
            os.mkdir(resource_dir)

        # === Save Icons ===
        icons_dir = os.path.join(resource_dir, 'icons')
        if not os.path.exists(icons_dir):
            os.mkdir(icons_dir)
        # Save Icons16
        save_icons(icons_dir, 'icons_16x16', self.icons16)
        delete_unused_icons(icons_dir, 'icons_16x16', self.icons16)
        # Save Icons32
        save_icons(icons_dir, 'icons_32x32', self.icons32)
        delete_unused_icons(icons_dir, 'icons_32x32', self.icons32)
        # Save Icons80
        save_icons(icons_dir, 'icons_80x72', self.icons80)
        delete_unused_icons(icons_dir, 'icons_80x72', self.icons80)

        # === Save Portraits ===
        portraits_dir = os.path.join(resource_dir, 'portraits')
        if not os.path.exists(portraits_dir):
            os.mkdir(portraits_dir)
        # Also write the portrait coords to the correct file
        root = ET.Element('portrait_info')
        for portrait in self.portraits:
            move_image(portrait, portraits_dir)

            elem = ET.SubElement(root, 'portrait', {'name': portrait.nid})
            mouth = ET.SubElement(elem, 'mouth')
            mouth.text = ','.join([str(s) for s in portrait.smiling_offset])
            blink = ET.SubElement(elem, 'blink')
            blink.text = ','.join([str(s) for s in portrait.blinking_offset])

        tree = ET.ElementTree(root)
        tree.write(os.path.join(portraits_dir, 'portrait_coords.xml'))
        delete_unused_images(portraits_dir, self.portraits)

        # === Save Panoramas ===
        panoramas_dir = os.path.join(resource_dir, 'panoramas')
        if not os.path.exists(panoramas_dir):
            os.mkdir(panoramas_dir)
        for panorama in self.panoramas:
            new_full_path = os.path.join(panoramas_dir, panorama.nid + '.png')
            if os.path.abspath(panorama.full_path) != os.path.abspath(new_full_path):
                paths = panorama.get_all_paths()
                if len(paths) > 1:
                    for idx, path in enumerate(paths):
                        shutil.copy(path, new_full_path + str(idx) + '.png')
                else:
                    shutil.copy(paths[0], new_full_path + '.png')
                panorama.set_full_path(new_full_path)
        # Deleting unused panoramas
        nids = set(d.nid for d in self.panoramas)
        for fn in os.listdir(panoramas_dir):
            if fn.endswith('.png') and utilities.get_prefix(fn) not in nids:
                full_path = os.path.join(panoramas_dir, fn)
                print("Deleting %s" % full_path)
                os.remove(full_path)

        # === Save Map Sprites ===
        map_sprites_dir = os.path.join(resource_dir, 'map_sprites')
        if not os.path.exists(map_sprites_dir):
            os.mkdir(map_sprites_dir)

        for map_sprite in self.map_sprites:
            for variant in map_sprite.variants:
                # Standing sprite
                new_full_path = os.path.join(map_sprites_dir, map_sprite.nid + '-' + variant.nid + '-stand.png')
                if os.path.abspath(variant.standing_full_path) != os.path.abspath(new_full_path):
                    shutil.copy(variant.standing_full_path, new_full_path)
                    variant.set_standing_full_path(new_full_path)
                # Moving sprite
                new_full_path = os.path.join(map_sprites_dir, map_sprite.nid + '-' + variant.nid + '-move.png')
                if os.path.abspath(variant.moving_full_path) != os.path.abspath(new_full_path):
                    shutil.copy(variant.moving_full_path, new_full_path)
                    variant.set_moving_full_path(new_full_path)

        map_sprite_save = [m.serialize() for m in self.map_sprites]
        save_loc = os.path.join(map_sprites_dir, 'map_sprites.json')
        print("Serializing map sprites to %s" % save_loc)
        with open(save_loc, 'w') as serialize_file:
            json.dump(map_sprite_save, serialize_file, indent=4) 

        # Deleting unused map sprites
        all_paths = set()
        for map_sprite in self.map_sprites:
            all_paths |= map_sprite.get_all_paths()
        for fn in os.listdir(map_sprites_dir):
            if fn.endswith('.png') and fn not in all_paths:
                print("Deleting %s" % fn)
                os.remove(fn)

        # === Save Animations ===
        animation_dir = os.path.join(resource_dir, 'animations')
        if not os.path.exists(animation_dir):
            os.mkdir(animation_dir)
        root = ET.Element('animation_info')
        for anim in self.animations:
            new_full_path = os.path.join(animation_dir, anim.nid + '.png')
            if os.path.abspath(anim.full_path) != os.path.abspath(new_full_path):
                shutil.copy(anim.full_path, new_full_path)
                anim.set_full_path(new_full_path)
            elem = ET.SubElement(root, 'animation', {'nid': anim.nid})
            full_path = ET.SubElement(elem, 'full_path')
            full_path.text = os.path.split(new_full_path)[-1]
            frame_x = ET.SubElement(elem, 'frame_x')
            frame_x.text = str(anim.frame_x)
            frame_y = ET.SubElement(elem, 'frame_y')
            frame_y.text = str(anim.frame_y)
            num_frames = ET.SubElement(elem, 'num_frames')
            num_frames.text = str(anim.num_frames)
            speed = ET.SubElement(elem, 'speed')
            if utilities.is_int(anim.speed):
                speed.text = str(anim.speed)
            else:
                speed.text = ','.join([str(_) for _ in anim.speed])
        tree = ET.ElementTree(root)
        tree.write(os.path.join(animation_dir, 'animation_manifest.xml'))
        delete_unused_images(animation_dir, self.animations)

        # === Save TileSets & TileMaps === 
        tileset_dir = os.path.join(resource_dir, 'tilesets')
        if not os.path.exists(tileset_dir):
            os.mkdir(tileset_dir)
        for tileset in self.tilesets:
            move_image(tileset, tileset_dir)
        delete_unused_images(tileset_dir, self.tilesets)

        # Also save terrain information
        tileset_save = [t.serialize() for t in self.tilesets]
        save_loc = os.path.join(tileset_dir, 'tilesets.json')
        print("Serializing tilesets to %s" % save_loc)
        with open(save_loc, 'w') as serialize_file:
            json.dump(tileset_save, serialize_file, indent=4)

        # Also save tilemap information
        tilemap_save = [t.serialize() for t in self.tilemaps]
        save_loc = os.path.join(tileset_dir, 'tilemaps.json')
        print("Serializing tilemaps to %s" % save_loc)
        with open(save_loc, 'w') as serialize_file:
            json.dump(tilemap_save, serialize_file, indent=4)

        # === Save SFX ===
        sfx_dir = os.path.join(resource_dir, 'sfx')
        if not os.path.exists(sfx_dir):
            os.mkdir(sfx_dir)
        for sfx in self.sfx:
            if sfx.tag:
                if not os.path.exists(os.path.join(sfx_dir, sfx.tag)):
                    os.mkdir(os.path.join(sfx_dir, sfx.tag))
                new_full_path = os.path.join(sfx_dir, sfx.tag, sfx.nid + '.ogg')
            else:
                new_full_path = os.path.join(sfx_dir, sfx.nid + '.ogg')
            if os.path.abspath(sfx.full_path) != os.path.abspath(new_full_path):
                shutil.copy(sfx.full_path, new_full_path)
                sfx.set_full_path(new_full_path)
        # Delete unused sfx
        full_paths = {sfx.full_path for sfx in self.sfx}
        for root, dirs, files in os.walk(sfx_dir, topdown=False):
            for name in files:
                fn = os.path.join(root, name)
                if not fn.endswith('.ogg') or fn not in full_paths:
                    full_path = os.path.join(root, fn)
                    print("Deleting %s" % full_path)
                    os.remove(full_path)

        # === Save Music ===
        music_dir = os.path.join(resource_dir, 'music')
        if not os.path.exists(music_dir):
            os.mkdir(music_dir)
        root = ET.Element('music_info')
        for music in self.music:
            # Handle regular music
            new_full_path = os.path.join(music_dir, music.nid + '.ogg')
            if os.path.abspath(music.full_path) != os.path.abspath(new_full_path):
                shutil.copy(music.full_path, new_full_path)
                music.set_full_path(new_full_path)
            elem = ET.SubElement(root, 'song', {'nid': music.nid})
            full_path = ET.SubElement(elem, 'full_path')
            full_path.text = os.path.split(new_full_path)[-1]
            # Handle battle variant
            if music.battle_full_path:
                battle_full_path = os.path.join(music_dir, os.path.split(music.battle_full_path)[-1])
                if os.path.abspath(music.battle_full_path) != os.path.abspath(battle_full_path):
                    shutil.copy(music.battle_full_path, battle_full_path)
                    music.set_battle_full_path(battle_full_path)
                battle_path = ET.SubElement(elem, 'battle_path')
                battle_path.text = os.path.split(battle_full_path)[-1]
            else:
                battle_path = ET.SubElement(elem, 'battle_path')
                battle_path.text = ''
            # Handle intro section
            if music.intro_full_path:
                intro_full_path = os.path.join(music_dir, os.path.split(music.intro_full_path)[-1])
                if os.path.abspath(music.intro_full_path) != os.path.abspath(intro_full_path):
                    shutil.copy(music.intro_full_path, intro_full_path)
                    music.set_intro_full_path(intro_full_path)
                intro_path = ET.SubElement(elem, 'intro_path')
                intro_path.text = os.path.split(intro_full_path)[-1]
            else:
                intro_path = ET.SubElement(elem, 'intro_path')
                intro_path.text = ''
        tree = ET.ElementTree(root)
        tree.write(os.path.join(music_dir, 'music_manifest.xml'))
        # Delete unused music -- no need with music manifest in future
        # Because this takes a LOT of time
        # full_paths = {os.path.split(m.full_path)[-1] for m in self.music} | \
        #              {os.path.split(m.battle_path)[-1] for m in self.music if m.battle_full_path} | \
        #              {os.path.split(m.intro_full_path)[-1] for m in self.music if m.intro_full_path}
        # for fn in os.listdir(music_dir):
        #     if not (fn.endswith('.ogg') or fn.endswith('.xml')) or fn not in full_paths:
        #         full_path = os.path.join(music_dir, fn)
        #         print("Deleting %s" % full_path)
        #         os.remove(full_path)

        print('Done Resource Serializing!')

    def create_new_16x16_icon(self, nid, full_path, pixmap):
        # full_path = os.path.join(self.main_folder, 'icons/icons_16x16', nid)
        new_icon = ImageResource(nid, full_path, pixmap)
        self.icons16.append(new_icon)
        return new_icon

    def create_new_32x32_icon(self, nid, full_path, pixmap):
        # full_path = os.path.join(self.main_folder, 'icons/icons_32x32', nid)
        new_icon = ImageResource(nid, full_path, pixmap)
        self.icons32.append(new_icon)
        return new_icon

    def create_new_80x72_icon(self, nid, full_path, pixmap):
        # full_path = os.path.join(self.main_folder, 'icons_80x72', nid)
        new_icon = ImageResource(nid, full_path, pixmap)
        self.icons80.append(new_icon)
        return new_icon

    def create_new_portrait(self, nid, full_path, pixmap):
        new_portrait = Portrait(nid, full_path, pixmap)
        self.portraits.append(new_portrait)
        return new_portrait

    def create_new_map_sprite(self, nid):
        new_map_sprite = MapSprite(nid)
        self.map_sprites.append(new_map_sprite)
        return new_map_sprite

    def create_new_map_sprite_variant(self, map_sprite, nid, standing_full_path, moving_full_path, standing_pixmap, moving_pixmap):
        new_variant = MapSpriteVariant(nid, standing_full_path, moving_full_path, standing_pixmap, moving_pixmap)
        map_sprite.variants.append(new_variant)
        return new_variant

    def create_new_panorama(self, nid, full_path, pixmaps):
        new_panorama = Panorama(nid, full_path, pixmaps)
        self.panoramas.append(new_panorama)
        return new_panorama

    def create_new_map(self, nid, full_path, pixmap):
        new_map = ImageResource(nid, full_path, pixmap)
        self.maps.append(new_map)
        return new_map

    def create_new_music(self, nid, full_path):
        new_music = Song(nid, full_path)
        self.music.append(new_music)
        return new_music

    def create_new_sfx(self, nid, full_path):
        new_sfx = SFX(nid, full_path)
        self.sfx.append(new_sfx)
        return new_sfx

    def create_new_animation(self, nid, full_path, pixmap):
        new_animation = Animation(nid, full_path, pixmap)
        self.animations.append(new_animation)
        return new_animation

    def create_new_tileset(self, nid, full_path, pixmap):
        new_tileset = TileSet(nid, full_path)
        new_tileset.set_pixmap(pixmap)
        self.tilesets.append(new_tileset)
        return new_tileset

class ImageResource():
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap
        self.image = None

        self.sub_images = []
        self.parent_image = None
        self.icon_index = (0, 0)

    def set_full_path(self, full_path):
        self.full_path = full_path

    def unhook(self):
        if self.parent_image:
            self.parent_image.sub_images.remove(self)
            self.parent_image = None
        self.sub_images = []

class Portrait():
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap
        self.image = None

        self.blinking_offset = [0, 0]
        self.smiling_offset = [0, 0]

    def set_full_path(self, full_path):
        self.full_path = full_path

class Animation():
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap
        self.sprite = None

        self.frame_x, self.frame_y = 1, 1
        self.num_frames = 1
        self.speed = 75

    def set_full_path(self, full_path):
        self.full_path = full_path

class MapSprite():
    def __init__(self, nid):
        self.nid = nid
        self.variants = data.Data()

class MapSpriteVariant():
    def __init__(self, nid, stand_full_path=None, move_full_path=None, standing_pixmap=None, moving_pixmap=None):
        self.nid = nid
        self.standing_full_path = stand_full_path
        self.moving_full_path = move_full_path
        self.standing_pixmap = standing_pixmap
        self.moving_pixmap = moving_pixmap
        self.standing_image = None
        self.moving_image = None

    def set_standing_full_path(self, full_path):
        self.standing_full_path = full_path

    def set_moving_full_path(self, full_path):
        self.moving_full_path = full_path

class Panorama():
    def __init__(self, nid, full_path=None, pixmaps=None, num_frames=0):
        self.nid = nid
        self.full_path = full_path  # Ignores numbers at the end
        self.num_frames = num_frames or len(pixmaps)
        self.pixmaps = pixmaps or []
        self.images = []
        self.idx = 0

    def set_full_path(self, full_path):
        self.full_path = full_path

    def get_all_paths(self):
        paths = []
        if self.num_frames == 1:
            paths.append(self.full_path)
        else:
            for idx in range(self.num_frames):
                path = self.full_path[:-4] + str(idx) + '.png'
                paths.append(path)
        return paths

    def get_frame(self):
        if self.pixmaps:
            return self.pixmaps[self.idx]

    def get_img_frame(self):
        if self.images:
            return self.images[self.idx]

    def increment_frame(self):
        if self.pixmaps:
            self.idx = (self.idx + 1) % len(self.pixmaps)  # Wrap around
        elif self.images:
            self.idx = (self.idx + 1) % len(self.images)  # Wrap around

class Song():
    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.full_path = full_path

        # Mutually exclusive. Can't have both start and battle versions
        self.intro_full_path = None
        self.battle_full_path = None

    def set_full_path(self, full_path):
        self.full_path = full_path

    def set_intro_full_path(self, full_path):
        self.intro_full_path = full_path

    def set_battle_full_path(self, full_path):
        self.battle_full_path = full_path

class SFX():
    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.tag = None
        self.full_path = full_path

    def set_full_path(self, full_path):
        self.full_path = full_path

class Font():
    def __init__(self, nid, png_path, idx_path):
        self.nid = nid
        self.png_path = png_path
        self.idx_path = idx_path

RESOURCES = Resources()
