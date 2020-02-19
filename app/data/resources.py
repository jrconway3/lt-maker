import os, glob, shutil

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data import data
import app.utilities as utilities

class Resources(object):
    def __init__(self):
        self.main_folder = None

        # Modifiable Resources
        self.clear()

        # Standardized, Locked resources
        self.platforms = {}
        self.misc = {}
        
        self.init_load()

    def init_load(self):
        # Grab project resources
        # self.load()

        # Standard locked resources
        self.platforms = self.get_sprites("resources", 'platforms')
        self.misc = self.get_sprites("resources", 'misc')

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

    def set_up_portrait_coords(self, fn):
        loc = os.path.join(self.main_folder, fn)
        data = ET.parse(loc)
        portrait_dict = {}
        for portrait in data.getroot().findall('portrait'):
            portrait_dict[portrait.get('name')] = {'mouth': [int(coord) for coord in portrait.find('mouth').text.split(',')],
                                                   'blink': [int(coord) for coord in portrait.find('blink').text.split(',')]}
        for portrait in self.portraits:
            offsets = portrait_dict.get(portrait.nid)
            if offsets:
                portrait.blinking_offset = portrait_dict[portrait.nid]['blink']
                portrait.smiling_offset = portrait_dict[portrait.nid]['mouth']

    def populate_map_sprites(self, folder):
        for root, dirs, files in os.walk(os.path.join(self.main_folder, folder)):
            for name in files:
                if name.endswith('-stand.png'):
                    stand_full_path = os.path.join(root, name)
                    move_full_path = os.path.join(root, name[:-10] + '-move.png')
                    new_map_sprite = MapSprite(name[:-10], stand_full_path, move_full_path)
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

    def clear(self):
        self.icons16 = data.Data()
        self.icons32 = data.Data()
        self.icons80 = data.Data()
        self.portraits = data.Data()
        self.panoramas = data.Data()
        self.map_sprites = data.Data()
        self.combat_anims = data.Data()
        self.combat_effects = data.Data()
        self.map_effects = data.Data()
        self.music = data.Data()
        self.sfx = data.Data()

    def load(self, proj_dir='./default'):
        self.main_folder = os.path.join(proj_dir, 'resources')
        self.populate_database(self.icons16, 'icons/icons_16x16', '.png', ImageResource)
        self.populate_database(self.icons32, 'icons/icons_32x32', '.png', ImageResource)
        self.populate_database(self.icons80, 'icons/icons_80x72', '.png', ImageResource)
        self.populate_database(self.portraits, 'portraits', '.png', Portrait)
        self.set_up_portrait_coords('portraits/portrait_coords.xml')
        self.populate_map_sprites('map_sprites')
        self.populate_panoramas('panoramas')
        self.populate_database(self.music, 'music', '.ogg', Song)

    def reload(self):
        self.clear()
        self.load()

    def serialize(self, proj_dir='./default'):
        print("Starting Serialization...")

        def move_image(image, parent_dir):
            image_parent_dir = os.path.split(image.full_path)[0]
            if os.path.abspath(image_parent_dir) != os.path.abspath(parent_dir):
                new_full_path = os.path.join(parent_dir, image.nid + '.png')
                shutil.copy(image.full_path, new_full_path)
                image.set_full_path(new_full_path)

        def save_icons(icons_dir, new_icon_dirname, database):
            subicons_dir = os.path.join(icons_dir, new_icon_dirname)
            if not os.path.exists(subicons_dir):
                os.mkdir(subicons_dir)
            for icon in database:
                move_image(icon, subicons_dir)

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
        save_icons(icons_dir, 'icons_16x16', self.icons16)
        # Save Icons32
        save_icons(icons_dir, 'icons_32x32', self.icons32)
        # Save Icons80
        save_icons(icons_dir, 'icons_80x72', self.icons80)
        # Save Portraits
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
        # Save Panoramas
        panoramas_dir = os.path.join(resource_dir, 'panoramas')
        if not os.path.exists(panoramas_dir):
            os.mkdir(panoramas_dir)
        for panorama in self.panoramas:
            panorama_parent_dir = os.path.split(panorama.full_path)[0]
            if os.path.abspath(panorama_parent_dir) != os.path.abspath(panoramas_dir):
                new_full_path = os.path.join(panoramas_dir, panorama.nid)
                paths = panorama.get_all_paths()
                if len(paths) > 1:
                    for idx, path in enumerate(paths):
                        shutil.copy(path, new_full_path + str(idx) + '.png')
                else:
                    shutil.copy(paths[0], new_full_path + '.png')
                panorama.set_full_path(new_full_path)
        # Save Map Sprites
        map_sprites_dir = os.path.join(resource_dir, 'map_sprites')
        if not os.path.exists(map_sprites_dir):
            os.mkdir(map_sprites_dir)
        for map_sprite in self.map_sprites:
            # Standing sprite
            standing_parent_dir = os.path.split(map_sprite.standing_full_path)[0]
            if os.path.abspath(standing_parent_dir) != os.path.abspath(map_sprites_dir):
                new_full_path = os.path.join(map_sprites_dir, map_sprite.nid)
                shutil.copy(map_sprite.standing_full_path, new_full_path + '-stand.png')
            # Moving sprite
            moving_parent_dir = os.path.split(map_sprite.moving_full_path)[0]
            if os.path.abspath(moving_parent_dir) != os.path.abspath(map_sprites_dir):
                new_full_path = os.path.join(map_sprites_dir, map_sprite.nid)
                shutil.copy(map_sprite.moving_full_path, new_full_path + '-move.png')
                map_sprite.set_full_path(new_full_path)
        # Save Music
        music_dir = os.path.join(resource_dir, 'music')
        if not os.path.exists(music_dir):
            os.mkdir(music_dir)
        for music in self.music:
            music_parent_dir = os.path.split(music.full_path)[0]
            if os.path.abspath(music_parent_dir) != os.path.abspath(music_dir):
                new_full_path = os.path.join(music_dir, music.nid + '.ogg')
                shutil.copy(music.full_path, new_full_path)
                music.set_full_path(new_full_path)
        print('Done Serializing!')

    def create_new_16x16_icon(self, nid, pixmap):
        full_path = os.path.join(self.main_folder, 'icons/icons_16x16', nid)
        nid = nid[:-4]  # Get rid of .png ending
        new_icon = ImageResource(nid, full_path, pixmap)
        self.icons16.append(new_icon)
        return new_icon

    def create_new_32x32_icon(self, nid, pixmap):
        full_path = os.path.join(self.main_folder, 'icons/icons_32x32', nid)
        nid = nid[:-4]  # Get rid of .png ending
        new_icon = ImageResource(nid, full_path, pixmap)
        self.icons32.append(new_icon)
        return new_icon

    def create_new_80x72_icon(self, nid, pixmap):
        full_path = os.path.join(self.main_folder, 'icons_80x72', nid)
        nid = nid[:-4]  # Get rid of .png ending
        new_icon = ImageResource(nid, full_path, pixmap)
        self.icons80.append(new_icon)
        return new_icon

    def create_new_portrait(self, nid, pixmap):
        full_path = os.path.join(self.main_folder, 'portraits', nid)
        nid = nid[:-4]  # Get rid of .png ending
        new_portrait = Portrait(nid, full_path, pixmap)
        self.portraits.append(new_portrait)
        return new_portrait

    def create_new_map_sprite(self, nid, standing_pixmap, moving_pixmap):
        nid = nid[:-4]
        standing_full_path = os.path.join(self.main_folder, 'map_sprites', nid + '-stand.png')
        moving_full_path = os.path.join(self.main_folder, 'map_sprites', nid + '-move.png')
        new_map_sprite = MapSprite(nid, standing_full_path, moving_full_path, standing_pixmap, moving_pixmap)
        self.map_sprites.append(new_map_sprite)
        return new_map_sprite

    def create_new_panorama(self, nid, pixmaps, full_path):
        new_panorama = Panorama(nid, full_path, pixmaps)
        self.panoramas.append(new_panorama)
        return new_panorama

    def create_new_music(self, nid, full_path):
        new_music = Song(nid, full_path)
        self.music.append(new_music)
        return new_music

