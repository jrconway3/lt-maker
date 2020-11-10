from app.data.database import DB

from app.engine import combat_calcs, item_system, skill_system, static_random

import logging
logger = logging.getLogger(__name__)

class SolverState():
    def get_next_state(self, solver):
        return None

    def process(self, solver, actions, playback):
        return None

    def process_command(self, command):
        if command in ('hit2', 'crit2', 'miss2'):
            return 'defender'
        elif command in ('hit1', 'crit1', 'miss1'):
            return 'attacker'
        elif command == 'end':
            return None
        return None

class InitState(SolverState):
    def get_next_state(self, solver):
        command = solver.get_script()
        if command == '--':
            if solver.defender_has_vantage():
                return 'defender'
            else:
                return 'attacker'
        else:
            return self.process_command(command) 

class AttackerState(SolverState):
    def get_next_state(self, solver):
        command = solver.get_script()
        if command == '--':
            if solver.attacker_alive() and solver.main_target_alive():
                if solver.allow_counterattack() and \
                        solver.num_defends < combat_calcs.outspeed(solver.main_target, solver.attacker, solver.target_item, 'defense'):
                    return 'defender'
                elif solver.item_has_uses() and \
                        solver.num_attacks < combat_calcs.outspeed(solver.attacker, solver.main_target, solver.item, 'attack'):
                    return 'attacker'
            return None
        else:
            return self.process_command(command)

    def process(self, solver, actions, playback):
        playback.append(('attacker_phase',))
        multiattacks = combat_calcs.compute_multiattacks(solver.attacker, solver.main_target, solver.item, 'attack')
        for attack in range(multiattacks):
            if solver.main_target:
                solver.process(actions, playback, solver.attacker, solver.main_target, solver.item, 'attack')
            for target in solver.splash:
                solver.process(actions, playback, solver.attacker, target, solver.item, 'splash')
        solver.num_attacks += 1

class DefenderState(SolverState):
    def get_next_state(self, solver):
        command = solver.get_script()
        if command == '--':
            if solver.attacker_alive() and solver.main_target_alive():
                if solver.item_has_uses() and \
                        solver.num_attacks < combat_calcs.outspeed(solver.attacker, solver.main_target, solver.item, 'attack'):
                    return 'attacker'
                elif solver.allow_counterattack() and \
                        solver.num_defends < combat_calcs.outspeed(solver.main_target, solver.attacker, solver.target_item, 'defense'):
                    return 'defender'
        else:
            return self.process_command(command)

    def process(self, solver, actions, playback):
        playback.append(('defender_phase',))
        multiattacks = combat_calcs.compute_multiattacks(solver.main_target, solver.attacker, solver.target_item, 'defense')
        for attack in range(multiattacks):
            solver.process(actions, playback, solver.main_target, solver.attacker, solver.target_item, 'defense')
        solver.num_defends += 1

class CombatPhaseSolver():
    states = {'init': InitState,
              'attacker': AttackerState,
              'defender': DefenderState}

    def __init__(self, attacker, main_target, splash, item, script=None):
        self.attacker = attacker
        self.main_target = main_target
        self.splash = splash
        self.item = item
        self.target_item = self.main_target.get_weapon()
        self.state = InitState()
        self.num_attacks, self.num_defends = 0, 0

        # For event combats
        self.script = reversed(script) if script else []
        self.current_command = '--'

    def get_state(self):
        return self.state

    def do(self):
        actions, playback = [], []
        self.state.process(self, actions, playback)
        return actions, playback

    def setup_next_state(self):
        next_state = self.state.get_next_state(self)
        if next_state:
            self.state = self.states[next_state]()
        else:
            self.state = None

    def get_script(self):
        if self.script:
            self.current_command = self.script.pop()
        else:
            self.current_command = '--'
        return self.current_command

    def generate_roll(self):
        rng_mode = DB.constants.get('rng').value
        if rng_mode == 'Classic':
            roll = static_random.get_combat()
        elif rng_mode == 'True Hit':
            roll = (static_random.get_combat() + static_random.get_combat()) // 2
        elif rng_mode == 'True Hit+':
            roll = (static_random.get_combat() + static_random.get_combat() + static_random.get_combat()) // 3
        elif rng_mode == 'Grandmaster':
            roll = 0
        return roll

    def generate_crit_roll(self):
        return static_random.get_combat()

    def process(self, actions, playback, attacker, defender, item, mode):
        to_hit = combat_calcs.compute_hit(attacker, defender, item, mode)

        if self.current_command in ('hit1', 'hit2', 'crit1', 'crit2'):
            roll = -1
        elif self.current_command in ('miss1', 'miss2'):
            roll = 100
        else:
            roll = self.generate_roll()

        if roll < to_hit:
            crit = False
            if DB.constants.get('crit').value or self.current_command in ('crit1', 'crit2'):
                to_crit = combat_calcs.compute_crit(attacker, defender, item, mode)
                if self.current_command in ('crit1', 'crit2'):
                    crit_roll = -1
                elif self.current_command in ('hit1', 'hit2', 'miss1', 'miss2'):
                    crit_roll = 100
                else:
                    crit_roll = self.generate_crit_roll()
                if crit_roll < to_crit:
                    crit = True
            if crit:
                item_system.on_crit(actions, playback, attacker, item, defender, mode)
                playback.append(('mark_crit', attacker, defender))
            else:
                item_system.on_hit(actions, playback, attacker, item, defender, mode)
                playback.append(('mark_hit', attacker, defender))
        else:
            item_system.on_miss(actions, playback, attacker, item, defender, mode)
            playback.append(('mark_miss', attacker, defender))

    def attacker_alive(self):
        return self.attacker.get_hp() > 0

    def main_target_alive(self):
        return self.main_target and self.main_target.get_hp() > 0

    def defender_has_vantage(self) -> bool:
        return self.allow_counterattack() and \
            skill_system.vantage(self.main_target)

    def allow_counterattack(self) -> bool:
        return combat_calcs.can_counterattack(self.attacker, self.item, self.main_target, self.target_item)

    def item_has_uses(self):
        return item_system.available(self.attacker, self.item)

    def target_item_has_uses(self):
        return self.main_target and self.target_item and item_system.available(self.main_target, self.target_item)
