import os

from app.data.data import Data

class Font():
    def __init__(self, nid, png_path, idx_path):
        self.nid = nid
        self.png_path = png_path
        self.idx_path = idx_path

class FontCatalog(Data):
    datatype = Font

    @classmethod
    def load(cls, home, sub):
        self = cls()
        loc = os.path.join(home, sub)
        for root, dirs, files in os.walk(loc):
            for name in files:
                if name.endswith('.png'):
                    full_name = os.path.join(root, name)
                    nid = name[:-4]
                    idx_name = nid.split('_')[0] + '.idx'
                    idx_full_name = os.path.join(root, idx_name)
                    self.append(Font(nid, full_name, idx_full_name))
        return self
