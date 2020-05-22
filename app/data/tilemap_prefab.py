from app.data.constants import TILEWIDTH, TILEHEIGHT, TILEX, TILEY

from app.data.data import Data, Prefab

class TileMapPrefab(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.width, self.height = TILEX, TILEY
        self.layers = Data()
        self.tilesets = Data()

    def clear(self):
        self.width, self.height = TILEX, TILEY
        self.layers.clear()

    def set_pixmap(self, pixmap):
        new_tileset = TileSet('base')
        new_tileset.set_pixmap(pixmap)
        self.width = new_tileset.width
        self.height = new_tileset.height

        new_layer = LayerGrid('base', self)
        for x in range(self.width):
            for y in range(self.height):
                new_tile = Tile(0, (x, y), self)
                new_tile_sprite = TileSprite('base', (x, y), self)
                new_layer.set((x, y), (new_tile, new_tile_sprite))
        self.layers.append(new_layer)

    def serialize(self):
        s_dict = {}
        s_dict['size'] = self.width, self.height
        if self.width == 0 or self.height == 0:
            print("Width or Height == 0!!!")
        s_dict[]


class TileSet(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.width, self.height = 0, 0
        self.pixmap = None
        self.pixmaps = {}

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.width = self.pixmap.width() // TILEWIDTH
        self.height = self.pixmap.height() // TILEHEIGHT
        # Subsurface
        self.pixmaps.clear()
        for x in range(self.width):
            for y in range(self.height):
                p = self.pixmap.copy(x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                self.pixmaps[(x, y)] = p

class LayerGrid(Prefab):
    def __init__(self, nid: str, parent):
        self.nid: str = nid
        self.parent = parent
        self.visible: bool = True
        self.grid = {}

    def set(self, coord, tile):
        self.grid[coord] = tile

    def get(self, coord):
        return self.grid[coord]

class Tile(Prefab):
    def __init__(self, terrain_nid, position, parent):
        self.parent = parent
        self.terrain_nid = terrain_nid
        self.position = position

        self.current_hp = 0

    def serialize(self):
        return self.terrain_nid

    @classmethod
    def deserialize(cls, terrain_nid, position, parent):
        new_tile = cls(terrain_nid, position, parent)
        return new_tile

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


