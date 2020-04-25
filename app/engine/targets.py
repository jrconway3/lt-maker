from app import utilities
from app.data.database import DB
from app.data.item_components import SpellAffect, SpellTarget
from app.engine import a_star, interaction
from app.engine.game_state import game

class TargetSystem():
    def __init__(self):
        pass

    def check_ally(self, unit1, unit2):
        if 'ignore_alliances' in unit1.status_bundle:
            return True
        if unit1.team == 'player' or unit1.team == 'other':
            return unit2.team == 'player' or unit2.team == 'other'
        else:
            return unit2.team == unit1.team
        return False

    def check_enemy(self, unit1, unit2):
        if 'ignore_alliances' in unit1.status_bundle:
            return True
        if unit1.team == 'player' or unit1.team == 'other':
            return not (unit2.team == 'player' or unit2.team == 'other')
        else:
            return not unit2.team == unit1.team
        return True

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

    def get_adjacent_positions(self, pos):
        x, y = pos
        adjs = ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))
        return [a for a in adjs if 0 <= a[0] <= game.tilemap.width and 0 <= a[1] <= game.tilemap.height]

    # Uses all weapons the unit has access to to find its potential range
    def find_potential_range(self, unit, weapon=True, spell=False, boundary=False) -> set:
        if weapon and spell:
            items = [item for item in unit.items if unit.can_wield(item) and item.weapon or (item.spell and item.spell.affect == SpellAffect.Harmful)]
        elif weapon:
            items = [item for item in unit.items if item.weapon and unit.can_wield(item)]
        elif spell:
            items = [item for item in unit.items if item.spell and unit.can_wield(item)]
            if boundary:
                items = [item for item in items if item.spell.affect == SpellAffect.Harmful]
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

    def get_attacks(self, unit, weapon=None) -> tuple:
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
        attacks = self.get_shell({unit.position}, item_range, game.tilemap.width, game.tilemap.height)
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

    def get_spell_attacks(self, unit, spell=None) -> set:
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
        attacks = self.get_shell({unit.position}, item_range, game.tilemap.width, game.tilemap.height)

        # Now filter based on target:
        if spell.spell.target == SpellTarget.Enemy:
            attacks = {pos for pos in attacks if not utilities.compare_teams(unit.team, game.grid.get_team(pos))}
        elif spell.spell.target == SpellTarget.Ally:
            attacks = {pos for pos in attacks if utilities.compare_teams(unit.team, game.grid.get_team(pos)) is not False}
        # TODO line of sight

        return attacks

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
            if all(spell.spell.target == SpellTarget.Ally for spell in spells):
                valid_attacks = {pos for pos in valid_attacks if not game.grid.get_team(pos) or utilities.compare_teams(unit.team, game.grid.get_team(pos))}
            elif all(spell.spell.target == SpellTarget.Enemy for spell in spells):
                valid_attacks = {pos for pos in valid_attacks if not game.grid.get_team(pos) or not utilities.compare_teams(unit.team, game.grid.get_team(pos))}

        # TODO Line of Sight
        return valid_attacks

    def get_path(self, unit, position, ally_block=False) -> list:
        mtype = DB.classes.get(unit.klass).movement_group
        grid = game.grid.get_grid(mtype)

        width, height = game.tilemap.width, game.tilemap.height
        pathfinder = a_star.AStar(unit.position, position, grid, width, height, unit.team, 'pass_through' in unit.status_bundle)

        path = pathfinder.process(game.grid.team_grid, ally_block=ally_block)
        return path

    def get_valid_weapon_targets(self, unit, weapon=None, force_range=None) -> set:
        if weapon is None:
            weapon = unit.get_weapon()
        if weapon is None:
            return set()

        if force_range is not None:
            weapon_range = force_range
        else:
            weapon_range = game.equations.get_range(weapon, unit)

        enemy_pos = {enemy.position for enemy in game.level.units if enemy.position and self.check_enemy(unit, enemy)}
        valid_targets = {pos for pos in enemy_pos if utilities.calculate_distance(pos, unit.position) in weapon_range}
        return valid_targets

    def get_valid_spell_targets(self, unit, spell=None) -> set:
        if spell is None:
            spell = unit.get_spell()
        if spell is None:
            return set()

        spell_range = game.equations.get_range(spell, unit)

        if spell.spell.target == SpellTarget.Ally:
            if spell.heal:
                places_unit_can_target = self.find_manhattan_spheres(spell_range, unit.position)
                valid_units = {game.grid.get_unit(pos) for pos in places_unit_can_target}
                valid_pos = {u.position for u in valid_units if u and self.check_ally(unit, u)}
                targetable_pos = set()
                for pos in valid_pos:
                    defender, splash = interaction.convert_positions(unit, unit.position, pos, spell)
                    if (defender and defender.get_hp() < game.equations.hitpoints(defender)) or \
                            any(self.check_ally(unit, s) and s.get_hp() < game.equations.hitpoints(s) for s in splash):
                        targetable_pos.add(pos)
            else:
                targetable_pos = {ally.position for ally in game.level.units if ally.position and self.check_ally(unit, ally) and 
                                  utilities.calculate_distance(unit.position, ally.position) in spell_range}
        elif spell.spell.target == SpellTarget.Enemy:
            targetable_pos = {target.position for target in game.level.units if target.position and self.check_enemy(unit, target) and 
                              utilities.calculate_distance(unit.position, target.position) in spell_range}
        elif spell.spell.target == SpellTarget.Unit:
            targetable_pos = {target.position for target in game.level.units if target.position and 
                              utilities.calculate_distance(unit.position, target.position) in spell_range}

        return targetable_pos

    def get_all_weapon_targets(self, unit) -> set:
        weapons = [item for item in unit.items if item.weapon and unit.can_wield(item)]
        targets = set()
        for weapon in weapons:
            targets |= self.get_valid_weapon_targets(unit, weapon=weapon)
        return targets

    def get_all_spell_targets(self, unit) -> set:
        spells = [item for item in unit.items if item.spell and unit.can_wield(item)]
        targets = set()
        for spell in spells:
            targets |= self.get_valid_spell_targets(unit, spell=spell)
        return targets

class SelectionHelper():
    def __init__(self, pos_list):
        self.pos_list = pos_list

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
