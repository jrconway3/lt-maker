from app import utilities

from app.engine.sprites import SPRITES
from app.data.constants import TILEWIDTH, TILEHEIGHT

from app.engine import engine, targets
from app.engine.game_state import game

class BoundaryInterface():
    draw_order = ('all_spell', 'all_attack', 'spell', 'attack')
    enemy_teams = ('enemy', 'enemy2')

    def __init__(self, width, height):
        self.modes = {'attack': SPRITES.get('boundary_red'),
                      'all_attack': SPRITES.get('boundary_purple'),
                      'spell': SPRITES.get('boundary_green'),
                      'all_spell': SPRITES.get('boundary_blue')}
        
        self.width = width
        self.height = height
        
        self.grids = {'attack': self.init_grid(),
                      'spell': self.init_grid(),
                      'movement': self.init_grid()}
        self.dictionaries = {'attack': {},
                             'spell': {},
                             'movement': {}}

        self.draw_flag = False
        self.all_on_flag = False

        self.displaying_units = set()

        self.surf = None

    def init_grid(self):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                cells.append(set())
        return cells

    def show(self):
        self.draw_flag = True

    def hide(self):
        self.draw_flag = False

    def check_bounds(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def toggle_unit(self, unit):
        if unit.nid in self.displaying_units:
            self.displaying_units.discard(unit.nid)
        else:
            self.displaying_units.add(unit.nid)
        self.surf = None

    def reset_unit(self, unit):
        if unit.nid in self.displaying_units:
            self.display_units.discard(unit.nid)
            self.surf = None

    def _set(self, positions, mode, nid):
        grid = self.grids[mode]
        self.dictionaries[mode][nid] = set()
        for pos in positions:
            grid[pos[0] * self.height + pos[1]].add(nid)
            self.dictionaries[mode][nid].add(pos)

    def clear(self, mode=None):
        if mode:
            modes = [mode]
        else:
            modes = list(self.grids.keys())
        for m in modes:
            for x in range(self.width):
                for y in range(self.height):
                    self.grids[m][x * self.height + y].clear()

    def _add_unit(self, unit):
        valid_moves = targets.get_valid_moves(unit, force=True)
        valid_attacks = targets.get_possible_attacks(unit, valid_moves, boundary=True)
        valid_spells = targets.get_possible_spell_attacks(unit, valid_moves, boundary=True)
        self._set(valid_attacks, 'attack', unit.nid)
        self._set(valid_spells, 'spell', unit.nid)

        area_of_influence = targets.find_manhattan_spheres(set(range(1, game.equations.movement(unit) + 1)), *unit.position)
        area_of_influence = {pos for pos in area_of_influence if self.check_bounds(pos)}
        self._set(area_of_influence, 'movement', unit.nid)

        self.surf = None

    def _remove_unit(self, unit):
        for mode, grid in self.grids.items():
            if unit.nid in self.dictionaries[mode]:
                for (x, y) in self.dictionaries[mode][unit.nid]:
                    grid[x * self.height + y].discard(unit.nid)
        self.surf = None

    def leave(self, unit):
        if unit.team in self.enemy_teams:
            self._remove_unit(unit)

        # Update ranges of other units that might be affected by my leaving
        if unit.position:
            x, y = unit.position
            other_units = {game.level.units.get(nid) for nid in self.grids['movement'][x * self.height + y]}
            other_units = {other_unit for other_unit in other_units if not utilities.compare_teams(unit.team, other_unit.team)}

            for other_unit in other_units:
                self._remove_unit(other_unit)
            for other_unit in other_units:
                if other_unit.position:
                    self._add_unit(other_unit)

    def arrive(self, unit):
        if unit.position:
            if unit.team in self.enemy_teams:
                self._add_unit(unit)

            # Update ranges of other units that might be affected by my arrival
            x, y = unit.position
            # print(self.grids['movement'][x * self.height + y])
            other_units = {game.level.units.get(nid) for nid in self.grids['movement'][x * self.height + y]}
            other_units = {other_unit for other_unit in other_units if not utilities.compare_teams(unit.team, other_unit.team)}

            for other_unit in other_units:
                self._remove_unit(other_unit)
            for other_unit in other_units:
                if other_unit.position:
                    self._add_unit(other_unit)

    # Called when map changes
    def reset(self):
        self.clear()
        for unit in game.level.units:
            if unit.position and unit.team in self.enemy_teams:
                self._add_unit(unit)

    def toggle_all_enemy_attacks(self):
        if self.all_on_flag:
            self.clear_all_enemy_attacks()
        else:
            self.show_all_enemy_attacks()

    def show_all_enemy_attacks(self):
        self.all_on_flag = True
        self.surf = None

    def clear_all_enemy_attacks(self):
        self.all_on_flag = False
        self.surf = None

    def draw(self, surf, size):
        if not self.draw_flag:
            return surf

        if not self.surf:
            self.surf = engine.create_surface(size, transparent=True)
            for grid_name in self.draw_order:
                if grid_name == 'attack' and not self.displaying_units:
                    continue
                elif grid_name == 'spell' and not self.displaying_units:
                    continue
                elif grid_name == 'all_attack' and not self.all_on_flag:
                    continue
                elif grid_name == 'all_spell' and not self.all_on_flag:
                    continue
                if grid_name == 'all_attack' or grid_name == 'attack':
                    grid = self.grids['attack']
                else:
                    grid = self.grids['spell']

                for y in range(self.height):
                    for x in range(self.width):
                        cell = grid[x * self.height + y]
                        if cell:
                            display = any(nid in self.displaying_units for nid in cell)

                            if grid_name == 'all_attack' and display:
                                continue
                            if grid_name == 'all_spell' and display:
                                continue
                            if grid_name == 'attack' and not display:
                                continue
                            if grid_name == 'spell' and not display:
                                continue

                            image = self.create_image(grid, x, y, grid_name)
                            self.surf.blit(image, (x * TILEWIDTH, y * TILEHEIGHT))

        surf.blit(self.surf, (0, 0))
        return surf

    def create_image(self, grid, x, y, grid_name):
        top_pos = (x, y - 1)
        left_pos = (x - 1, y)
        right_pos = (x + 1, y)
        bottom_pos = (x, y + 1)

        if grid_name == 'all_attack' or grid_name == 'all_spell':
            top = bool(grid[x * self.height + y - 1]) if self.check_bounds(top_pos) else False
            left = bool(grid[(x - 1) * self.height + y]) if self.check_bounds(left_pos) else False
            right = bool(grid[(x + 1) * self.height + y]) if self.check_bounds(right_pos) else False
            bottom = bool(grid[x * self.height + y + 1]) if self.check_bounds(bottom_pos) else False
        else:
            top = any(nid in self.displaying_units for nid in grid[x * self.height + y - 1]) if self.check_bounds(top_pos) else False
            left = any(nid in self.displaying_units for nid in grid[(x - 1) * self.height + y]) if self.check_bounds(left_pos) else False
            right = any(nid in self.displaying_units for nid in grid[(x + 1) * self.height + y]) if self.check_bounds(right_pos) else False
            bottom = any(nid in self.displaying_units for nid in grid[x * self.height + y + 1]) if self.check_bounds(bottom_pos) else False
        idx = top*8 + left*4 + right*2 + bottom  # Binary logis to get correct index
        return engine.subsurface(self.modes[grid_name], (idx * TILEWIDTH, 0, TILEWIDTH, TILEHEIGHT))
