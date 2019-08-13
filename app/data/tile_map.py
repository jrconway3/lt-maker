from tile import Tile
from data import database

class TileMap(object):
    def __init__(self, image_fn, terrain_fn):
        map_key, self.width, self.height = self.build_map_key(terrain_fn)

        self.tiles = {} # The mechanical information about the tile organized by position
        self.tile_sprites = {}  # The sprite information about the tile organized by position

        self.populate_tiles(map_key)

    def build_map_key(self, terrain_fn):
        with open(terrain_fn) as fp:
            lines = [l.strip().split() for l in fp.readlines]
        width = len(lines[0])
        height = len(lines)

        return lines, width, height

    def populate_tiles(self, map_key):
        for y in range(map_key):
            for x in range(map_key[y]):
                terrain = database.terrain.get(int(map_key[y][x]))
                new_tile = Tile(terrain, (x, y), self)
                self.tiles[(x, y)] = new_tile
