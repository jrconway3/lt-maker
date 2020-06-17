import heapq

from app.data.database import DB

def compare_teams(t1: str, t2: str) -> bool:
    # Returns True if allies, False if enemies
    if t1 == t2:
        return True
    elif (t1 == 'player' and t2 == 'other') or (t2 == 'player' and t1 == 'other'):
        return True
    else:
        return False

class Node():
    __slots__ = ['reachable', 'cost', 'x', 'y', 'parent', 'g', 'h', 'f']

    def __init__(self, x: int, y: int, reachable: bool, cost: float):
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

    def __repr__(self):
        return "Node(%d, %d): cost=%d, g=%d, h=%d, f=%f, %s" % (self.x, self.y, self.cost, self.g, self.h, self.f, self.reachable)

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
        return self.unit_grid[pos[0] * self.height + pos[1]]

    def get_team(self, pos):
        return self.team_grid[pos[0] * self.height + pos[1]]

    # For movement
    def init_grid(self, mode, tilemap):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                terrain_nid = tilemap.get_terrain((x, y))
                terrain = DB.terrain.get(terrain_nid)
                tile_cost = DB.mcost.get_mcost(mode, terrain.mtype)
                cells.append(Node(x, y, tile_cost < 99, tile_cost))
        return cells

    def get_grid(self, mode):
        return self.grids[mode]

class Djikstra():
    __slots__ = ['open', 'closed', 'cells', 'width', 'height', 'start_pos', 'start_cell', 'unit_team', 'pass_through']

    def __init__(self, start_pos, grid, width, height, unit_team, pass_through):
        self.open = []
        heapq.heapify(self.open)
        self.closed = set()
        self.cells = grid # Must keep order
        self.width, self.height = width, height
        self.reset_grid()
        self.start_pos = start_pos
        self.start_cell = self.get_cell(start_pos[0], start_pos[1])
        self.unit_team = unit_team
        self.pass_through = pass_through

    def reset_grid(self):
        for cell in self.cells:
            cell.reset()

    def get_cell(self, x, y):
        return self.cells[x * self.height + y]

    def get_adjacent_cells(self, cell):
        """
        Returns adjacent cells to a cell.
        """
        cells = []
        if cell.x < self.width - 1:
            cells.append(self.get_cell(cell.x + 1, cell.y))
        if cell.y > 0:
            cells.append(self.get_cell(cell.x, cell.y - 1))
        if cell.x > 0:
            cells.append(self.get_cell(cell.x - 1, cell.y))
        if cell.y < self.height - 1:
            cells.append(self.get_cell(cell.x, cell.y + 1))
        return cells

    def update_cell(self, adj, cell):
        # g is true distance between this cell and starting position
        adj.g = cell.g + adj.cost
        adj.parent = cell

    def process(self, team_map, movement_left):
        # add starting cell to open heap queue
        heapq.heappush(self.open, (self.start_cell.g, self.start_cell))
        while self.open:
            # pop cell from heap queue
            g, cell = heapq.heappop(self.open)
            # If we've traveled too far -- always g ordered, so leaving at the 
            # first sign of trouble will always work
            if g > movement_left:
                return {(cell.x, cell.y) for cell in self.closed}
            # add cell to closed set so we don't process it twice
            self.closed.add(cell)
            # get adjacent cells for cell
            adj_cells = self.get_adjacent_cells(cell)
            for adj in adj_cells:
                if adj.reachable and adj not in self.closed:
                    unit_team = team_map[adj.x * self.height + adj.y]
                    if not unit_team or compare_teams(self.unit_team, unit_team) or self.pass_through:
                        if (adj.g, adj) in self.open:
                            # if adj cell in open list, check if current path
                            # is better than the one previously found for this adj cell
                            if adj.g > cell.g + adj.cost:
                                self.update_cell(adj, cell)
                                heapq.heappush(self.open, (adj.g, adj))
                        else:
                            self.update_cell(adj, cell)
                            heapq.heappush(self.open, (adj.g, adj))
        # Sometimes gets here if unit is enclosed
        return {(cell.x, cell.y) for cell in self.closed}

