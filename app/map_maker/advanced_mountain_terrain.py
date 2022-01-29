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
        for index, coord in self.index_dict.items():
            print(index, coord)

    def process_group(self, tilemap, group: set):
        # Determine coord for each pos in group
        for pos in group:
            north, east, south, west = tilemap.get_cardinal_terrain(pos)
            north_edge = bool(north and north not in self.terrain_like)
            south_edge = bool(south and south not in self.terrain_like)
            east_edge = bool(east and east not in self.terrain_like)
            west_edge = bool(west and west not in self.terrain_like)
            index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
            valid_coords = self.index_dict[index]
            self.organization[pos] = random_choice(list(valid_coords), pos)
