from app import utilities
from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.database import DB
from app.data.item_components import SpellTarget
from app.engine import a_star, interaction, status_system, item_system
from app.engine.game_state import game

# Consider making these sections faster
def get_shell(valid_moves: set, potential_range: set, width: int, height: int) -> set:
    valid_attacks = set()
    for valid_move in valid_moves:
        valid_attacks |= find_manhattan_spheres(potential_range, valid_move[0], valid_move[1])
    return {pos for pos in valid_attacks if pos[0] >= 0 and pos[1] >= 0 and pos[0] < width and pos[1] < height}

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

def distance_to_closest_enemy(unit, pos=None):
    if pos is None:
        pos = unit.position
    enemy_list = [u for u in game.level.units if u.position and status_system.check_enemy(u, unit)]
    if not enemy_list:
        return 100  # No enemies
    dist_list = [utilities.calculate_distance(enemy.position, pos) for enemy in enemy_list]
    return min(dist_list)

def get_adjacent_positions(pos):
    x, y = pos
    adjs = ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))
    return [a for a in adjs if 0 <= a[0] <= game.tilemap.width and 0 <= a[1] <= game.tilemap.height]

# Uses all weapons the unit has access to to find its potential range
def find_potential_range(unit, weapon=True, spell=False, boundary=False) -> set:
    if weapon and spell:
        items = [item for item in unit.items if item_system.available(unit, item) and
                 item_system.is_weapon(unit, item) or item_system.is_spell(unit, item)]
    elif weapon:
        items = [item for item in unit.items if item_system.available(unit, item) and
                 item_system.is_weapon(unit, item)]
    elif spell:
        items = [item for item in unit.items if item_system.available(unit, item) and
                 item_system.is_spell(unit, item)]
    else:
        return set()
    potential_range = set()
    for item in items:
        for rng in item_system.get_range(unit, item):
            potential_range.add(rng)
    return potential_range

def get_valid_moves(unit, force=False) -> set:
    # Assumes unit is on the map
    if not force and unit.finished or (unit.has_moved and not status_system.has_canto(unit)):
        return set()

    mtype = DB.classes.get(unit.klass).movement_group
    grid = game.grid.get_grid(mtype)
    width, height = game.tilemap.width, game.tilemap.height
    pathfinder = a_star.Djikstra(unit.position, grid, width, height, unit.team, 'pass_through' in unit.status_bundle)

    movement_left = game.equations.movement(unit) if force else unit.movement_left
    # Alternative method if the first thing doesn't work
    # Maybe also try functools.update_wrapper
    # movement_left = game.equations.get('MOVEMENT', unit) if force else unit.movement_left

    valid_moves = pathfinder.process(game.grid.team_grid, movement_left)
    valid_moves.add(unit.position)
    return valid_moves

def get_attacks(unit, weapon=None) -> tuple:
    """
    Determines all possible positions the unit could attack, given
    one main weapon or an optionally given main weapon
    Should be called after unit has moved
    Does not attempt to determine if an enemy is actually in that specific place
    """
    if unit.has_attacked:
        return set(), set()
    if not weapon:
        weapon = unit.get_weapon()
    if not weapon:
        return set(), set()

    # Calculate legal targets for cursor
    item_range = game.equations.get_range(weapon, unit)
    attacks = get_shell({unit.position}, item_range, game.tilemap.width, game.tilemap.height)
    attacks = {pos for pos in attacks if not utilities.compare_teams(unit.team, game.grid.get_team(pos))}
    # TODO line of sight

    # Now actually find true and splash attack position
    true_attacks = set()
    splash_attacks = set()
    for position in attacks:
        attack, splash_pos = interaction.get_aoe(weapon, unit, unit.position, position)
        if attack:
            true_attacks.add(attack)
        splash_attacks |= splash_pos
    splash_attacks -= true_attacks
    return true_attacks, splash_attacks

def get_spell_attacks(unit, spell=None) -> set:
    """
    Determines all possible positions the unit could spell, given
    one spell or an optionally given spell
    Should be called after unit has moved
    Does not attempt to determine if an enemy is actually in that specific place
    """
    if unit.has_attacked:
        return set()
    if not spell:
        spell = unit.get_spell()
    if not spell:
        return set()

    # Calculate legal targets
    item_range = game.equations.get_range(spell, unit)
    attacks = get_shell({unit.position}, item_range, game.tilemap.width, game.tilemap.height)

    # Now filter based on target:
    if spell.spell.target == SpellTarget.Enemy:
        attacks = {pos for pos in attacks if not utilities.compare_teams(unit.team, game.grid.get_team(pos))}
    elif spell.spell.target == SpellTarget.Ally:
        attacks = {pos for pos in attacks if utilities.compare_teams(unit.team, game.grid.get_team(pos)) is not False}
    # TODO line of sight

    return attacks

