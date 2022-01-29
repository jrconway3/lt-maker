try:
    import cPickle as pickle
except ImportError:
    import pickle

from app.map_maker.utilities import random_choice, flood_fill, find_bounds
from app.utilities import utils
from app.map_maker.terrain import Terrain

class MountainTerrain(Terrain):
    terrain_like = ('Mountain')
    organization = {}
    to_process = []  # Keeps track of what tiles still need to be process for group
    order = []  # Keeps track of the order that tiles have been processed
    locked_values = {}  # Keeps track of what coords unfortunately don't work
    mountain_data = None

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

            self.process_group(tilemap, group)

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords = self.organization[pos]
        new_coords1 = [(new_coords[0]*2, new_coords[1]*2)]
        new_coords2 = [(new_coords[0]*2 + 1, new_coords[1]*2)]
        new_coords3 = [(new_coords[0]*2 + 1, new_coords[1]*2 + 1)]
        new_coords4 = [(new_coords[0]*2, new_coords[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

    def initial_process(self, ):
        data_loc = 'app/map_maker/mountain_data.p'
        with open(data_loc, 'rb') as fp:
            self.mountain_data = pickle.load(fp)
        self.border_dict = {}  # Coord: Index (0-15)
        self.index_dict = {i: set() for i in range(16)}  # Index: Coord 
        for coord, rules in self.mountain_data.items():
            north_edge = None in rules['up']
            south_edge = None in rules['down']
            east_edge = None in rules['right']
            west_edge = None in rules['left']
            index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
            self.border_dict[coord] = index
            self.index_dict[index].add(coord)
        # for index, coord in self.index_dict.items():
        #     print(index, coord)

    def find_valid_coord(self, tilemap, pos) -> bool:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(north and north not in self.terrain_like)
        south_edge = bool(south and south not in self.terrain_like)
        east_edge = bool(east and east not in self.terrain_like)
        west_edge = bool(west and west not in self.terrain_like)
        valid_coords = \
            [coord for coord, rules in self.mountain_data.items() if
             ((north_edge and None in rules['up']) or (not north_edge and rules['up'])) and
             ((south_edge and None in rules['down']) or (not south_edge and rules['down'])) and
             ((east_edge and None in rules['right']) or (not east_edge and rules['right'])) and
             ((west_edge and None in rules['left']) or (not west_edge and rules['left']))]
        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        print("Valid coord")
        print(pos, self.order)
        print(north_edge, south_edge, east_edge, west_edge)
        print(valid_coords)
        # Remove locked coords
        if pos in self.locked_values:
            print("Locked", self.locked_values[pos])
            valid_coords = [coord for coord in valid_coords if coord not in self.locked_values[pos]]
            print(valid_coords)
        if not north_edge and north_pos in self.organization:
            chosen_coord = self.organization[north_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['down']]
        if not south_edge and south_pos in self.organization:
            chosen_coord = self.organization[south_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['up']]
        if not east_edge and east_pos in self.organization:
            chosen_coord = self.organization[east_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['left']]
        if not west_edge and west_pos in self.organization:
            chosen_coord = self.organization[west_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['right']]
        print(valid_coords)
        if not valid_coords:
            self.revert_order((north_pos, south_pos, east_pos, west_pos))
            # valid_coords = self.index_dict[15]
            return False
        valid_coord = random_choice(list(valid_coords), pos)
        print("Final", valid_coord)
        self.organization[pos] = valid_coord
        return True

    def revert_order(self, positions):
        while self.order:
            pos = self.order.pop()
            coord = self.organization[pos]
            del self.organization[pos]
            self.to_process.insert(0, pos)
            # if pos in self.locked_values:
            #     del self.locked_values[pos]
            if pos in positions:
                if pos not in self.locked_values:
                    self.locked_values[pos] = set()
                self.locked_values[pos].add(coord)
                print("Locking ", coord, "for ", pos)
                break

    def find_num_borders(self, tilemap, pos) -> int:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(north and north not in self.terrain_like)
        south_edge = bool(south and south not in self.terrain_like)
        east_edge = bool(east and east not in self.terrain_like)
        west_edge = bool(west and west not in self.terrain_like)
        num_borders = sum((north_edge, south_edge, east_edge, west_edge))
        return num_borders

    def find_num_partners(self, tilemap, pos) -> int:
        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        north_edge = north_pos in self.organization
        south_edge = south_pos in self.organization
        east_edge = east_pos in self.organization
        west_edge = west_pos in self.organization
        num_partners = sum((north_edge, south_edge, east_edge, west_edge))
        return num_partners

    def process_group(self, tilemap, group: set):
        # Determine coord 
        self.locked_values.clear()
        self.order.clear()
        self.to_process = sorted(group)

        def process(seq):
            pos = seq[0]
            did_work = self.find_valid_coord(tilemap, pos)
            if did_work:
                self.to_process.remove(pos)
                self.order.append(pos)

        while self.to_process:
            four_borders = [pos for pos in self.to_process if self.find_num_borders(tilemap, pos) == 4]
            if four_borders:
                process(four_borders)
                continue
            four_partners = [pos for pos in self.to_process if self.find_num_partners(tilemap, pos) == 4]
            if four_partners:
                process(four_partners)
                continue
            three_borders = [pos for pos in self.to_process if self.find_num_borders(tilemap, pos) == 3]
            if three_borders:
                process(three_borders)
                continue
            three_partners = [pos for pos in self.to_process if self.find_num_partners(tilemap, pos) == 3]
            if three_partners:
                process(three_partners)
                continue
            two_borders = [pos for pos in self.to_process if self.find_num_borders(tilemap, pos) == 2]
            if two_borders:
                process(two_borders)
                continue
            two_partners = [pos for pos in self.to_process if self.find_num_partners(tilemap, pos) == 2]
            if two_partners:
                process(two_partners)
                continue
            one_borders = [pos for pos in self.to_process if self.find_num_borders(tilemap, pos) == 1]
            if one_borders:
                process(one_borders)
                continue
            one_partners = [pos for pos in self.to_process if self.find_num_partners(tilemap, pos) == 1]
            if one_partners:
                process(one_partners)
                continue
            process(self.to_process)

        # while to_process:
        #     pos = to_process.pop(0)
        #     if pos in self.order:
        #         continue
        #     num_borders = self.find_num_borders(tilemap, pos)
        #     if num_borders == 4:
        #         self.find_valid_coord(tilemap, pos)
        #         self.order.append(pos)

        # four_border_positions = set()
        # three_border_positions = set()
        # two_border_positions = set()
        # one_border_positions = set()
        # no_border_positions = set()
        # for pos in group:
        #     north, east, south, west = tilemap.get_cardinal_terrain(pos)
        #     north_edge = bool(north and north not in self.terrain_like)
        #     south_edge = bool(south and south not in self.terrain_like)
        #     east_edge = bool(east and east not in self.terrain_like)
        #     west_edge = bool(west and west not in self.terrain_like)
        #     num_borders = sum((north_edge, south_edge, east_edge, west_edge))
        #     if num_borders == 0:
        #         no_border_positions.add(pos)
        #     elif num_borders == 1:
        #         one_border_positions.add(pos)
        #     elif num_borders == 2:
        #         two_border_positions.add(pos)
        #     elif num_borders == 3:
        #         three_border_positions.add(pos)
        #     elif num_borders == 4:
        #         four_border_positions.add(pos)
        # for border_list in [four_border_positions, three_border_positions, two_border_positions, one_border_positions, no_border_positions]:
        #     for pos in sorted(border_list):
        #         self.find_valid_coord(tilemap, pos)
