import json
import logging
import os
import re
import shutil
from app.utilities.data import Prefab
from app.resources.base_catalog import ManifestCatalog

from app.constants import COLORKEY

class Palette(Prefab):
    def __init__(self, nid):
        self.nid = nid
        # Mapping of color indices to true colors
        # Color indices are generally (0, 1) -> (240, 160, 240), etc.
        self.colors = {(0, 0): COLORKEY}

    def is_similar(self, colors) -> bool:
        counter = 0
        my_colors = [color for coord, color in self.colors.items()]
        for color in colors:
            if color in my_colors:
                counter += 1
        # Similar if more than 75% of colors match
        return (counter / len(colors)) > .75

    def assign_colors(self, colors: list):
        self.colors = {
            (int(idx % 8), int(idx / 8)): color for idx, color in enumerate(colors)
        }

    def save(self):
        return (self.nid, list(self.colors.items()))

    @classmethod
    def restore(cls, s):
        self = cls(s[0])
        self.colors = {tuple(k): tuple(v) for k, v in s[1].copy()}
        return self

class PaletteCatalog(ManifestCatalog[Palette]):
    datatype = Palette
    manifest = 'palettes.json'
    title = 'palettes'

    def save(self, loc):
        # No need to finagle with full paths
        # Because Palettes don't have any connection to any actual file.
        self.dump(loc)

    def load(self, loc):
        if not os.path.exists(os.path.join(loc, 'palette_data')): # old palettes.json
            tilemap_dict = self.read_manifest(os.path.join(loc, self.manifest))
            for s_dict in tilemap_dict:
                new_tilemap = Palette.restore(s_dict)
                self.append(new_tilemap)
        else:
            data_fnames = os.listdir(os.path.join(loc, 'palette_data'))
            save_data = []
            for fname in data_fnames:
                save_loc = os.path.join(loc, 'palette_data', fname)
                logging.info("Deserializing %s from %s" % ('palette data', save_loc))
                with open(save_loc) as load_file:
                    for data in json.load(load_file):
                        save_data.append(data)
            save_data = sorted(save_data, key=lambda obj: obj[2])
            for s_dict in save_data:
                new_tilemap = Palette.restore(s_dict)
                self.append(new_tilemap)

    def dump(self, loc):
        saves = [datum.save() for datum in self]
        save_dir = os.path.join(loc, 'palette_data')
        if os.path.exists(save_dir):
            shutil.rmtree(save_dir)
        os.mkdir(save_dir)
        for idx, save in enumerate(saves):
            # ordering
            save = list(save)
            save.append(idx)
            name = save[0]
            name = re.sub(r'[\\/*?:"<>|]',"", name)
            name = name.replace(' ', '_')
            save_loc = os.path.join(save_dir, name + '.json')
            with open(save_loc, 'w') as serialize_file:
                json.dump([save], serialize_file, indent=4)