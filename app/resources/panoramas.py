import os
import glob
import shutil

from app import utilities
from app.data.data import Data

class Panorama():
    def __init__(self, nid, full_path=None, pixmaps=None, num_frames=0):
        self.nid = nid
        self.full_path = full_path  # Ignores numbers at the end
        self.num_frames = num_frames or len(pixmaps)
        self.pixmaps = pixmaps or []
        self.images = []
        self.idx = 0

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

    def get_frame(self):
        if self.pixmaps:
            return self.pixmaps[self.idx]

    def get_img_frame(self):
        if self.images:
            return self.images[self.idx]

    def increment_frame(self):
        if self.pixmaps:
            self.idx = (self.idx + 1) % len(self.pixmaps)  # Wrap around
        elif self.images:
            self.idx = (self.idx + 1) % len(self.images)  # Wrap around

class PanoramaCatalog(Data):
    def load(self, loc):
        for root, dirs, files in os.walk(loc):
            for name in files:
                if name.endswith('.png'):
                    nid = name[:-4]
                    last_number = utilities.find_last_number(nid)
                    if last_number == 0:
                        movie_prefix = name[:-5]
                        full_path = os.path.join(root, movie_prefix + '.png')
                        num_frames = len(glob.glob(os.path.join(root, movie_prefix + '*' + '.png')))
                    elif last_number is None:
                        movie_prefix = nid
                        full_path = os.path.join(root, name)
                        num_frames = 1
                    else:
                        continue
                    new_panorama = Panorama(movie_prefix, full_path, num_frames=num_frames)
                    self.append(new_panorama)

    def save(self, loc):
        for panorama in self:
            new_full_path = os.path.join(loc, panorama.nid + '.png')
            if os.path.abspath(panorama.full_path) != os.path.abspath(new_full_path):
                paths = panorama.get_all_paths()
                if len(paths) > 1:
                    for idx, path in enumerate(paths):
                        shutil.copy(path, new_full_path + str(idx) + '.png')
                else:
                    shutil.copy(paths[0], new_full_path + '.png')
                panorama.set_full_path(new_full_path)
        # Deleting unused panoramas
        for fn in os.listdir(loc):
            if fn.endswith('.png') and utilities.get_prefix(fn) not in self.keys():
                full_path = os.path.join(loc, fn)
                if os.path.exists(full_path):
                    print("Deleting %s" % full_path)
                    os.remove(full_path)
