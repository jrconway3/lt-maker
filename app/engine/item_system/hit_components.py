from app import utilities

from app.data.database import DB

from app.engine.item_system.item_component import ItemComponent, Type

from app.engine import action, status_system, combat_calcs
from app.engine.game_state import game 

class Heal(ItemComponent):
    nid = 'heal'
    desc = "Item heals on hit"
    expose = Type.Int

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
        heal = self.value + game.equations.heal(unit, item, dist)
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
    expose = Type.Int

    def damage(self, unit, item):
        return self.value

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

class PermanentStatChange(ItemComponent):
    nid = 'permanent_stat_change'
    desc = "Item changes target's stats on hit."
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
    expose = (Type.Dict, Type.Stat)

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.PermanentGrowthChange(unit, self.value))
        playback.append(('hit', unit, item, target))

class WexpChange(ItemComponent):
    nid = 'wexp_change'
    desc = "Item changes target's wexp on hit"
    expose = (Type.Dict, Type.WeaponType)

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.WexpChange(unit, self.value))
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
    expose = Type.Status  # Nid

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.AddStatus(target, self.value))
        playback.append(('status_hit', unit, item, target, self.value))

class Restore(ItemComponent):
    nid = 'restore'
    desc = "Item removes status with time from target on hit"
    expose = Type.Status # Nid

    def _can_be_restored(self, status):
        return (self.value.lower() == 'all' or status.nid == self.value)

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
