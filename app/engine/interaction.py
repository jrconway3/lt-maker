from app.engine.solver import CombatPhaseSolver
from app.engine.map_combat import MapCombat
from app.engine import item_system, action
from app.engine.game_state import game

def has_animation(attacker, item, main_target, splash):
    return False

def engage(attacker, position, item, skip=False):
    # Does one round of combat
    if len(position) > 1:
        # Multiple targets
        splash = set()
        for pos in position:
            main_target, s = item_system.splash(attacker, item, pos)
            if main_target:
                splash.add(main_target)
            splash |= s
        main_target = None
    else:
        main_target, splash = item_system.splash(attacker, item, position[0])
    if skip:
        combat = SimpleCombat(attacker, item, main_target, splash)
    elif has_animation(attacker, item, main_target, splash):
        combat = AnimationCombat(attacker, item, main_target, splash)
    else:
        combat = MapCombat(attacker, item, position[0], main_target, splash)
    return combat

class SimpleCombat():
    """
    Used when engaging in combat within the base or when for
    some reason, an animation combat cannot be used and the attacker
    has no position
    """
    def __init__(self, attacker, item, main_target, splash):
        self.attacker = attacker
        self.state_machine = CombatPhaseSolver(attacker, main_target, splash, item)
        while self.state_machine.get_state():
            self.actions, self.playback = self.state_machine.do()
            self._apply_actions()

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



