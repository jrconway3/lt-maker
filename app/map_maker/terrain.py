import os
from dataclasses import dataclass

from PyQt5.QtGui import QPixmap

from app.constants import TILEWIDTH, TILEHEIGHT, AUTOTILE_FRAMES
from app.utilities.data import Data, Prefab

@dataclass
class Terrain(Prefab):
    nid: str = None
    name: str = None
    palette_path: str = None
    tileset_path: str = None

    display_tile_coord: tuple = (0, 0)

    display_pixmap: QPixmap = None
    tileset_pixmap: QPixmap = None

    autotiles: dict = None
    autotile_pixmap: QPixmap = None

    def has_autotiles(self):
        return self.autotiles and self.autotile_pixmap

    @property
    def check_flood_fill(self):
        return False

    def set_tileset(self):
        full_path = os.path.join(self.palette_path, self.tileset_path)
        self.tileset_pixmap = QPixmap(full_path)
        autotile_path = full_path[:-4] + '_autotiles.png'
        if os.path.exists(autotile_path):
            self.autotile_pixmap = QPixmap(autotile_path)
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

    def determine_sprite(self, tilemap, pos: tuple, ms: float, autotile_fps: float) -> QPixmap:
        coord = self.display_tile_coord
        return self.get_pixmap(coord, ms, autotile_fps)

    def get_pixmap(self, tile_coord: tuple, ms: float, autotile_fps: float) -> QPixmap:
        if autotile_fps and self.has_autotiles() and tile_coord in self.autotiles:
            column = self.autotiles[tile_coord]
            autotile_wait = autotile_fps * 16.66
            num = int(ms / autotile_wait) % AUTOTILE_FRAMES
            pix = self.autotile_pixmap.copy(
                column * TILEWIDTH, 
                num * TILEHEIGHT, 
                TILEWIDTH, TILEHEIGHT)
        else:
            pix = self.tileset_pixmap.copy(
                tile_coord[0] * TILEWIDTH,
                tile_coord[1] * TILEHEIGHT,
                TILEWIDTH, TILEHEIGHT)
        return pix

    def single_process(self, tilemap):
        pass

class TerrainCatalog(Data[Terrain]):
    datatype = Terrain
