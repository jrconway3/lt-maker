from app.data.data import Data, Prefab

required_poses = ('Stand', 'Hit', 'Miss', 'Dodge')
other_poses = ('RangedStand', 'RangedDodge', 'Critical')

class Pose(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.timeline = []

class Frame():
    def __init__(self, nid, offset, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap
        self.image = None
        self.offset = offset

    def set_full_path(self, full_path):
        self.full_path = full_path

class Palette():
    def __init__(self, nid, colors=None):
        self.nid = nid
        self.colors = colors or []

class WeaponAnimation(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.poses = Data()
        self.frames = Data()

class CombatVariant(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.weapon_anims = Data()

class CombatAnimation(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.variants = Data()
        self.palettes = Data()

base_palette = Palette('base', [(248, 248, 248)] + [(0, 0, x*8) for x in range(15)])
