from app.utilities import utils

from app.data.database import DB

from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import action, combat_calcs, equations, banner
from app.engine import item_system, skill_system, item_funcs
from app.engine.game_state import game

class Heal(ItemComponent):
    nid = 'heal'
    desc = "Item heals this amount on hit"
    tag = 'weapon'

    expose = Type.Int
    value = 10

    def _get_heal_amount(self, unit):
        return self.value

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Restricts target based on whether any unit has < full hp
        if defender and defender.get_hp() < equations.parser.hitpoints(defender):
            return True
        for s in splash:
            if s.get_hp() < equations.parser.hitpoints(s):
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        heal = self._get_heal_amount(unit)
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

    def ai_priority(self, unit, item, target, move):
        if skill_system.check_ally(unit, target):
            max_hp = equations.parser.hitpoints(target)
            missing_health = max_hp - target.get_hp()
            help_term = utils.clamp(missing_health / float(max_hp), 0, 1)
            heal = self._get_heal_amount(unit)
            heal_term = utils.clamp(min(heal, missing_health) / float(max_hp), 0, 1)
            return help_term * heal_term
        return 0

class MagicHeal(Heal, ItemComponent):
    nid = 'magic_heal'
    desc = "Item heals this amount + HEAL on hit"

    def _get_heal_amount(self, unit):
        return self.value + equations.parser.heal(unit)

class Damage(ItemComponent):
    nid = 'damage'
    desc = "Item does damage on hit"
    tag = 'weapon'

    expose = Type.Int
    value = 0

    def damage(self, unit, item):
        return self.value

    def on_hit(self, actions, playback, unit, item, target, mode):
        damage = combat_calcs.compute_damage(unit, target, item, mode)

        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(('damage_hit', unit, item, target, damage))
        if damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

    def on_crit(self, actions, playback, unit, item, target, mode):
        damage = combat_calcs.compute_damage(unit, target, item, mode, crit=True)

        actions.append(action.ChangeHP(target, -damage))

        playback.append(('damage_crit', unit, item, target, damage))
        if damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

class PermanentStatChange(ItemComponent):
    nid = 'permanent_stat_change'
    desc = "Item changes target's stats on hit."
    tag = 'extra'

    expose = (Type.Dict, Type.Stat)

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Ignore's splash
        klass = DB.classes.get(defender.klass)
        for stat, inc in self.value.items():
            if inc <= 0 or defender.stats[stat] < klass.maximum:
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.PermanentStatChange(unit, self.value))
        playback.append(('hit', unit, item, target))

class PermanentGrowthChange(ItemComponent):
    nid = 'permanent_growth_change'
    desc = "Item changes target's growths on hit"
    tag = 'extra'

    expose = (Type.Dict, Type.Stat)

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.PermanentGrowthChange(unit, self.value))
        playback.append(('hit', unit, item, target))

class WexpChange(ItemComponent):
    nid = 'wexp_change'
    desc = "Item changes target's wexp on hit"
    tag = 'extra'

    expose = (Type.Dict, Type.WeaponType)

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.WexpChange(unit, self.value))
        playback.append(('hit', unit, item, target))

class Refresh(ItemComponent):
    nid = 'refresh'
    desc = "Item allows target to move again on hit"
    tag = 'extra'

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
    tag = 'extra'

    expose = Type.Skill  # Nid

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        act = action.AddSkill(target, self.value, unit)
        actions.append(act)
        playback.append(('status_hit', unit, item, target, self.value))

class Restore(ItemComponent):
    nid = 'restore'
    desc = "Item removes all time statuses from target on hit"
    tag = 'extra'

    def _can_be_restored(self, status):
        return status.time

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # only targets units that need to be restored
        if defender and skill_system.check_ally(unit, defender) and any(self._can_be_restored(skill) for skill in defender.skills):
            return True
        for s in splash:
            if skill_system.check_ally(unit, s) and any(self._can_be_restored(skill) for skill in s.skills):
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode):
        for skill in unit.skill:
            if self._can_be_restored(skill):
                actions.append(action.RemoveSkill(unit, skill))
        playback.append(('restore_hit', unit, item, target))

class RestoreSpecific(Restore, ItemComponent):
    nid = 'restore_specific'
    desc = "Item removes status from target on hit"
    tag = 'extra'

    expose = Type.Skill # Nid

    def _can_be_restored(self, status):
        return status.nid == self.value

class Shove(ItemComponent):
    nid = 'shove'
    desc = "Item shoves target on hit"
    tag = 'extra'

    expose = Type.Int
    value = 1

    def _check_shove(self, unit_to_move, anchor_pos, magnitude):
        offset_x = utils.clamp(unit_to_move.position[0] - anchor_pos[0], -1, 1)
        offset_y = utils.clamp(unit_to_move.position[1] - anchor_pos[1], -1, 1)
        new_position = (unit_to_move.position[0] + offset_x * magnitude,
                        unit_to_move.position[1] + offset_y * magnitude)

        mcost = game.movement.get_mcost(unit_to_move, new_position)
        if game.tilemap.check_bounds(new_position) and \
                not game.board.get_unit(new_position) and \
                mcost <= equations.parser.movement(unit_to_move):
            return new_position
        return False

    def on_hit(self, actions, playback, unit, item, target, mode):
        if not skill_system.ignore_forced_movement(target):
            new_position = self._check_shove(target, unit.position, self.value)
            if new_position:
                actions.append(action.ForcedMovement(target, new_position))
                playback.append(('shove_hit', unit, item, target))

