import math

from app import utilities
from app.data.constants import FRAMERATE
from app.data.database import DB

from app.engine import engine, action, interaction, combat_calcs, a_star, unit_object, targets, equations, item_system
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

class AIController():
    def __init__(self):
        self.unit = None
        self.state = "Init"

        self.behaviour_idx = 0
        self.behaviour = None
        self.inner_ai = None

        self.did_something = False

        self.move_ai_complete = False
        self.attack_ai_complete = False
        self.canto_ai_complete = False

    def load_unit(self, unit):
        self.reset()
        self.unit = unit

    def reset(self):
        self.unit = None
        self.state = "Init"

        self.behaviour_idx = 0
        self.behaviour = None
        self.inner_ai = None

        self.did_something = False

        self.move_ai_complete = False
        self.attack_ai_complete = False
        self.canto_ai_complete = False

    def is_done(self):
        return self.move_ai_complete and self.attack_ai_complete and self.canto_ai_complete

    def clean_up(self):
        self.goal_position = None
        self.goal_item = None
        self.goal_target = None

    def set_next_behaviour(self):
        behaviours = DB.ai.get(self.unit.ai).behaviours
        if self.behaviour_idx < len(behaviours):
            self.behaviour = behaviours[self.behaviour_idx]
            self.behaviour_idx += 1
        else:
            self.behaviour = None
            self.behaviour_idx = 0

    def get_behaviour(self):
        return self.behaviour

    def act(self):
        logger.info("AI Act!")

        if not self.move_ai_complete:
            if self.think():
                self.move()
                self.move_ai_complete = True
        elif not self.attack_ai_complete:
            self.attack()
            self.attack_ai_complete = True
        elif not self.canto_ai_complete:
            if self.unit.has_attacked and self.unit.has_canto_plus():
                self.retreat()
                self.move()
            self.canto_ai_complete = True

        return self.did_something

    def move(self):
        if self.goal_position and self.goal_position != self.unit.position:
            path = targets.get_path(self.unit, self.goal_position)
            if self.unit.has_attacked:
                action.do(action.Wait(self.unit))
            game.state.change('movement')
            action.do(action.Move(self.unit, self.goal_position, path))
            return True
        else:
            return False

    def attack(self):
        if self.goal_target:  # Target is a tuple
            if self.goal_item:
                if self.goal_item in self.unit.items:
                    self.unit.equip(self.goal_item)
                    # Highlights
                    if self.goal_item.weapon:
                        game.highlight.remove_highlights()
                        attack_position, splash_positions = \
                            interaction.get_aoe(self.goal_item, self.unit, self.unit.position, self.goal_target)
                        game.highlight.display_possible_attacks({attack_position})
                        game.highlight.display_possible_attacks(splash_positions, light=True)
                    elif self.goal_item.spell:
                        game.highlight.remove_highlights()
                        attack_position, splash_positions = \
                            interaction.get_aoe(self.goal_item, self.unit, self.unit.position, self.goal_target)
                        if attack_position:
                            game.highlight.display_possible_spells({attack_position})
                        game.highlight.display_possible_spells(splash_positions)
                    # Combat
                    defender, splash = interaction.convert_positions(self.unit, self.unit.position, self.goal_target, self.goal_item)
                    game.combat_instance = interaction.start_combat(self.unit, defender, self.goal_target, splash, self.goal_item, ai_combat=True)
                    game.state.change('combat')

    def canto_retreat(self):
        valid_positions = self.get_true_valid_moves()
        enemy_positions = {u.position for u in game.level.units if u.position and targets.check_enemy(self.unit, u)}
        self.goal_position = utilities.farthest_away_pos(self.unit.position, valid_positions, enemy_positions)

    def smart_retreat(self):
        valid_positions = self.get_true_valid_moves()

        if self.behaviour.targets == 'Enemy':
            target_positions = {u.position for u in game.level.units if u.position and targets.check_enemy(self.unit, u)}
        elif self.behaviour.targets == 'Ally':
            target_positions = {u.position for u in game.level.units if u.position and targets.check_ally(self.unit, u)}
        elif self.behaviour.targets == 'Unit':
            target_positions = {u.position for u in game.level.units if u.position}

        zero_move = max(targets.find_potential_range(self.unit, True, True))
        single_move = zero_move + equations.parser.movement(self.unit)
        double_move = self.single_move + equations.parser.movement(self.unit)

        target_positions = {(pos, utilities.calculate_distance(self.unit.position, pos)) for pos in target_positions}

        if self.behaviour.view_range == -4:
            pass
        elif self.behaviour.view_range == -3:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < double_move}
        elif self.behaviour.view_range == -2:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < single_move}
        elif self.behaviour.view_range == -1:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < zero_move}
        else:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < self.view_range}

        self.goal_position = utilities.smart_farthest_away_pos(self.unit.position, valid_positions, target_positions)

    def get_true_valid_moves(self) -> set:
        valid_moves = targets.get_valid_moves(self.unit)
        other_unit_positions = {unit.position for unit in game.level.units if unit.position and unit is not self.unit}
        valid_moves -= other_unit_positions
        return valid_moves

    def think(self):
        time = engine.get_time()
        success = False
        self.did_something = False
        orig_pos = self.unit.position

        logger.info("AI Thinking...")

        # Can spend up to half a frame thinking
        while engine.get_true_time() - time < FRAMERATE//2:
            logger.info("Current State: %s", self.state)

            if self.state == 'Init':
                self.start_time = engine.get_time()
                logger.info("Starting AI with nid: %s, position: %s, class: %s, AI: %s", self.unit.nid, self.unit.position, self.unit.klass, self.unit.ai)
                self.clean_up()
                # Get next behaviour
                self.set_next_behaviour()
                if self.behaviour:
                    if self.behaviour.action == "None":
                        pass  # Try again
                    elif self.behaviour.action == "Attack":
                        self.inner_ai = self.build_primary()
                        self.state = "Primary"
                    elif self.behaviour.action == 'Move_to':
                        self.inner_ai = self.build_secondary()
                        self.state = "Secondary"
                    elif self.behaviour.action == "Move_away_from":
                        self.smart_retreat()
                        success = True
                        self.state = "Done"
                else:
                    self.state = 'Done'

            elif self.state == 'Primary':
                done, self.goal_target, self.goal_position, self.goal_item = self.inner_ai.run()
                if done:
                    if self.goal_target:
                        success = True
                        self.state = "Done"
                    else:
                        self.inner_ai = self.build_secondary()
                        self.state = "Secondary"  # Try secondary

            elif self.state == 'Secondary':
                done, self.goal_position = self.inner_ai.run()
                if done:
                    if self.goal_position:
                        success = True
                        self.state = "Done"
                    else:
                        self.state = "Init"  # Try another behaviour

            if self.state == 'Done':
                self.did_something = success
                self.state = 'Init'
                return True

        return False

    def build_primary(self):
        if self.behaviour.view_range == -1:  # Guard AI
            valid_moves = {self.unit.position}
        else:
            valid_moves = self.get_true_valid_moves()

        return PrimaryAI(self.unit, valid_moves, self.behaviour)

    def build_secondary(self):
        return SecondaryAI(self.unit, self.behaviour)

