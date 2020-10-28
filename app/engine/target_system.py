from app.utilities import utils
from app.data.database import DB
from app.engine import pathfinding, skill_system, equations, item_funcs, item_system
from app.engine.game_state import game

# Consider making these sections faster
def get_shell(valid_moves: set, potential_range: set, width: int, height: int) -> set:
    valid_attacks = set()
    for valid_move in valid_moves:
        valid_attacks |= find_manhattan_spheres(potential_range, valid_move[0], valid_move[1])
    return {pos for pos in valid_attacks if 0 <= pos[0] < width and 0 <= pos[1] < height}

# Consider making these sections faster -- use memory?
def find_manhattan_spheres(rng: set, x: int, y: int) -> set:
    _range = range
    _abs = abs
    main_set = set()
    for r in rng:
        # Finds manhattan spheres of radius r
        for i in _range(-r, r + 1):
            magn = _abs(i)
            main_set.add((x + i, y + r - magn))
            main_set.add((x + i, y - r + magn))
    return main_set

def get_nearest_open_tile(self, unit, position):
    r = 0
    _abs = abs
    while r < 10:
        for x in range(-r, r + 1):
            magn = _abs(x)
            n1 = position[0] + x, position[1] + r - magn
            n2 = position[0] + x, position[1] - r + magn
            if not game.board.check_bounds(n1) and game.board.get_unit(n1):
                mcost = game.movement.get_mcost(unit, n1)
                if mcost < 5:
                    return n1
            elif not game.board.check_bounds(n1) and game.board.get_unit(n1):
                mcost = game.movement.get_mcost(unit, n2)
                if mcost < 5:
                    return n2
        r += 1
    return None

def distance_to_closest_enemy(unit, pos=None):
    if pos is None:
        pos = unit.position
    enemy_list = [u for u in game.level.units if u.position and skill_system.check_enemy(u, unit)]
    if not enemy_list:
        return 100  # No enemies
    dist_list = [utils.calculate_distance(enemy.position, pos) for enemy in enemy_list]
    return min(dist_list)

def get_adjacent_positions(pos):
    x, y = pos
    adjs = ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))
    return [a for a in adjs if 0 <= a[0] < game.tilemap.width and 0 <= a[1] < game.tilemap.height]

def get_attacks(unit, item=None) -> set:
    """
    Determines all possible positions the unit could attack
    Does not attempt to determine if an enemy is actually in that place
    """
    if unit.has_attacked:
        return set()
    if not item:
        item = unit.get_weapon()
    if not item:
        return set()

    item_range = item_system.get_range(unit, item)
    attacks = get_shell({unit.position}, item_range, game.tilemap.width, game.tilemap.height)
    return attacks

def get_possible_attacks(unit, valid_moves) -> set:
    attacks = set()
    for item in get_all_weapons(unit):
        item_range = item_system.get_range(unit, item)
        attacks |= get_shell(valid_moves, item_range, game.tilemap.width, game.tilemap.height)
    return attacks

def get_possible_spell_attacks(unit, valid_moves) -> set:
    attacks = set()
    for item in get_all_spells(unit):
        item_range = item_system.get_range(unit, item)
        attacks |= get_shell(valid_moves, item_range, game.tilemap.width, game.tilemap.height)
    return attacks

# Uses all weapons the unit has access to to find its potential range
def find_potential_range(unit, weapon=True, spell=False, boundary=False) -> set:
    if weapon and spell:
        items = [item for item in unit.items if item_system.available(unit, item) and
                 item_system.is_weapon(unit, item) or item_system.is_spell(unit, item)]
    elif weapon:
        items = get_all_weapons(unit)
    elif spell:
        items = get_all_spells(unit)
    else:
        return set()
    potential_range = set()
    for item in items:
        for rng in item_system.get_range(unit, item):
            potential_range.add(rng)
    return potential_range

def get_valid_moves(unit, force=False) -> set:
    # For some reason, I need to forcefully import the game
    # object here, otherwise it is recorded as None...
    # from app.engine.game_state import game
    # Assumes unit is on the map
    if not force and unit.finished or (unit.has_moved and not skill_system.has_canto(unit)):
        return set()

    mtype = DB.classes.get(unit.klass).movement_group

    grid = game.board.get_grid(mtype)
    width, height = game.tilemap.width, game.tilemap.height
    pass_through = skill_system.pass_through(unit)
    pathfinder = pathfinding.Djikstra(unit.position, grid, width, height, unit.team, pass_through)

    movement_left = equations.parser.movement(unit) if force else unit.movement_left

    valid_moves = pathfinder.process(game.board.team_grid, movement_left)
    valid_moves.add(unit.position)
    return valid_moves

def get_path(unit, position, ally_block=False) -> list:
    mtype = DB.classes.get(unit.klass).movement_group
    grid = game.board.get_grid(mtype)

    width, height = game.tilemap.width, game.tilemap.height
    pass_through = skill_system.pass_through(unit)
    pathfinder = pathfinding.AStar(unit.position, position, grid, width, height, unit.team, pass_through)

    path = pathfinder.process(game.board.team_grid, ally_block=ally_block)
    return path

def travel_algorithm(path, moves, unit, grid):
    """
    Given a long path, travels along that path as far as possible
    """
    if not path:
        return unit.position

    moves_left = moves
    through_path = 0
    for position in path[::-1][1:]:  # Remove start position, travel backwards
        moves_left -= grid[position[0] * game.tilemap.height + position[1]].cost
        if moves_left >= 0:
            through_path += 1
        else:
            break
    # Don't move where a unit already is, and don't make through path < 0
    # Lower the through path by one, cause we can't move that far
    while through_path > 0 and any(other_unit.position == path[-(through_path + 1)] for other_unit in game.level.units if unit is not other_unit):
        through_path -= 1
    return path[-(through_path + 1)]  # Travel as far as we can

def get_valid_targets(unit, item=None) -> set:
    """
    Determines all the valid targets given use of the item
    """
    if not item:
        item = unit.get_equipped_item()
    if not item:
        return set()
    return {target for target in item_system.valid_targets(unit, item) if 
            item_system.target_restrict(unit, item, *item_system.splash(unit, item, target))}

def get_all_weapons(unit) -> list:
    return [item for item in item_funcs.get_all_items(unit) if item_system.is_weapon(unit, item) and item_system.available(unit, item)]

def get_all_weapon_targets(unit) -> set:
    weapons = get_all_weapons(unit)
    targets = set()
    for weapon in weapons:
        targets |= get_valid_targets(unit, weapon)
    return targets

def get_all_spells(unit):
    return [item for item in item_funcs.get_all_items(unit) if item_system.is_spell(unit, item) and item_system.available(unit, item)]

def get_all_spell_targets(unit) -> set:
    spells = get_all_spells(unit)
    targets = set()
    for spell in spells:
        targets |= get_valid_targets(unit, spell)
    return targets
