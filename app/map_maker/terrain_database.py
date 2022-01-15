import random
from dataclasses import dataclass

from PyQt5.QtGui import QPixmap

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

    # Extra database information
    regular: list = None

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

class TerrainCatalog(Data[Terrain]):
    datatype = Terrain

tileset = 'app/map_maker/rainlash_fields1.png'

Plains = Terrain('Plains', 'Plains', tileset, (2, 2))
Plains.regular = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (2, 4), (3, 4), (4, 4), (5, 4), (2, 5), (3, 5), (4, 5), (5, 5)]
Road = Terrain('Road', 'Road', tileset, (20, 22))
Forest = Terrain('Forest', 'Forest', tileset, (16, 22))
Thicket = Terrain('Thicket', 'Thicket', tileset, (17, 22))

d = [Plains, Road, Forest, Thicket]
DB_terrain = TerrainCatalog(d)
