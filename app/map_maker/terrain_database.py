import random
from dataclasses import dataclass

from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities.data import Data, Prefab

@dataclass
class Terrain(Prefab):
    nid: str = None
    name: str = None
    tileset_path: str = None

    display_tile_coord: tuple = (0, 0)

    display_pixmap: QPixmap = None
    tileset_pixmap: QPixmap = None

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
            painter.drawPixmap(0, 0, self.tileset_pixmap.copy(0, 0 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(0, TILEHEIGHT//2, self.tileset_pixmap.copy(0, 1 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, 0, self.tileset_pixmap.copy(0, 2 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, TILEHEIGHT//2, self.tileset_pixmap.copy(0, 3 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.end()
            self.display_pixmap = main_pix
        return self.display_pixmap

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        index1 = \
            bool(north and north != self.nid) + \
            8 * bool(west and west != self.nid)
        index2 = \
            bool(north and north != self.nid) + \
            2 * bool(east and east != self.nid)
        index3 = \
            4 * bool(south and south != self.nid) + \
            2 * bool(east and east != self.nid)
        index4 = \
            4 * bool(south and south != self.nid) + \
            8 * bool(west and west != self.nid)
        new_coords1 = [(index1, k) for k in range(self.limits[index1])]
        new_coords2 = [(index2, k) for k in range(self.limits[index2])]
        new_coords3 = [(index3, k) for k in range(self.limits[index3])]
        new_coords4 = [(index4, k) for k in range(self.limits[index4])]
        return new_coords1, new_coords2, new_coords3, new_coords4

class ForestTerrain(Terrain):
    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:    
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        forest_like = ('Forest', 'Thicket')
        total_index = \
            bool(north and north not in forest_like) + \
            2 * bool(east and east not in forest_like) + \
            4 * bool(south and south not in forest_like) + \
            8 * bool(west and west not in forest_like)
        index1 = \
            bool(north and north not in forest_like) + \
            8 * bool(west and west not in forest_like)
        index2 = \
            bool(north and north not in forest_like) + \
            2 * bool(east and east not in forest_like)
        index3 = \
            4 * bool(south and south not in forest_like) + \
            2 * bool(east and east not in forest_like)
        index4 = \
            4 * bool(south and south not in forest_like) + \
            8 * bool(west and west not in forest_like)
        if total_index == 15 and random.choice([1, 2, 3]) != 3:  # When by itself
            new_coords1 = [(14, 0)]
            new_coords2 = [(15, 0)]
            new_coords3 = [(15, 1)]
            new_coords4 = [(14, 1)]
        elif total_index in (7, 11, 13, 14) and random.choice([1, 2]) == 2:  # When at the edge of a treeline
            new_coords1 = [(14, 0)]
            new_coords2 = [(15, 0)]
            new_coords3 = [(15, 1)]
            new_coords4 = [(14, 1)]
        elif total_index in (1, 2, 3, 4, 6, 8, 9, 12) and random.choice([1, 2, 3, 4]) == 4:  # When at the corner of a treeline
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

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        _, east, _, west = tilemap.get_cardinal_terrain(pos)
        _, far_east, _, _ = tilemap.get_cardinal_terrain((pos[0] + 1, pos[1]))
        _, _, _, far_west = tilemap.get_cardinal_terrain((pos[0] - 1, pos[1]))
        if east != self.nid and west != self.nid:
            choice = random.choice([1, 2, 3, 4, 5, 6])
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

Forest = ForestTerrain('Forest', 'Forest', 'app/map_maker/rainlash_fields1_forest.png', (7, 0))

Thicket = RandomTerrain('Thicket', 'Thicket', tileset, (17, 22))
Thicket.data = [(17, 22), (18, 22), (19, 22), (17, 23), (18, 23), (19, 23), (18, 24), (19, 24), (18, 25)]

Hill = HillTerrain('Hill', 'Hill', tileset, (13, 21))

d = [Plains, Road, Forest, Thicket, Hill]
DB_terrain = TerrainCatalog(d)
