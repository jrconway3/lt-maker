from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.map_maker.utilities import random_choice, edge_random, get_random_seed
from app.map_maker.wang_terrain import WangEdge2Terrain
from app.utilities import utils

class SeaTerrain(WangEdge2Terrain):
    terrain_like = ('Sea', 'River', 'BridgeH', 'BridgeV')
    sand_tileset_path = None
    sand_tileset_pixmap = None
    serration_chance = 0.6

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

    def _determine_index(self, tilemap, pos: tuple) -> int:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        return index

    def _modify_index(self, index: int, tilemap, pos: tuple) -> int:
        # For randomly serrating the straight edges of the sea
        odd = bool((pos[0] + pos[1] + get_random_seed()) % 2)
        even = not odd
        # Left
        if index == 13:
            if odd and self._determine_index(tilemap, (pos[0], pos[1] - 1)) == 13 and edge_random((pos[0], pos[1] - 1), pos) < self.serration_chance:
                index = 12
            elif even and self._determine_index(tilemap, (pos[0], pos[1] + 1)) == 13 and edge_random(pos, (pos[0], pos[1] + 1)) < self.serration_chance:
                index = 9
            # Right
        elif index == 7:
            if odd and self._determine_index(tilemap, (pos[0], pos[1] - 1)) == 7 and edge_random((pos[0], pos[1] - 1), pos) < self.serration_chance:
                index = 6
            elif even and self._determine_index(tilemap, (pos[0], pos[1] + 1)) == 7 and edge_random(pos, (pos[0], pos[1] + 1)) < self.serration_chance:
                index = 3
        # Top
        elif index == 11:
            if odd and self._determine_index(tilemap, (pos[0] - 1, pos[1])) == 11 and edge_random((pos[0] - 1, pos[1]), pos) < self.serration_chance:
                index = 3
            elif even and self._determine_index(tilemap, (pos[0] + 1, pos[1])) == 11 and edge_random(pos, (pos[0] + 1, pos[1])) < self.serration_chance:
                index = 9
        # Bottom
        elif index == 14:
            if odd and self._determine_index(tilemap, (pos[0] - 1, pos[1])) == 14 and edge_random((pos[0] - 1, pos[1]), pos) < self.serration_chance:
                index = 6
            elif even and self._determine_index(tilemap, (pos[0] + 1, pos[1])) == 14 and edge_random(pos, (pos[0] + 1, pos[1])) < self.serration_chance:
                index = 12

        return index

    def _distance_to_closest(self, tilemap, pos: tuple) -> float:
        min_distance = 99
        for other_pos in tilemap.terrain_grid.keys():
            if tilemap.get_terrain(other_pos) not in ('Sea', 'BridgeV', 'BridgeH'):
                distance = utils.distance(pos, other_pos)
                if distance < min_distance:
                    min_distance = distance
        return min_distance

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        index = self._determine_index(tilemap, pos)
        index = self._modify_index(index, tilemap, pos)
        if index == 15 and self._distance_to_closest(tilemap, pos) > 2:  # Open Sea
            # Measure distance to closest non sea, bridge terrain
            new_coords = [(0, k) for k in range(2, 9)]
        else:
            new_coords = [(index, k) for k in range(self.limits[index])]

        # So it always uses the same set of coords...
        new_coords1 = [random_choice([(c[0]*2, c[1]*2) for c in new_coords], pos)]
        new_coords2 = [random_choice([(c[0]*2 + 1, c[1]*2) for c in new_coords], pos)]
        new_coords3 = [random_choice([(c[0]*2 + 1, c[1]*2 + 1) for c in new_coords], pos)]
        new_coords4 = [random_choice([(c[0]*2, c[1]*2 + 1) for c in new_coords], pos)]
        return new_coords1, new_coords2, new_coords3, new_coords4
