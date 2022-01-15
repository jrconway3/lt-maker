from app.constants import TILEX, TILEY

from app.utilities.data import Prefab

class MapPrefab(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.width, self.height = TILEX, TILEY
        self.autotile_fps = 29

        self.pixmap = None
        
        self.terrain_grid = {}  # Key: Position, Value: Terrain Nids
        self.tile_grid = {}  # Key: Position, Value: Tileset Coordinate

    def set(self, pos: tuple, terrain: str):
        self.terrain_grid[pos] = terrain

    def get_terrain(self, pos: tuple):
        return self.terrain_grid.get(pos)

    def erase_terrain(self, pos: tuple):
        if pos in self.terrain_grid:
            del self.terrain_grid[pos]

    def clear(self):
        self.width, self.height = TILEX, TILEY
        self.terrain_grid.clear()

    def check_bounds(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def resize(self, width, height, x_offset, y_offset):
        self.width = width
        self.height = height

        new_terrain_grid = {}
        for pos, terrain_nid in self.terrain_grid.items():
            new_pos = pos[0] + x_offset, pos[1] + y_offset
            if self.check_bounds(new_pos):
                new_terrain_grid[new_pos] = terrain_nid
        self.terrain_grid = new_terrain_grid

        new_tile_grid = {}
        for pos, tile_coord in self.tile_grid.items():
            new_pos = pos[0] + x_offset, pos[1] + y_offset
            if self.check_bounds(new_pos):
                new_tile_grid[new_pos] = tile_coord
        self.tile_grid = new_tile_grid

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['size'] = self.width, self.height
        if self.width == 0 or self.height == 0:
            print("TileMap: Width or Height == 0!!!")
        s_dict['autotile_fps'] = self.autotile_fps
        s_dict['terrain_grid'] = {}
        for coord, terrain_nid in self.terrain_grid.items():
            str_coord = "%d,%d" % (coord[0], coord[1])
            s_dict['terrain_grid'][str_coord] = terrain_nid
        s_dict['tile_grid'] = {}
        for coord, tile_coord in self.terrain_grid.items():
            str_coord = "%d,%d" % (coord[0], coord[1])
            str_tile_coord = "%d,%d" % (tile_coord[0], tile_coord[1])
            s_dict['tile_grid'][str_coord] = str_tile_coord
        return s_dict

    @classmethod
    def restore(cls, s_dict):
        self = cls(s_dict['nid'])
        self.width, self.height = s_dict['size']
        self.autotile_fps = s_dict.get('autotile_fps', 29)
        for str_coord, terrain_nid in s_dict['terrain_grid'].items():
            coord = tuple(int(_) for _ in str_coord.split(','))
            self.terrain_grid[coord] = terrain_nid
        for str_coord, str_tile_coord in s_dict['tile_grid'].items():
            coord = tuple(int(_) for _ in str_coord.split(','))
            tile_coord = tuple(int(_) for _ in str_tile_coord.split(','))
            self.tile_grid[coord] = tile_coord
        return self

    # Used only in tilemap editor
    def restore_edits(self, s_dict):
        self.width, self.height = s_dict['size']
        for str_coord, terrain_nid in s_dict['terrain_grid'].items():
            coord = tuple(int(_) for _ in str_coord.split(','))
            self.terrain_grid[coord] = terrain_nid
        for str_coord, str_tile_coord in s_dict['tile_grid'].items():
            coord = tuple(int(_) for _ in str_coord.split(','))
            tile_coord = tuple(int(_) for _ in str_tile_coord.split(','))
            self.tile_grid[coord] = tile_coord
        return self
