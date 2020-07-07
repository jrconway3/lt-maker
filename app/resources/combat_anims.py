import os
import shutil

from app.data.constants import COLORKEY
from app.resources.base_catalog import ManifestCatalog
from app.resources import combat_commands
from app.data.data import Data

required_poses = ('Stand', 'Hit', 'Miss', 'Dodge')
other_poses = ('RangedStand', 'RangedDodge', 'Critical')

class Pose():
    def __init__(self, nid):
        self.nid = nid
        self.timeline = []

    def serialize(self):
        return (self.nid, [command.serialize() for command in self.timeline])

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(s_tuple[0])
        for command_save in s_tuple[1]:
            nid, value = command_save
            command = combat_commands.get_command(nid)
            command.value = value
            self.timeline.append(command)
        return self

class Frame():
    def __init__(self, nid, rect, offset, full_path=None, pixmap=None):
        self.nid = nid

        self.rect = rect
        self.offset = offset

        self.pixmap = pixmap
        self.image = None

    def serialize(self):
        return (self.nid, self.rect, self.offset)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(*s_tuple)
        return self

class Palette():
    def __init__(self, nid, colors=None):
        self.nid = nid
        self.colors = colors or []

    def __repr__(self):
        return self.nid + ": " + str(self.colors)

    def serialize(self):
        return (self.nid, self.colors)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(*s_tuple)
        self.colors = [tuple(c) for c in self.colors]
        return self

class WeaponAnimation():
    def __init__(self, nid):
        self.nid = nid
        self.full_path = None
        self.poses = Data()
        self.frames = Data()

        self.pixmap = None

    def set_full_path(self, full_path):
        self.full_path = full_path

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['full_path'] = self.full_path
        s_dict['poses'] = [pose.serialize() for pose in self.poses]
        s_dict['frames'] = [frame.serialize() for frame in self.frames]
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls(s_dict['nid'])
        self.full_path = s_dict['full_path']
        for frame_save in s_dict['frames']:
            self.frames.append(Frame.deserialize(frame_save))
        for pose_save in s_dict['poses']:
            self.poses.append(Pose.deserialize(pose_save))
        return self

class CombatAnimation():
    def __init__(self, nid):
        self.nid = nid
        self.weapon_anims = Data()
        self.palettes = Data()

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['weapon_anims'] = [weapon_anim.serialize() for weapon_anim in self.weapon_anims]
        s_dict['palettes'] = [palette.serialize() for palette in self.palettes]
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls(s_dict['nid'])
        for palette_save in s_dict['palettes']:
            self.palettes.append(Palette.deserialize(palette_save))
        for weapon_anim_save in s_dict['weapon_anims']:
            self.weapon_anims.append(WeaponAnimation.deserialize(weapon_anim_save))
        return self

class CombatCatalog(ManifestCatalog):
    manifest = 'combat_anims.json'
    title = 'Combat Animations'

    def load(self, loc):
        combat_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in combat_dict:
            new_combat_anim = CombatAnimation.deserialize(s_dict)
            for weapon_anim in new_combat_anim.weapon_anims:
                weapon_anim.set_full_path(os.path.join(loc, weapon_anim.full_path))
            self.append(new_combat_anim)

    def save(self, loc):
        for combat_anim in self:
            for weapon_anim in combat_anim.weapon_anims:
                new_full_path = os.path.join(loc, "%s-%s.png" % (combat_anim.nid, weapon_anim.nid))
                if not weapon_anim.full_path:
                    weapon_anim.full_path = new_full_path
                    weapon_anim.pixmap.save(weapon_anim.full_path)
                if os.path.abspath(weapon_anim.full_path) != os.path.abspath(new_full_path):
                    shutil.copy(weapon_anim.full_path, new_full_path)
                    weapon_anim.set_full_path(new_full_path)
        self.dump(loc)

base_palette = Palette('base', [COLORKEY] + [(0, 0, x*8) for x in range(15)])
