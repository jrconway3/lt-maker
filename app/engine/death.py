from app.engine.sound import SOUNDTHREAD
from app.engine import action
from app.engine.game_state import game

class DeathManager():
    def __init__(self):
        self.dying_units = {}

    def should_die(self, unit):
        unit.is_dying = True
        self.dying_units[unit.nid] = 0

    def update(self) -> bool:
        for unit_nid in list(self.dying_units.keys()):
            death_counter = self.dying_units[unit_nid]
            unit = game.level.units.get(unit_nid)
            if death_counter == 0:
                SOUNDTHREAD.play_sfx('Death')
            elif death_counter == 1:
                unit.sprite.set_transition('fade_out')

            self.dying_units[unit_nid] += 1

            if death_counter >= 27:
                unit.is_dying = False
                action.do(action.Die(unit))
                del self.dying_units[unit_nid]

        return not self.dying_units  # Done when no dying units left

    def is_dying(self, unit):
        return unit.nid in self.dying_units
