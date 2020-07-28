from app.data.database import DB

from app.engine.item_system.item_component import ItemComponent, Type

from app.engine import targets
from app.engine.item_system import item_system
from app.engine.game_state import game 

class WeaponType(ItemComponent):
    nid = 'weapon_type'
    desc = "Item has a weapon type and can only be used by certain classes"
    expose = Type.WeaponType

    def weapon_type(self, unit, item):
        return self.value

    def available(self, unit, item) -> bool:
        klass = DB.classes.get(unit.klass)
        klass_usable = klass.wexp_gain.get(self.value).usable
        return unit.wexp[self.value] > 0 and klass_usable

class WeaponRank(ItemComponent):
    nid = 'weapon_rank'
    desc = "Item has a weapon rank and can only be used by units with high enough rank"
    requires = ['weapon_type']
    expose = (Type.WeaponRank)

    def weapon_rank(self, unit, item):
        return self.value

    def available(self, unit, item):
        required_wexp = DB.weapon_ranks.get(self.value).value
        weapon_type = item_system.weapon_type(unit, item)
        if weapon_type:
            return unit.wexp.get(weapon_type(unit, item)) > required_wexp
        else:  # If no weapon type, then always available
            return True

class Magic(ItemComponent):
    nid = 'magic'
    desc = 'Makes Item use magic damage formula'

    def damage_formula(self, unit, item):
        return 'MAGIC_DAMAGE'

class Hit(ItemComponent):
    nid = 'hit'
    desc = "Item has a chance to hit. If left off, item will always hit."
    expose = Type.Int

    def hit(self, unit, item):
        return self.value

class Crit(ItemComponent):
    nid = 'crit'
    desc = "Item has a chance to crit. If left off, item cannot crit."
    expose = Type.Int

    def crit(self, unit, item):
        return self.value

class Weight(ItemComponent):
    nid = 'weight'
    desc = "Item has a weight."
    expose = Type.Int

    def modify_double_attack(self, unit, item):
        return -max(0, self.value - game.equations.constitution(unit))

    def modify_double_defense(self, unit, item):
        return -max(0, self.value - game.equations.constitution(unit))

class Effective(ItemComponent):
    nid = 'effective'
    desc = 'Item does extra damage against certain units'
    requires = ['damage']
    expose = Type.Int

    def effective(self, unit, item):
        return self.value

class EffectiveTag(ItemComponent):
    nid = 'effective_tag'
    desc = "Item is effective against units with these tags"
    requires = ['effective', 'damage']
    expose = (Type.Dict, Type.Tag)

    def modify_damage(self, unit, item, target, mode=None) -> int:
        if any(tag in targets.tags for tag in self.value):
            return item_system.effective(unit, item)
        return 0

    def item_icon_mod(self, unit, item, target, sprite):
        if any(tag in target.tags for tag in self.value):
            # Make sprite white
            pass
        return sprite
