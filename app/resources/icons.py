import os
import shutil

from app.resources.base_catalog import BaseResourceCatalog

class Icon():
    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.full_path = full_path
        self.image = None
        self.pixmap = None

        # self.sub_images = []
        # self.parent_image = None
        # self.icon_index = (0, 0)

    def set_full_path(self, full_path):
        self.full_path = full_path

    # def unhook(self):
    #     if self.parent_image:
    #         self.parent_image.sub_images.remove(self)
    #         self.parent_image = None
    #     self.sub_images = []

class IconCatalog(BaseResourceCatalog):
    datatype = Icon
    filetype = '.png'

    def move_image(self, icon, loc):
        new_full_path = os.path.join(loc, icon.nid + self.filetype)
        if os.path.abspath(icon.full_path) != os.path.abspath(new_full_path):
            shutil.copy(icon.full_path, new_full_path)
            icon.set_full_path(new_full_path)

    def save(self, loc):
        for icon in self:
            self.move_image(icon, loc)
        # Delete unused in loc
        for fn in os.listdir(loc):
            if not fn.endswith('.png') or fn[:-4] not in self.keys():
                full_path = os.path.join(loc, fn)
                print("Deleting %s" % full_path)
                os.remove(full_path)
