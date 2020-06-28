import os

from app.resources.base_catalog import ManifestCatalog

class Portrait():
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path
        self.pixmap = pixmap
        self.image = None

        self.blinking_offset = [0, 0]
        self.smiling_offset = [0, 0]

    def set_full_path(self, full_path):
        self.full_path = full_path

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['full_path'] = os.path.split(self.full_path)[-1]
        s_dict['blinking_offset'] = self.blinking_offset
        s_dict['smiling_offset'] = self.smiling_offset
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls(s_dict['nid'], s_dict['full_path'])
        self.blinking_offset = [int(_) for _ in s_dict['blinking_offset']]
        self.smiling_offset = [int(_) for _ in s_dict['smiling_offset']]
        return self

class PortraitCatalog(ManifestCatalog):
    manifest = 'portraits.json'
    title = 'portraits'

    def load(self, loc):
        portrait_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in portrait_dict:
            new_portrait = Portrait.deserialize(s_dict)
            new_portrait.set_full_path(os.path.join(loc, new_portrait.full_path))
            self.append(new_portrait)
