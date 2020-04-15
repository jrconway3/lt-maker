from app import utilities
from app.data.database import DB
from app.data.item_components import SpellAffect, SpellTarget
from app.engine import a_star
from app.engine.game_state import game

class TargetSystem():
    def __init__(self):
        pass

    # Consider making these sections faster
    def get_shell(self, valid_moves: set, potential_range: set, width: int, height: int) -> set:
        valid_attacks = set()
        for valid_move in valid_moves:
            valid_attacks |= self.find_manhattan_spheres(potential_range, valid_move[0], valid_move[1])
        return {pos for pos in valid_attacks if pos[0] >= 0 and pos[1] >= 0 and pos[0] < width and pos[1] < height}

    # Consider making these sections faster -- use memory?
    def find_manhattan_spheres(self, rng: set, x: int, y: int) -> set:
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

    # Uses all weapons the unit has access to to find its potential range
    def find_potential_range(self, unit, weapon=True, spell=False, boundary=False) -> set:
        if weapon and spell:
            items = [item for item in unit.items if unit.can_wield(item) and item.weapon or (item.spell and item.spell.value[1] == SpellAffect.Harmful)]
        elif weapon:
            items = [item for item in unit.items if item.weapon and unit.can_wield(item)]
        elif spell:
            items = [item for item in unit.items if item.spell and unit.can_wield(item)]
            if boundary:
                items = [item for item in items if item.spell.value[1] == SpellAffect.Harmful]
        else:
            return []
        potential_range = set()
        for item in items:
            for rng in game.equations.get_range(item, unit):
                potential_range.add(rng)
        return potential_range

    def get_valid_moves(self, unit, force=False) -> set:
        # Assumes unit is on the map
        if not force and unit.finished or (unit.has_moved and not unit.has_canto()):
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

    def get_possible_attacks(self, unit, valid_moves: set, boundary=False) -> set:
        potential_range = self.find_potential_range(unit, weapon=True, boundary=boundary)

        valid_attacks = self.get_shell(valid_moves, potential_range, game.tilemap.width, game.tilemap.height)
        # Cannot attack own team
        if not boundary:
            valid_attacks = {pos for pos in valid_attacks if not utilities.compare_teams(unit.team, game.grid.get_team(pos))}
        # TODO Line of Sight
        return valid_attacks

    def get_possible_spell_attacks(self, unit, valid_moves: set, boundary=False) -> set:
        potential_range = self.find_potential_range(unit, spell=True, boundary=boundary)

        valid_attacks = self.get_shell(valid_moves, potential_range, game.tilemap.width, game.tilemap.height)
        # Cannot attack own team
        if not boundary:
            spells = [item for item in unit.items if item.spell and unit.can_wield(item)]
            # If can only hit allies, ignore enemies
            if all(spell.spell.value[2]== SpellTarget.Ally for spell in spells):
                valid_attacks = {pos for pos in valid_attacks if not game.grid.get_team(pos) or utilities.compare_teams(unit.team, game.grid.get_team(pos))}
            elif all(spell.spell.valud[2] == SpellTarget.Enemy for spell in spells):
                valid_attacks = {pos for pos in valid_attacks if not game.grid.get_team(pos) or not utilities.compare_teams(unit.team, game.grid.get_team(pos))}

        # TODO Line of Sight
        return valid_attacks
