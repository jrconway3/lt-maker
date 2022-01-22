from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.map_maker.utilities import random_choice, edge_random, flood_fill
from app.map_maker.wang_terrain import WangCorner2Terrain

class CliffTerrain(WangCorner2Terrain):
    terrain_like = ('Cliff_Topleft', 'Cliff_Bottomright')
    organization = {}

    @property
    def check_flood_fill(self):
        return 'diagonal'

    def _find_longest_path(self, group: set) -> list:
        # https://stackoverflow.com/questions/21880419/how-to-find-the-longest-simple-path-in-a-graph
        path = []
        best_path = []
        used = set()

        def find_path(pos):
            nonlocal path
            nonlocal best_path
            used.add(pos)
            adj = {(pos[0] - 1, pos[1] - 1), (pos[0], pos[1] - 1), (pos[0] + 1, pos[1] - 1),
                   (pos[0] - 1, pos[1]), (pos[0] + 1, pos[1]),
                   (pos[0] - 1, pos[1] + 1), (pos[0], pos[1] + 1), (pos[0] + 1, pos[1] + 1)}
            for v in adj & group:
                if v not in used:
                    path.append(v)
                    if len(path) > len(best_path):
                        best_path = path[:]
                    find_path(v)
                    path.pop()
            used.discard(pos)

        for pos in group:
            path.append(pos)
            if len(path) > len(best_path):
                best_path = path[:]
            find_path(pos)
            path.pop()

        return best_path

    def _calc_corners(self, pos: tuple, partners: list) -> tuple:
        corner_topleft = False
        corner_bottomleft = False
        corner_topright = False
        corner_bottomright = False
        for other_pos in partners:
            # Topleft
            if other_pos[0] == pos[0] - 1 and other_pos[1] == pos[1] - 1:
                corner_topleft = True
            # Topright
            elif other_pos[0] == pos[0] + 1 and other_pos[1] == pos[1] - 1:
                corner_topright = True
            # Bottomleft
            elif other_pos[0] == pos[0] - 1 and other_pos[1] == pos[1] + 1:
                corner_bottomleft = True
            # Bottomright
            elif other_pos[0] == pos[0] + 1 and other_pos[1] == pos[1] + 1:
                corner_bottomright = True
            # Top
            elif other_pos[0] == pos[0] and other_pos[1] == pos[1] - 1:
                if edge_random(other_pos, pos) < 0.5:
                    corner_topleft = True
                else:
                    corner_topright = True
            # Bottom
            elif other_pos[0] == pos[0] and other_pos[1] == pos[1] + 1:
                if edge_random(pos, other_pos) < 0.5:
                    corner_bottomleft = True
                else:
                    corner_bottomright = True
            # Left
            elif other_pos[0] == pos[0] - 1 and other_pos[1] == pos[1]:
                if edge_random(other_pos, pos) < 0.5:
                    corner_topleft = True
                else:
                    corner_bottomleft = True
            # Right
            elif other_pos[0] == pos[0] + 1 and other_pos[1] == pos[1]:
                if edge_random(pos, other_pos) < 0.5:
                    corner_topright = True
                else:
                    corner_bottomright = True
        return corner_topright, corner_bottomright, corner_bottomleft, corner_topleft

    def _chain_end_process(self, pos: tuple, other_pos: tuple) -> tuple:
        topright, bottomright, bottomleft, topleft = \
            self._calc_corners(pos, [other_pos])
        if topright:
            bottomleft = True
        elif bottomright:
            topleft = True
        elif topleft:
            bottomright = True
        elif bottomleft:
            topright = True

        return topright, bottomright, bottomleft, topleft

    def single_process(self, tilemap):
        match_set: set = {'Cliff_Topleft', 'Cliff_Bottomright'}
        positions: set = tilemap.get_all_terrain('Cliff_Topleft')
        positions |= tilemap.get_all_terrain('Cliff_Bottomright')
        self.organization.clear()
        groupings: list = [] # of sets
        while positions:
            pos = positions.pop()
            near_positions: set = flood_fill(tilemap, pos, diagonal=True, match=match_set)
            groupings.append(near_positions)
            for near_pos in near_positions:
                positions.discard(near_pos)

        while groupings:
            group = groupings.pop()
            if not (group & tilemap.terrain_grid_to_update):
                # Don't need to bother updating this one if no intersections
                continue
            longest_path: list = self._find_longest_path(group)

            # Handle the case where the longest path does not include some members of the group
            present = set(longest_path)
            new_group = group - present  # The leftovers become a new group
            if new_group:
                groupings.append(new_group)

            # now that we have longest path, we can fill in according to rules
            for idx, pos in list(enumerate(longest_path))[1:-1]:  # Skip first
                prev_pos = longest_path[idx - 1]              
                next_pos = longest_path[idx + 1]
                topright, bottomright, bottomleft, topleft = \
                    self._calc_corners(pos, [prev_pos, next_pos])
                
                self.organization[pos] = (topright, bottomright, bottomleft, topleft)
            # For first and last path
            if len(longest_path) > 1:
                self.organization[longest_path[0]] = self._chain_end_process(longest_path[0], longest_path[1])
                self.organization[longest_path[-1]] = self._chain_end_process(longest_path[-1], longest_path[-2])
            else:
                self.organization[longest_path[0]] = (True, False, False, True)  # Facing down

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        corner_topright, corner_bottomright, corner_bottomleft, corner_topleft = self.organization[pos]
        index = 1 * corner_topright + \
            2 * corner_bottomright + \
            4 * corner_bottomleft + \
            8 * corner_topleft
        return index

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
