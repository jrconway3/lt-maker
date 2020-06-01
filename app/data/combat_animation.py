from app.data.data import Data, Prefab

required_poses = ('Stand', 'Hit', 'Miss')
other_poses = ('RangedStand', 'Critical')

class Pose(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.timeline = []

class Frame():
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap
        self.image = None

    def set_full_path(self, full_path):
        self.full_path = full_path

class WeaponAnimation(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.poses = Data()
        self.frames = Data()

class CombatAnimation(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.weapon_anims = Data()
