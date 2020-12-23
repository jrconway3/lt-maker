from app.utilities import utils
from app.constants import TILEWIDTH, TILEHEIGHT
from app.resources.resources import RESOURCES
from app.data.database import DB

from app.engine.solver import CombatPhaseSolver

from app.engine.sound import SOUNDTHREAD
from app.engine import engine, combat_calcs, gui, action, skill_system, banner, item_system, item_funcs
from app.engine.health_bar import MapCombatInfo
from app.engine.animations import MapAnimation
from app.engine.game_state import game

class MapCombat():
    ai_combat = False
    event_combat = False

    def __init__(self, attacker, item, position, main_target, splash, script):
        self.target_position = position
        self.attacker = attacker
        self.defender = main_target
        self.splash = splash

        self.item = item
        self.def_item = self.defender.get_weapon() if self.defender else None

        self.state_machine = CombatPhaseSolver(attacker, main_target, splash, item, script)

        self.last_update = engine.get_time()
        self.state = 'init'
        self.hp_bar_time = 400

        self._skip = False
        self.full_playback = []  # From all phases
        self.playback = []
        self.actions = []

        self.animations = []
        self.damage_numbers = []
        self.health_bars = {}

    def skip(self):
        self._skip = True
        self.attacker.sprite.reset()
        if self.defender:
            self.defender.sprite.reset()

    def get_from_playback(self, s):
        return [brush for brush in self.playback if brush[0] == s]

    def get_from_full_playback(self, s):
        return [brush for brush in self.full_playback if brush[0] == s]

    def update(self) -> bool:
        current_time = engine.get_time() - self.last_update

        # Only for the very first phase
        if self.state == 'init':
            if self._skip or current_time > 200:

                game.events.trigger('combat_start', self.attacker, self.defender, self.attacker.position)
                skill_system.pre_combat(self.full_playback, self.attacker, self.item, self.defender)
                if self.defender:
                    skill_system.pre_combat(self.full_playback, self.defender, self.def_item, self.attacker)
                for unit in self.splash:
                    skill_system.pre_combat(self.full_playback, unit, None, None)
                skill_system.start_combat(self.full_playback, self.attacker, self.item, self.defender)
                item_system.start_combat(self.full_playback, self.attacker, self.item, self.defender)
                if self.defender:
                    skill_system.start_combat(self.full_playback, self.defender, self.def_item, self.attacker)
                    item_system.start_combat(self.full_playback, self.defender, self.def_item, self.attacker)
                for unit in self.splash:
                    skill_system.start_combat(self.full_playback, unit, None, None)

                self.state = 'begin_phase'
                self.last_update = engine.get_time()

        # print("Map Combat %s" % self.state)
        elif self.state == 'begin_phase':
            # Get playback
            if not self.state_machine.get_state():
                self.clean_up()
                return True
            self.actions, self.playback = self.state_machine.do()
            self.full_playback += self.playback
            if not self.actions and not self.playback:
                self.state_machine.setup_next_state()
                return False
            self._build_health_bars()

            # Camera
            if self.get_from_playback('defender_phase'):
                game.cursor.set_pos(self.attacker.position)
            else:
                if self.defender:
                    game.cursor.set_pos(self.defender.position)
                else:
                    game.cursor.set_pos(self.target_position)
            if not self._skip:
                game.state.change('move_camera')

            # Sprites
            if self.get_from_playback('defender_phase'):
                self.defender.sprite.change_state('combat_attacker')
                self.attacker.sprite.change_state('combat_counter')
            else:
                self.attacker.sprite.change_state('combat_attacker')
                if self.defender:
                    self.defender.sprite.change_state('combat_defender')
            # for unit in self.splash:
            #     unit.sprite.change_state('combat_defender')
            self.state = 'red_cursor'

        elif self.state == 'red_cursor':
            if self.defender:
                game.cursor.combat_show()
            elif any(unit.position == self.target_position for unit in self.splash):
                game.cursor.combat_show()
            else:
                game.cursor.hide()
            self.state = 'start_anim'
            self.last_update = engine.get_time()

        elif self.state == 'start_anim':
            if self._skip or current_time > 400:
                game.cursor.hide()
                game.highlight.remove_highlights()
                animation_brushes = self.get_from_playback('cast_anim')
                for brush in animation_brushes:
                    anim = RESOURCES.animations.get(brush[1])
                    pos = game.cursor.position
                    if anim:
                        anim = MapAnimation(anim, pos)
                        self.animations.append(anim)
                self.state = 'sound'
                self.last_update = engine.get_time()

        elif self.state == 'sound':
            if self._skip or current_time > 250:
                if self.defender and self.defender.sprite.state == 'combat_attacker':
                    self.defender.sprite.change_state('combat_anim')
                else:
                    self.attacker.sprite.change_state('combat_anim')
                sound_brushes = self.get_from_playback('cast_sound')
                for brush in sound_brushes:
                    SOUNDTHREAD.play_sfx(brush[1])

                self.state = 'anim'
                self.last_update = engine.get_time()

        elif self.state == 'anim':
            if self._skip or current_time > 83:
                self._handle_playback()
                self._apply_actions()

                # Force update hp bars so we can get timing info
                for hp_bar in self.health_bars.values():
                    hp_bar.update()
                if self.health_bars:
                    self.hp_bar_time = max(hp_bar.get_time_for_change() for hp_bar in self.health_bars.values())
                else:
                    self.hp_bar_time = 0
                self.state = 'hp_bar_wait'
                self.last_update = engine.get_time()

        elif self.state == 'hp_bar_wait':
            if self._skip or current_time > self.hp_bar_time:
                self.state = 'end_phase'
                self.last_update = engine.get_time()

        elif self.state == 'end_phase':
            if self._skip or current_time > 550:
                if self.defender and self.defender.sprite.state == 'combat_anim':
                    self.defender.sprite.change_state('combat_attacker')
                else:
                    self.attacker.sprite.change_state('combat_attacker')
                self._end_phase()
                self.state_machine.setup_next_state()
                self.state = 'begin_phase'

        if self.state not in ('begin_phase', 'red_cursor'):
            for hp_bar in self.health_bars.values():
                hp_bar.update()

        return False

    def _build_health_bars(self):
        if (self.defender and self.splash) or len(self.splash) > 1:
            # Many splash attacks
            # No health bars!!
            self.health_bars.clear()

        else:
            # P1 on P1
            if self.defender and self.attacker is self.defender:
                hit = combat_calcs.compute_hit(self.attacker, self.defender, self.item, 'Attack')
                mt = combat_calcs.compute_damage(self.attacker, self.defender, self.item, 'Attack')
                if self.attacker not in self.health_bars:
                    attacker_health = MapCombatInfo('p1', self.attacker, self.item, self.defender, (hit, mt))
                    self.health_bars[self.attacker] = attacker_health

            # P1 on P2
            elif self.defender:
                hit = combat_calcs.compute_hit(self.attacker, self.defender, self.item, 'Attack')
                mt = combat_calcs.compute_damage(self.attacker, self.defender, self.item, 'Attack')
                if self.attacker not in self.health_bars:
                    attacker_health = MapCombatInfo('p1', self.attacker, self.item, self.defender, (hit, mt))
                    self.health_bars[self.attacker] = attacker_health

                if combat_calcs.can_counterattack(self.attacker, self.item, self.defender, self.def_item):
                    hit = combat_calcs.compute_hit(self.defender, self.attacker, self.def_item, 'Defense')
                    mt = combat_calcs.compute_damage(self.defender, self.attacker, self.def_item, 'Defense')
                else:
                    hit, mt = None, None
                if self.defender not in self.health_bars:
                    defender_health = MapCombatInfo('p2', self.defender, self.def_item, self.attacker, (hit, mt))
                    self.health_bars[self.defender] = defender_health

            # P1 on single splash
            elif len(self.splash) == 1:
                hit = combat_calcs.compute_hit(self.attacker, self.defender, self.item, 'Attack')
                mt = combat_calcs.compute_damage(self.attacker, self.defender, self.item, 'Attack')
                if self.attacker not in self.health_bars:
                    attacker_health = MapCombatInfo('p1', self.attacker, self.item, self.defender, (hit, mt))
                    self.health_bars[self.attacker] = attacker_health
                if self.defender not in self.health_bars:
                    splash_health = MapCombatInfo('splash', self.defender, None, self.attacker, (None, None))
                    self.health_bars[self.defender] = splash_health

    def _handle_playback(self):
        for brush in self.playback:
            if brush[0] == 'unit_tint':
                color = brush[2]
                brush[1].sprite.begin_flicker(333, color)
            elif brush[0] == 'crit_tint':
                color = brush[2]
                brush[1].sprite.begin_flicker(33, color)
                # Delay five frames
                brush[1].sprite.start_flicker(83, 33, color)
                # Delay five more frames
                brush[1].sprite.start_flicker(166, 333, color, fade_out=True)
            elif brush[0] == 'crit_vibrate':
                # In 10 frames, start vibrating for 12 frames
                brush[1].sprite.start_vibrate(166, 200)
            elif brush[0] == 'hit_sound':
                sound = brush[1]
                SOUNDTHREAD.play_sfx(sound)
            elif brush[0] == 'shake':
                shake = brush[1]
                for health_bar in self.health_bars.values():
                    health_bar.shake(shake)
            elif brush[0] == 'hit_anim':
                anim = RESOURCES.animations.get(brush[1])
                pos = brush[2].position
                if anim and pos:
                    anim = MapAnimation(anim, pos)
                    self.animations.append(anim)
            elif brush[0] == 'damage_hit':
                damage = brush[4]
                if damage <= 0:
                    continue
                str_damage = str(damage)
                left = brush[3].position
                for idx, num in enumerate(str_damage):
                    d = gui.DamageNumber(int(num), idx, len(str_damage), left, 'small_red')
                    self.damage_numbers.append(d)
            elif brush[0] == 'damage_crit':
                damage = brush[4]
                if damage <= 0:
                    continue
                str_damage = str(damage)
                left = brush[3].position
                for idx, num in enumerate(str_damage):
                    d = gui.DamageNumber(int(num), idx, len(str_damage), left, 'small_yellow')
                    self.damage_numbers.append(d)
            elif brush[0] == 'heal_hit':
                damage = brush[4]
                if damage <= 0:
                    continue
                str_damage = str(damage)
                left = brush[3].position
                for idx, num in enumerate(str_damage):
                    d = gui.DamageNumber(int(num), idx, len(str_damage), left, 'small_cyan')
                    self.damage_numbers.append(d)

    def _apply_actions(self):
        """
        Actually commit the actions that we had stored!
        """
        for act in self.actions:
            action.do(act)

    def _end_phase(self):
        pass

    def draw(self, surf):
        for hp_bar in self.health_bars.values():
            hp_bar.draw(surf)

        # Animations
        self.animations = [anim for anim in self.animations if not anim.update()]
        for anim in self.animations:
            anim.draw(surf)

        # Damage Nums
        for damage_num in self.damage_numbers:
            damage_num.update()
            position = damage_num.left
            c_pos = game.camera.get_xy()
            rel_x = position[0] - c_pos[0]
            rel_y = position[1] - c_pos[1]
            damage_num.draw(surf, (rel_x * TILEWIDTH + 4, rel_y * TILEHEIGHT))
        self.damage_numbers = [d for d in self.damage_numbers if not d.done]

        return surf

    def clean_up(self):
        game.state.back()

        # attacker has attacked
        action.do(action.HasAttacked(self.attacker))
        
        # Messages
        if self.defender:
            if skill_system.check_enemy(self.attacker, self.defender):
                action.do(action.Message("%s attacked %s" % (self.attacker.name, self.defender.name)))
            elif self.attacker is not self.defender:
                action.do(action.Message("%s helped %s" % (self.attacker.name, self.defender.name)))
            else:
                action.do(action.Message("%s used %s" % (self.attacker.name, self.item.name)))
        else:
            action.do(action.Message("%s attacked" % self.attacker.name))

        # Handle death
        all_units = [unit for unit in self.splash] + [self.attacker]
        if self.defender and self.attacker is not self.defender:
            all_units.append(self.defender)
        for unit in all_units:
            if unit.get_hp() <= 0:
                game.death.should_die(unit)
            else:
                unit.sprite.change_state('normal')

        self.turnwheel_death_messages(all_units)

        self.handle_state_stack()
        game.events.trigger('combat_end', self.attacker, self.defender, self.attacker.position)
        self.handle_item_gain()
        a_broke, d_broke = self.find_broken_items()

        # handle wexp & skills
        if not self.attacker.is_dying:
            self.handle_wexp(self.attacker, self.item, self.defender)
        if self.def_item and not self.defender.is_dying:
            self.handle_wexp(self.defender, self.def_item, self.attacker)

        # handle exp & records
        if self.attacker.team == 'player' and not self.attacker.is_dying:
            exp = self.handle_exp(self.attacker, self.item)
            if self.defender and skill_system.check_ally(self.attacker, self.defender):
                exp = int(utils.clamp(exp, 0, 100))
            else:
                exp = int(utils.clamp(exp, DB.constants.value('min_exp'), 100))

            if exp > 0:
                game.memory['exp'] = (self.attacker, exp, None, 'init')
                game.state.change('exp')

        elif self.defender and self.defender.team == 'player' and not self.defender.is_dying:
            exp = self.handle_exp(self.defender, self.def_item)
            exp = int(utils.clamp(exp, DB.constants.value('min_exp'), 100))
            if exp > 0:
                game.memory['exp'] = (self.defender, exp, None, 'init')
                game.state.change('exp')

        # Skill system end combat clean up
        skill_system.end_combat(self.full_playback, self.attacker, self.item, self.defender)
        item_system.end_combat(self.full_playback, self.attacker, self.item, self.defender)
        if self.defender:
            skill_system.end_combat(self.full_playback, self.defender, self.def_item, self.attacker)
            item_system.end_combat(self.full_playback, self.defender, self.def_item, self.attacker)
        for unit in self.splash:
            skill_system.end_combat(self.full_playback, unit, None, None)
        skill_system.post_combat(self.full_playback, self.attacker, self.item, self.defender)
        if self.defender:
            skill_system.post_combat(self.full_playback, self.defender, self.def_item, self.attacker)
        for unit in self.splash:
            skill_system.post_combat(self.full_playback, unit, None, None)

        self.handle_death(all_units)

        self.check_equipped_items()
        self.handle_broken_items(a_broke, d_broke)

