from dataclasses import dataclass

from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities.data import Data, Prefab
import app.utilities as utils
from app.map_maker.utilities import random_choice, edge_random, flood_fill

@dataclass
class Terrain(Prefab):
    nid: str = None
    name: str = None
    tileset_path: str = None

    display_tile_coord: tuple = (0, 0)

    display_pixmap: QPixmap = None
    tileset_pixmap: QPixmap = None

    # Determines whether we should put all types of this terrain to be updated
    check_flood_fill: bool = False

    def set_tileset(self, tileset_path=None):
        if tileset_path:
            self.tileset_path = tileset_path
        self.tileset_pixmap = QPixmap(self.tileset_path)
        self.display_pixmap = None
        self.get_display_pixmap()

    def get_display_pixmap(self):
        if not self.display_pixmap:
            pix = self.tileset_pixmap.copy(
                self.display_tile_coord[0] * TILEWIDTH, 
                self.display_tile_coord[1] * TILEHEIGHT,
                TILEWIDTH, TILEHEIGHT)
            self.display_pixmap = pix
        return self.display_pixmap
        
    def restore_attr(self, name, value):
        if name in ('tileset_path', 'display_tile_coord'):
            value = tuple(value)
        else:
            value = super().restore_attr(name, value)
        return value

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords1 = [(self.display_tile_coord[0]*2, self.display_tile_coord[1]*2)]
        new_coords2 = [(self.display_tile_coord[0]*2 + 1, self.display_tile_coord[1]*2)]
        new_coords3 = [(self.display_tile_coord[0]*2 + 1, self.display_tile_coord[1]*2 + 1)]
        new_coords4 = [(self.display_tile_coord[0]*2, self.display_tile_coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

class TerrainCatalog(Data[Terrain]):
    datatype = Terrain

class RandomTerrain(Terrain):
    data = []

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords1 = [(p[0]*2, p[1]*2) for p in self.data]
        new_coords2 = [(p[0]*2 + 1, p[1]*2) for p in self.data]
        new_coords3 = [(p[0]*2 + 1, p[1]*2 + 1) for p in self.data]
        new_coords4 = [(p[0]*2, p[1]*2 + 1) for p in self.data]
        return new_coords1, new_coords2, new_coords3, new_coords4

class WangEdge2Terrain(Terrain):
    terrain_like = ()

    def set_tileset(self, tileset_path=None):
        super().set_tileset(tileset_path)
        self.limits = {k: self._find_limit(k) for k in range(16)}
        print(self.nid, self.limits)

    def _find_limit(self, idx: int) -> int:
        bg_color = qRgb(0, 0, 0)
        img = self.tileset_pixmap.toImage()
        x = idx * TILEWIDTH//2
        for y in range(0, img.height(), TILEHEIGHT//2):
            current_color = img.pixel(x, y)
            if current_color == bg_color:
                return y // (TILEHEIGHT//2)
        return (img.height() // (TILEHEIGHT//2))

    def get_display_pixmap(self):
        if not self.display_pixmap:
            main_pix = QPixmap(16, 16)
            painter = QPainter()
            painter.begin(main_pix)
            painter.drawPixmap(0, 0, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 0 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(0, TILEHEIGHT//2, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 1 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, 0, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 2 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, TILEHEIGHT//2, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 3 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.end()
            self.display_pixmap = main_pix
        return self.display_pixmap

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index1 = 6 + 1 * north_edge + 8 * west_edge
        index2 = 12 + 1 * north_edge + 2 * east_edge
        index3 = 9 + 4 * south_edge + 2 * east_edge
        index4 = 3 + 4 * south_edge + 8 * west_edge
        new_coords1 = [(index1, k) for k in range(self.limits[index1])]
        new_coords2 = [(index2, k) for k in range(self.limits[index2])]
        new_coords3 = [(index3, k) for k in range(self.limits[index3])]
        new_coords4 = [(index4, k) for k in range(self.limits[index4])]
        return new_coords1, new_coords2, new_coords3, new_coords4

class WangCorner2Terrain(WangEdge2Terrain):
    terrain_like = ()

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index1 = 1 * north_edge + \
            2 * True + \
            4 * west_edge + \
            8 * (bool(not northwest or northwest in self.terrain_like) and north_edge and west_edge)
        index2 = 1 * (bool(not northeast or northeast in self.terrain_like) and north_edge and east_edge) + \
            2 * east_edge + \
            4 * True + \
            8 * north_edge
        index3 = 1 * east_edge + \
            2 * (bool(not southeast or southeast in self.terrain_like) and south_edge and east_edge) + \
            4 * south_edge + \
            8 * True
        index4 = 1 * True + \
            2 * south_edge + \
            4 * (bool(not southwest or southwest in self.terrain_like) and south_edge and west_edge) + \
            8 * west_edge
        return index1, index2, index3, index4

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        index1, index2, index3, index4 = self._determine_index(tilemap, pos)
        new_coords1 = [(index1, k) for k in range(self.limits[index1])]
        new_coords2 = [(index2, k) for k in range(self.limits[index2])]
        new_coords3 = [(index3, k) for k in range(self.limits[index3])]
        new_coords4 = [(index4, k) for k in range(self.limits[index4])]
        return new_coords1, new_coords2, new_coords3, new_coords4

class SandTerrain(WangCorner2Terrain):
    terrain_like = ('Sand', 'Road')
    memory = {}

    def _kth_bit_set(self, n: int, k: int) -> bool:
        """
        n is number you are checking
        k is which bit to check
        1 => 0
        2 => 1
        4 => 2
        8 => 3
        """
        return bool(n & (1 << k))

    def _determine_index(self, tilemap, pos: tuple, use_memory: bool = False) -> tuple:
        """
        pos is in 16x16 space
        assumes tiles fill left to right, then top to bottom
        [
         00 10 20 30
         01 11 21 31
         02 12 22 32
         03 13 23 33
        ]
        00 10 01 11 is [0]
        20 30 21 31 is [1]
        22 32 23 33 is [2]
        02 12 03 13 is [3]
        # For additive indexing
        northwest == 8
        northeast == 1
        southwest == 4
        southeast == 2
        """
        if use_memory and pos in self.memory:
            return self.memory[pos]
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        northeast_edge = bool(not northeast or northeast in self.terrain_like)
        southeast_edge = bool(not southeast or southeast in self.terrain_like)
        southwest_edge = bool(not southwest or southwest in self.terrain_like)
        northwest_edge = bool(not northwest or northwest in self.terrain_like)
        north_index = self._determine_index(tilemap, (pos[0], pos[1] - 1), True) if north_edge and north else ((0, 0, 0, 0) if north else (15, 15, 15, 15,))
        west_index = self._determine_index(tilemap, (pos[0] - 1, pos[1]), True) if west_edge and west else ((0, 0, 0, 0) if west else (15, 15, 15, 15))
        northwest_index = self._determine_index(tilemap, (pos[0] - 1, pos[1] - 1), True) if northwest_edge and northwest else ((0, 0, 0, 0) if northwest else (15, 15, 15, 15))
        # northeast_index = self._determine_index(tilemap, (pos[0] + 1, pos[1] - 1), True) if northeast_edge and northeast else ((0, 0, 0, 0) if northeast else (15, 15, 15, 15))
        southwest_index = self._determine_index(tilemap, (pos[0] - 1, pos[1] + 1), True) if southwest_edge and southwest else ((0, 0, 0, 0) if southwest else (15, 15, 15, 15))

        # Topleft
        corner00_full = north_edge and northwest_edge and west_edge
        corner10_full = north_edge
        corner01_full = west_edge
        corner11_full = True
        # Check if partners have a corner there
        corner00 = corner00_full and self._kth_bit_set(north_index[3], 2) and self._kth_bit_set(northwest_index[2], 1) and self._kth_bit_set(west_index[1], 0)
        corner10 = corner10_full and self._kth_bit_set(north_index[3], 1)
        corner01 = corner01_full and self._kth_bit_set(west_index[1], 1)
        corner11 = corner11_full
        index1 = 1 * corner10 + 2 * corner11 + 4 * corner01 + 8 * corner00

        # Topright
        corner20_full = north_edge
        corner30_full = north_edge and northeast_edge and east_edge
        corner21_full = True
        corner31_full = east_edge
        # Check if partners have a corner there
        corner20 = corner20_full and self._kth_bit_set(north_index[2], 2)
        corner30 = corner30_full and self._kth_bit_set(north_index[2], 1) and True and True
        corner21 = corner21_full
        corner31 = corner31_full and True
        index2 = 1 * corner30 + 2 * corner31 + 4 * corner21 + 8 * corner20

        # Bottomleft
        corner02_full = west_edge
        corner12_full = True
        corner03_full = west_edge and southwest_edge and south_edge
        corner13_full = south_edge
        # Check if partners have a corner there
        corner02 = corner02_full and self._kth_bit_set(west_index[2], 0)
        corner12 = corner12_full
        corner03 = corner03_full and self._kth_bit_set(west_index[2], 1) and self._kth_bit_set(southwest_index[1], 0) and True
        corner13 = corner13_full and True
        index4 = 1 * corner12 + 2 * corner13 + 4 * corner03 + 8 * corner02

        # Bottomright
        corner22_full = True
        corner32_full = east_edge
        corner23_full = south_edge
        corner33_full = east_edge and southeast_edge and south_edge
        # Check if partners have a corner there
        corner22 = corner22_full
        corner32 = corner32_full and True
        corner23 = corner23_full and True
        corner33 = corner33_full and True and True and True
        index3 = 1 * corner32 + 2 * corner33 + 4 * corner23 + 8 * corner22

        # Save so we can use these results later
        self.memory[pos] = index1, index2, index3, index4

        return index1, index2, index3, index4

class ForestTerrain(Terrain):
    forest_like = ('Forest', 'Thicket')
    check_flood_fill = True

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:    
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        blob_positions = flood_fill(tilemap, pos)
        left_most = min(p[0] for p in blob_positions)
        right_most = max(p[0] for p in blob_positions)
        top_most = min(p[1] for p in blob_positions)
        bottom_most = max(p[1] for p in blob_positions)
        # Extend to out of bounds when we are on a tilemap edge
        if left_most == 0 and right_most == tilemap.width - 1:
            left_most = -tilemap.width
            right_most = tilemap.width*2 - 1
        elif left_most == 0:
            left_most = -right_most
        elif right_most == tilemap.width - 1:
            right_most = left_most + 2*(tilemap.width - left_most)
        if top_most == 0 and bottom_most == tilemap.height - 1:
            top_most = -tilemap.height
            bottom_most = tilemap.height*2 - 1
        elif top_most == 0:
            top_most = -bottom_most
        elif bottom_most == tilemap.height - 1:
            bottom_most = top_most + 2*(tilemap.height - top_most)
        right_most += 1
        bottom_most += 1
        blob_width = (right_most - left_most)
        blob_height = (bottom_most - top_most)
        center_x = (right_most - left_most)/2 + left_most
        center_y = (bottom_most - top_most)/2 + top_most
        my_radius_width = abs(pos[0] + 0.5 - center_x)
        my_radius_height = abs(pos[1] + 0.5 - center_y)
        depth_w = (blob_width / 2) - my_radius_width
        depth_h = (blob_height / 2) - my_radius_height
        chance_w = utils.lerp(1, 0, depth_w/4)
        chance_h = utils.lerp(1, 0, depth_h/4)
        chance_to_lose_adjacent_edges = utils.clamp(max(chance_w, chance_h), 0, 1)

        north_edge = bool(north and north not in self.forest_like)  # Whether we don't border a forest
        if not north_edge and north and north != 'Thicket':  # We border a forest
            north_edge = (edge_random((pos[0], pos[1] - 1), pos) < chance_to_lose_adjacent_edges)
        east_edge = bool(east and east not in self.forest_like)
        if not east_edge and east and east != 'Thicket':  # We border a forest
            east_edge = (edge_random(pos, (pos[0] + 1, pos[1])) < chance_to_lose_adjacent_edges)
        south_edge = bool(south and south not in self.forest_like)
        if not south_edge and south and south != 'Thicket':  # We border a forest
            south_edge = (edge_random(pos, (pos[0], pos[1] + 1)) < chance_to_lose_adjacent_edges)
        west_edge = bool(west and west not in self.forest_like)
        if not west_edge and west and west != 'Thicket':  # We border a forest
            west_edge = (edge_random((pos[0] - 1, pos[1]), pos) < chance_to_lose_adjacent_edges)
        
        total_index = \
            north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        index1 = north_edge + 8 * west_edge
        index2 = north_edge + 2 * east_edge
        index3 = 4 * south_edge + 2 * east_edge
        index4 = 4 * south_edge + 8 * west_edge
        if total_index == 15 and random_choice([1, 2, 3], pos) != 3:  # When by itself
            new_coords1 = [(14, 0)]
            new_coords2 = [(15, 0)]
            new_coords3 = [(15, 1)]
            new_coords4 = [(14, 1)]
        else:
            new_coords1 = [(index1, {0: 0, 1: 0, 8: 0, 9: 0}[index1])]
            new_coords2 = [(index2, {0: 1, 1: 1, 2: 0, 3: 0}[index2])]
            new_coords3 = [(index3, {0: 3, 2: 1, 4: 1, 6: 0}[index3])]
            new_coords4 = [(index4, {0: 2, 4: 0, 8: 1, 12: 0}[index4])]
        return new_coords1, new_coords2, new_coords3, new_coords4

class HillTerrain(Terrain): 
    data = {'main': (12, 21), 'pair1': (13, 20), 'pair2': (14, 20), 'alter1': (13, 21)}
    check_flood_fill = True

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        _, east, _, west = tilemap.get_cardinal_terrain(pos)
        _, far_east, _, _ = tilemap.get_cardinal_terrain((pos[0] + 1, pos[1]))
        _, _, _, far_west = tilemap.get_cardinal_terrain((pos[0] - 1, pos[1]))
        if east != self.nid and west != self.nid:
            choice = random_choice([1, 2, 3, 4, 5, 6], pos)
            if choice <= 3:
                coord = self.data['main']
            elif choice in (4, 5):
                coord = self.data['alter1']
            else:
                coord = self.data['pair2']
        elif west != self.nid:
            coord = self.data['main']
        elif east != self.nid:
            if far_west == self.nid:
                coord = self.data['pair2']
            else:
                coord = self.data['pair1']
        else:
            coord = self.data['pair1']
        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

tileset = 'app/map_maker/rainlash_fields1.png'

Plains = RandomTerrain('Plains', 'Plains', tileset, (2, 2))
Plains.data = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (2, 4), (3, 4), (4, 4), (5, 4), (2, 5), (3, 5), (4, 5), (5, 5)]

Road = WangEdge2Terrain('Road', 'Road', 'app/map_maker/rainlash_fields1_road.png')
Road.terrain_like = ('Sand', 'Road')

Sand = SandTerrain('Sand', 'Sand', 'app/map_maker/rainlash_fields1_sand.png')

Forest = ForestTerrain('Forest', 'Forest', 'app/map_maker/rainlash_fields1_forest.png', (7, 0))

Thicket = RandomTerrain('Thicket', 'Thicket', tileset, (17, 22))
Thicket.data = [(17, 22), (18, 22), (19, 22), (17, 23), (18, 23), (19, 23), (18, 24), (19, 24), (18, 25)]

Hill = HillTerrain('Hill', 'Hill', tileset, (13, 21))

d = [Plains, Road, Sand, Forest, Thicket, Hill]
DB_terrain = TerrainCatalog(d)
