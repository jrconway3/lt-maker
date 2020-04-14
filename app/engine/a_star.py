from app.data.database import DB

class Node():
    __slots__ = ['reachable', 'cost', 'x', 'y', 'parent', 'g', 'h', 'f']

    def __init__(self, x: int, y: int, reachable: bool, cost: int):
        """
        Initialize new cell
        reachable - is cell reachable? is not a wall?
        cost - how many movement points to reach
        """
        self.reachable = reachable
        self.cost = cost
        self.x = x
        self.y = y
        self.reset()

    def reset(self):
        self.parent = None
        self.g = 0
        self.h = 0
        self.f = 0

    def __gt__(self, n):
        return self.cost > n

    def __lt__(self, n):
        return self.cost < n

class GridManager(object):
    __slots__ = ['width', 'height', 'grids', 'team_grid', 'unit_grid', 'aura_grid', 'known_auras']

    def __init__(self, tilemap):
        self.width = tilemap.width
        self.height = tilemap.height
        self.grids = {}

        # For each movement type
        for idx, col in enumerate(DB.mcost.column_headers):
            self.grids[col] = self.init_grid(col, tilemap)

        self.team_grid = self.init_unit_grid()
        self.unit_grid = self.init_unit_grid()
        self.aura_grid = self.init_aura_grid()
        # Key: Aura, Value: Set of positions
        self.known_auras = {}  

    def init_unit_grid(self):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                cells.append(None)
        return cells

    def init_aura_grid(self):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                cells.append(set())
        return cells

    def set_unit(self, pos, unit):
        idx = pos[0] * self.height + pos[1]
        self.unit_grid[idx] = unit
        if unit:
            self.team_grid[idx] = unit.team
        else:
            self.team_grid[idx] = None

    def get_unit(self, pos):
        return self.unit_map[pos[0] * self.height + pos[1]]

    def get_team(self, pos):
        return self.team_map[pos[0] * self.height + pos[1]]

    # For movement
    def init_grid(self, mode, tilemap):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                tile = tilemap.tiles[(x, y)]
                terrain = DB.terrain.get(tile.terrain_nid)
                tile_cost = DB.mcost.get_mcost(mode, terrain.mtype)
                cells.append(Node(x, y, tile_cost != 99, tile_cost))
        return cells

    def get_grid(self, mode):
        return self.grids[mode]
