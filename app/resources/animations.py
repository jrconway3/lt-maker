import os

from app import utilities
from app.resources.base_catalog import ManifestCatalog

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

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['full_path'] = os.path.split(self.full_path)[-1]
        s_dict['frame_x'] = self.frame_x
        s_dict['frame_y'] = self.frame_y
        s_dict['num_frames'] = self.num_frames
        if utilities.is_int(self.speed):
            s_dict['speed'] = str(self.speed)
        else:
            s_dict['speed'] = ','.join([str(_) for _ in self.speed])
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls(s_dict['nid'], s_dict['full_path'])
        self.frame_x = s_dict['frame_x']
        self.frame_y = s_dict['frame_y']
        self.num_frames = s_dict['num_frames']
        if utilities.is_int(s_dict['speed']):
            self.speed = int(s_dict['speed'])
        else:
            self.speed = [int(_) for _ in s_dict['speed'].split(',')]
        return self

class AnimationCatalog(ManifestCatalog):
    manifest = 'animations.json'
    title = 'animations'

    def load(self, loc):
        anim_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in anim_dict:
            new_anim = Animation.deserialize(s_dict)
            new_anim.set_full_path(os.path.join(loc, new_anim.full_path))
            self.append(new_anim)