class AStar():
    def __init__(self, start_pos, goal_pos, grid, width, height, unit_team, pass_through=False):
        self.cells = grid
        self.width = width
        self.height = height
        self.start_pos = start_pos
        self.goal_pos = goal_pos

        self.start_cell = self.get_cell(start_pos[0], start_pos[1])
        self.end_cell = self.get_cell(goal_pos[0], goal_pos[1]) if goal_pos else None
        self.adj_end = self.get_adjacent_cells(self.end_cell) if self.end_cell else None

        self.unit_team = unit_team
        self.pass_through = pass_through

        self.reset()

    def reset_grid(self):
        for cell in self.cells:
            cell.reset()

    def reset(self):
        self.open = []
        heapq.heapify(self.open)
        self.closed = set()
        self.path = []
        self.reset_grid()

    def set_goal_pos(self, goal_pos):
        self.goal_pos = goal_pos
        self.end_cell = self.get_cell(goal_pos[0], goal_pos[1])
        self.adj_end = self.get_adjacent_cells(self.end_cell) 

    def get_heuristic(self, cell):
        """
        Compute the heuristic for this cell
        h is the approximate distance between this cell and the goal cell
        """
        # Get main heuristic
        dx1 = cell.x - self.end_cell.x
        dy1 = cell.y - self.end_cell.y
        h = abs(dx1) + abs(dy1)
        # Are we going in direction of goal?
        # Slight nudge in direction that lies along path from start to end
        dx2 = self.start_cell.x - self.end_cell.x
        dy2 = self.start_cell.y - self.end_cell.y
        cross = abs(dx1 * dy2 - dx2 * dy1)
        return h + cross * .001

    def get_cell(self, x, y):
        return self.cells[x * self.height + y]

    def get_adjacent_cells(self, cell):
        cells = []
        if cell.x < self.width - 1:
            cells.append(self.get_cell(cell.x + 1, cell.y))
        if cell.y > 0:
            cells.append(self.get_cell(cell.x, cell.y - 1))
        if cell.x > 0:
            cells.append(self.get_cell(cell.x - 1, cell.y))
        if cell.y < self.height - 1:
            cells.append(self.get_cell(cell.x, cell.y + 1))
        return cells

    def update_cell(self, adj, cell):
        # h is approximate distance between this cell and the goal
        # g is true distance between this cell and the starting position
        # f is simply them added together
        adj.g = cell.g + adj.cost
        adj.h = self.get_heuristic(adj)
        adj.parent = cell
        adj.f = adj.h + adj.g

    def return_path(self, cell):
        path = []
        while cell:
            path.append((cell.x, cell.y))
            cell = cell.parent
        return path

    def process(self, team_map, adj_good_enough=False, ally_block=False, limit=None):
        # Add starting cell to open queue
        heapq.heappush(self.open, (self.start_cell.f, self.start_cell))
        while self.open:
            f, cell = heapq.heappop(self.open)
            # Make sure we don't process the cell twice
            self.closed.add(cell)
            # If this cell is past the limit, just return None
            # Uses f, not g, because g will cut off if first greedy path fails
            # f only cuts off if all cells are bad
            if limit and cell.f > limit:
                return self.path
            # if ending cell, display found path
            if cell is self.end_cell or (adj_good_enough and cell in self.adj_end):
                self.path = self.return_path(cell)
                return self.path
            # get adjacent cells for cell
            adj_cells = self.get_adjacent_cells(cell)
            for adj in adj_cells:
                if adj.reachable and adj not in self.closed:
                    unit_team = team_map[adj.x * self.height + adj.y]
                    if not unit_team or self.pass_through or (not ally_block and compare_teams(self.unit_team, unit_team)):
                        if (adj.f, adj) in self.open:
                            # if adj cell in open list, check if current path
                            # is better than the one previously found for this adj cell
                            if adj.g > cell.g + adj.cost:
                                self.update_cell(adj, cell)
                                heapq.heappush(self.open, (adj.f, adj))
                        else:
                            self.update_cell(adj, cell)
                            heapq.heappush(self.open, (adj.f, adj))
