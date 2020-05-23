from app.data.constants import TILEWIDTH, TILEHEIGHT, TILEX, TILEY

from app.data.data import Data, Prefab

class TileMapPrefab(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.width, self.height = TILEX, TILEY
        self.layers = Data()
        self.tilesets = []  # Opened tilesets associated with this tilemap, nothing more

    def clear(self):
        self.width, self.height = TILEX, TILEY
        self.layers.clear()

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['size'] = self.width, self.height
        if self.width == 0 or self.height == 0:
            print("Width or Height == 0!!!")
        s_dict['layers'] = self.layers.serialize()
        s_dict['tilesets'] = self.tilesets
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls(s_dict['nid'])
        self.width, self.height = s_dict['size']
        self.tilesets = s_dict['tilesets']
        self.layers = Data([LayerGrid.deserialize(layer, self) for layer in s_dict['layers']])
        return self

class TileSet(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.width, self.height = 0, 0
        self.terrain_grid = {}
        self.full_path = None
        self.pixmap = None
        self.pixmaps = {}
        self.image = None  # For use with engine

    def set_pixmap(self, pixmap, pixmap_path):
        self.full_path = pixmap_path
        self.pixmap = pixmap
        self.width = self.pixmap.width() // TILEWIDTH
        self.height = self.pixmap.height() // TILEHEIGHT
        # Subsurface
        self.pixmaps.clear()
        for x in range(self.width):
            for y in range(self.height):
                p = self.pixmap.copy(x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                self.pixmaps[(x, y)] = p

    def set_full_path(self, full_path):
        self.full_path = full_path

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['full_path'] = self.full_path
        s_dict['terrain_grid'] = {}
        for coord, terrain_nid in self.terrain_grid.items():
            s_dict['terrain_grid'][coord] = terrain_nid
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls(s_dict['nid'])
        self.full_path = s_dict['full_path']
        for coord, terrain_nid in s_dict['terrain_grid'].items():
            self.terrain_grid[coord] = terrain_nid
        return self

class LayerGrid(Prefab):
    def __init__(self, nid: str, parent):
        self.nid: str = nid
        self.parent = parent
        self.visible: bool = True
        self.terrain_grid = {}
        self.sprite_grid = {}

    def set(self, coord, tile, tile_sprite):
        self.terrain_grid[coord] = tile
        self.sprite_grid[coord] = tile_sprite

    def get_terrain(self, coord):
        return self.terrain_grid[coord]

    def get_sprite(self, coord):
        return self.sprite_grid[coord]

    def serialize(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['visible'] = self.visible
        s_dict['terrain_grid'] = {}
        for coord, terrain_nid in self.terrain_grid.items():
            s_dict['terrain_grid'][coord] = terrain_nid
        s_dict['sprite_grid'] = {}
        for coord, tile_sprite in self.sprite_grid.items():
            s_dict['sprite_grid'][coord] = tile_sprite.serialize()
        return s_dict

    @classmethod
    def deserialize(cls, s_dict, parent):
        self = cls(s_dict['nid'], parent)
        self.visible = s_dict['visible']
        for coord, terrain_nid in s_dict['terrain_grid'].items():
            self.terrain_grid[coord] = terrain_nid
        for coord, data in s_dict['sprite_grid'].items():
            self.sprite_grid[coord] = TileSprite.deserialize(*data, self)

class TileSprite(Prefab):
    def __init__(self, tileset_nid, tileset_position, parent):
        self.parent = parent
        self.tileset_nid = tileset_nid
        self.tileset_position = tileset_position

    def serialize(self):
        return self.tileset_nid, self.tileset_position

    @classmethod
    def deserialize(cls, tileset_nid, tileset_position, parent):
        new_tile_sprite = cls(tileset_nid, tileset_position, parent)
        return new_tile_sprite