class ShoveOnEndCombat(Shove):
    nid = 'shove_on_end_combat'
    desc = "Item shoves target at the end of combat"
    tag = 'extra'

    expose = Type.Int
    value = 1

    def end_combat(self, playback, unit, item, target):
        if not skill_system.ignore_forced_movement(target):
            new_position = self._check_shove(target, unit.position, self.value)
            if new_position:
                action.do(action.ForcedMovement(target, new_position))

class ShoveTargetRestrict(Shove, ItemComponent):
    nid = 'shove_target_restrict'
    desc = "Target restriction for Shove"
    tag = 'extra'

    expose = Type.Int
    value = 1

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # only targets units that need to be restored
        if defender and self._check_shove(defender, unit.position, self.value) and \
                not skill_system.ignore_forced_movement(defender):
            return True
        for s in splash:
            if self._check_shove(s, unit.position, self.value) and \
                    not skill_system.ignore_forced_movement(s):
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode):
        pass

    def end_combat(self, playback, unit, item, target):
        pass

class Swap(ItemComponent):
    nid = 'swap'
    desc = "Item swaps user with target on hit"
    tag = 'extra'

    def on_hit(self, actions, playback, unit, item, target, mode):
        if not skill_system.ignore_forced_movement(unit) and not skill_system.ignore_forced_movement(target):
            actions.append(action.Swap(unit, target))
            playback.append(('swap_hit', unit, item, target))

"""
class Warp(ItemComponent):
    nid = 'warp'
    desc = 'Item warps target to position on hit'
    tag = 'extra'

    def on_hit(self, actions, playback, unit, item, target, mode):
        if not skill_system.ignore_forced_movement(unit):
            actions.append(action.Warp(target, (0, 0)))
            playback.append(('warp_hit', unit, item, target, (0, 0)))
"""

class EvalTargetRestrict(ItemComponent):
    nid = 'eval_target_restrict'
    desc = "Use this to restrict what units can be targeted"
    tag = 'extra'

    expose = Type.String
    value = 'True'

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Restricts target based on whether any unit has < full hp
        try:
            if defender and eval(self.value):
                return True
            for unit in splash:
                if eval(self.value):
                    return True
        except:
            return True
        return False

class Steal(ItemComponent):
    nid = 'steal'
    desc = "Item steals from target on hit"
    tag = 'weapon'

    def init(self, item):
        item.data['target_item'] = None
        self._did_steal = False

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Unit has item that can be stolen
        attack = equations.parser.steal_atk(unit)
        defense = equations.parser.steal_def(unit)
        if attack >= defense:
            for item in defender.items:
                if not item_system.locked(defender, item) and \
                        not item_funcs.inventory_full(unit, item) and \
                        not item is defender.get_weapon():
                    return True
        return False

    def targets_items(self, unit, item) -> bool:
        return True

    def item_restrict(self, unit, item, defender, def_item) -> bool:
        if item_system.locked(defender, def_item):
            return False
        if item_funcs.inventory_full(unit, def_item):
            return False
        if def_item is defender.get_weapon():
            return False
        return True

    def on_hit(self, actions, playback, unit, item, target, mode):
        target_item = item.data.get('target_item')
        if target_item:
            actions.append(action.RemoveItem(target, target_item))
            actions.append(action.DropItem(unit, target_item))
            self._did_steal = True

    def end_combat(self, playback, unit, item, target):
        if self._did_steal:
            target_item = item.data.get('target_item')
            game.alerts.append(banner.StoleItem(unit, target_item))
            game.state.change('alert')
        item.data['target_item'] = None
        self._did_steal = False

class GBASteal(Steal, ItemComponent):
    nid = 'gba_steal'
    desc = "Item steals from target on hit"
    tag = 'weapon'

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Unit has item that can be stolen
        attack = equations.parser.steal_atk(unit)
        defense = equations.parser.steal_def(unit)
        if attack >= defense:
            for item in defender.items:
                if not item_system.locked(defender, item) and \
                        not item_funcs.inventory_full(unit, item) and \
                        not item_system.is_weapon(defender, item) and \
                        not item_system.is_spell(defender, item):
                    return True
        return False

    def item_restrict(self, unit, item, defender, def_item) -> bool:
        if item_system.locked(defender, def_item):
            return False
        if item_funcs.inventory_full(unit, def_item):
            return False
        if item_system.is_weapon(defender, def_item) or item_system.is_spell(defender, def_item):
            return False
        return True

class Repair(ItemComponent):
    nid = 'repair'
    desc = "Item repairs target item on hit"
    tag = 'weapon'

    def init(self, item):
        item.data['target_item'] = None

    def target_restrict(self, unit, item, defender, splash) -> bool:
        # Unit has item that can be repaired
        for item in defender.items:
            if item.uses and item.data['uses'] < item.data['starting_uses'] and \
                    not item_system.unrepairable(defender, item):
                return True
        return False

    def targets_items(self, unit, item) -> bool:
        return True

    def item_restrict(self, unit, item, defender, def_item) -> bool:
        if def_item.uses and def_item.data['uses'] < def_item.data['starting_uses'] and \
                not item_system.unrepairable(defender, def_item):
            return True
        return False

    def on_hit(self, actions, playback, unit, item, target, mode):
        target_item = item.data.get('target_item')
        print(target_item)
        if target_item:
            actions.append(action.RepairItem(target_item))

    def end_combat(self, playback, unit, item, target):
        item.data['target_item'] = None

class Trade(ItemComponent):
    nid = 'trade'
    desc = "Item allows user to trade with target on hit"
    tag = 'weapon'

    def init(self, item):
        self._did_hit = False

    def on_hit(self, actions, playback, unit, item, target, mode):
        self._did_hit = True

    def end_combat(self, playback, unit, item, target):
        if self._did_hit and target:
            game.cursor.cur_unit = unit
            game.cursor.set_pos(target.position)
            game.state.change('combat_trade')
        self._did_hit = False
