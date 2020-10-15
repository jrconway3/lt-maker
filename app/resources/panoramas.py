import os
import shutil

from app.resources.base_catalog import ManifestCatalog

class Panorama():
    """
    A collection of background images
    """
    def __init__(self, nid, full_path=None, num_frames=0):
        self.nid = nid
        self.full_path = full_path  # Ignores numbers at the end
        self.num_frames = num_frames
        self.images = []
        self.pixmaps = []

        # self.idx = 0

    def set_full_path(self, full_path):
        self.full_path = full_path

    def get_all_paths(self):
        paths = []
        if self.num_frames == 1:
            paths.append(self.full_path)
        else:
            for idx in range(self.num_frames):
                path = self.full_path[:-4] + str(idx) + '.png'
                paths.append(path)
        return paths

    def save(self):
        return (self.nid, self.num_frames)

    @classmethod
    def restore(cls, s_tuple):
        self = cls(s_tuple[0], num_frames=s_tuple[1])
        return self

class PanoramaCatalog(ManifestCatalog):
    manifest = 'panoramas.json'
    title = 'panoramas'

    def load(self, loc):
        panorama_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in panorama_dict:
            new_panorama = Panorama.restore(s_dict)
            new_panorama.set_full_path(os.path.join(loc, new_panorama.nid + self.filetype))
            self.append(new_panorama)

    def save(self, loc):
        for panorama in self:
            new_full_path = os.path.join(loc, panorama.nid + '.png')
            if os.path.abspath(panorama.full_path) != os.path.abspath(new_full_path):
                if panorama.num_frames > 1:
                    paths = panorama.get_all_paths()
                    for idx, path in enumerate(paths):
                        shutil.copy(path, new_full_path[:-4] + str(idx) + '.png')
                else:
                    shutil.copy(panorama.full_path, new_full_path)
                panorama.set_full_path(new_full_path)
        self.dump(loc)
