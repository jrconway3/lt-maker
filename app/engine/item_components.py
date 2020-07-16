from app import utilities

from app.data.database import DB

from app.engine.item_system import ItemComponent, Type

from app.engine import action, status_system, item_system
from app.engine.game_state import game

class Spell(ItemComponent):
    nid = 'spell'
    desc = "Item will be treated as a spell (cannot counterattack or double)"

    def is_spell(self, unit, item):
        return True

    def is_weapon(self, unit, item):
        return False

class Weapon(ItemComponent):
    nid = 'weapon'
    desc = "Item will be treated as a normal weapon (can double, counterattack, be equipped, etc.)" 

    def is_weapon(self, unit, item):
        return True

    def is_spell(self, unit, item):
        return False

    def equippable(self, unit, item):
        return True

class Uses(ItemComponent):
    nid = 'uses'
    desc = "Number of uses of item"
    expose = ('starting_uses', Type.Int)

    def init(self, item):
        item.data['uses'] = self.starting_uses

    def available(self, unit, item) -> bool:
        return item.data['uses'] > 0

    def on_use(self, unit, item):
        item.data['uses'] -= 1

    def on_not_available(self, unit, item):
        action.do(action.RemoveItem(unit, item))

class ChapterUses(ItemComponent):
    nid = 'c_uses'
    desc = "Number of uses per chapter for item. (Refreshes after each chapter)"

    expose = ('starting_uses', Type.Int)

    def init(self, item):
        item.data['uses'] = self.starting_uses

    def available(self, unit, item) -> bool:
        return item.data['c_uses'] > 0

    def on_use(self, unit, item):
        item.data['c_uses'] -= 1

    def on_not_available(self, unit, item):
        pass

    def on_end_chapter(self, unit, item):
        item.data['c_uses'] = self.starting_uses

class HPCost(ItemComponent):
    nid = 'hp_cost'
    desc = "Item costs HP to use"
    expose = ('hp_cost', Type.Int)

    def available(self, unit, item) -> bool:
        return unit.get_hp() > self.hp_cost

    def on_use(self, unit, item):
        unit.change_hp(-self.hp_cost)

    def on_not_available(self, unit, item):
        pass

class ManaCost(ItemComponent):
    nid = 'mana_cost'
    desc = "Item costs mana to use"
    expose = ('mana_cost', Type.Int)

    def available(self, unit, item) -> bool:
        return unit.get_hp() > self.mana_cost

    def on_use(self, unit, item):
        unit.change_mana(-self.mana_cost)

    def on_not_available(self, unit, item):
        pass

class PrfUnit(ItemComponent):
    nid = 'prf_unit'
    desc = 'Item can only be wielded by certain units'
    expose = ('units', Type.Set, Type.Unit)

    def available(self, unit, item) -> bool:
        return unit.nid in self.units

class PrfClass(ItemComponent):
    nid = 'prf_class'
    desc = 'Item can only be wielded by certain classes'
    expose = ('classes', Type.Set, Type.Class)

    def available(self, unit, item) -> bool:
        return unit.klass in self.classes

class PrfTag(ItemComponent):
    nid = 'prf_tags'
    desc = 'Item can only be wielded by units with certain tags'
    expose = ('tags', Type.Set, Type.Tag)

    def available(self, unit, item) -> bool:
        return any(tag in self.tags for tag in unit.tags)

class WeaponType(ItemComponent):
    nid = 'weapon_type'
    desc = "Item has a weapon type and can only be used by certain classes"
    expose = ('weapon_type', Type.WeaponType)

    def available(self, unit, item) -> bool:
        klass = DB.classes.get(unit.klass)
        klass_usable = klass.wexp_gain.get(self.weapon_type).usable
        return unit.wexp[self.weapon_type] > 0 and klass_usable

class WeaponRank(ItemComponent):
    nid = 'weapon_rank'
    desc = "Item has a weapon rank and can only be used by units with high enough rank"
    requires = ['weapon_type']
    expose = ('weapon_rank', Type.WeaponRank)

    def available(self, unit, item):
        required_wexp = DB.weapon_ranks.get(self.weapon_rank).value
        return unit.wexp.get(item.weapon_type.weapon_type) > required_wexp

class TargetsUnits(ItemComponent):
    nid = 'target_unit'
    desc = "Item targets any unit"

    def valid_targets(self, unit, item) -> set:
        return {other.position for other in game.level.units if other.position and 
                utilities.calculate_distance(unit.position, other.position) in item_system.get_range(unit, item)}

class TargetsEnemies(ItemComponent):
    nid = 'target_enemy'
    desc = "Item targets any enemy"

    def valid_targets(self, unit, item) -> set:
        return {other.position for other in game.level.units if other.position and 
                status_system.check_enemy(unit, other) and 
                utilities.calculate_distance(unit.position, other.position) in item_system.get_range(unit, item)}

class TargetsAllies(ItemComponent):
    nid = 'target_ally'
    desc = "Item targets any ally"

    def valid_targets(self, unit, item) -> set:
        return {other.position for other in game.level.units if other.position and 
                status_system.check_ally(unit, other) and 
                utilities.calculate_distance(unit.position, other.position) in item_system.get_range(unit, item)}

class TargetsInjuredAllies(ItemComponent):
    nid = 'target_injured'
    desc = "Item targets any injured ally"

    def valid_targets(self, unit, item) -> set:
        return {other.position for other in game.level.units if 
                other.position and 
                status_system.check_ally(unit, other) and 
                other.get_hp() < game.equations.hitpoints(other) and
                utilities.calculate_distance(unit.position, other.position) in item_system.get_range(unit, item)}

class MinimumRange(ItemComponent):
    nid = 'min_range'
    desc = "Set the minimum_range of the item to an integer"

    expose = ('minimum_range', Type.Int)

    def minimum_range(self, unit, item) -> int:
        return self.minimum_range

class MaximumRange(ItemComponent):
    nid = 'max_range'
    desc = "Set the maximum_range of the item to an integer"
    expose = ('maximum_range', Type.Int)

    def maximum_range(self, unit, item) -> int:
        return self.maximum_range

class HealUsable(ItemComponent):
    nid = 'usable_heal'
    desc = "Item is usable when unit's HP < max HP"

    def can_use(self, unit, item) -> bool:
        return unit.get_hp() < game.equations.hitpoints(unit)

class AlwaysUsable(ItemComponent):
    nid = 'usable_always'
    desc = "Item is usable"

    def can_use(self, unit, item) -> bool:
        return True

class Locked(ItemComponent):
    nid = 'locked'
    desc = 'Item cannot be discarded, traded, or stolen'

    def locked(self, unit, item) -> bool:
        return True
