from app import utilities
from app.data.database import DB
from app.engine import static_random, action, combat_calcs, unit_object
from app.engine.game_state import game

class Result():
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender
        self.outcome = 0  # 0 -- Miss, 1 -- Hit, 2 -- Crit

        self.atk_damage = 0  # Damage dealt to the attacker
        self.def_damage = 0  # Damage dealt to the defender

        # used for calculating records only
        self.atk_damage_done = 0  # Actual damage dealt to attacker
        self.def_damage_done = 0  # Actual damage dealt to defender

        self.atk_status = []  # Statuses to give to attacker
        self.def_status = []  # Statuses to give to defender

        self.atk_movement = None   # Movement to attacker
        self.def_movement = None   # Movement to defender

        self.attacker_proc_used = None  # Proc skill used by attacker
        self.defender_proc_used = None  # Proc skill used by defender

class SolverState():
    def get_next_state(self, solver):
        return None

    def process(self, solver):
        return None

class PreInitState(SolverState):
    def get_next_state(self, solver):
        return 'Init'

class InitState(SolverState):
    def get_next_state(self, solver):
        if solver.defender:
            if solver.defender_has_vantage():
                solver.def_rounds += 1
                return 'Defender'
            else:
                solver.atk_rounds += 1
                return 'Attacker'
        elif solver.splash:
            return 'Splash'
        else:
            return 'Done'

    def process(self, solver):
        solver.reset()
        # Pre Proc stuff here

class AttackerState(SolverState):
    def is_brave(self, item):
        if item.brave:
            if item.brave.value == 'Always Brave':
                return True
            elif item.brave.value == 'Brave while attacking':
                return True
        return False

    def check_brave(self, solver, unit, item):
        if self.is_brave(item):
            return True
        # Adept Proc
        return False

    def get_next_state(self, solver):
        if solver.event_combat and solver.event_combat[-1] == 'quit':
            return 'Done'
        if solver.attacker.get_hp() > 0:
            if solver.splash and any(unit.get_hp() > 0 for unit in solver.splash):
                return 'Splash'
            elif solver.defender.get_hp() > 0:
                if solver.item_uses(solver.item) and self.check_brave(solver, solver.attacker, solver.item) and solver.attacker_brave < 1:
                    solver.attacker_brave += 1  # Mark first brave attack
                    return 'Attacker'
                elif solver.allow_counterattack():
                    solver.defender_brave = 0
                    solver.def_rounds += 1
                    return 'Defender'
                elif solver.atk_rounds < 2 and solver.item.weapon and \
                        combat_calcs.outspeed(solver.attacker, solver.defender, solver.item, "Attack") and \
                        solver.item_uses(solver.item):
                    solver.attacker_brave = 0  # New round
                    solver.atk_rounds += 1
                    return 'Attacker'
                elif solver.next_round():
                    return 'Init'
        return 'Done'

    def process(self, solver):
        action.do(action.UseItem(solver.item))
        solver.uses_count += 1
        result = solver.generate_result(solver.attacker, solver.defender, solver.item, 'Attack')
        return result

class DefenderState(AttackerState):
    def is_brave(self, item):
        if item.brave:
            if item.brave.value == 'Always Brave':
                return True
            elif item.brave.value == 'Brave while defending':
                return True
        return False

    def get_next_state(self, solver):
        if solver.event_combat and solver.event_combat[-1] == 'quit':
            return 'Done'
        if solver.attacker.get_hp() > 0 and solver.defender.get_hp() > 0:
            ditem = solver.p2_item
            if solver.item_uses(ditem) and self.check_brave(solver, solver.defender, ditem) and solver.defender_brave < 1:
                solver.defender_brave += 1
                return 'Defender'
            elif solver.def_rounds < 2 and solver.defender_has_vantage():
                solver.atk_rounds += 1
                return 'Attacker'
            elif solver.atk_rounds < 2 and combat_calcs.outspeed(solver.attacker, solver.defender, solver.item, "Attack") and \
                    solver.item_uses(solver.item) and not solver.item.no_double:
                solver.atk_rounds += 1
                return 'Attacker'
            elif solver.def_double() and solver.defender_can_counterattack() and not ditem.no_double:
                solver.defender_brave = 0  # Reset
                solver.def_rounds += 1
                return 'Defender'
            elif solver.next_round():
                return 'Init'
        return 'Done'

    def process(self, solver):
        ditem = solver.p2_item
        action.do(action.UseItem(ditem))
        result = solver.generate_result(solver.defender, solver.attacker, ditem, 'Defense')
        return result

