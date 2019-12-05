from app.data import data

class Resources(object):
    def __init__(self):
        self.icons = data.data()
        self.portraits = data.data()
        self.panoramas = data.data()
        self.map_sprites = data.data()
        self.combat_anims = data.data()
        self.combat_effects = data.data()
        self.map_effects = data.data()
        self.music = data.data()
        self.sfx = data.data()
        
        self.init_load()

    def init_load(self):
        pass

    def restore(self, data):
        pass

    def save(self):
        pass

RESOURCES = Resources()
