from collections import OrderedDict

class McostGrid(object):
    default_value = 1

    def __init__(self):
        self.grid = []
        self.row_headers = []
        self.column_headers = []

    def import_data(self, fn):
        mcost_dict = OrderedDict()
        with open(fn) as mcost_data:
            self.column_headers = [l.strip() for l in mcost_data.readline().split('-')[1:]]
            for line in mcost_data.readlines()[1:]:
                s_line = line.strip().split()
                mcost_dict[s_line[0]] = [int(s) if s != '-' else 99 for s in s_line[1:]]
        self.row_headers = list(mcost_dict.keys())

        # Now convert to grid
        self.grid = [([self.default_value] * self.width()) for _ in range(self.height())]
        for y, row in enumerate(self.row_headers):
            for x, val in enumerate(mcost_dict[row]):
                self.set((x, y), val)

    def set(self, coord, val):
        x, y = coord
        self.grid[y][x] = val

    def get(self, coord):
        x, y = coord
        return self.grid[y][x]

    def width(self):
        return len(self.column_headers)

    def height(self):
        return len(self.row_headers)

    def add_row(self, name):
        self.row_headers.append(name)
        self.grid.append([self.default_value] * self.width())

    def add_column(self, name):
        self.column_headers.append(name)
        for row in self.grid:
            row.append(self.default_value)

    def get_terrain_types(self):
        return self.row_headers

    def serialize(self):
        return (self.grid, self.row_headers, self.column_headers)

    @classmethod
    def deserialize(cls, data):
        mcost_grid = cls()
        mcost_grid.grid = data[0]
        mcost_grid.row_headers = data[1]
        mcost_grid.column_headers = data[2]
        return mcost_grid
