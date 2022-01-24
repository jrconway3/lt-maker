from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.map_maker.utilities import random_choice
from app.map_maker.wang_terrain import WangEdge2Terrain

class SeaTerrain(WangEdge2Terrain):
    terrain_like = ('Sea', 'River', 'BridgeH', 'BridgeV')
    sand_tileset_path = None
    sand_tileset_pixmap = None

    def set_sand_tileset(self, tileset_path):
        self.sand_tileset_path = tileset_path

    @property
    def check_flood_fill(self):
        return True

    def _find_limit(self, idx: int) -> int:
        bg_color = qRgb(0, 0, 0)
        img = self.tileset_pixmap.toImage()
        x = idx * TILEWIDTH
        for y in range(0, img.height(), TILEHEIGHT):
            current_color = img.pixel(x, y)
            if current_color == bg_color:
                return y // TILEHEIGHT
        return (img.height() // TILEHEIGHT)

    def get_display_pixmap(self):
        if not self.display_pixmap:
            main_pix = QPixmap(16, 16)
            painter = QPainter()
            painter.begin(main_pix)
            painter.drawPixmap(0, 0, self.tileset_pixmap.copy(TILEWIDTH * 15, 0, TILEWIDTH, TILEHEIGHT))
            painter.end()
            self.display_pixmap = main_pix
            self.sand_tileset_pixmap = QPixmap(self.sand_tileset_path)
        return self.display_pixmap

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        return 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        index = self._determine_index(tilemap, pos)
        new_coords = [(index, k) for k in range(self.limits[index])]

        # So it always uses the same set of coords...
        new_coords1 = [random_choice([(c[0]*2, c[1]*2) for c in new_coords], pos)]
        new_coords2 = [random_choice([(c[0]*2 + 1, c[1]*2) for c in new_coords], pos)]
        new_coords3 = [random_choice([(c[0]*2 + 1, c[1]*2 + 1) for c in new_coords], pos)]
        new_coords4 = [random_choice([(c[0]*2, c[1]*2 + 1) for c in new_coords], pos)]
        return new_coords1, new_coords2, new_coords3, new_coords4