class SplashState(AttackerState):
    def __init__(self):
        self.idx = 0

    def get_next_state(self, solver):
        if solver.attacker.get_hp() > 0:
            if self.idx < len(solver.splash):
                return 'Splash'
            if solver.item_uses(solver.item) and self.check_brave(solver, solver.attacker, solver.item) and solver.attacker_brave < 1:
                if solver.defender and solver.defender.get_hp() > 0:
                    solver.attacker_brave += 1
                    return 'Attacker'
                elif any(s.get_hp() > 0 for s in solver.splash):
                    solver.attacker_brave += 1
                    return 'Splash'
            if solver.allow_counterattack():
                solver.defender_brave = 0
                solver.def_rounds += 1
                return 'Defender'
            elif solver.defender and solver.atk_rounds < 2 and \
                    combat_calcs.outspeed(solver.attacker, solver.defender, solver.item, "Attack") and \
                    solver.item_uses(solver.item) and solver.defender.get_hp() > 0:
                solver.attacker_brave = 0
                solver.atk_rounds += 1
                return 'Attacker'
            elif solver.next_round():
                return 'Init'
        return 'Done'

    def process(self, solver):
        if solver.uses_count < 1:   # Means we didn't have an attack state
            action.do(action.UseItem(solver.item))
            solver.uses_count ++ 1
        result = solver.generate_result(solver.attacker, solver.splash[self.idx], solver.item, "Attack")
        self.index += 1
        return result

class DoneState(SolverState):
    pass

class SolverStateMachine():
    states = {'PreInit': PreInitState,
              'Init': InitState,
              'Attacker': AttackerState,
              'Defender': DefenderState,
              'Splash': SplashState,
              'Done': DoneState}
    
    def __init__(self, starting_state):
        self.change_state(starting_state)

    def get_state(self):
        return self.state

    def get_state_name(self):
        return self.state_name

    def change_state(self, state):
        self.state_name = state
        self.state = self.states[state]() if state else None

    def ratchet(self, solver):
        next_state = self.state.get_next_state(solver)
        if next_state != self.state_name:
            self.change_state(next_state)
        if self.get_state():  # If we actually went anywhere, process it
            result = self.get_state().process(solver)
            return result
        return None

