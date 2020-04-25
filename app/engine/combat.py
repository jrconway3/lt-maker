import math

from app.data.constants import TILEWIDTH, TILEHEIGHT
from app import utilities
from app.data import unit_object
from app.data.item_components import SpellAffect
from app.data.database import DB

from app.engine import engine, banner, action, combat_calcs, gui, solver
from app.engine.health_bar import HealthBar
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

class Combat():
    """
    Abstract base class for combat
    """
    def calc_damage_done(self, result):
        result.atk_damage_done = 0
        if result.atk_damage > 0:
            result.atk_damage_done = min(result.atk_damage, result.attacker.get_hp())
        elif result.atk_damage < 0:
            result.atk_damage_done = -min(-result.atk_damage, game.equations.hitpoints(result.attacker) - result.attacker.get_hp())
            
        result.def_damage_done = 0
        if result.defender:
            if result.def_damage > 0:
                result.def_damage_done = min(result.def_damage, result.defender.get_hp())
            elif result.def_damage < 0:
                result.def_damage_done = -min(-result.def_damage, game.equations.hitpoints(result.defender) - result.defender.get_hp())

    def _apply_result(self, result):
        self.calc_damage_done(result)
        action.do(action.ChangeHP(result.attacker, -result.atk_damage))
        if result.defender:
            if isinstance(result.defender, unit_object.UnitObject):
                action.do(action.ChangeHP(result.defender, -result.def_damage))
            else:
                action.do(action.ChangeTileHp(result.defender.position, -result.def_damage))

    def find_broken_items(self):
        a_broke_item, d_broke_item = False, False
        if self.item.uses and self.item.uses.value <= 0:
            a_broke_item = True
        if self.p2:
            weapon = self.p2.get_weapon()
            if weapon and weapon.uses and weapon.uses.value <= 0:
                d_broke_item = True
        return a_broke_item, d_broke_item

    def broken_item_alert(self, a_broke_item, d_broke_item):
        if a_broke_item and self.p1.team == 'player' and not self.p1.is_dying:
            game.alerts.append(banner.BrokenItem(self.p1, self.item))
            game.state.change('display_alerts')
        if d_broke_item and self.p2.team == 'player' and not self.p2.is_dying:
            game.alerts.append(banner.BrokenItem(self.p2, self.p2.get_weapon()))
            game.state.change('display_alerts')

    def handle_wexp(self, results, item):
        if not DB.constants.get('miss_wexp').value:
            results = [result for result in results if result.outcome]
        if DB.constants.get('double_wexp').value:
            for result in results:
                action.do(action.GainWexp(result.attacker, item))
            if DB.constants.get('kill_wexp').value:
                already_dead = set()
                for result in results:
                    if result.defender.is_dying and result.defender.nid not in already_dead:
                        already_dead.add(result.defender.nid)
                        action.do(action.GainWexp(result.attacker, item))
        elif results:
            unit = results[0].attacker
            action.do(action.GainWexp(unit, item))
            if DB.constants.get('kill_wexp').value and any(result.defender.is_dying for result in results):
                action.do(action.GainWexp(unit, item))

    def calc_init_exp_p1(self, my_exp, other_unit, applicable_results):
        p1_klass = DB.classes.get(self.p1.klass)
        other_unit_klass = DB.classes.get(other_unit.klass)
        exp_multiplier = p1_klass.exp_mult * other_unit_klass.opponent_exp_mult

        damage, healing, kills = 0, 0, 0

        damage_done = sum([result.def_damage_done for result in applicable_results])
        
        if self.item.heal:
            healing += damage_done
        else:
            damage += damage_done

        if self.item.exp:
            normal_exp = int(self.item.exp.value)
        elif self.item.weapon or not game.target.check_ally(self.p1, other_unit):
            level_diff = other_unit.get_internal_level() - self.p1.get_internal_level() + DB.constants.get('exp_offset').value
            exp_gained = DB.constants.get('exp_magnitude').value * math.exp(level_diff * DB.constants.get('exp_curve').value)
            exp_gained *= exp_multiplier
            normal_exp = max(exp_gained, DB.constants.get('min_exp').value)
        elif self.item.spell:
            if self.item.heal:
                heal_diff = damage_done - self.p1.get_internal_level() + DB.constants.get('heal_offset').value      
                exp_gained = (DB.constants.get('heal_curve').value * heal_diff) + DB.constants.get('heal_magnitude').value
                exp_gained *= p1_klass.exp_mult
                normal_exp = max(exp_gained, DB.constants.get('heal_min').value)
            else: # Status (Fly, Mage Shield, etc.)
                normal_exp = p1_klass * DB.constants.get('default_exp').value
        else:
            normal_exp = 0
            
        if other_unit.is_dying:
            kills += 1
            my_exp += int(DB.constants.get('kill_multiplier').value * normal_exp)
            my_exp += int(DB.constants.get('boss_bonus').value if 'Boss' in other_unit.tags else 0)
        else:
            my_exp += normal_exp
        if 'no_exp' in other_unit.status_bundle:
            my_exp = 0
        if self.item.max_exp:
            my_exp = min(my_exp, int(self.item.max_exp))
        logger.info('Attacker gained %s exp', my_exp)
        return my_exp, (damage, healing, kills)

    def calc_init_exp_p2(self, defender_results):
        p2_klass = DB.classes.get(self.p2.klass)
        other_unit_klass = DB.classes.get(self.p1.klass)
        exp_multiplier = p2_klass.exp_mult * other_unit_klass.opponent_exp_mult

        damage, healing, kills = 0, 0, 0

        my_exp = 0
        applicable_results = [result for result in self.old_results if result.outcome and result.attacker is self.p2 and
                              result.defender is self.p1 and result.def_damage > 0]
        if applicable_results:
            damage_done = sum([result.def_damage_done for result in applicable_results])
            damage += damage_done
            level_diff = self.p1.get_internal_level() - self.p2.get_internal_level() + DB.constants.get('exp_offset').value
            exp_gained = DB.constants.get('exp_magnitude').value * math.exp(level_diff * DB.constants.get('exp_curve').value)
            exp_gained *= exp_multiplier
            normal_exp = max(exp_gained, DB.constants.get('min_exp').value)
            if self.p1.is_dying:
                kills += 1
                my_exp += int(DB.constants.get('kill_multiplier').value * normal_exp)
                my_exp += int(DB.constants.get('boss_bonus').value if 'Boss' in self.p1.tags else 0)
            else:
                my_exp += normal_exp 
            if 'no_exp' in self.p1.status_bundle:
                my_exp = 0

        # No free exp for affecting myself or being affected by allies
        if game.targets.check_ally(self.p2, self.p1):
            my_exp = utilities.clamp(my_exp, 0, 100)
        else:
            my_exp = utilities.clamp(my_exp, DB.constants.get('min_exp').value, 100)
        return my_exp, (damage, healing, kills)

    def handle_item_gain(self, all_units):
        units = [u for u in all_units if isinstance(u, unit_object.UnitObject)]
        for unit in units:
            if unit.is_dying:
                for item in unit.items:
                    if item.droppable:
                        if unit in self.splash or unit is self.p2:
                            action.do(action.DropItem(self.p1, item))
                        elif self.p2:  # Else if defender exists
                            action.do(action.DropItem(self.p2, item))

        # if self.arena and self.p2.currenthp <= 0:
        #     action = Action.GiveGold(gameStateObj.level_constants['_wager']*2, gameStateObj.current_party)
        #     Action.do(action, gameStateObj)

    def handle_state_stack(self):
        if self.event_combat:
            # gameStateObj.message[-1].current_state = "Processing"
            if not self.p1.is_dying:
                self.p1.sprite.change_state('normal')
        else:
            if self.p1.team == 'player':
                # Check if this is an ai controlled player
                if self.ai_combat:
                    pass
                elif not self.p1.has_attacked:
                    game.state.change('menu')
                elif self.p1.has_canto_plus() and not self.p1.is_dying:
                    game.state.change('move')
                else:
                    game.state.clear()
                    game.state.change('free')
                    game.state.change('wait')

    def handle_death(self, all_units):
        for unit in all_units:
            if unit.is_dying:
                logger.info('%s is dying.', unit.nid)
                if isinstance(unit, unit_object.UnitObject):
                    game.state.change('dying')
                #     killer = self.p2 if unit is self.p1 else self.p1
                #     # scene = Dialogue.Dialogue_Scene(metaDataObj['death_quotes'], unit=unit, unit2=killer)
                #     # gameStateObj.message.append(scene)
                #     # game.state.change('dialogue')
                # else:
                #     # gameStateObj.map.destroy(unit, gameStateObj)

    def turnwheel_death_messages(self, all_units):
        messages = []
        dying_units = [u for u in all_units if isinstance(u, unit_object.UnitObject) and u.is_dying]
        any_player_dead = any(not u.team.startswith('enemy') for u in dying_units)
        for unit in dying_units:
            if unit.team.startswith('enemy'):
                if any_player_dead:
                    messages.append("%s was defeated" % unit.name)
                else:
                    messages.append("Prevailed over %s" % unit.name)
            else:
                messages.append("%s was defeated" % unit.name)

        for message in messages:
            action.do(action.Message(message))

