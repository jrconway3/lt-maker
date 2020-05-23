from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.data import Data, Prefab

from app.data.resources import RESOURCES

from app.engine import engine

class LayerObject():
    def __init__(self, nid: str, parent):
        self.nid: str = nid
        self.parent = parent
        self.visible = True
        self.terrain = {}
        self.image = None

    def set_image(self, image):
        self.image = image

class TileMapObject(Prefab):
    @classmethod
    def from_prefab(cls, prefab):
        self = cls()
        self.nid = prefab.nid
        self.width = prefab.width
        self.height = prefab.height
        self.layers = Data()

        # Stitch together image layers
        for layer in prefab.layers:
            new_layer = LayerObject(layer.nid, self)
            # Terrain
            for coord, terrain_nid in layer.terrain_grid.items():
                new_layer.terrain[coord] = terrain_nid
            # Image
            image = engine.create_surface((self.width, self.height), transparent=True)
            for coord, tile_sprite in layer.sprite_grid.items():
                tileset = RESOURCES.get(tile_sprite.tileset_nid)
                if not tileset.image:
                    tileset.image = engine.image_load(tileset.full_path)
                rect = (tile_sprite.tileset_position[0] * TILEWIDTH, 
                        tile_sprite.tileset_position[1] * TILEHEIGHT,
                        TILEWIDTH, TILEHEIGHT)
                sub_image = engine.subsurface(tileset.image, rect)
                image.blit(sub_image, (coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT))
            layer.image = image

        # First layer should be visible, rest invisible
        for layer in prefab.layers:
            layer.visible = False
        prefab.layers[0].visible = True

    def get_terrain(self, pos):
        for layer in reversed(self.layers):
            if layer.visible and pos in layer.terrain:
                return layer.terrain[pos]
        return None

    def get_full_image(self):
        if not self.full_image:
            image = engine.create_surface((self.width, self.height), transparent=True)
            for layer in self.layers:
                if layer.visible:
                    image.blit(layer.image, (0, 0))
            self.full_image = image
        return self.full_image

    def reset(self):
        self.full_image = None

    def serialize(self):
        pass

    def deserialize(cls, s_dict):
        # TODO
        self = cls()
        return self
