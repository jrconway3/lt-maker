from app.data.database import DB

from app.engine import combat_calcs, item_system, status_system, static_random
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

class SolverState():
    def get_next_state(self, solver):
        return None

    def process(self, solver, actions, playback):
        return None

class InitState(SolverState):
    def get_next_state(self, solver):
        if solver.defender_has_vantage():
            return 'defender'
        else:
            return 'attacker'

class AttackerState(SolverState):
    def get_next_state(self, solver):
        if solver.attacker_alive() and solver.main_target_alive():
            if solver.allow_counterattack() and \
                    solver.num_defends < combat_calcs.outspeed(solver.main_target, solver.attacker, solver.target_item, 'defend'):
                return 'defender'
            elif solver.item_has_uses() and \
                    solver.num_attacks < combat_calcs.outspeed(solver.attacker, solver.main_target, solver.item, 'attack'):
                return 'attacker'
        return None

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
        if solver.attacker_alive() and solver.main_target_alive():
            if solver.item_has_uses() and \
                    solver.num_attacks < combat_calcs.outspeed(solver.attacker, solver.main_target, solver.item, 'attack'):
                return 'attacker'
            elif solver.allow_counterattack() and \
                    solver.num_defends < combat_calcs.outspeed(solver.main_target, solver.attacker, solver.target_item, 'defend'):
                return 'defender'

    def process(self, solver, actions, playback):
        playback.append(('defender_phase',))
        multiattacks = combat_calcs.compute_multiattacks(solver.main_target, solver.attacker, solver.target_item, 'defense')
        for attack in range(multiattacks):
            solver.process(actions, playback, solver.main_target, solver.attacker, solver.target_item, 'defend')
        solver.num_defends += 1

class CombatPhaseSolver():
    states = {'init': InitState,
              'attacker': AttackerState,
              'defender': DefenderState}

    def __init__(self, attacker, main_target, splash, item):
        self.attacker = attacker
        self.main_target = main_target
        self.splash = splash
        self.item = item
        self.target_item = self.main_target.get_weapon()
        self.state = InitState()
        self.num_attacks, self.num_defends = 0, 0

    def get_state(self):
        return self.state

    def do(self):
        actions, playback = [], []
        self.state.process(self, actions, playback)
        next_state = self.state.get_next_state(self)
        if next_state:
            self.state = self.states[next_state]()
        return actions, playback

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
        roll = self.generate_roll()
        if roll < to_hit:
            crit = False
            if DB.constants.get('crit').value:
                to_crit = combat_calcs.compute_crit(attacker, defender, item, mode)
                crit_roll = self.generate_crit_roll()
                if crit_roll < to_crit:
                    crit = True
            if crit:
                combat_calcs.on_crit(actions, playback, attacker, item, defender, mode)
            else:
                combat_calcs.on_hit(actions, playback, attacker, item, defender, mode)
        else:
            combat_calcs.on_miss(actions, playback, attacker, item, defender, mode)

    def attacker_alive(self):
        return self.attacker.get_hp() > 0

    def main_target_alive(self):
        return self.main_target and self.main_target.get_hp() > 0

    def defender_has_vantage(self):
        return self.allow_counterattack() and \
            status_system.vantage(self.main_target) and \
            not item_system.can_be_countered(self.attacker, self.item)

    def allow_counterattack(self):
        return self.target_item_has_uses() and \
            item_system.can_be_countered(self.attacker, self.item) and \
            item_system.can_counter(self.main_target, self.target_item) and \
            (not self.attacker.position or \
             self.attacker.position in self.attacker.item_system.valid_targets(self.main_target, self.target_item))

    def item_has_uses(self):
        return item_system.available(self.attacker, self.item)

    def target_item_has_uses(self):
        return self.main_target and self.target_item and item_system.available(self.main_target, self.target_item)