class PrimaryAI():
    def __init__(self, unit, valid_moves, behaviour):
        self.max_tp = 0

        self.unit = unit
        self.orig_pos = self.unit.position
        self.orig_item = self.unit.items[0] if self.unit.items else None
        self.behaviour = behaviour

        if self.behaviour.action == "Attack":
            self.items = [item for item in self.unit.items if 
                          self.unit.can_wield(item) and
                          (item.weapon or item.spell or item.usable) and not item.no_ai]

        self.all_targets = self.get_all_targets(self.unit)

        logger.info("Testing Items: %s", self.items)
        
        self.item_index = 0
        self.move_index = 0
        self.target_index = 0

        self.valid_moves = list(valid_moves)
        self.possible_moves = []

        self.best_target = None
        self.best_position = None
        self.best_item = None

        if self.item_index < len(self.items):
            self.unit.equip(self.items[self.item_index])
            self.get_all_valid_targets()
            self.possible_moves = self.get_possible_moves()

    def get_all_targets(self, unit) -> set:
        if self.behaviour.target == "Enemy":
            targets = {u for u in game.level.units if u.position and targets.check_enemy(unit, u)}
        elif self.behaviour.target == "Unit":
            targets = {u for u in game.level.units if u.position}
        elif self.behaviour.target == "Ally":
            targets = {u for u in game.level.units if u.position and targets.check_ally(unit, u)}
        elif self.behaviour.target == "Tile":
            targets = set()  # TODO add destroyable tiles
        return targets

    def get_valid_targets(self, unit, item, valid_moves) -> list:
        item_range = item_system.get_range(unit, item)
        valid_targets = set()

        if item.weapon:
            filtered_targets = [u.position for u in self.all_targets if targets.check_enemy(unit, u)]
        elif item.spell:
            if item.spell.target == SpellTarget.Ally:
                filtered_targets = [u.position for u in self.all_targets if targets.check_ally(unit, u)]
            elif item.spell.target == SpellTarget.Enemy:
                filtered_targets = [u.position for u in self.all_targets if targets.check_enemy(unit, u)]
            else:
                filtered_targets = [u.position for u in self.all_targets]

        while filtered_targets:
            pos = filtered_targets.pop()
            for valid_move in valid_moves:
                # Determine if we can hit this unit at one of our moves
                if utilities.calculate_distance(pos, valid_move) in item_range:
                    valid_targets.add(pos)
                    break

        return list(valid_targets)

    def get_all_valid_targets(self):
        item = self.items[self.item_index]
        logger.info(item)
        self.valid_targets = self.get_valid_targets(self.unit, item, self.valid_moves)
        if 0 in item_system.get_range(self.unit, item):
            self.valid_targets += self.valid_moves  # Hack to target self in all valid positions
            self.valid_targets = list(set(self.valid_targets))  # Only uniques
        logger.info("Valid Targets: %s", self.valid_targets)

    def get_possible_moves(self):
        if self.target_index < len(self.valid_targets) and self.item_index < len(self.items):
            # Given an item and a target, find all positions in valid_moves that I can strike the target at.
            item = self.items[self.item_index]
            target = self.valid_targets[self.target_index]
            a = targets.find_manhattan_spheres(item_system.get_range(self.unit, item), target[0], target[1])
            b = set(self.valid_moves)
            return list(a & b)
        else:
            return []

    def quick_move(self, move):
        game.leave(self.unit, test=True)
        self.unit.position = move
        game.arrive(self.unit, test=True)

    def run(self):
        if self.item_index >= len(self.items):
            self.quick_move(self.orig_pos)
            if self.orig_item:
                self.unit.equip(self.orig_item)
            return (True, self.best_target, self.best_position, self.best_item)

        elif self.target_index >= len(self.valid_targets):
            self.target_index = 0
            self.item_index += 1
            if self.item_index < len(self.items):
                self.unit.equip(self.items[self.item_index])
                self.get_all_valid_targets()
                self.possible_moves = self.get_possible_moves()

        elif self.move_index >= len(self.possible_moves):
            self.move_index = 0
            self.target_index += 1
            self.possible_moves = self.get_possible_moves()

        else:
            target = self.valid_targets[self.target_index]
            item = self.items[self.item_index]
            move = self.possible_moves[self.move_index]
            if self.unit.position != move:
                self.quick_move(move)

            self.determine_utility(move, target, item)
            self.move_index += 1

        # Not done yet
        return (False, self.best_target, self.best_position, self.best_item)

    def determine_utility(self, move, target, item):
        defender, splash = interaction.convert_positions(self.unit, move, target, item)
        tp = 0
        if defender or splash:
            if item.spell:
                tp = self.compute_priority_spell(defender, splash, move, item)
            elif item.weapon:
                tp = self.compute_priority_weapon(defender, splash, move, item)
            if item.usable:
                itp = self.compute_prority_usable(defender, splash, move, item)
                if itp > tp:  # Only use usable if greater than item spell or weapon
                    tp = itp
        unit = game.grid.get_unit(target)
        if unit:
            name = unit.nid
        else:
            name = '--'

        logger.info("Choice %s - Weapon: %s, Position: %s, Target: %s, Target Position: %s", tp, item, move, name, target)
        if tp > self.max_tp:
            self.best_target = target
            self.best_position = move
            self.best_item = item
            self.max_tp = tp

    def compute_priority_weapon(self, defender, splash, move, item):
        terms = []

        offensive_term = 0
        defensive_term = 1
        status_term = 0

        if defender:
            target = defender
            raw_damage = combat_calcs.compute_damage(self.unit, target, item, "Attack")
            crit_damage = combat_calcs.compute_damage(self.unit, target, item, "Attack", crit=True)

            # Damage I do compared to target's current hp
            lethality = utilities.clamp(raw_damage / float(target.get_hp()), 0, 1)
            # TODO Do I add a new status to the target
            status = 0
            # Accuracy
            accuracy = utilities.clamp(combat_calcs.compute_hit(self.unit, target, item, "Attack")/100., 0, 1)
            crit_accuracy = utilities.clamp(combat_calcs.compute_crit(self.unit, target, item, "Attack")/100., 0, 1)

            target_damage = 0
            target_accuracy = 0
            # Determine if I would get countered
            target_weapon = target.get_weapon()
            if target_weapon and utilities.calculate_distance(move, target.position) in item_system.get_range(target_weapon, target):
                target_damage = utilities.clamp(combat_calcs.compute_damage(target, self.unit, target_weapon, "Defense"), 0, 1)
                target_accuracy = utilities.clamp(combat_calcs.compute_hit(target, self.unit, target_weapon, "Defense")/100., 0, 1)

            double = 1 if combat_calcs.outspeed(self.unit, target, item, "Attack") else 0
            first_strike = lethality * accuracy if lethality == 1 else 0

            if double and target_damage >= 1:
                # Calculate chance I actually get to strike twice
                double *= (1 - (target_accuracy * (1 - first_strike)))

            offensive_term += 3 if lethality * accuracy >= 1 else lethality * accuracy * (double + 1)
            offensive_term += crit_damage * crit_accuracy * accuracy * (double + 1)
            status_term += status * min(1, accuracy * (double + 1))
            defensive_term -= target_damage * target_accuracy * (1 - first_strike)

        splash = [s for s in splash if isinstance(s, unit_object.UnitObject)]

        for target in splash:
            raw_damage = combat_calcs.compute_damage(self.unit, target, item, "Attack")
            lethality = utilities.clamp(raw_damage / float(target.get_hp()), 0, 1)
            status = 0
            accuracy = utilities.clamp(combat_calcs.compute_hit(self.unit, target, item, "Attack")/100., 0, 1)

            offensive_term += 3 if lethality * accuracy == 1 else lethality * accuracy
            status_term += status * accuracy

        if offensive_term <= 0 and status_term <= 0:
            logger.info("Offense: %d, Defense: %d, Status: %d", offensive_term, defensive_term, status_term)
            return 0

        # Only here to break ties
        # Tries to minmize how far the unit should move
        max_distance = equations.parser.movement(self.unit)
        if max_distance > 0:
            distance_term = (max_distance - utilities.calculate_distance(move, self.orig_pos)) / float(max_distance)
        else:
            distance_term = 1

        logger.info("Damage: %s, Accuracy: %s", lethality, accuracy)
        logger.info("Offense: %s, Defense: %s, Status: %s, Distance: %s", offensive_term, defensive_term, status_term, distance_term)
        terms.append((offensive_term, 49))
        terms.append((status_term, 10))
        terms.append((defensive_term, 20))
        terms.append((distance_term, 1))

        return utilities.process_terms(terms)

    def compute_priority_spell(self, defender, splash, move, item):
        terms = []
        closest_enemy_distance = targets.distance_to_closest_enemy(self.unit, move)

        targets = [s for s in splash if isinstance(s, unit_object.UnitObject)]
        if defender:
            targets.insert(0, defender)

        if item.spell.affect == SpellAffect.Helpful:
            if item.heal_on_hit:
                heal_term = 0
                help_term = 0

                for target in targets:
                    if targets.check_ally(self.unit, target):
                        max_hp = equations.parser.hitpoints(target)
                        missing_health = max_hp - target.get_hp()
                        help_term += utilities.clamp(missing_health / float(max_hp), 0, 1)
                        spell_heal = combat_calcs.compute_heal(self.unit, target, item, 'Attack')
                        heal_term += utilities.clamp(min(spell_heal, missing_health) / float(max_hp), 0, 1)

                    logger.info("Help: %s, Heal: %s", help_term, heal_term)
                    if help_term <= 0:
                        return 0

                    terms.append((help_term, 40))
                    terms.append((heal_term, 40))

            elif item.status:
                # TODO status
                status_term = 0
                terms.append((status_term, 40))

            closest_enemy_term = math.log(closest_enemy_distance)/4.
            terms.append((closest_enemy_term, 10))

        else:
            offensive_term = 0
            status_term = 0

            for target in targets:
                raw_damage = combat_calcs.compute_damage(self.unit, target, item, "Attack")
                crit_damage = combat_calcs.compute_damage(self.unit, target, item, "Attack", crit=True)

                # Damage I do compared to target's current hp
                lethality = utilities.clamp(raw_damage / float(target.get_hp()), 0, 1)
                # TODO Do I add a new status to the target
                status = 0
                # Accuracy
                accuracy = utilities.clamp(combat_calcs.compute_hit(self.unit, target, item, "Attack")/100., 0, 1)
                crit_accuracy = utilities.clamp(combat_calcs.compute_crit(self.unit, target, item, "Attack")/100., 0, 1)

                if targets.check_enemy(self.unit, target):
                    offensive_term += lethality * accuracy
                    offensive_term += crit_damage * crit_accuracy * accuracy
                    status_term += status * accuracy
                else:
                    offensive_term -= lethality * accuracy
                    offensive_term -= crit_damage * crit_accuracy * accuracy
                    status_term -= status * accuracy

                logger.info("Damage: %s, Accuracy: %s", lethality, accuracy)

            if offensive_term <= 0 and status_term <= 0:
                logger.info("Offense: %d, Status: %d", offensive_term, status_term)
                return 0

            # Only here to break ties
            closest_enemy_term = math.log(closest_enemy_distance)/4.
            terms.append((closest_enemy_term, 1))

            logger.info("Offense: %s, Status: %s, Distance: %s", offensive_term, status_term, closest_enemy_term)
            terms.append((offensive_term, 59))
            terms.append((status_term, 20))
            terms.append((closest_enemy_term, 1))

        return utilities.process_terms(terms)

    # Currently only computes utility correctly for healing items
    def compute_priority_usable(self, defender, splash, move, item):
        terms = []
        closest_enemy_distance = targets.distance_to_closest_enemy(self.unit, move)
        if item.heal_on_use:
            max_hp = equations.parser.hitpoints(self.unit)
            missing_health = max_hp - defender.get_hp()
            if missing_health <= 0:
                return 0
            heal_term = utilities.clamp(int(item.heal_on_use.value) / float(missing_health), 0, 1)
            help_term = utilities.clamp(missing_health / float(max_hp), 0, 1)
            terms.append((heal_term, 10))
            terms.append((help_term, 20))

            closest_enemy_term = math.log(closest_enemy_distance)/4.
            terms.append((closest_enemy_term, 5))

            logger.info("Help: %s, Heal: %s", help_term, heal_term)
            return utilities.process_terms(terms) / 2  # Divide by two to make it less likely to make this choice
        else:
            return 0

