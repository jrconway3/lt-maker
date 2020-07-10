import os
import shutil

from app.resources.base_catalog import ManifestCatalog

class MapSprite():
    def __init__(self, nid, stand_full_path=None, move_full_path=None, standing_pixmap=None, moving_pixmap=None):
        self.nid = nid
        self.standing_full_path = stand_full_path
        self.moving_full_path = move_full_path
        self.standing_pixmap = standing_pixmap
        self.moving_pixmap = moving_pixmap
        self.standing_image = None
        self.moving_image = None

    def set_standing_full_path(self, full_path):
        self.standing_full_path = full_path

    def set_moving_full_path(self, full_path):
        self.moving_full_path = full_path

    def serialize(self):
        stand = os.path.split(self.standing_full_path)[-1]
        move = os.path.split(self.moving_full_path)[-1]
        return (self.nid, stand, move)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(*s_tuple)
        return self

class MapSpriteCatalog(ManifestCatalog):
    manifest = 'map_sprites.json'
    title = 'map sprites'

    def load(self, loc):
        map_sprite_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in map_sprite_dict:
            new_map_sprite = MapSprite.deserialize(s_dict)
            new_map_sprite.set_standing_full_path(os.path.join(loc, new_map_sprite.standing_full_path))
            new_map_sprite.set_moving_full_path(os.path.join(loc, new_map_sprite.moving_full_path))
            self.append(new_map_sprite)

    def save(self, loc):
        for map_sprite in self:
            # Standing sprite
            new_full_path = os.path.join(loc, map_sprite.nid + '-stand.png')
            if not map_sprite.standing_full_path:
                map_sprite.set_standing_full_path(new_full_path)
                map_sprite.standing_pixmap.save(new_full_path)
            elif os.path.abspath(map_sprite.standing_full_path) != os.path.abspath(new_full_path):
                shutil.copy(map_sprite.standing_full_path, new_full_path)
                map_sprite.set_standing_full_path(new_full_path)
            # Moving sprite
            new_full_path = os.path.join(loc, map_sprite.nid + '-move.png')
            if not map_sprite.moving_full_path:
                map_sprite.set_moving_full_path(new_full_path)
                map_sprite.moving_pixmap.save(new_full_path)
            elif os.path.abspath(map_sprite.moving_full_path) != os.path.abspath(new_full_path):
                shutil.copy(map_sprite.moving_full_path, new_full_path)
                map_sprite.set_moving_full_path(new_full_path)
        self.dump(loc)
