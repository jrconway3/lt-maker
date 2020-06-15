from app.data.data import Data, Prefab

from app.data import combat_animation_command

required_poses = ('Stand', 'Hit', 'Miss', 'Dodge')
other_poses = ('RangedStand', 'RangedDodge', 'Critical')

class Pose(Prefab):
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
            command = combat_animation_command.get_command(nid)
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

    def set_full_path(self, full_path):
        self.full_path = full_path

    def serialize(self):
        return (self.nid, self.full_path, self.offset)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(s_tuple[0], s_tuple[2], s_tuple[1])
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

class WeaponAnimation(Prefab):
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

class CombatAnimation(Prefab):
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

base_palette = Palette('base', [(128, 160, 128)] + [(0, 0, x*8) for x in range(15)])
