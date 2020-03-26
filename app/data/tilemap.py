from app.data import constants

class TileMap(object):
    def __init__(self, image_nid, terrain_fn):
        map_key, self.width, self.height = self.build_map_key(terrain_fn)

        self.tiles = {} # The mechanical information about the tile organized by position
        self.tile_sprites = {}  # The sprite information about the tile organized by position

        self.populate_tiles(map_key)
        self.base_image_nid = image_nid

    def build_map_key(self, terrain_fn):
        with open(terrain_fn) as fp:
            lines = [l.strip().split() for l in fp.readlines()]
        width = len(lines[0])
        height = len(lines)

        return lines, width, height

    def populate_tiles(self, map_key):
        from app.data.database import DB
        for x in range(self.width):
            for y in range(self.height):
                terrain = DB.terrain.get(map_key[y][x])
                new_tile = Tile(terrain.nid, (x, y), self)
                self.tiles[(x, y)] = new_tile

    def change_image(self, image_nid, width, height):
        from app.data.database import DB
        self.base_image_nid = image_nid
        self.width, self.height = width//constants.TILEWIDTH, height//constants.TILEHEIGHT
        # Preserve as much as possible about the old terrain information
        old_tiles = self.tiles.copy()
        self.tiles.clear()
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) in old_tiles:
                    self.tiles[(x, y)] = old_tiles[(x, y)]
                else:
                    default_terrain = DB.terrain[0]
                    new_tile = Tile(default_terrain.nid, (x, y), self)
                    self.tiles[(x, y)] = new_tile

    @classmethod
    def default(cls):
        return cls("default", "./app/default_data/default_tilemap_terrain.txt")

    def serialize(self):
        s_dict = {}
        s_dict['size'] = (self.width, self.height)
        s_dict['tiles'] = []
        for x in range(self.width):
            for y in range(self.height):
                s_dict['tiles'].append(self.tiles[(x, y)].serialize())
        s_dict['base_image_nid'] = self.base_image_nid
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        new_tilemap = cls.default()
        width, height = s_dict['size']
        new_tilemap.change_image(s_dict['base_image_nid'], width, height)
        new_tilemap.tiles.clear()
        for idx, val in enumerate(s_dict['tiles']):
            x = idx//height
            y = idx%height
            new_tilemap.tiles[(x, y)] = Tile.deserialize(val, (x, y), new_tilemap)
        return new_tilemap

class Tile(object):
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

class TileSprite(object):
    def __init__(self, image, position, parent):
        self.image = image
        self.parent = parent
        self.position = position
