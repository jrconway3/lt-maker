import math

from app import utilities
from app.data.constants import FRAMERATE
from app.data.item_components import SpellAffect
from app.data.database import DB
from app.data import unit_object

from app.engine import engine, action, interaction, combat_calcs, a_star
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
                self.canto_retreat()
                self.move()
            self.canto_ai_complete = True

        return self.did_something

    def move(self):
        if self.goal_position and self.goal_position != self.unit.position:
            path = game.targets.get_path(self.unit, self.goal_position)
            if self.unit.has_attacked:
                action.do(action.Wait(self.unit))
            game.state.change('movement')
            action.do(action.Move(self.unit, self.goal_position, path))
            return True
        else:
            return False

    def attack(self):
        if self.goal_target:
            if self.goal_item:
                if self.goal_item in self.unit.items:
                    self.unit.equip(self.goal_item)
                    # Highlights
                    if self.goal_item.weapon:
                        game.highlight.remove_highlights()
                        attack_position, splash_positions = \
                            interaction.get_aoe(self.goal_item, self.unit, self.unit.position, self.goal_target.position)
                        game.highlight.display_possible_attacks({attack_position})
                        game.highlight.display_possible_attacks(splash_positions, light=True)
                    elif self.goal_item.spell:
                        game.highlight.remove_highlights()
                        attack_position, splash_positions = \
                            interaction.get_aoe(self.goal_item, self.unit, self.unit.position, self.goal_target.position)
                        if attack_position:
                            game.highlight.display_possible_spells({attack_position})
                        game.highlight.display_possible_spells(splash_positions)
                    # Combat
                    defender, splash = interaction.convert_positions(self.unit, self.unit.position, self.goal_target.position, self.goal_item)
                    game.combat_instance = interaction.start_combat(self.unit, defender, self.goal_target.position, splash, self.goal_item)
                    game.state.change('combat')

    def canto_retreat(self):
        valid_positions = self.get_true_valid_moves()
        enemy_positions = {u.position for u in game.level.units if u.position and game.targets.check_enemy(self.unit, u)}
        self.goal_position = utilities.farthest_away_pos(self.unit.position, valid_positions, enemy_positions)

    def get_true_valid_moves(self) -> set:
        valid_moves = game.targets.get_valid_moves(self.unit)
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

    def build_attack_primary(self):
        if self.behaviour.view_range == -1:  # Guard AI
            valid_moves = {self.unit.position}
        else:
            valid_moves = self.get_true_valid_moves()

        return PrimaryAI(self.unit, valid_moves, self.behaviour)

    def build_attack_secondary(self):
        return SecondaryAI(self.unit, self.behaviour)

class PrimaryAI():
    def __init__(self, unit, valid_moves, behaviour):
        self.max_tp = 0

        self.unit = unit
        self.orig_pos = self.unit.position
        self.orig_item = self.unit.items[0] if self.unit.items else None
        self.behaviour = behaviour

        if self.behaviour.action == "Attack":
            self.items = [item for item in self.unit.items if self.unit.can_wield(item) and 
                          (item.weapon or (item.spell and item.spell.affect == SpellAffect.Harmful))]

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

    def get_targets(self, unit, item, valid_moves):
        targets = set()
        item_range = game.equations.get_range(item, unit)

        if self.behaviour.target == "Enemy":
            test = [u.position for u in game.level.units if u.position and game.targets.check_enemy(unit, u)]
            while test:
                pos = test.pop()
                for valid_move in valid_moves:
                    if utilities.calculate_distance(pos, valid_move) in item_range:
                        targets.add(pos)
                        break
        elif self.behaviour.target == "Tile":
            # TODO add destroyable tiles
            pass

        return targets

    def get_all_valid_targets(self):
        item = self.items[self.item_index]
        logger.info(item)
        self.valid_targets = self.get_targets(self.unit, item, self.valid_moves)
        if 0 in game.equations.get_range(item, self.unit):
            self.valid_targets += self.valid_moves  # Hack to target self in all valid positions
            self.valid_targets = list(set(self.valid_targets))  # Only uniques
        logger.info("Valid Targets: %s", self.valid_targets)

    def get_possible_moves(self):
        if self.target_index < self.valid_targets and self.item_index < len(self.items):
            # Given an item and a target, find all positions in valid_moves that I can strike the target at.
            item = self.items[self.item_index]
            target = self.valid_targets[self.target_index]
            a = game.targets.find_manhattan_spheres(game.equations.get_range(item, self.unit), target[0], target[1])
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
        if defender or splash:
            if item.spell:
                tp = self.compute_priority_spell(defender, splash, move, item)
            elif item.weapon:
                tp = self.compute_priority_weapon(defender, splash, move, item)
            else:
                tp = self.compute_prority_item(defender, splash, move, item)
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

    def compute_priorty_weapon(self, defender, splash, move, item):
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
            if target_weapon and utilities.calculate_distance(move, target.position) in game.equations.get_range(target_weapon, target):
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
        max_distance = game.equations.movement(self.unit)
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

