import itertools

from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
import app.utilities as utils
from app.map_maker.utilities import random_choice, random_random, edge_random, flood_fill
from app.map_maker.terrain import Terrain, TerrainCatalog
from app.map_maker.building_terrain import CastleTerrain, HouseTerrain, RuinsTerrain

class RandomTerrain(Terrain):
    data = []

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords1 = [(p[0]*2, p[1]*2) for p in self.data]
        new_coords2 = [(p[0]*2 + 1, p[1]*2) for p in self.data]
        new_coords3 = [(p[0]*2 + 1, p[1]*2 + 1) for p in self.data]
        new_coords4 = [(p[0]*2, p[1]*2 + 1) for p in self.data]
        return new_coords1, new_coords2, new_coords3, new_coords4

class WangEdge2Terrain(Terrain):
    terrain_like = ()

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
            painter.drawPixmap(0, 0, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 0 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(0, TILEHEIGHT//2, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 1 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, 0, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 2 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, TILEHEIGHT//2, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 3 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.end()
            self.display_pixmap = main_pix
        return self.display_pixmap

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index1 = 6 + 1 * north_edge + 8 * west_edge
        index2 = 12 + 1 * north_edge + 2 * east_edge
        index3 = 9 + 4 * south_edge + 2 * east_edge
        index4 = 3 + 4 * south_edge + 8 * west_edge
        new_coords1 = [(index1, k) for k in range(self.limits[index1])]
        new_coords2 = [(index2, k) for k in range(self.limits[index2])]
        new_coords3 = [(index3, k) for k in range(self.limits[index3])]
        new_coords4 = [(index4, k) for k in range(self.limits[index4])]
        return new_coords1, new_coords2, new_coords3, new_coords4

class WangCorner2Terrain(WangEdge2Terrain):
    terrain_like = ()

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index1 = 1 * north_edge + \
            2 * True + \
            4 * west_edge + \
            8 * (bool(not northwest or northwest in self.terrain_like) and north_edge and west_edge)
        index2 = 1 * (bool(not northeast or northeast in self.terrain_like) and north_edge and east_edge) + \
            2 * east_edge + \
            4 * True + \
            8 * north_edge
        index3 = 1 * east_edge + \
            2 * (bool(not southeast or southeast in self.terrain_like) and south_edge and east_edge) + \
            4 * south_edge + \
            8 * True
        index4 = 1 * True + \
            2 * south_edge + \
            4 * (bool(not southwest or southwest in self.terrain_like) and south_edge and west_edge) + \
            8 * west_edge
        return index1, index2, index3, index4

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        index1, index2, index3, index4 = self._determine_index(tilemap, pos)
        new_coords1 = [(index1, k) for k in range(self.limits[index1])]
        new_coords2 = [(index2, k) for k in range(self.limits[index2])]
        new_coords3 = [(index3, k) for k in range(self.limits[index3])]
        new_coords4 = [(index4, k) for k in range(self.limits[index4])]
        return new_coords1, new_coords2, new_coords3, new_coords4

class SandTerrain(WangCorner2Terrain):
    terrain_like = ('Sand', 'Road')
    corner_chance = 0.6
    edge_chance = 0.4
    vertices: dict = {}

    def _pos_to_vertices(self, pos) -> tuple:
        center_vertex_pos = pos[0]*2 + 1, pos[1]*2 + 1
        left_vertex_pos = pos[0]*2, pos[1]*2 + 1
        right_vertex_pos = pos[0]*2 + 2, pos[1]*2 + 1
        top_vertex_pos = pos[0]*2 + 1, pos[1]*2
        bottom_vertex_pos = pos[0]*2 + 1, pos[1]*2 + 2
        topleft_vertex_pos = pos[0]*2, pos[1]*2
        topright_vertex_pos = pos[0]*2 + 2, pos[1]*2
        bottomleft_vertex_pos = pos[0]*2, pos[1]*2 + 2
        bottomright_vertex_pos = pos[0]*2 + 2, pos[1]*2 + 2
        return center_vertex_pos, left_vertex_pos, right_vertex_pos, \
            top_vertex_pos, bottom_vertex_pos, topleft_vertex_pos, \
            topright_vertex_pos, bottomleft_vertex_pos, bottomright_vertex_pos

    def single_process(self, tilemap):
        # For each vertex, assign a random value
        # Then go through each vertex and determine if corner, edge, or neither
        # Check values for each vertex to decide if it should be removed
        # Save data somewhere
        positions: set = tilemap.get_all_terrain(self.nid)
        self.vertices.clear()
        for pos in positions:
            north, east, south, west = tilemap.get_cardinal_terrain(pos)
            north_edge = bool(not north or north in self.terrain_like)
            south_edge = bool(not south or south in self.terrain_like)
            east_edge = bool(not east or east in self.terrain_like)
            west_edge = bool(not west or west in self.terrain_like)
            northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
            northeast_edge = bool(not northeast or northeast in self.terrain_like)
            southeast_edge = bool(not southeast or southeast in self.terrain_like)
            southwest_edge = bool(not southwest or southwest in self.terrain_like)
            northwest_edge = bool(not northwest or northwest in self.terrain_like)
            # 0 is patch
            # 1 is end
            # 2 is corner (unless north and south or east and west, then end)
            # 3 is edge
            # 4 is center
            center_vertex_type = sum((north_edge, south_edge, east_edge, west_edge))
            if center_vertex_type == 2 and ((north_edge and south_edge) or (east_edge and west_edge)):
                center_vertex_type = 1
            # if not north: 0
            # if north: 0
            # if north and ((east and northeast) or (west and northwest)): edge
            # if north and both: center
            left_vertex_type = west_edge + (south_edge and southwest_edge) + (north_edge and northwest_edge)
            if left_vertex_type == 3:
                left_vertex_type = 4
            elif left_vertex_type == 2 and west_edge:
                left_vertex_type = 3
            else:
                left_vertex_type = west_edge
            right_vertex_type = east_edge + (south_edge and southeast_edge) + (north_edge and northeast_edge)
            if right_vertex_type == 3:
                right_vertex_type = 4
            elif right_vertex_type == 2 and east_edge:
                right_vertex_type = 3
            else:
                right_vertex_type = east_edge
            top_vertex_type = north_edge + (west_edge and northwest_edge) + (east_edge and northeast_edge)
            if top_vertex_type == 3:
                top_vertex_type = 4
            elif top_vertex_type == 2 and north_edge:
                top_vertex_type = 3
            else:
                top_vertex_type = north_edge
            bottom_vertex_type = south_edge + (west_edge and southwest_edge) + (east_edge and southeast_edge)
            if bottom_vertex_type == 3:
                bottom_vertex_type = 4
            elif bottom_vertex_type == 2 and south_edge:
                bottom_vertex_type = 3
            else:
                bottom_vertex_type = south_edge
            # 0 is not possible
            # 1 is empty
            # 2 is empty
            # 3 is empty
            # 4 is center
            topleft_vertex_type = 4 if (1 + sum((north_edge, west_edge, northwest_edge))) == 4 else 0
            bottomleft_vertex_type = 4 if (1 + sum((south_edge, west_edge, southwest_edge))) == 4 else 0
            topright_vertex_type = 4 if (1 + sum((north_edge, east_edge, northeast_edge))) == 4 else 0
            bottomright_vertex_type = 4 if (1 + sum((south_edge, east_edge, southeast_edge))) == 4 else 0

            center, left, right, top, bottom, topleft, topright, bottomleft, bottomright = self._pos_to_vertices(pos)

            self.vertices[center] = (center_vertex_type, random_random(center))
            self.vertices[left] = (left_vertex_type, random_random(left))
            self.vertices[right] = (right_vertex_type, random_random(right))
            self.vertices[top] = (top_vertex_type, random_random(top))
            self.vertices[bottom] = (bottom_vertex_type, random_random(bottom))
            self.vertices[topleft] = (topleft_vertex_type, random_random(topleft))
            self.vertices[topright] = (topright_vertex_type, random_random(topright))
            self.vertices[bottomleft] = (bottomleft_vertex_type, random_random(bottomleft))
            self.vertices[bottomright] = (bottomright_vertex_type, random_random(bottomright))

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        center, left, right, top, bottom, topleft, topright, bottomleft, bottomright = self._pos_to_vertices(pos)
        center_edge = True
        left_edge = bool(self.vertices[left][0])
        right_edge = bool(self.vertices[right][0])
        top_edge = bool(self.vertices[top][0])
        bottom_edge = bool(self.vertices[bottom][0])
        topleft_edge = bool(self.vertices[topleft][0])
        topright_edge = bool(self.vertices[topright][0])
        bottomleft_edge = bool(self.vertices[bottomleft][0])
        bottomright_edge = bool(self.vertices[bottomright][0])
        # Randomly determine some to remove
        if self.vertices[center][0] == 3 and self.vertices[center][1] < self.edge_chance:
            center_edge = False
        if self.vertices[center][0] == 2 and self.vertices[center][1] < self.corner_chance:
            center_edge = False
        if self.vertices[left][0] in (2, 3) and self.vertices[left][1] < self.edge_chance:
            left_edge = False
        if self.vertices[right][0] in (2, 3) and self.vertices[right][1] < self.edge_chance:
            right_edge = False
        if self.vertices[top][0] in (2, 3) and self.vertices[top][1] < self.edge_chance:
            top_edge = False
        if self.vertices[bottom][0] in (2, 3) and self.vertices[bottom][1] < self.edge_chance:
            bottom_edge = False

        index1 = 1 * top_edge + \
            2 * center_edge + \
            4 * left_edge + \
            8 * topleft_edge
        index2 = 1 * topright_edge + \
            2 * right_edge + \
            4 * center_edge + \
            8 * top_edge
        index3 = 1 * right_edge + \
            2 * bottomright_edge + \
            4 * bottom_edge + \
            8 * center_edge
        index4 = 1 * center_edge + \
            2 * bottom_edge + \
            4 * bottomleft_edge + \
            8 * left_edge
        return index1, index2, index3, index4

class ForestTerrain(Terrain):
    forest_like = ('Forest', 'Thicket')
    
    @property
    def check_flood_fill(self):
        return True

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:    
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        blob_positions = flood_fill(tilemap, pos)
        left_most = min(p[0] for p in blob_positions)
        right_most = max(p[0] for p in blob_positions)
        top_most = min(p[1] for p in blob_positions)
        bottom_most = max(p[1] for p in blob_positions)
        # Extend to out of bounds when we are on a tilemap edge
        if left_most == 0 and right_most == tilemap.width - 1:
            left_most = -tilemap.width
            right_most = tilemap.width*2 - 1
        elif left_most == 0:
            left_most = -right_most
        elif right_most == tilemap.width - 1:
            right_most = left_most + 2*(tilemap.width - left_most)
        if top_most == 0 and bottom_most == tilemap.height - 1:
            top_most = -tilemap.height
            bottom_most = tilemap.height*2 - 1
        elif top_most == 0:
            top_most = -bottom_most
        elif bottom_most == tilemap.height - 1:
            bottom_most = top_most + 2*(tilemap.height - top_most)
        right_most += 1
        bottom_most += 1
        blob_width = (right_most - left_most)
        blob_height = (bottom_most - top_most)
        center_x = (right_most - left_most)/2 + left_most
        center_y = (bottom_most - top_most)/2 + top_most
        my_radius_width = abs(pos[0] + 0.5 - center_x)
        my_radius_height = abs(pos[1] + 0.5 - center_y)
        depth_w = (blob_width / 2) - my_radius_width
        depth_h = (blob_height / 2) - my_radius_height
        chance_w = utils.lerp(1, 0, depth_w/4)
        chance_h = utils.lerp(1, 0, depth_h/4)
        chance_to_lose_adjacent_edges = utils.clamp(max(chance_w, chance_h), 0, 1)

        north_edge = bool(north and north not in self.forest_like)  # Whether we don't border a forest
        if not north_edge and north and north != 'Thicket':  # We border a forest
            north_edge = (edge_random((pos[0], pos[1] - 1), pos) < chance_to_lose_adjacent_edges)
        east_edge = bool(east and east not in self.forest_like)
        if not east_edge and east and east != 'Thicket':  # We border a forest
            east_edge = (edge_random(pos, (pos[0] + 1, pos[1])) < chance_to_lose_adjacent_edges)
        south_edge = bool(south and south not in self.forest_like)
        if not south_edge and south and south != 'Thicket':  # We border a forest
            south_edge = (edge_random(pos, (pos[0], pos[1] + 1)) < chance_to_lose_adjacent_edges)
        west_edge = bool(west and west not in self.forest_like)
        if not west_edge and west and west != 'Thicket':  # We border a forest
            west_edge = (edge_random((pos[0] - 1, pos[1]), pos) < chance_to_lose_adjacent_edges)
        
        total_index = \
            north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        index1 = north_edge + 8 * west_edge
        index2 = north_edge + 2 * east_edge
        index3 = 4 * south_edge + 2 * east_edge
        index4 = 4 * south_edge + 8 * west_edge
        if total_index == 15 and random_choice([1, 2, 3], pos) != 3:  # When by itself
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
    
    @property
    def check_flood_fill(self):
        return True

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        _, east, _, west = tilemap.get_cardinal_terrain(pos)
        _, far_east, _, _ = tilemap.get_cardinal_terrain((pos[0] + 1, pos[1]))
        _, _, _, far_west = tilemap.get_cardinal_terrain((pos[0] - 1, pos[1]))
        if east != self.nid and west != self.nid:
            choice = random_choice([1, 2, 3, 4, 5, 6], pos)
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

class CliffTerrain(WangCorner2Terrain):
    terrain_like = ('Cliff_Topleft', 'Cliff_Bottomright')
    organization = {}

    @property
    def check_flood_fill(self):
        return 'diagonal'

    # def _find_longest_path(self, group: set) -> list:
    #     Permutation brute force. Far too slow
    #     def is_adjacent(seq: list) -> bool:
    #         _abs = abs
    #         curr_pos: tuple = seq[0]
    #         for link in seq[1:]:
    #             if _abs(curr_pos[0] - link[0]) <= 1 and _abs(curr_pos[0] - link[0]) <= 1:
    #                 curr_pos = link
    #             else:
    #                 return False
    #         return True

    #     permutations = itertools.permutations(group)
    #     for permutation in permutations:
    #         if is_adjacent(permutation):
    #             return permutation

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
                corner_topleft = True
            # Bottom
            elif other_pos[0] == pos[0] and other_pos[1] == pos[1] + 1:
                corner_bottomleft = True
            # Left
            elif other_pos[0] == pos[0] - 1 and other_pos[1] == pos[1]:
                corner_topleft = True
            # Right
            elif other_pos[0] == pos[0] + 1 and other_pos[1] == pos[1]:
                corner_topright = True
        return corner_topright, corner_bottomright, corner_bottomleft, corner_topleft

    def _chain_end_process(self, pos: tuple, other_pos: tuple) -> tuple:
        topright, bottomright, bottomleft, topleft = \
            self._calc_corners(pos, [other_pos])
        corner_topright = False
        corner_topleft = False
        corner_bottomleft = False
        corner_bottomright = False
        if topright:
            corner_topright = True
            corner_bottomleft = True
        elif bottomright:
            corner_bottomright = True
            corner_topleft = True
        elif topleft:
            corner_topleft = True
            corner_bottomright = True
        elif bottomleft:
            corner_bottomleft = True
            corner_topright = True

        return corner_topright, corner_bottomright, corner_bottomleft, corner_topleft

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
                
tileset = 'app/map_maker/rainlash_fields1.png'

Plains = RandomTerrain('Plains', 'Plains', tileset, (2, 2))
Plains.data = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (2, 4), (3, 4), (4, 4), (5, 4), (2, 5), (3, 5), (4, 5), (5, 5)]

Road = WangEdge2Terrain('Road', 'Road', 'app/map_maker/rainlash_fields1_road.png')
Road.terrain_like = ('Sand', 'Road')

Sand = SandTerrain('Sand', 'Sand', 'app/map_maker/rainlash_fields1_sand.png')

Forest = ForestTerrain('Forest', 'Forest', 'app/map_maker/rainlash_fields1_forest.png', (7, 0))

Thicket = RandomTerrain('Thicket', 'Thicket', tileset, (17, 22))
Thicket.data = [(17, 22), (18, 22), (19, 22), (17, 23), (18, 23), (19, 23), (18, 24), (19, 24), (18, 25)]

Hill = HillTerrain('Hill', 'Hill', tileset, (13, 21))

Cliff_Topleft = CliffTerrain('Cliff_Topleft', 'Cliff', 'app/map_maker/rainlash_fields1_cliff_topleft.png', (15, 0))
Cliff_Bottomright = CliffTerrain('Cliff_Bottomright', 'Cliff', 'app/map_maker/rainlash_fields1_cliff_bottomright.png', (15, 0))

BridgeH = RandomTerrain('BridgeH', 'Bridge', tileset, (2, 0))
BridgeH.data = [(2, 0)]
BridgeV = RandomTerrain('BridgeV', 'Bridge', tileset, (2, 1))
BridgeH.data = [(2, 1)]

Castle = CastleTerrain('Castle', 'Castle', tileset, (4, 27))
House = HouseTerrain('House', 'House', tileset, (4, 25))
Ruins = RuinsTerrain('Ruins', 'Ruins', tileset, (3, 28))

d = [Plains, Sand, Road, Forest, Thicket, Cliff_Topleft, Cliff_Bottomright, Hill, BridgeH, BridgeV, House, Castle, Ruins]
DB_terrain = TerrainCatalog(d)
