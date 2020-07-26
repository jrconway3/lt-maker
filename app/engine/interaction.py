from app.engine.solver import CombatPhaseSolver
from app.engine.map_combat import MapCombat
from app.engine.item_system import item_system

def has_animation(attacker, item, main_target, splash):
    return False

def engage(attacker, position, item, skip=False):
    # Does one round of combat
    main_target, splash = item_system.splash(attacker, item, position)
    if skip:
        combat = SimpleCombat(attacker, item, position, main_target, splash)
    elif has_animation(attacker, item, main_target, splash):
        combat = AnimationCombat(attacker, item, position, main_target, splash)
    else:
        combat = MapCombat(attacker, item, position, main_target, splash)
    return combat

class SimpleCombat():
    """
    Used when engaging in combat within the base or when for
    some reason, an animation combat cannot be used and the attacker
    has no position
    """
    def __init__(self, attacker, item, position, main_target, splash):
        self.state_machine = CombatPhaseSolver(attacker, main_target, splash, item)
        while self.state_machine.get_state():
            self.state_machine.do()

    def update(self) -> bool:
        return True

    def draw(self, surf):
        return surf

class AnimationCombat(Combat):
    # TODO Implement
    pass