class SecondaryAI():
    def __init__(self, unit, behaviour):
        self.unit = unit
        self.behaviour = behaviour
        self.view_range = self.behaviour.view_range
        if self.view_range == -4:
            self.view_range = -3  # Try this first

        self.available_targets = []

        # Determine all targets
        if self.behaviour.action == "Attack":
            if self.behaviour.target == "Enemy":
                self.all_targets = [u.position for u in game.level.units if u.position and targets.check_enemy(self.unit, u)]
            elif self.behaviour.target == "Unit":
                self.all_targets = [u.position for u in game.level.units if u.position]
            elif self.behaviour.target == "Ally":
                self.all_targets = [u.position for u in game.level.units if u.position and targets.check_ally(self.unit, u)]
            elif self.behaviour.target == "Tile":
                # TODO add breakable tiles
                self.all_targets = []
        elif self.behaviour.action == "Move_to":
            # Move to a specific position
            if self.behaviour.target == "Position":
                if self.behaviour.target_spec == ["Starting"]:
                    self.all_targets = [self.unit.starting_position]
                else:
                    self.all_targets = [tuple(self.behaviour.target_spec)]
            elif self.behaviour.target == "Ally":
                self.all_targets = [u for u in game.level.units if u.position and targets.check_ally(self.unit, u)]
                if self.behaviour.target_spec:
                    if self.behaviour.target_spec[0] == "Tag":
                        self.all_targets = [u.position for u in self.all_targets if self.behaviour.target_spec[1] in u.tags]
                    elif self.behaviour.target_spec[0] == "Class":
                        self.all_targets = [u.position for u in self.all_targets if u.klass == self.behaviour.target_spec[1]]
                else:
                    self.all_targets = [u.position for u in self.all_targets]

        self.single_move = equations.parser.movement(self.unit) + max(targets.find_potential_range(self.unit, True, True))
        self.double_move = self.single_move + equations.parser.movement(self.unit)

        mtype = DB.classes.get(self.unit.klass).movement_group
        self.grid = game.grid.get_grid(mtype)
        self.pathfinder = a_star.AStar(self.unit.position, None, self.grid, 
                                       game.tilemap.width, game.tilemap.height, 
                                       self.unit.team, 'pass_through' in self.unit.status_bundle)

        self.widen_flag = False  # Determines if we've widened our search
        self.reset()

    def reset(self):
        self.max_tp = 0
        self.best_target = 0
        self.best_path = None

        if self.view_range == -3:
            self.available_targets = [t for t in self.all_targets if utilities.calculate_distance(self.unit.position, t) <= self.double_move]
        elif self.view_range == -2:
            self.available_targets = [t for t in self.all_targets if utilities.calculate_distance(self.unit.position, t) <= self.single_move]
        elif self.view_range == -1:
            self.available_targets = []
        else:
            self.available_targets = [t for t in self.all_targets if utilities.calculate_distance(self.unit.position, t) <= self.view_range]

        self.best_position = None

    def run(self):
        if self.available_targets:
            target = self.available_targets.pop()
            # Find a path to the target
            path = self.get_path(target)
            if not path:
                logger.info("No valid path to %s.", target)
                return False, None
            # We found a path
            tp = self.compute_priority(target, len(path))
            logger.info("Path to %s. -- %s", target, tp)
            if tp > self.max_tp:
                self.max_tp = tp
                self.best_target = target
                self.best_path = path

        elif self.best_target:
            self.best_position = targets.travel_algorithm(self.best_path, self.unit.movement_left, self.unit, self.grid)
            return True, self.best_position

        else:
            if self.behaviour.view_range == -4 and not self.widen_flag:
                logger.info("Widening search!")
                self.widen_flag = True
                self.view_range = -4
                self.available_targets = [t for t in self.all_targets if t not in self.available_targets]
            else:
                return True, None
        return False, None

    def get_path(self, goal_pos):
        self.pathfinder.set_goal_pos(goal_pos)
        path = self.pathfinder.process(game.grid.team_grid, adj_good_enough=True, ally_block=False)
        self.pathfinder.reset()
        return path

    def compute_priority(self, target, distance=0):
        terms = []
        if distance:
            distance_term = 1 - math.log(distance)/4.
        else:
            target_distance = utilities.calculate_distance(self.unit.position, target)
            distance_term = 1 - math.log(target_distance)/4.
        terms.append((distance_term, 60))

        enemy = game.grid.get_unit(target)
        if self.behaviour.action == "Attack" and enemy and targets.check_enemy(self.unit, enemy):
            hp_max = equations.parser.hitpoints(enemy)
            weakness_term = float(hp_max - enemy.get_hp()) / hp_max

            max_damage = 0
            status_term = 0
            items = [item for item in self.unit.items if self.unit.can_wield(item)]
            for item in items:
                if item.status:
                    status_term = 1
                if item.weapon or item.spell:
                    raw_damage = combat_calcs.compute_damage(self.unit, enemy, item)
                    hit = utilities.clamp(combat_calcs.compute_hit(self.unit, enemy, item)/100., 0, 1)
                    true_damage = raw_damage * hit
                    if true_damage > max_damage:
                        max_damage = true_damage

                if max_damage <= 0 and status_term <= 0:
                    return 0  # If no damage could be dealt, ignore
                damage_term = min(float(max_damage / hp_max), 1.)
                terms.append((damage_term, 15))
                terms.append((weakness_term, 15))
                terms.append((status_term, 10))

        else:
            pass

        return utilities.process_terms(terms)