class Solver():
    def __init__(self, attacker, defender, def_pos, splash, item, skill_used, event_combat):
        self.attacker = attacker
        self.defender = defender
        self.def_pos = def_pos
        # Have splash damage spiral out from position it started on...
        self.splash = sorted(splash, key=lambda s_unit: utilities.calculate_distance(self.def_pos, s_unit.position))
        self.item = item
        self.p2_item = self.defender.get_weapon() if self.defender else None
        self.skill_used = skill_used
        if event_combat:
            # Must make a copy, because we'll be modifying this list
            self.event_combat = [e.lower() for e in event_combat]
        else:
            self.event_combat = None

        self.state = SolverStateMachine('PreInit')

        self.current_round = 0
        self.total_rounds = 1
        self.new_round = True
        self.atk_rounds = 0
        self.def_rounds = 0
        self.attacker_brave = 0
        self.defender_brave = 0

        self.uses_count = 0  # How many times has item been used

    def reset(self):
        self.current_round += 1
        self.new_round = True
        self.atk_rounds = 0
        self.def_rounds = 0
        self.attacker_brave = 0
        self.defender_brave = 0

    def get_state(self):
        return self.state.get_state()

    def item_uses(self, item):
        if (item.uses and item.uses.value <= 0) or (item.c_uses and item.c_uses.value <= 0):
            return False
        return True

    def defender_can_counterattack(self):
        weapon = self.p2_item
        if weapon and self.item_uses(weapon) and \
                utilities.calculate_distance(self.attacker.position, self.defender.position) in \
                game.equations.get_range(weapon, self.defender):
            return True
        else:
            return False

    def defender_has_vantage(self):
        return False and isinstance(self.defender, unit_object.UnitObject)

    def def_double(self):
        return DB.constants.get('def_double').value and \
            self.def_rounds < 2 and combat_calcs.outspeed(self.defender, self.attacker, self.p2_item, "Defense")

    def allow_counterattack(self):
        return isinstance(self.defender, unit_object.UnitObject) and \
            self.defender and self.item.weapon and not self.item.cannot_be_countered and \
            self.defender.get_hp() > 0 and \
            (self.def_rounds < 1 or self.def_double()) and \
            self.defender_can_counterattack()

    def next_round(self):
        return self.current_round < self.total_rounds

    def generate_roll(self, rng_mode, event_command=None):
        if event_command:
            if event_command in ('hit', 'crit'):
                return -1
            elif event_command == 'miss':
                return 100
        # Normal RNG
        if rng_mode == 'Classic':
            roll = static_random.get_combat()
        elif rng_mode == 'True Hit':
            roll = (static_random.get_combat() + static_random.get_combat()) // 2
        elif rng_mode == 'True Hit+':
            roll = (static_random.get_combat() + static_random.get_combat() + static_random.get_combat()) // 3
        elif rng_mode == 'Grandmaster':
            roll = 0
        return roll

    def generate_crit_roll(self, event_command=None):
        if event_command == 'crit':
            return -1
        else:
            return static_random.get_combat()

    def handle_crit(self, result, attacker, defender, item, mode, event_command):
        to_crit = combat_calcs.compute_crit(attacker, defender, item, mode)
        crit_roll = self.generate_crit_roll(event_command)
        if crit_roll < to_crit and isinstance(defender, unit_object.UnitObject):
            result.outcome = 2
            result.def_damage = combat_calcs.compute_damage(attacker, defender, item, mode, crit=True)

    def generate_result(self, attacker, defender, item, mode):
        result = Result(attacker, defender)
        if self.event_combat:
            event_command = self.event_combat.pop()
        else:
            event_command = None
        if event_command == 'quit':
            return None  # No result

        # Proc Skills for attacker and defender

        to_hit = combat_calcs.compute_hit(attacker, defender, item, mode)
        rng_mode = DB.constants.get('rng').value
        roll = self.generate_roll(rng_mode, event_command)

        damage_mod = to_hit / 100. if rng_mode == 'Grandmaster' else 1.

        if (item.weapon and attacker is not defender) or item.spell:
            if not item.hit or roll < to_hit:  # TODO Evasion here
                result.outcome = 1
                if item.might is not None:
                    result.def_damage = combat_calcs.compute_damage(attacker, defender, item, mode)
                    if DB.constants.get('crit').value:
                        self.handle_crit(result, attacker, defender, item, mode, event_command)
                if item.heal is not None:
                    result.def_damage = -combat_calcs.compute_heal(attacker, defender, item, mode)

                if item.movement:
                    result.def_movement = item.movement
                if item.self_movement:
                    result.atk_movement = item.self_movement

                result.def_damage *= damage_mod  # Handle hybrid nonsense
                result.def_damage = int(result.def_damage)

        else:  # Usable
            result.outcome = 1
            if item.heal is not None:
                result.def_damage = -combat_calcs.compute_heal(attacker, defender, item, mode)
            if item.movement:
                result.def_movement = item.movement
            if item.self_movement:
                result.atk_movement = item.self_movement

        # Additional statuses
        if result.def_damage > 0:
            if item.lifelink:
                result.atk_damage -= min(result.def_damage, defender.get_hp())
            if item.half_lifelink:
                result.atk_damage -= min(result.def_damage//2, defender.get_hp())

        # Remove proc skills

        # Boss crit
        if DB.constants.get('boss_crit').value and 'Boss' in defender.tags and result.outcome and result.def_damage >= defender.get_hp():
            result.outcome = 2

        return result

    def get_next_result(self):
        random_state = static_random.get_combat_random_state()
        result = None
        while not result:
            result = self.state.ratchet(self)

            new_random_state = static_random.get_combat_random_state()
            action.do(action.RecordRandomState(random_state, new_random_state))

            if not self.state.get_state():
                break
        return result

    def get_splash_results(self):
        results = []
        if self.state.get_state_name() == 'Attacker':
            results.append(self.get_next_result())
        while self.state.get_state() and \
                self.state.get_state_name() == 'Splash' and \
                self.state.get_state().index < len(self.splash):
            results.append(self.get_next_result())
        return results
