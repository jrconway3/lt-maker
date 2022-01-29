import math

from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.map_maker.utilities import random_choice, flood_fill, find_bounds
from app.utilities import utils
from app.map_maker.wang_terrain import WangCorner2Terrain

class MountainTerrain(WangCorner2Terrain):
    terrain_like = ('Mountain')
    organization = {}

    @property
    def check_flood_fill(self):
        return True

    def single_process(self, tilemap):
        positions: set = tilemap.get_all_terrain(self.nid)
        self.organization.clear()
        groupings: list = [] # of sets
        counter: int = 0
        while positions and counter < 99999:
            pos = positions.pop()
            near_positions: set = flood_fill(tilemap, pos)
            groupings.append(near_positions)
            for near_pos in near_positions:
                positions.discard(near_pos)
            counter += 1
        if counter >= 99999:
            raise RuntimeError("Unexpected infinite loop in cliff flood_fill")

        while groupings:
            group = groupings.pop()
            if not (group & tilemap.terrain_grid_to_update):
                # Don't need to bother updating this one if no intersections
                continue

            self.process_group(group)

    def get_display_pixmap(self):
        if not self.display_pixmap:
            main_pix = QPixmap(16, 16)
            painter = QPainter()
            painter.begin(main_pix)
            painter.drawPixmap(0, 0, self.tileset_pixmap.copy(TILEWIDTH * 15, TILEHEIGHT * 8, TILEWIDTH, TILEHEIGHT))
            painter.end()
            self.display_pixmap = main_pix
        return self.display_pixmap

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords = self.organization[pos]
        new_coords1 = new_coords[0]*2, new_coords[1]*2
        new_coords2 = new_coords[0]*2 + 1, new_coords[1]*2
        new_coords3 = new_coords[0]*2 + 1, new_coords[1]*2 + 1
        new_coords4 = new_coords[0]*2, new_coords[1]*2 + 1
        return new_coords1, new_coords2, new_coords3, new_coords4

    def process_group(self, group: set):
        pass