import os

from app.data import data

class Resources(object):
    def __init__(self):
        self.main_folder = 'resources'

        # Modifiable Resources
        self.icons = data.data()
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
        self.populate_database(self.icons, 'icons', '.png')

        self.platforms = self.get_sprites(self.main_folder, 'platforms')
        self.misc = self.get_sprites(self.main_folder, 'misc')

    def populate_database(self, d, folder, ftype):
        for root, dirs, files in os.walk(os.path.join(self.main_folder, folder)):
            for name in files:
                if name.endswith(ftype):
                    full_path = os.path.join(root, name)
                    if ftype == '.png':
                        new_resource = ImageResource(name[:-4], full_path)
                    d.append(new_resource)

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

    def create_new_icon(self, nid, pixmap):
        full_path = os.path.join(self.main_folder, 'icons', nid)
        nid = nid[:-4]  # Get rid of .png ending
        new_icon = ImageResource(nid, full_path, pixmap)
        self.icons.append(new_icon)
        return new_icon

class ImageResource(object):
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap

RESOURCES = Resources()
