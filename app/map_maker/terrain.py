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

    @property
    def check_flood_fill(self):
        return False

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

    def single_process(self, tilemap):
        pass

class TerrainCatalog(Data[Terrain]):
    datatype = Terrain
