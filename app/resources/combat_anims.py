import os
import shutil

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
    def __init__(self, nid, offset, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap
        self.image = None
        self.offset = offset
        self.location = None

    def set_full_path(self, full_path):
        self.full_path = full_path

    def serialize(self):
        full_path, tail = os.path.split(self.full_path)
        full_path, f = os.path.split(full_path)
        full_path = os.path.join(f, tail)
        return (self.nid, full_path, self.offset, self.location)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(s_tuple[0], s_tuple[2], s_tuple[1])
        if len(s_tuple) > 3 and s_tuple[3] is not None:
            self.location = tuple(s_tuple[3])
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
        self.poses = Data()
        self.frames = Data()

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['poses'] = [pose.serialize() for pose in self.poses]
        s_dict['frames'] = [frame.serialize() for frame in self.frames]
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls(s_dict['nid'])
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
            # new_map_sprite.set_standing_full_path(os.path.join(loc, new_map_sprite.standing_full_path))
            # new_map_sprite.set_moving_full_path(os.path.join(loc, new_map_sprite.moving_full_path))
            for weapon_anim in new_combat_anim.weapon_anims:
                for frame in weapon_anim.frames:
                    frame.set_full_path(os.path.join(loc, frame.full_path))
            self.append(new_combat_anim)

    def save(self, loc):
        for combat_anim in self:
            folder = os.path.join(loc, combat_anim.nid)
            if not os.path.exists(folder):
                os.mkdir(folder)
            for weapon_anim in combat_anim.weapon_anims:
                for frame in weapon_anim.frames:
                    new_full_path = os.path.join(loc, folder, "%s-%s.png" % (weapon_anim.nid, frame.nid))
                    if not frame.full_path:
                        frame.full_path = new_full_path
                        frame.pixmap.save(frame.pull_path)
                    if os.path.abspath(frame.full_path) != os.path.abspath(new_full_path):
                        shutil.copy(frame.full_path, new_full_path)
                        frame.set_full_path(new_full_path)
        self.dump(loc)

base_palette = Palette('base', [(128, 160, 128)] + [(0, 0, x*8) for x in range(15)])
