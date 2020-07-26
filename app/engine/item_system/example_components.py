from app import utilities

from app.data.database import DB

from app.engine.item_system.item_component import ItemComponent, Type

from app.engine import action, status_system, targets, combat_calcs
from app.engine.item_system import item_system
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

    def usable(self, unit, item) -> bool:
        return item.data['uses'] > 0

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'uses', -1))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'uses', -1))

    def on_not_usable(self, unit, item):
        action.do(action.RemoveItem(unit, item))

class ChapterUses(ItemComponent):
    nid = 'c_uses'
    desc = "Number of uses per chapter for item. (Refreshes after each chapter)"

    expose = ('starting_uses', Type.Int)

    def init(self, item):
        item.data['uses'] = self.starting_uses

    def available(self, unit, item) -> bool:
        return item.data['c_uses'] > 0

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'c_uses', -1))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'c_uses', -1))

    def on_end_chapter(self, unit, item):
        # Don't need to use action here because it will be end of chapter
        item.data['c_uses'] = self.starting_uses

class HPCost(ItemComponent):
    nid = 'hp_cost'
    desc = "Item costs HP to use"
    expose = ('hp_cost', Type.Int)

    def available(self, unit, item) -> bool:
        return unit.get_hp() > self.hp_cost

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeHP(unit, -self.hp_cost))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeHP(unit, -self.hp_cost))

class ManaCost(ItemComponent):
    nid = 'mana_cost'
    desc = "Item costs mana to use"
    expose = ('mana_cost', Type.Int)

    def available(self, unit, item) -> bool:
        return unit.get_mana() > self.mana_cost

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeMana(unit, -self.mana_cost))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeMana(unit, -self.mana_cost))

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

    def weapon_type(self, unit, item):
        return self.weapon_type

    def available(self, unit, item) -> bool:
        klass = DB.classes.get(unit.klass)
        klass_usable = klass.wexp_gain.get(self.weapon_type).usable
        return unit.wexp[self.weapon_type] > 0 and klass_usable

class WeaponRank(ItemComponent):
    nid = 'weapon_rank'
    desc = "Item has a weapon rank and can only be used by units with high enough rank"
    requires = ['weapon_type']
    expose = ('weapon_rank', Type.WeaponRank)

    def weapon_rank(self, unit, item):
        return self.weapon_rank

    def available(self, unit, item):
        required_wexp = DB.weapon_ranks.get(self.weapon_rank).value
        weapon_type = item_system.weapon_type(unit, item)
        if weapon_type:
            return unit.wexp.get(weapon_type(unit, item)) > required_wexp
        else:  # If no weapon type, then always available
            return True

class TargetsAnything(ItemComponent):
    nid = 'target_tile'
    desc = "Item targets any tile"

    def valid_targets(self, unit, item) -> set:
        rng = item_system.get_range(unit, item)
        return targets.find_manhattan_spheres(rng, *unit.position)

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

class Usable(ItemComponent):
    nid = 'usable'
    desc = "Item is usable"

    def can_use(self, unit, item):
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

class Magic(ItemComponent):
    nid = 'magic'
    desc = 'Makes Item use magic damage formula'

    def damage_formula(self, unit, item):
        return 'MAGIC_DAMAGE'

class Heal(ItemComponent):
    nid = 'heal'
    desc = "Item heals on hit"
    expose = ('heal', Type.Int)

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Restricts target based on whether any unit has < full hp
        if defender and defender.get_hp() < game.equations.hitpoints(defender):
            return True
        for s in splash:
            if s.get_hp() < game.equations.hitpoints(s):
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        dist = utilities.calculate_distance(unit.position, target.position)
        heal = self.heal + game.equations.heal(unit, item, dist)
        actions.append(action.ChangeHP(target, heal))

        # For animation
        playback.append(('heal_hit', unit, item, target, heal))
        playback.append(('hit_sound', 'MapHeal'))
        if heal >= 30:
            name = 'MapBigHealTrans'
        elif heal >= 15:
            name = 'MapMediumHealTrans'
        else:
            name = 'MapSmallHealTrans'
        playback.append(('hit_anim', name, target))


class Damage(ItemComponent):
    nid = 'damage'
    desc = "Item does damage on hit"
    expose = ('damage', Type.Int)

    def damage(self, unit, item):
        return self.damage

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        damage = combat_calcs.compute_damage(unit, target, item, mode)

        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(('damage_hit', unit, item, target, damage))
        if damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

    def on_crit(self, actions, playback, unit, item, target, mode=None):
        damage = combat_calcs.compute_damage(unit, target, item, mode, crit=True)

        actions.append(action.ChangeHP(target, -damage))

        playback.append(('damage_crit', unit, item, target, damage))
        if damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

class Effective(ItemComponent):
    nid = 'effective'
    desc = 'Item does extra damage against certain units'
    requires = ['damage']
    expose = ('effective', Type.Int)

    def effective(self, unit, item):
        return self.effective

