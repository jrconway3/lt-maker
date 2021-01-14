from app.data.database import DB

from app.engine import combat_calcs, item_system, skill_system, static_random, action, item_funcs

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
            if solver.main_target:
                if DB.constants.value('def_double') or skill_system.def_double(solver.main_target):
                    defender_outspeed = combat_calcs.outspeed(solver.main_target, solver.attacker, solver.target_item, 'defense')
                else:
                    defender_outspeed = 1
                attacker_outspeed = combat_calcs.outspeed(solver.attacker, solver.main_target, solver.item, 'attack')
            else:
                attacker_outspeed = defender_outspeed = 1
            multiattacks = combat_calcs.compute_multiattacks(solver.attacker, solver.main_target, solver.item, 'attack')

            if solver.attacker_alive() and solver.main_target_alive():
                if solver.item_has_uses() and \
                        solver.num_subattacks < multiattacks:
                    return 'attacker'
                elif solver.allow_counterattack() and \
                        solver.num_defends < defender_outspeed:
                    solver.num_subdefends = 0
                    return 'defender'
                elif solver.item_has_uses() and \
                        solver.num_attacks < attacker_outspeed:
                    solver.num_subattacks = 0
                    return 'attacker'
            return None
        else:
            return self.process_command(command)

    def process(self, solver, actions, playback):
        playback.append(('attacker_phase',))
        if solver.main_target:
            solver.process(actions, playback, solver.attacker, solver.main_target, solver.item, 'attack')
        for target in solver.splash:
            solver.process(actions, playback, solver.attacker, target, solver.item, 'splash')
        
        solver.num_subattacks += 1
        multiattacks = combat_calcs.compute_multiattacks(solver.attacker, solver.main_target, solver.item, 'attack')
        if solver.num_subattacks >= multiattacks:
            solver.num_attacks += 1

class DefenderState(SolverState):
    def get_next_state(self, solver):
        command = solver.get_script()
        if command == '--':
            if solver.attacker_alive() and solver.main_target_alive():
                if DB.constants.value('def_double') or skill_system.def_double(solver.main_target):
                    defender_outspeed = combat_calcs.outspeed(solver.main_target, solver.attacker, solver.target_item, 'defense')
                else:
                    defender_outspeed = 1
                attacker_outspeed = combat_calcs.outspeed(solver.attacker, solver.main_target, solver.item, 'attack')
                multiattacks = combat_calcs.compute_multiattacks(solver.main_target, solver.attacker, solver.target_item, 'defense')
                
                if solver.allow_counterattack() and \
                        solver.num_subdefends < multiattacks:
                    return 'defender'    
                elif solver.item_has_uses() and \
                        solver.num_attacks < attacker_outspeed:
                    solver.num_subattacks = 0
                    return 'attacker'
                elif solver.allow_counterattack() and \
                        solver.num_defends < defender_outspeed:
                    solver.num_subdefends = 0
                    return 'defender'
        else:
            return self.process_command(command)

    def process(self, solver, actions, playback):
        playback.append(('defender_phase',))
        solver.process(actions, playback, solver.main_target, solver.attacker, solver.target_item, 'defense')
        
        solver.num_subdefends += 1
        multiattacks = combat_calcs.compute_multiattacks(solver.main_target, solver.attacker, solver.target_item, 'defense')
        if solver.num_subdefends >= multiattacks:
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
        if self.main_target:
            self.target_item = self.main_target.get_weapon()
        else:
            self.target_item = None
        self.state = InitState()
        self.num_attacks, self.num_defends = 0, 0
        self.num_subattacks, self.num_subdefends = 0, 0

        # For event combats
        self.script = list(reversed(script)) if script else []
        self.current_command = '--'

    def get_state(self):
        return self.state

    def do(self):
        old_random_state = static_random.get_combat_random_state()
        
        actions, playback = [], []
        self.state.process(self, actions, playback)

        new_random_state = static_random.get_combat_random_state()
        action.do(action.RecordRandomState(old_random_state, new_random_state))

        return actions, playback

    def setup_next_state(self):
        old_random_state = static_random.get_combat_random_state()

        next_state = self.state.get_next_state(self)
        logger.debug("Next State: %s" % next_state)
        if next_state:
            self.state = self.states[next_state]()
        else:
            self.state = None
            
        new_random_state = static_random.get_combat_random_state()
        action.do(action.RecordRandomState(old_random_state, new_random_state))

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
                    crit = True
                elif self.current_command in ('hit1', 'hit2', 'miss1', 'miss2'):
                    crit = False
                elif to_crit is not None:
                    crit_roll = self.generate_crit_roll()
                    if crit_roll < to_crit:
                        crit = True
            if crit:
                item_system.on_crit(actions, playback, attacker, item, defender, mode)
                playback.append(('mark_crit', attacker, defender, self.attacker))
            else:
                item_system.on_hit(actions, playback, attacker, item, defender, mode)
                playback.append(('mark_hit', attacker, defender, self.attacker))
            item_system.after_hit(actions, playback, attacker, item, defender, mode)
            skill_system.after_hit(actions, playback, attacker, item, defender, mode)
        else:
            item_system.on_miss(actions, playback, attacker, item, defender, mode)
            playback.append(('mark_miss', attacker, defender, self.attacker))

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
        return item_funcs.available(self.attacker, self.item)

    def target_item_has_uses(self):
        return self.main_target and self.target_item and item_funcs.available(self.main_target, self.target_item)
