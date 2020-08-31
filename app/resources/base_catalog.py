import os
import shutil
import json

from app.utilities.data import Data

class BaseResourceCatalog(Data):
    def load(self, loc):
        for root, dirs, files in os.walk(loc):
            for name in files:
                if name.endswith(self.filetype):
                    full_path = os.path.join(root, name)
                    nid = name[:-len(self.filetype)]
                    new_resource = self.datatype(nid, full_path)
                    self.append(new_resource)

class ManifestCatalog(Data):
    filetype = '.png'

    def read_manifest(self, fn: str) -> dict:
        datum = {}
        if os.path.exists(fn):
            with open(fn) as load_file:
                datum = json.load(load_file)
        return datum

    def dump(self, loc):
        save = [datum.serialize() for datum in self]
        save_loc = os.path.join(loc, self.manifest)
        print("Serializing %s to %s" % (self.title, save_loc))
        with open(save_loc, 'w') as serialize_file:
            json.dump(save, serialize_file, indent=4)

    def save(self, loc):
        for datum in self:
            new_full_path = os.path.join(loc, datum.nid + self.filetype)
            if os.path.abspath(datum.full_path) != os.path.abspath(new_full_path):
                shutil.copy(datum.full_path, new_full_path)
                datum.set_full_path(new_full_path)
        self.dump(loc)
