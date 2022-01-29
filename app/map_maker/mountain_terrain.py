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
            print(group)
            if not (group & tilemap.terrain_grid_to_update):
                # Don't need to bother updating this one if no intersections
                continue
            left_most, right_most, top_most, bottom_most, \
                width, height, center_x, center_y = \
                find_bounds(tilemap, group)
            top_rim = [pos for pos in group if (pos[0], pos[1] - 1) not in group]
            bottom_rim = [pos for pos in group if (pos[0], pos[1] + 1) not in group]
            if left_most < 0 and right_most >= tilemap.width:
                top_rim += [(-p[0], p[1]) for p in top_rim]
                top_rim += [(2*tilemap.width - p[0], p[1]) for p in top_rim]
                bottom_rim += [(-p[0], p[1]) for p in bottom_rim]
                bottom_rim += [(2*tilemap.width - p[0], p[1]) for p in bottom_rim]
            elif left_most < 0:
                top_rim += [(-p[0], p[1]) for p in top_rim]
                bottom_rim += [(-p[0], p[1]) for p in bottom_rim]
            elif right_most >= tilemap.width:
                top_rim += [(2*tilemap.width - p[0], p[1]) for p in top_rim]
                bottom_rim += [(2*tilemap.width - p[0], p[1]) for p in bottom_rim]
            top_rim = sorted(top_rim)
            bottom_rim = sorted(bottom_rim)

            if width < 4:
                creases = [0]
            else:
                creases = [_ for _ in range(0, width - 1, 3)]  # TODO
            # Build ridges
            ridges = []
            for crease in creases:
                current_pos = (crease + 0.5, top_rim[crease][1])
                current_direction = 'down'
                current_ridge = [current_pos]
                while True:
                    seed = (current_pos[0]*2, current_pos[1]*2)
                    if current_direction == 'down':
                        current_direction = random_choice(['down', 'down', 'dleft', 'dright'], seed)
                        current_pos = current_pos[0], current_pos[1] + .5
                    elif current_direction == 'dleft':
                        current_direction = random_choice(['down', 'down', 'down', 'dleft'], seed)
                        current_pos = current_pos[0] - 0.5, current_pos[1] + .5
                    elif current_direction == 'dright':
                        current_direction = random_choice(['down', 'down', 'down', 'dright'], seed)
                        current_pos = current_pos[0] + 0.5, current_pos[1] + .5
                    if (int(current_pos[0]), int(current_pos[1])) not in group:
                        break
                    current_ridge.append(current_pos)
                ridges.append(current_ridge)
            # Now actually assign sprites
            for pos in group:
                print(pos)
                # Find nearest ridge position
                ridge1 = self._find_nearest_ridge((pos[0], pos[1]), ridges)
                ridge2 = self._find_nearest_ridge((pos[0] + .5, pos[1]), ridges)
                ridge3 = self._find_nearest_ridge((pos[0] + .5, pos[1] + .5), ridges)
                ridge4 = self._find_nearest_ridge((pos[0], pos[1] + .5), ridges)                
                # direction of nearest ridge position determines whether sun or shadow
                sun1 = ridge1[0] > pos[0]
                sun2 = ridge2[0] > pos[0] + .5
                sun3 = ridge3[0] > pos[0] + .5
                sun4 = ridge4[0] > pos[0]
                # If adjacent to non-mountain, grass
                self.organization[pos] = (sun2, sun3, sun4, sun1)
                        
    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        corner_topright, corner_bottomright, corner_bottomleft, corner_topleft = self.organization[pos]
        index = 1 * corner_topright + \
            2 * corner_bottomright + \
            4 * corner_bottomleft + \
            8 * corner_topleft
        return index

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
        index = self._determine_index(tilemap, pos)
        new_coords = [(index, k) for k in range(self.limits[index])]

        # So it always uses the same set of coords...
        new_coords1 = [random_choice([(c[0]*2, c[1]*2) for c in new_coords], pos)]
        new_coords2 = [random_choice([(c[0]*2 + 1, c[1]*2) for c in new_coords], pos)]
        new_coords3 = [random_choice([(c[0]*2 + 1, c[1]*2 + 1) for c in new_coords], pos)]
        new_coords4 = [random_choice([(c[0]*2, c[1]*2 + 1) for c in new_coords], pos)]
        return new_coords1, new_coords2, new_coords3, new_coords4
