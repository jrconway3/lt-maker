import os
import shutil
import ntpath

from PyQt5.QtGui import QIcon, QPixmap

from app.resources.base_catalog import ManifestCatalog

class MapIcon():
    def __init__(self, nid, image_path=None):
        self.nid = nid
        self.path = image_path
        self.full_path = None
        self.image = None
        self.pixmap = None

    def set_path(self, image_path):
        self.path = image_path

    def get_pixmap(self):
        if not self.pixmap:
            self.pixmap = QPixmap(self.full_path)
        return self.pixmap

    def save(self):
        return {"nid": self.nid, "path": self.path}

    @classmethod
    def restore(cls, nid, path):
        self = cls(nid, path)
        return self

class MapIconCatalog(ManifestCatalog):
    manifest = 'map_icons.json'
    title = 'map icons'

    def load(self, loc):
        map_icon_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in map_icon_dict:
            new_map_icon = MapIcon.restore(s_dict['nid'], s_dict['path'])
            new_map_icon.full_path = os.path.join(loc, s_dict['path'])
            self.append(new_map_icon)

    def save(self, loc):
        for map_icon in self:
            new_full_path = os.path.join(loc, map_icon.path)
            if not new_full_path == map_icon.full_path:
                shutil.copy(map_icon.full_path, new_full_path)
        self.dump(loc)

    @classmethod
    def DEFAULT(self):
        return '0'