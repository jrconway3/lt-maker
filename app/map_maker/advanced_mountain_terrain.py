try:
    import cPickle as pickle
except ImportError:
    import pickle

from app.map_maker.utilities import random_choice, flood_fill
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
            raise RuntimeError("Unexpected infinite loop in mountain flood_fill")

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
        self.noneless_rules = {}

        for coord, rules in self.mountain_data.items():
            north_edge = None in rules['up']
            south_edge = None in rules['down']
            east_edge = None in rules['right']
            west_edge = None in rules['left']
            index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
            self.border_dict[coord] = index
            self.index_dict[index].add(coord)
            # Keep track of the rules when None is not present as well
            noneless_rules = {}
            noneless_rules['up'] = {k: v for k, v in rules['up'].items() if k is not None}
            noneless_rules['down'] = {k: v for k, v in rules['down'].items() if k is not None}
            noneless_rules['left'] = {k: v for k, v in rules['left'].items() if k is not None}
            noneless_rules['right'] = {k: v for k, v in rules['right'].items() if k is not None}
            self.noneless_rules[coord] = noneless_rules
        for index, coord in self.index_dict.items():
            print(index, sorted(coord))

    def find_valid_coord(self, tilemap, pos, exact=True) -> bool:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        # Whether there is a border to the north
        north_edge = bool(north and north not in self.terrain_like)
        south_edge = bool(south and south not in self.terrain_like)
        east_edge = bool(east and east not in self.terrain_like)
        west_edge = bool(west and west not in self.terrain_like)
        valid_coords = \
            [coord for coord, rules in self.mountain_data.items() if
             ((north_edge and None in rules['up']) or (not north_edge and self.noneless_rules[coord]['up'])) and
             ((south_edge and None in rules['down']) or (not south_edge and self.noneless_rules[coord]['down'])) and
             ((east_edge and None in rules['right']) or (not east_edge and self.noneless_rules[coord]['right'])) and
             ((west_edge and None in rules['left']) or (not west_edge and self.noneless_rules[coord]['left']))]
        orig_valid_coords = valid_coords[:]
        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        southwest_pos = (pos[0] - 1, pos[1] + 1)
        # print("*Valid Coord", pos, self.order)
        # print(sorted(valid_coords))
        # Remove locked coords
        if pos in self.locked_values and exact:
            # print("Locked", sorted(self.locked_values[pos]))
            valid_coords = [coord for coord in valid_coords if coord not in self.locked_values[pos]]
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
        # If there's already a position filled to the southwest, check that we can find a reasonable
        # choice for the 
        if southwest_pos in self.organization and south and south in self.terrain_like:
            chosen_coord = self.organization[southwest_pos]
            valid_right_coords = self.noneless_rules[chosen_coord]['right']
            # For the remaining valid coords for this coordinate
            # check if any of that coordinate's southward connections match with the rightward coordinates
            # of the southwesst position
            valid_coords = [coord for coord in valid_coords if any(c in valid_right_coords for c in self.noneless_rules[coord]['down'])]
        # print(sorted(valid_coords))

        # print(sorted(valid_coords))
        if not valid_coords and not exact:
            valid_coords = orig_valid_coords
        if not valid_coords:
            # print("Reverting Order...")
            if pos in self.locked_values:
                del self.locked_values[pos]
            self.revert_order()
            # valid_coords = self.index_dict[15]
            return False

        # Weight the valid coord list by the likelihood that it's partners use it
        valid_coord_list = []
        for valid_coord in valid_coords:
            if west_pos in self.organization:
                west_coord = self.organization[west_pos]
                count = self.mountain_data[west_coord]['right'][valid_coord]
                valid_coord_list += [valid_coord] * count
            if north_pos in self.organization:
                north_coord = self.organization[north_pos]
                count = self.mountain_data[north_coord]['down'][valid_coord]
                valid_coord_list += [valid_coord] * count
            if south and south in self.terrain_like:
                count = sum(self.noneless_rules[valid_coord]['down'].values())
                valid_coord_list += [valid_coord] * count
            if east and east in self.terrain_like:
                count = sum(self.noneless_rules[valid_coord]['right'].values())
                valid_coord_list += [valid_coord] * count
        if not valid_coord_list:
            valid_coord_list = valid_coords
        valid_coord = random_choice(valid_coord_list, pos)
        # print("Final", valid_coord)
        self.organization[pos] = valid_coord
        return True

    def revert_order(self):
        if not self.order:
            print("Major loop error! No valid solution")
            # Just fill it up with generic pieces
            for pos in self.to_process:
                valid_coords = self.index_dict[15]
                valid_coord = random_choice(list(valid_coords), pos)
                self.organization[pos] = valid_coord
            self.to_process.clear()
            return

        pos = self.order.pop()
        coord = self.organization[pos]
        del self.organization[pos]
        self.to_process.insert(0, pos)
        if pos not in self.locked_values:
            self.locked_values[pos] = set()
        self.locked_values[pos].add(coord)
        # print("Locking ", coord, "for ", pos)

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

    def process_group(self, tilemap, group: set, exact=False):
        print("--- Process Group ---")
        # Determine coord 
        self.locked_values.clear()
        self.order.clear()
        # Sort from top left to bottom right
        # Break ties starting from the left
        self.to_process = sorted(group, key=lambda x: (x[0] + x[1], x[0]))

        def process(seq, exact=True):
            pos = seq[0]
            did_work = self.find_valid_coord(tilemap, pos, exact=exact)
            if did_work:
                self.to_process.remove(pos)
                self.order.append(pos)
            self.to_process = sorted(self.to_process, key=lambda x: (x[0] + x[1], x[0]))

        # Try about 1000 times for real, before entering don't care mode
        counter = 0
        if exact:
            max_counter = int(1e6)
        else:
            max_counter = len(self.to_process) * 12
        while self.to_process and counter < max_counter:
            counter += 1
            process(self.to_process)
        # Just throw shit at the wall
        if self.to_process:
            print("Inexact solution found")
            while self.to_process:
                process(self.to_process, exact=False)