class ImageResource(object):
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap

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

class Portrait(object):
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap

        self.blinking_offset = [0, 0]
        self.smiling_offset = [0, 0]

    def set_full_path(self, full_path):
        self.full_path = full_path

class MapSprite(object):
    def __init__(self, nid, stand_full_path=None, move_full_path=None, standing_pixmap=None, moving_pixmap=None):
        self.nid = nid
        self.standing_full_path = stand_full_path
        self.moving_full_path = move_full_path
        self.standing_pixmap = standing_pixmap
        self.moving_pixmap = moving_pixmap

    def set_full_path(self, full_path):
        full_path = full_path[:-4]  # Remove png ending
        self.standing_full_path = full_path + '-stand.png'
        self.moving_full_path = full_path + '-move.png'

class Panorama(object):
    def __init__(self, nid, full_path=None, pixmaps=None, num_frames=0):
        self.nid = nid
        self.full_path = full_path  # Ignores numbers at the end
        self.num_frames = num_frames or len(pixmaps)
        self.pixmaps = pixmaps or []
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

    def increment_frame(self):
        if self.pixmaps:
            self.idx = (self.idx + 1) % len(self.pixmaps)  # Wrap around

class Song(object):
    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.full_path = full_path

    def set_full_path(self, full_path):
        self.full_path = full_path

RESOURCES = Resources()
