from app import utilities

from app.data.database import DB

from app.engine.item_system import ItemComponent, Type

from app.engine import action, status_system, item_system, targets
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

    def can_be_countered(self, unit, item):
        return True

    def can_counter(self, unit, item):
        return True

class SiegeWeapon(ItemComponent):
    nid = 'siege_weapon'
    desc = "Item will be treated as a siege weapon (can not double or counterattack, but can still be equipped)"

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
        # item.data['uses'] -= 1
        action.do(action.IncItemData(item, 'uses', -1))

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
        # item.data['c_uses'] -= 1
        action.do(action.IncItemData(item, 'c_uses', -1))

    def on_not_available(self, unit, item):
        pass

    def on_end_chapter(self, unit, item):
        # Don't need to use action here because it will be end of chapter
        item.data['c_uses'] = self.starting_uses

class HPCost(ItemComponent):
    nid = 'hp_cost'
    desc = "Item costs HP to use"
    expose = ('hp_cost', Type.Int)

    def available(self, unit, item) -> bool:
        return unit.get_hp() > self.hp_cost

    def on_use(self, unit, item):
        action.do(action.ChangeHP(unit, -self.hp_cost))

class ManaCost(ItemComponent):
    nid = 'mana_cost'
    desc = "Item costs mana to use"
    expose = ('mana_cost', Type.Int)

    def available(self, unit, item) -> bool:
        return unit.get_mana() > self.mana_cost

    def on_use(self, unit, item):
        action.do(action.ChangeMana(unit, -self.mana_cost))

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
        weapon_type = item_system.weapon_type(unit, item)
        if weapon_type:
            return unit.wexp.get(weapon_type(unit, item)) > required_wexp
        else:  # If no weapon type, then always available
            return True

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

class BlastAOE(ItemComponent):
    nid = 'aoe_blast'
    desc = "Gives Blast AOE"
    expose = ('radius', Type.Int)

    def splash(self, unit, item, position) -> tuple:
        ranges = set(range(self.radius + 1))
        splash = targets.find_manhattan_spheres(ranges, position[0], position[1])
        if item_system.is_spell(unit, item):
            # spell blast
            splash = [game.grid.get_unit(s) for s in splash]
            splash = [s for s in splash if s]
            return None, splash
        else:
            # regular blast
            splash = [game.grid.get_unit(s) for s in splash if s != position]
            splash = [s for s in splash if s]
            return game.grid.get_unit(position), splash

class Damage(ItemComponent):
    nid = 'damage'
    desc = "Item does damage on hit"
    expose = ('damage', Type.Int)

    def display_might(self, unit, item) -> int:
        return combat_calcs.damage(unit, item) + self.damage

    def display_damage(self, unit, item, target, mode=None) -> int:
        return combat_calcs.compute_damage(unit, target, item, mode)

    def on_hit(self, unit, item, target, mode=None):
        damage = combat_calcs.compute_damage(unit, target, item, mode)
        action.do(action.ChangeHP(target, -damage))

    def on_crit(self, unit, item, target, mode=None):
        damage = combat_calcs.compute_damage(unit, target, item, mode, crit=True)
        action.do(action.ChangeHP(target, -damage))

class PermanentStatChange(ItemComponent):
    nid = 'permanent_stat_change'
    desc = "Item changes target's stats on hit."
    expose = ('stat_change', Type.Dict, Type.Stat)

    def target_restrict(self, unit, item, target) -> bool:
        klass = DB.classes.get(target.klass)
        for stat, inc in self.stat_change.items():
            if inc <= 0 or target.stats[stat] < klass.maximum:
                return True
        return False

    def on_hit(self, unit, item, target, mode=None):
        action.do(action.PermanentStatChange(unit, self.stat_change))

class PermanentGrowthChange(ItemComponent):
    nid = 'permanent_growth_change'
    desc = "Item changes target's growths on hit"
    expose = ('stat_change', Type.Dict, Type.Stat)

    def on_hit(self, unit, item, target, mode=None):
        action.do(action.PermanentGrowthChange(unit, self.stat_change))

class WexpChange(ItemComponent):
    nid = 'wexp_change'
    desc = "Item changes target's wexp on hit"
    expose = ('wexp_change', Type.Dict, Type.WeaponType)

    def on_hit(self, unit, item, target, mode=None):
        action.do(action.WexpChange(unit, self.wexp_change))

class 
