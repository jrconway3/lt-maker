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

    # Extra database information
    regular: list = None
    wang_edge2: bool = False
    wang_edge2_limits: dict = None
    # For forests only
    forest: bool = False
    subforests: set = None

    def set_tileset(self, tileset_path=None):
        if tileset_path:
            self.tileset_path = tileset_path
        self.tileset_pixmap = QPixmap(self.tileset_path)
        self.display_pixmap = None
        self.get_display_pixmap()

        # Find limits for wang tiles
        if self.wang_edge2:
            self.wang_edge2_limits = {k: self._find_limit(k) for k in range(16)}
            print(self.nid, self.wang_edge2_limits)

    def get_display_pixmap(self):
        if not self.display_pixmap:
            if self.wang_edge2:
                main_pix = QPixmap(16, 16)
                painter = QPainter()
                painter.begin(main_pix)
                painter.drawPixmap(0, 0, self.tileset_pixmap.copy(0, 0 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
                painter.drawPixmap(0, TILEHEIGHT//2, self.tileset_pixmap.copy(0, 1 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
                painter.drawPixmap(TILEWIDTH//2, 0, self.tileset_pixmap.copy(0, 2 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
                painter.drawPixmap(TILEWIDTH//2, TILEHEIGHT//2, self.tileset_pixmap.copy(0, 3 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
                painter.end()
                self.display_pixmap = main_pix
            else:
                pix = self.tileset_pixmap.copy(
                    self.display_tile_coord[0] * TILEWIDTH, 
                    self.display_tile_coord[1] * TILEHEIGHT,
                    TILEWIDTH, TILEHEIGHT)
                self.display_pixmap = pix
        return self.display_pixmap

    def _find_limit(self, idx: int) -> int:
        bg_color = qRgb(0, 0, 0)
        img = self.tileset_pixmap.toImage()
        x = idx * TILEWIDTH//2
        for y in range(0, img.height(), TILEHEIGHT//2):
            current_color = img.pixel(x, y)
            if current_color == bg_color:
                return y // (TILEHEIGHT//2)
        return (img.height() // (TILEHEIGHT//2))
        
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
Road = Terrain('Road', 'Road', 'app/map_maker/rainlash_fields1_road.png')
Road.wang_edge2 = True

Forest = Terrain('Forest', 'Forest', 'app/map_maker/rainlash_fields1_forest.png', (16, 22))
Forest.wang_edge2 = True
Forest.forest = True
Forest.subforests = set()
Thicket = Terrain('Thicket', 'Thicket', tileset, (17, 22))

d = [Plains, Road, Forest, Thicket]
DB_terrain = TerrainCatalog(d)
