try:
    import cPickle as pickle
except ImportError:
    import pickle

from app.map_maker.utilities import random_choice, find_bounding_rect

class Generator():
    def __init__(self):
        self.seed = 0
        self.organization = {}
        self.to_process = []  # Keeps track of what tiles still need to be process for group
        self.order = []  # Keeps track of the order that tiles have been processed
        self.locked_values = {}  # Keeps track of what coords unfortunately don't work
        self.mountain_data = None

        self.terrain_grid = None
        self.terrain_grids = self.generate_terrain_grids()

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
            print(index, sorted(coord))

        self.terrain_organization = {}
        for terrain_grid in self.terrain_grids:
            self.terrain_grid = terrain_grid
            _hash = frozenset(self.terrain_grid)
            if _hash not in self.terrain_organization:
                self.terrain_organization[_hash] = []
            # For each seed
            for idx in range(10):
                self.seed = idx
                self.organization.clear()
                self.process_terrain_grid()
                self.terrain_organization[_hash].append(self.organization.copy())

    def generate_terrain_grids(self) -> list:
        terrain_grid1 = {(0, 0)}
        terrain_grid2 = {(0, 0), (1, 0)}
        return [terrain_grid1, terrain_grid2]

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords = self.organization[pos]
        new_coords1 = [(new_coords[0]*2, new_coords[1]*2)]
        new_coords2 = [(new_coords[0]*2 + 1, new_coords[1]*2)]
        new_coords3 = [(new_coords[0]*2 + 1, new_coords[1]*2 + 1)]
        new_coords4 = [(new_coords[0]*2, new_coords[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

    def find_valid_coord(self, pos) -> bool:
        north, east, south, west = self.get_cardinal_terrain(pos)
        north_edge = not north
        south_edge = not south
        east_edge = not east
        west_edge = not west
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
        print("*Valid Coord", pos, self.order)
        # print(sorted(valid_coords))
        # Remove locked coords
        if pos in self.locked_values:
            print("Locked", sorted(self.locked_values[pos]))
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
        # print(sorted(valid_coords))
        if not valid_coords:
            print("Reverting Order...")
            if pos in self.locked_values:
                del self.locked_values[pos]
            self.revert_order()
            # valid_coords = self.index_dict[15]
            return False
        valid_coord = random_choice(list(valid_coords), pos, self.seed)
        print("Final", valid_coord)
        self.organization[pos] = valid_coord
        return True

    def revert_order(self):
        if not self.order:
            print("Major loop error! No valid solution")
            # Just fill it up with generic pieces
            for pos in self.to_process:
                valid_coords = self.index_dict[15]
                valid_coord = random_choice(list(valid_coords), pos, self.seed)
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
        print("Locking ", coord, "for ", pos)

    def get_terrain(self, pos: tuple) -> bool:
        return pos in self.terrain_grid

    def get_cardinal_terrain(self, pos: tuple) -> tuple:
        north = self.get_terrain((pos[0], pos[1] - 1))
        east = self.get_terrain((pos[0] + 1, pos[1]))
        south = self.get_terrain((pos[0], pos[1] + 1))
        west = self.get_terrain((pos[0] - 1, pos[1]))
        return north, east, south, west

    def find_num_borders(self, pos) -> int:
        north, east, south, west = self.get_cardinal_terrain(pos)
        num_borders = sum((not north, not south, not east, not west))
        return num_borders

    def find_num_partners(self, pos) -> int:
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

    def process_terrain_grid(self):
        # Determine coord 
        print("--- Process Group ---")
        self.locked_values.clear()
        self.order.clear()
        self.to_process = sorted(self.terrain_grid)

        def process(seq):
            pos = seq[0]
            did_work = self.find_valid_coord(pos)
            if did_work:
                self.to_process.remove(pos)
                self.order.append(pos)
            self.to_process = sorted(self.to_process)

        while self.to_process:
            four_borders = [pos for pos in self.to_process if self.find_num_borders(pos) == 4]
            if four_borders:
                process(four_borders)
                continue
            four_partners = [pos for pos in self.to_process if self.find_num_partners(pos) == 4]
            if four_partners:
                process(four_partners)
                continue
            three_borders = [pos for pos in self.to_process if self.find_num_borders(pos) == 3]
            if three_borders:
                process(three_borders)
                continue
            three_partners = [pos for pos in self.to_process if self.find_num_partners(pos) == 3]
            if three_partners:
                process(three_partners)
                continue
            two_borders = [pos for pos in self.to_process if self.find_num_borders(pos) == 2]
            if two_borders:
                process(two_borders)
                continue
            two_partners = [pos for pos in self.to_process if self.find_num_partners(pos) == 2]
            if two_partners:
                process(two_partners)
                continue
            one_and_one = [pos for pos in self.to_process if self.find_num_borders(pos) == 1 and self.find_num_partners(pos) == 1]
            if one_and_one:
                process(one_and_one)
                continue
            one_borders = [pos for pos in self.to_process if self.find_num_borders(pos) == 1]
            if one_borders:
                process(one_borders)
                continue
            one_partners = [pos for pos in self.to_process if self.find_num_partners(pos) == 1]
            if one_partners:
                process(one_partners)
                continue
            process(self.to_process)

if __name__ == '__main__':
    import sys
    from PyQt5.QtGui import QImage, QColor, QPainter
    from PyQt5.QtWidgets import QApplication

    from app.constants import TILEWIDTH, TILEHEIGHT

    app = QApplication(sys.argv)

    tileset = 'app/map_maker/rainlash_fields1.png'
    save_dir = 'app/map_maker/test_output/'
    main_image = QImage(tileset)

    g = Generator()
    for key, terrain_grids in g.terrain_organization.items():
        # print(key, terrain_grids)
        width, height = find_bounding_rect(key)

        for idx, terrain_grid in enumerate(terrain_grids):
            new_im = QImage(width * TILEWIDTH, height * TILEHEIGHT, QImage.Format_RGB32)
            new_im.fill(QColor(0, 0, 0))
            painter = QPainter()
            painter.begin(new_im)

            for pos, coord in terrain_grid.items():
                rect = (coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                im = main_image.copy(*rect)
                painter.drawImage(pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT, im)

            painter.end()

            h = str(hash(key))[:16]
            new_im.save(save_dir + ('%s_%02d.png' % (h, idx)))
