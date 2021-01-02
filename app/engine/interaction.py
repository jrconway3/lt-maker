from app.engine.solver import CombatPhaseSolver
from app.engine.map_combat import MapCombat
from app.engine import item_system, action
from app.engine.game_state import game

def has_animation(attacker, item, main_target, splash):
    return False

def engage(attacker, positions, item, skip=False, script=None):
    # Does one round of combat
    if len(positions) > 1:
        # Multiple targets
        splash = set()
        for pos in positions:
            main_target, s = item_system.splash(attacker, item, pos)
            if main_target:
                splash.add(main_target)
            splash |= s
        main_target = None
    elif len(positions) == 0:
        main_target, splash = item_system.splash(attacker, item, attacker.position)
    else:
        main_target, splash = item_system.splash(attacker, item, positions[0])
    if skip:
        combat = SimpleCombat(attacker, item, main_target, splash, script)
    elif has_animation(attacker, item, main_target, splash):
        combat = AnimationCombat(attacker, item, main_target, splash, script)
    else:
        combat = MapCombat(attacker, item, positions[0], main_target, splash, script)
    return combat

def start_combat(self, unit, target, item, ai_combat=False, event_combat=False, script=None):
    if item.sequence_item:
        for subitem in item.subitems:
            num_targets = item_system.num_targets(unit, subitem)
            combat = engage(unit, [target] * num_targets, subitem, script=script)
            combat.ai_combat = ai_combat # Must mark this so we can come back!
            combat.event_combat = event_combat # Must mark this so we can come back!
            game.combat_instance.append(combat)
            game.state.change('combat')
    else:
        num_targets = item_system.num_targets(unit, subitem)
        combat = engage(unit, [target] * num_targets, item, script=script)
        combat.ai_combat = ai_combat # Must mark this so we can come back!
        combat.event_combat = event_combat # Must mark this so we can come back!
        game.combat_instance.append(combat)
        game.state.change('combat')

class SimpleCombat():
    """
    Used when engaging in combat within the base or when for
    some reason, an animation combat cannot be used and the attacker
    has no position
    """
    def __init__(self, attacker, item, main_target, splash, script):
        self.attacker = attacker
        self.state_machine = CombatPhaseSolver(attacker, main_target, splash, item, script)
        while self.state_machine.get_state():
            self.actions, self.playback = self.state_machine.do()
            self._apply_actions()
            self.state_machine.setup_next_state()

    def _apply_actions(self):
        """
        Actually commit the actions that we had stored!
        """
        for act in self.actions:
            action.execute(act)

    def update(self) -> bool:
        self.clean_up()
        return True

    def draw(self, surf):
        return surf

    def clean_up(self):
        action.do(action.HasAttacked(self.attacker))
        if self.attacker.team == 'player':
            game.state.clear()
            game.state.change('free')
            game.state.change('wait')
        else:
            game.state.back()
            game.state.change('wait')

class AnimationCombat(SimpleCombat):
    # TODO Implement
    pass



