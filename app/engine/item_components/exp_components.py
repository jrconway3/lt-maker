import math

from app.data.database import DB

from app.data.item_component import ItemComponent, Type

from app.engine import status_system, equations

class Exp(ItemComponent):
    nid = 'exp'
    desc = "Item gives a custom number of exp to user on use"
    expose = Type.Int
    tag = 'exp'

    def exp(self, unit, item, target) -> int:
        return self.value

class LevelExp(ItemComponent):
    nid = 'level_exp'
    desc = "Item gives exp to user based on level difference"
    tag = 'exp'

    def exp(self, unit, item, target) -> int:
        if status_system.check_enemy(unit, target):
            level_diff = target.get_internal_level() - unit.get_internal_level()
            level_diff += DB.constants.get('exp_offset').value
            exp_gained = math.exp(level_diff * DB.constants.get('exp_curve'))
            exp_gained *= DB.constants.get('exp_magnitude').value
        else:
            exp_gained = 0
        return exp_gained

class HealExp(ItemComponent):
    nid = 'heal_exp'
    desc = "Item gives exp to user based on amount of damage healed"
    requires = ['heal']
    tag = 'exp'

    healing_done = 0

    def exp(self, unit, item, target) -> int:
        heal_diff = self.healing_done - unit.get_internal_level()
        heal_diff += DB.constants.get('heal_offset').value
        exp_gained = DB.constants.get('heal_curve').value * heal_diff
        exp_gained += DB.constants.get('heal_magnitude').value
        self.healing_done = 0
        return max(exp_gained, DB.constants.get('heal_min').value)

    def on_hit(self, action, playback, unit, item, target, mode=None):
        heal = item.heal.heal + equations.parser.heal(unit)
        missing_hp = equations.parser.hitpoints(unit) - unit.get_hp()
        self.healing_done = min(heal, missing_hp)

class Wexp(ItemComponent):
    nid = 'wexp'
    desc = "Item gives a custom number of wexp to user on use"
    expose = Type.Int
    tag = 'exp'

    def wexp(self, unit, item, target):
        return self.value - 1  # Because 1 will already be given by WeaponComponent
