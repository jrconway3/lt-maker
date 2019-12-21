import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data import data

class Resources(object):
    def __init__(self):
        self.main_folder = 'resources'

        # Modifiable Resources
        self.icons16 = data.data()
        self.icons32 = data.data()
        self.icons80 = data.data()
        self.portraits = data.data()
        self.panoramas = data.data()
        self.map_sprites = data.data()
        self.combat_anims = data.data()
        self.combat_effects = data.data()
        self.map_effects = data.data()
        self.music = data.data()
        self.sfx = data.data()

        # Standardized, Locked resources
        self.platforms = {}
        self.misc = {}
        
        self.init_load()

    def init_load(self):
        self.populate_database(self.icons16, 'icons/icons_16x16', '.png', ImageResource)
        self.populate_database(self.icons32, 'icons/icons_32x32', '.png', ImageResource)
        self.populate_database(self.icons80, 'icons/icons_80x72', '.png', ImageResource)
        self.populate_database(self.portraits, 'portraits', '.png', Portrait)
        self.set_up_portrait_coords('portraits/portrait_coords.xml')
        self.populate_map_sprites('map_sprites')

        self.platforms = self.get_sprites(self.main_folder, 'platforms')
        self.misc = self.get_sprites(self.main_folder, 'misc')

    def populate_database(self, d, folder, ftype, obj):
        for root, dirs, files in os.walk(os.path.join(self.main_folder, folder)):
            for name in files:
                if name.endswith(ftype):
                    full_path = os.path.join(root, name)
                    if ftype == '.png':
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

    def get_sprites(self, home, sub):
        s = {}
        for root, dirs, files in os.walk(os.path.join(home, sub)):
            for name in files:
                if name.endswith('.png'):
                    full_name = os.path.join(root, name)
                    s[name[:-4]] = full_name
        return s

    def restore(self, data):
        pass

    def save(self):
        pass

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

class ImageResource(object):
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap

        self.sub_images = []
        self.parent_image = None

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

class MapSprite(object):
    def __init__(self, nid, stand_full_path=None, move_full_path=None, standing_pixmap=None, moving_pixmap=None):
        self.nid = nid
        self.standing_full_path = stand_full_path
        self.moving_full_path = move_full_path
        self.standing_pixmap = standing_pixmap
        self.moving_pixmap = moving_pixmap

RESOURCES = Resources()