class EffectiveTag(ItemComponent):
    nid = 'effective_tag'
    desc = "Item is effective against units with these tags"
    requires = ['effective', 'damage']
    expose = ('effective_tag', Type.Dict, Type.Tag)

    def modify_damage(self, unit, item, target, mode=None) -> int:
        if any(tag in targets.tags for tag in self.effective_tag):
            return item_system.effective(unit, item)
        return 0

    def item_icon_mod(self, unit, item, target, sprite):
        if any(tag in target.tags for tag in self.effective_tag):
            # Make sprite white
            pass
        return sprite

class Hit(ItemComponent):
    nid = 'hit'
    desc = "Item has a chance to hit. If left off, item will always hit."
    expose = ('hit', Type.Int)

    def hit(self, unit, item):
        return self.hit

class Crit(ItemComponent):
    nid = 'crit'
    desc = "Item has a chance to crit. If left off, item cannot crit."
    expose = ('crit', Type.Int)

    def crit(self, unit, item):
        return self.crit

class Weight(ItemComponent):
    nid = 'weight'
    desc = "Item has a weight."
    expose = ('weight', Type.Int)

    def modify_double_attack(self, unit, item):
        return -max(0, self.weight - game.equations.constitution(unit))

    def modify_double_defense(self, unit, item):
        return -max(0, self.weight - game.equations.constitution(unit))

class Exp(ItemComponent):
    nid = 'exp'
    desc = "Item gives a custom number of exp to user on use"
    expose = ('exp', Type.Int)

    def exp(self, unit, item, target) -> int:
        return self.exp

class LevelExp(ItemComponent):
    nid = 'level_exp'
    desc = "Item gives exp to user based on level difference"

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

    healing_done = 0

    def exp(self, unit, item, target) -> int:
        heal_diff = self.healing_done - unit.get_internal_level()
        heal_diff += DB.constants.get('heal_offset').value
        exp_gained = DB.constants.get('heal_curve').value * heal_diff
        exp_gained += DB.constants.get('heal_magnitude').value
        self.healing_done = 0
        return max(exp_gained, DB.constants.get('heal_min').value)

    def on_hit(self, action, playback, unit, item, target, mode=None):
        heal = item.heal.heal + game.equations.heal(unit)
        missing_hp = game.equations.hitpoints(unit) - unit.get_hp()
        self.healing_done = min(heal, missing_hp)

class Wexp(ItemComponent):
    nid = 'wexp'
    desc = "Item gives a custom number of wexp to user on use"
    expose = ('wexp', Type.Int)

    def wexp(self, unit, item, target):
        return self.wexp

class Value(ItemComponent):
    nid = 'value'
    desc = "Item has a value and can be bought and sold. Items sell for half their value."
    expose = ('value', Type.Int)

    def buy_price(self, unit, item):
        if item.uses:
            frac = item.data['uses'] / item.uses.starting_uses
            return self.value * frac
        return self.value

    def sell_price(self, unit, item):
        if item.uses:
            frac = item.data['uses'] / item.uses.starting_uses
            return self.value * frac // 2
        return self.value // 2

class PermanentStatChange(ItemComponent):
    nid = 'permanent_stat_change'
    desc = "Item changes target's stats on hit."
    expose = ('stat_change', Type.Dict, Type.Stat)

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Ignore's splash
        klass = DB.classes.get(defender.klass)
        for stat, inc in self.stat_change.items():
            if inc <= 0 or defender.stats[stat] < klass.maximum:
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.PermanentStatChange(unit, self.stat_change))
        playback.append(('hit', unit, item, target))

class PermanentGrowthChange(ItemComponent):
    nid = 'permanent_growth_change'
    desc = "Item changes target's growths on hit"
    expose = ('stat_change', Type.Dict, Type.Stat)

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.PermanentGrowthChange(unit, self.stat_change))
        playback.append(('hit', unit, item, target))

class WexpChange(ItemComponent):
    nid = 'wexp_change'
    desc = "Item changes target's wexp on hit"
    expose = ('wexp_change', Type.Dict, Type.WeaponType)

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.WexpChange(unit, self.wexp_change))
        playback.append(('hit', unit, item, target))

class Refresh(ItemComponent):
    nid = 'refresh'
    desc = "Item allows target to move again on hit"

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # only targets areas where unit could move again
        if defender and defender.finished:
            return True
        for s in splash:
            if s.finished:
                return True

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.Reset(target))
        playback.append(('refresh_hit', unit, item, target))

class StatusOnHit(ItemComponent):
    nid = 'status_on_hit'
    desc = "Item gives status to target when it hits"
    expose = ('status', Type.Status)  # Nid

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.AddStatus(target, self.status))
        playback.append(('status_hit', unit, item, target, self.status))

class Restore(ItemComponent):
    nid = 'restore'
    desc = "Item removes status with time from target on hit"
    expose = ('status', Type.Status)

    def _can_be_restored(self, status):
        return (self.status.lower() == 'all' or status.nid == self.status)

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # only targets units that need to be restored
        if defender and status_system.check_ally(unit, defender) and any(status.time and self._can_be_restored(status) for status in defender.status_effects):
            return True
        for s in splash:
            if status_system.check_ally(unit, s) and any(status.time and self._can_be_restored(status) for status in s.status_effects):
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        for status in unit.status_effects:
            if status.time and self._can_be_restored(status):
                actions.append(action.RemoveStatus(unit, status))
        playback.append(('hit', unit, item, target))