class MapCombat(Combat):
    combat_length = 2000

    def __init__(self, attacker, defender, def_pos, splash, item, 
                 skill_used, event_combat, ai_combat):
        self.p1 = attacker
        self.p2 = defender
        self.def_pos = def_pos
        self.splash = splash
        self.item = item
        self.skill_used = skill_used
        self.event_combat = event_combat
        self.ai_combat = ai_combat

        self.solver = solver.Solver(attacker, defender, def_pos, splash, item, skill_used, event_combat)
        self.results = []
        self.old_results = []

        self._skip = False

        self.last_update = engine.get_time()
        self.additional_time = 0
        self.state = 'pre_init'

        self.damage_numbers = []
        self.health_bars = {}

    def skip(self):
        self._skip = True
        self.p1.sprite.reset()
        if self.p2 and isinstance(self.p2, unit_object.UnitObject):
            self.p2.sprite.reset()

    def update(self):
        current_time = engine.get_time() - self.last_update
        # Get the results needed for this phase
        if not self.results:
            next_result = self.solver.get_next_result()
            if next_result is None:
                self.clean_up()
                return True
            self.results.append(next_result)
            if self.solver.splash:
                self.results += self.solver.get_splash_results()

            self._build_health_bars()

            # Pre Proc Skills

        elif self.results:
            result = self.results[0]
            if self.state == 'pre_init':
                # Move Camera
                if len(self.results) > 1:
                    game.cursor.set_pos(self.def_pos)
                else:
                    game.cursor.set_pos(result.defender.position)
                # Sprite Changes
                if result.defender == self.p1:
                    if self.p2 and game.targets.check_enemy(self.p1, self.p2):
                        self.p2.sprite.change_state('combat_attacker')
                        self.p1.sprite.change_state('combat_counter')
                    else:
                        self.p1.sprite.change_state('combat_active')
                else:
                    self.p1.sprite.change_state('combat_attacker')
                    if isinstance(self.p2, unit_object.UnitObject):
                        self.p2.sprite.change_state('combat_defender')
                for unit in self.splash:
                    if isinstance(self.p2, unit_object.UnitObject):
                        unit.sprite.change_state('combat_defender')
                if not self.skip:
                    game.state.change('move_camera')
                self.state = 'init1'

            elif self.state == 'init1':
                self.last_update = engine.get_time()
                self.state = 'init2'
                if any(result.defender.position == game.cursor.position for result in self.results):
                    game.cursor.combat_show()
                else:
                    game.cursor.hide()
                for hp_bar in self.health_bars.values():
                    hp_bar.force_position_update()
                # Proc Skills

            elif self.state == 'init2':
                if self._skip or current_time > self.combat_length//5 + self.additional_time:
                    game.cursor.hide()
                    game.highlight.remove_highlights()
                    # AOE Anim
                    # Weapons get extra time, spells and item do not need it, since they are one sided
                    if not self.item.weapon:
                        self.additional_time -= self.combat_length//5
                    self.state = '2'

            elif self.state == '2':
                if self._skip or current_time > 2 * self.combat_length//5 + self.additional_time:
                    self.state = 'anim'
                    if result.attacker.sprite.state in ('combat_attacker', 'combat_defender'):
                        result.attacker.sprite.change_state('combat_anim')
                    for result in self.results:
                        if result.attacker is self.p1:
                            item = self.item
                        else:
                            item = result.attacker.get_weapon()
                        # Sound

            elif self.state == 'anim':
                if self._skip or current_time > 3 * self.combat_length//5 + self.additional_time:
                    if result.attacker.sprite.state == 'combat_anim':
                        result.attacker.sprite.change_state('combat_attacker')
                    for result in self.results:
                        self._handle_result_anim(result)
                        self.apply_result(result)
                    # Force update hp bars
                    for hp_bar in self.health_bars.values():
                        hp_bar.update()
                    if self.health_bars:
                        self.additional_time += \
                            max(hp_bar.time_for_change for hp_bar in self.health_bars.values())
                    else:
                        self.additional_time += self.combat_length//5
                    self.state = 'clean'

            elif self.state == 'clean':
                if self._skip or current_time > 3 * self.combat_length//5 + self.additional_time:
                    self.state = 'wait'

            elif self.state == 'wait':
                if self._skip or current_time > 4 * self.combat_length//5 + self.additional_time:
                    self._end_phase()
                    self.old_results += self.results
                    self.results.clear()
                    self.state = 'pre_init'

            if self.state not in ('pre_init', 'init1'):
                for hp_bar in self.health_bars.values():
                    hp_bar.update()

        return False

    def _build_health_bars(self):
        if len(self.results) == 1:
            result = self.results[0]
            # P1 on P1
            if result.attacker == self.p1 and result.defender == self.p1:
                hit = combat_calcs.compute_hit(self.p1, self.p1, self.item, 'Attack')
                mt = combat_calcs.compute_damage(self.p1, self.p1, self.item, 'Attack')
                if self.p1 not in self.health_bars:
                    p1_health = HealthBar('p1', self.p1, self.item, self.p1, hit, mt)
                    self.health_bars[self.p1] = p1_health

            # P1 on P2 or P2 on P1
            elif (result.attacker == self.p1 and result.defender == self.p2) or \
                    (result.attacker == self.p2 and result.defender == self.p1):
                hit = combat_calcs.compute_hit(self.p1, self.p2, self.item, 'Attack')
                mt = combat_calcs.compute_damage(self.p1, self.p2, self.item, 'Attack')
                if self.p1 not in self.health_bars:
                    p1_health = HealthBar('p1', self.p1, self.item, self.p2, hit, mt)
                    self.health_bars[self.p1] = p1_health
                if self.item.weapon and self.solver.defender_can_counterattack():
                    hit = combat_calcs.compute_hit(self.p2, self.p1, self.p2.get_weapon(), 'Defense')
                    mt = combat_calcs.compute_damage(self.p2, self.p1, self.p2.get_weapon(), 'Defense')
                else:
                    hit, mt = None, None
                if self.p2 not in self.health_bars:
                    p2_health = HealthBar('p2', self.p2, self.p2.get_weapon(), self.p1, hit, mt)
                    self.health_bars[self.p2] = p2_health

            # P1 on single splash
            elif result.attacker == self.p1:
                hit = combat_calcs.compute_hit(result.attacker, result.defender, self.item, 'Attack')
                mt = combat_calcs.compute_damage(result.attacker, result.defender, self.item, 'Attack')
                if self.p1 not in self.health_bars:
                    p1_health = HealthBar('p1', result.attacker, self.item, result.defender, hit, mt)
                    self.health_bars[self.p1] = p1_health
                if result.defender not in self.health_bars:
                    p2_health = HealthBar('splash', result.defender, None, result.attacker, None, None)
                    self.health_bars[result.defender] = p2_health

        elif len(self.results) > 1:
            # Many splash attacks
            # No health bars!!
            self.health_bars.clear()

    def _handle_result_anim(self, result):
        if result.outcome:
            if result.attacker is self.p1:
                item = self.item
            else:
                item = result.attacker.get_weapon()
            if isinstance(result.defender, unit_object.UnitObject):
                color = item.map_hit_color.value if item.map_hit_color else (255, 255, 255)  # default to white
                result.defender.sprite.begin_flicker(self.combat_length//5, color)
            # Sound and Shake
            pass
            # Animations
            # Self Anim
            # Other Anim
            # Heal Anim
            # No Damage
            self._start_damage_num_animation(result)

        else:  # Miss
            # Miss Sound
            # Miss Animation
            pass
        # Status Effects

    def _start_damage_num_animation(self, result):
        damage = result.def_damage
        str_damage = str(min(999, abs(damage)))
        left = result.defender.position
        for idx, num in enumerate(str_damage):
            if result.outcome == 2:  # Crit
                d = gui.DamageNumber(int(num), idx, len(str_damage), left, 'small_yellow')
                self.damage_numbers.append(d)
            elif result.def_damage < 0:  # Heal
                d = gui.DamageNumber(int(num), idx, len(str_damage), left, 'small_cyan')
                self.damage_numbers.append(d)
            elif result.def_damage > 0:  # Damage
                d = gui.DamageNumber(int(num), idx, len(str_damage), left, 'small_red')
                self.damage_numbers.append(d)

    def apply_result(self, result):
        self._apply_result(result)
        # Handle forced movement
        def_pos = result.defender.position
        atk_pos = result.attacker.position
        if result.atk_movement:
            game.movement.forced_movement(result.attacker, result.defender, def_pos, result.atk_movement)
        if result.def_movement:
            game.movement.forced_movement(result.defender, result.attacker, atk_pos, result.def_movement)
        # Summoning

    def _end_phase(self):
        self.additional_time = 0

    def draw(self, surf):
        # Hp Bars
        for hp_bar in self.health_bars.values():
            surf = hp_bar.draw(surf)

        # Damage Nums
        for damage_num in self.damage_numbers:
            damage_num.update()
            position = damage_num.left
            c_pos = game.camera.get_xy()
            rel_x = position[0] - c_pos[0]
            rel_y = position[0] - c_pos[1]
            damage_num.draw(surf, (rel_x * TILEWIDTH + 4, rel_y * TILEHEIGHT))
        self.damage_numbers = [d for d in self.damage_numbers if not d.done]

        return surf

    def clean_up(self):
        game.state.back()
        # Skill used
        # Skill used
        action.do(action.HasAttacked(self.p1))
        if self.p2:
            if isinstance(self.p2, unit_object.UnitObject):
                if game.targets.check_enemy(self.p1, self.p2):
                    action.do(action.Message("%s attacked %s" % (self.p1.name, self.p2.name)))
                elif self.p1 is not self.p2:
                    action.do(action.Message("%s helped %s" % (self.p1.name, self.p2.name)))
                else:
                    action.do(action.Message("%s used %s" % (self.p1.name, self.p2.name)))
            else:
                action.do(action.Message("%s attacked a tile" % self.p1.name))
        else:
            action.do(action.Message("%s attacked" % self.p1.name))

        if not self.p1.has_canto_plus() and not self.event_combat:
            game.state.change('wait')

        a_broke_item, d_broke_item = self.find_broken_items()

        all_units = [unit for unit in self.splash] + [self.p1]
        if self.p2:
            all_units.append(self.p2)

        for unit in all_units:
            if unit.get_hp() <= 0:
                unit.is_dying = True
            if isinstance(unit, unit_object.UnitObject):
                unit.sprite.change_state('normal')

        self.turnwheel_death_messages(all_units)

        self.handle_state_stack()
        self.handle_item_gain(all_units)
        if self.p1 is not self.p2:
            self.broken_item_alert(a_broke_item, d_broke_item)

        # handle exp and stat gane
        if not self.event_combat and (self.item.weapon or self.item.spell):
            attacker_results = [result for result in self.old_results if result.attacker is self.p1]
            # wexp and skills
            if attacker_results and not self.p1.is_dying:
                # Charge Skills
                self.handle_wexp(attacker_results, self.item)

            # exp and records
            if self.p1.team == 'player' and not self.p1.is_dying:
                my_exp = 0
                for other_unit in self.splash + [self.p2]:
                    applicable_results = [result for result in attacker_results if result.outcome and result.defender is other_unit]
                    # Doesn't count if it did 0 damage
                    applicable_results = [result for result in applicable_results if not (self.item.weapon and result.def_damage <= 0)]
                    # Doesn't count if you attacked an ally
                    applicable_results = [result for result in applicable_results if not 
                                          ((self.item.weapon or self.item.spell.affect == SpellAffect.Harmful) and 
                                           game.targets.check_ally(result.attacker, result.defender))]
                    if isinstance(other_unit, unit_object.UnitObject) and applicable_results:
                        my_exp, records = self.calc_init_exp_p1(my_exp, other_unit, applicable_results)
                        action.do(action.UpdateUnitRecords(self.p1, records))

                # No free exp for affecting myself or being affected by allies
                if not isinstance(self.p2, unit_object.UnitObject) or game.target.check_ally(self.p1, self.p2):
                    my_exp = int(utilities.clamp(my_exp, 0, 100))
                else:
                    my_exp = int(utilities.clamp(my_exp, DB.constants.get('min_exp'), 100))

                # Also handles actually adding the exp to the unit
                if my_exp > 0:
                    game.memory['exp'] = (self.p1, my_exp, None, 'init')
                    game.state.change('exp')

            if self.p2 and isinstance(self.p2, unit_object.UnitObject) and not self.p2.is_dying and self.p2 is not self.p1:
                defender_results = [result for result in self.old_results if result.attacker is self.p2]
                # WEXP and Skills
                if defender_results:
                    # Action.do(Action.ChargeAllSkills(self.p2), gameStateObj)
                    self.handle_wexp(defender_results, self.p2.get_weapon())
                # EXP and Records
                if self.p2.team == 'player':  
                    my_exp, records = self.calc_init_exp_p2(defender_results)
                    action.do(action.UpdateUnitRecords(self.p2, records))
                    if my_exp > 0:
                        game.memory['exp'] = (self.p2, my_exp, None, 'init')
                        game.state.change('exp_gain')

        self.handle_death(all_units)
        # Actually remove items
        self.remove_broken_items(a_broke_item, d_broke_item)

class AnimationCombat(Combat):
    # TODO Implement
    pass