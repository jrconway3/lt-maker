from app.data.database import DB

from app.engine import action, banner, combat_calcs, item_system, status_system, static_random
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

def handle_booster(unit, item):
    action.do(action.UseItem(item))
    if item.uses and item.uses.value <= 0:
        game.alerts.append(banner.BrokenItem(unit, item))
        game.state.change('alert')
        action.do(action.RemoveItem(unit, item))

    # Actually use item
    if item.permanent_stat_increase:
        game.memory['exp'] = (unit, item.permanent_stat_increase, None, 'booster')
        game.state.change('exp')
    elif item.permanent_growth_increase:
        action.do(action.PermanentGrowthIncrease(unit, item.permanent_growth_increase))
    elif item.wexp_increase:
        action.do(action.GainWexp(unit, item.wexp_increase))
    elif item.promotion:
        game.memory['exp'] = (unit, 0, None, 'item_promote')
        game.state.change('exp')
    elif item.event_script:
        pass  # TODO

class SolverState():
    def get_next_state(self, solver):
        return None

    def process(self, solver):
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

    def process(self, solver):
        multiattacks = combat_calcs.compute_multiattacks(solver.attacker, solver.main_target, solver.item, 'attack')
        for attack in range(multiattacks):
            if solver.main_target:
                solver.process(solver.attacker, solver.main_target, solver.item, 'attack')
            for target in solver.splash:
                solver.process(solver.attacker, target, solver.item, 'attack')
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

    def process(self, solver):
        multiattacks = combat_calcs.compute_multiattacks(solver.main_target, solver.attacker, solver.target_item, 'defense')
        for attack in range(multiattacks):
            solver.process(solver.main_target, solver.attacker, solver.target_item, 'defend')
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
        self.state.process(self)
        next_state = self.state.get_next_state(self)
        if next_state:
            self.state = self.states[next_state]()

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

    def process(self, attacker, defender, item, mode):
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
                combat_calcs.on_crit(attacker, item, defender, mode)
            else:
                combat_calcs.on_hit(attacker, item, defender, mode)

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

def engage(attacker, position, item):
    # Does one round of combat
    starting_action_index = game.action_log.action_index
    main_target, splash = item_system.splash(attacker, item, position)
    state_machine = CombatPhaseSolver(attacker, main_target, splash, item)
    while state_machine.get_state():
        state_machine.do()
    return starting_action_index