def get_possible_attacks(unit, valid_moves: set, boundary=False) -> set:
    """
    Given all valid moves the unit can go to
    returns all positions the unit could attack with at least one weapon
    """
    potential_range = find_potential_range(unit, weapon=True, boundary=boundary)

    valid_attacks = get_shell(valid_moves, potential_range, game.tilemap.width, game.tilemap.height)
    # Cannot attack own team
    if not boundary:
        combined_targets = get_all_weapon_targets(unit)
        for pos in valid_attacks:
            if game.grid.get_unit() and pos not in combined_targets:
                valid_attacks.remove(pos)

    # TODO Line of Sight
    return valid_attacks

def get_possible_spell_attacks(unit, valid_moves: set, boundary=False) -> set:
    """
    Given all valid moves the unit can go to
    returns all positions the unit could attack with at least one spell
    """
    potential_range: set = find_potential_range(unit, spell=True, boundary=boundary)

    valid_attacks = get_shell(valid_moves, potential_range, game.tilemap.width, game.tilemap.height)
    # Cannot attack own team
    if not boundary:
        combined_targets = get_all_spell_targets(unit)
        for pos in valid_attacks:
            if game.grid.get_unit() and pos not in combined_targets:
                valid_attacks.remove(pos)

    # TODO Line of Sight
    return valid_attacks

def get_path(unit, position, ally_block=False) -> list:
    mtype = DB.classes.get(unit.klass).movement_group
    grid = game.grid.get_grid(mtype)

    width, height = game.tilemap.width, game.tilemap.height
    pathfinder = a_star.AStar(unit.position, position, grid, width, height, unit.team, 'pass_through' in unit.status_bundle)

    path = pathfinder.process(game.grid.team_grid, ally_block=ally_block)
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

def get_valid_targets(unit, item=None):
    if not item:
        item = unit.get_equipped_item()
    if not item:
        return set()
    return item_system.valid_targets(unit, item)

def get_all_weapon_targets(unit) -> set:
    weapons = [item for item in unit.items if item_system.is_weapon(unit, item) and item_system.available(unit, item)]
    targets = set()
    for weapon in weapons:
        targets |= item_system.valid_targets(unit, weapon)
    return targets

def get_all_spell_targets(unit) -> set:
    spells = [item for item in unit.items if item_system.is_spell(unit, item) and item_system.available(unit, item)]
    targets = set()
    for spell in spells:
        targets |= item_system.valid_targets(unit, spell)
    return targets

class SelectionHelper():
    def __init__(self, pos_list):
        self.pos_list = pos_list

    def handle_mouse(self):
        mouse_position = game.input_manager.get_mouse_position()
        if mouse_position:
            new_pos = mouse_position[0] // TILEWIDTH, mouse_position[1] // TILEHEIGHT
            if new_pos in self.pos_list:
                return new_pos
        return None

    # For a given position, determine which position in self.pos_list is closest
    def get_closest(self, position):
        if self.pos_list:
            return min(self.pos_list, key=lambda pos: utilities.calculate_distance(pos, position))
        else:
            return None

    # For a given position, determine which position in self.pos_list is the closest position in the downward direction
    def get_down(self, position):
        min_distance, closest = 100, None
        for pos in self.pos_list:
            if pos[1] > position[1]: # If further down than the position
                dist = utilities.calculate_distance(pos, position)
                if dist < min_distance:
                    closest = pos
                    min_distance = dist
        if closest is None: # Nothing was found in the down direction
            # Just find the closest
            closest = self.get_closest(position)
        return closest

    def get_up(self, position):
        min_distance, closest = 100, None
        for pos in self.pos_list:
            if pos[1] < position[1]: # If further up than the position
                dist = utilities.calculate_distance(pos, position)
                if dist < min_distance:
                    closest = pos
                    min_distance = dist
        if closest is None: # Nothing was found in the down direction
            # Just find the closest
            closest = self.get_closest(position)
        return closest

    def get_right(self, position):
        min_distance, closest = 100, None
        for pos in self.pos_list:
            if pos[0] > position[0]: # If further right than the position
                dist = utilities.calculate_distance(pos, position)
                if dist < min_distance:
                    closest = pos
                    min_distance = dist
        if closest is None: # Nothing was found in the down direction
            # Just find the closest
            closest = self.get_closest(position)
        return closest

    def get_left(self, position):
        min_distance, closest = 100, None
        for pos in self.pos_list:
            if pos[0] < position[0]: # If further left than the position
                dist = utilities.calculate_distance(pos, position)
                if dist < min_distance:
                    closest = pos
                    min_distance = dist
        if closest is None: # Nothing was found in the down direction
            # Just find the closest
            closest = self.get_closest(position)
        return closest
