from app.utilities import utils

from app.data.database import DB

from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import action, skill_system, combat_calcs, equations
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

class MagicHeal(Heal):
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
        actions.append(action.AddSkill(target, self.value))
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

class RestoreSpecific(Restore):
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

        mcost = self.get_mcost(unit_to_move, new_position)
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

class Swap(ItemComponent):
    nid = 'swap'
    desc = "Item swaps user with target on hit"
    tag = 'extra'

    def on_hit(self, actions, playback, unit, item, target, mode):
        if not skill_system.ignore_forced_movement(unit) and not skill_system.ignore_forced_movement(target):
            actions.append(action.Swap(unit, target))
            playback.append(('swap_hit', unit, item, target))

class Warp(ItemComponent):
    nid = 'warp'
    desc = 'Item warps target to position on hit'
    tag = 'extra'

    def on_hit(self, actions, playback, unit, item, target, mode):
        if not skill_system.ignore_forced_movement(unit):
            actions.append(action.Warp(target, (0, 0)))
            playback.append(('warp_hit', unit, item, target, (0, 0)))