class SecondaryAI():
    def __init__(self, unit, behaviour):
        self.unit = unit
        self.behaviour = behaviour
        self.view_range = self.behaviour.view_range
        if self.view_range == -4:
            self.view_range = -3  # Try this first

        self.available_targets = []
        if self.behaviour.target == "Enemy":
            self.all_targets = [u.position for u in game.level.units if u.position and game.targets.check_enemy(self.unit, u)]
        elif self.behaviour.target == "Tile":
            # TODO add breakable tiles
            self.all_targets = []

        self.single_move = game.equations.movement(self.unit) + max(game.targets.find_potential_range(self.unit, True, True))
        self.double_move = self.single_move + game.equations.movement(self.unit)

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
            self.available_targets = [u for u in self.all_targets if utilities.calculate_distance(self.unit.position, u.position) <= self.double_move]
        elif self.view_range == -2:
            self.available_targets = [u for u in self.all_targets if utilities.calculate_distance(self.unit.position, u.position) <= self.single_move]
        elif self.view_range == -1:
            self.available_targets = []
        else:
            self.available_targets = [u for u in self.all_targets if utilities.calculate_distance(self.unit.position, u.position) <= self.view_range]

        self.best_position = None

    def update(self):
        if self.available_targets:
            target = self.available_targets.pop()
            # Find a path to the target
            path = self.get_path(target.position)
            if not path:
                logger.info("No valid path to %s.", target.nid)
                return False, None
            # We found a path
            tp = self.compute_priority(target, len(path))
            logger.info("Path to %s. -- %s", target.nid, tp)
            if tp > self.max_tp:
                self.max_tp = tp
                self.best_target = target
                self.best_path = path

        elif self.best_target:
            self.best_position = utilities.travel_algorithm(self.best_path, self.unit.movement_left, self.unit, self.grid)
            return True, self.best_position

        else:
            if self.behaviour.view_range == -4 and not self.widen_flag:
                logger.info("Widening search!")
                self.widen_flag = True
                self.view_range = -4
                self.available_targets = [u for u in self.all_targets if u not in self.available_targets]
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
            target_distance = utilities.calculate_distance(self.unit.position, target.position)
            distance_term = 1 - math.log(target_distance)/4.
        terms.append((distance_term, 60))

        if isinstance(target, unit_object.UnitObject) and game.targets.check_enemy(self.unit, target):
            hp_max = game.equations.hitpoints(target)
            weakness_term = float(hp_max - target.get_hp()) / hp_max

            max_damage = 0
            status_term = 0
            items = [item for item in self.unit.items if self.unit.can_wield(item)]
            for item in items:
                if item.status:
                    status_term = 1
                if item.weapon or item.spell:
                    raw_damage = combat_calcs.compute_damage(self.unit, target, item)
                    hit = utilities.clamp(combat_calcs.compute_hit(self.unit, target, item)/100., 0, 1)
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