# === POSSIBLY SHOULD BE SHARED AMONGST ALL COMBATS ===
    def turnwheel_death_messages(self, units):
        messages = []
        dying_units = [u for u in units if u.is_dying]
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

    def handle_state_stack(self):
        if self.event_combat:
            pass
        elif self.ai_combat:
            if skill_system.has_canto(self.attacker):
                pass
            else:
                game.state.change('wait')
        else:
            if not self.attacker.has_attacked and not self.attacker.is_dying:
                game.state.change('menu')
            elif skill_system.has_canto(self.attacker) and not self.attacker.is_dying:
                game.state.change('move')
            else:
                game.state.clear()
                game.state.change('free')
                game.state.change('wait')

    def handle_item_gain(self):
        enemies = self.splash
        if self.defender:
            enemies.append(self.defender)
        for unit in enemies:
            if unit.is_dying:
                for item in unit.items:
                    if item.droppable:
                        action.do(action.DropItem(self.attacker, item))
        if self.attacker.is_dying and self.defender:
            for item in self.attacker.items:
                if item.droppable:
                    action.do(action.DropItem(self.defender, item))

    def find_broken_items(self):
        a_broke, d_broke = False, False
        if not item_funcs.available(self.attacker, self.item):
            a_broke = True
        if self.def_item and not item_funcs.available(self.defender, self.def_item):
            d_broke = True
        return a_broke, d_broke

    def handle_broken_items(self, a_broke, d_broke):
        if a_broke:
            alert = item_system.on_not_usable(self.attacker, self.item)
            if self.attacker is not self.defender and alert and \
                    self.attacker.team == 'player' and not self.attacker.is_dying:
                game.alerts.append(banner.BrokenItem(self.attacker, self.item))
                game.state.change('alert')
        if d_broke:
            alert = item_system.on_not_usable(self.defender, self.def_item)
            if self.attacker is not self.defender and alert and \
                    self.defender.team == 'player' and not self.defender.is_dying:
                game.alerts.append(banner.BrokenItem(self.defender, self.def_item))
                game.state.change('alert')

    def handle_wexp(self, unit, item, target):
        marks = self.get_from_full_playback('mark_hit')
        marks += self.get_from_full_playback('mark_crit')
        if DB.constants.value('miss_wexp'):
            marks += self.get_from_full_playback('mark_miss')
        marks = [mark for mark in marks if mark[1] == unit]
        wexp = item_system.wexp(self.full_playback, unit, item, target)

        if DB.constants.value('double_wexp'):
            for mark in marks:
                if mark[2].is_dying and DB.constants.value('kill_wexp'):
                    action.do(action.GainWexp(unit, item, wexp*2))
                else:
                    action.do(action.GainWexp(unit, item, wexp))
        else:
            if any(mark[2].is_dying for mark in marks):
                action.do(action.GainWexp(unit, item, wexp*2))
            else:
                action.do(action.GainWexp(unit, item, wexp))

    def handle_exp(self, unit, item):
        marks = self.get_from_full_playback('mark_hit')
        marks += self.get_from_full_playback('mark_crit')
        marks = [mark for mark in marks if mark[1] == unit]
        total_exp = 0
        all_defenders = set()
        for mark in marks:
            attacker = mark[1]
            defender = mark[2]
            if defender in all_defenders:
                continue  # Don't double count defenders
            all_defenders.add(defender)

            exp = item_system.exp(self.full_playback, attacker, item, defender)
            exp *= skill_system.exp_multiplier(attacker, defender)
            exp *= skill_system.enemy_exp_multiplier(defender, attacker)
            if defender.is_dying:
                exp *= float(DB.constants.value('kill_multiplier'))
                if 'Boss' in defender.tags:
                    exp += int(DB.constants.value('boss_bonus'))
            total_exp += exp

        return total_exp

    def handle_death(self, units):
        for unit in units:
            if unit.is_dying:
                game.state.change('dying')
                break
        for unit in units:
            if unit.is_dying:
                game.events.trigger('unit_death', unit, position=unit.position)

    def check_equipped_items(self):
        if not item_funcs.available(self.attacker, self.item):
            self.attacker.check_equipped_weapon()
        if self.def_item and not item_funcs.available(self.defender, self.def_item):
            self.defender.check_equipped_weapon()
