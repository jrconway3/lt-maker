from app.utilities import utils

from app.data.database import DB

from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import action
from app.engine import item_funcs, skill_system
from app.engine.game_state import game

class UnlockStaff(ItemComponent):
    nid = 'unlock_staff'
    desc = "Item allows user to unlock locked regions. Doesn't work with other splash/aoe components"
    tag = 'special'

    _did_hit = False

    def _valid_region(self, region) -> bool:
        return region.region_type == 'event' and 'can_unlock' in region.condition

    def ai_targets(self, unit, item) -> set:
        targets = set()
        for region in game.level.regions:
            if self._valid_region(region):
                for position in region.get_all_positions():
                    targets.add(position)
        return targets

    def valid_targets(self, unit, item) -> set:
        targets = self.ai_targets(unit, item)
        return {t for t in targets if utils.calculate_distance(unit.position, t) in item_funcs.get_range(unit, item)}

    def splash(self, unit, item, position):
        return position, []

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        for pos in [def_pos] + splash:
            for region in game.level.regions:
                if self._valid_region(region) and region.contains(def_pos):
                    return True
        return False

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode):
        self._did_hit = True

    def end_combat(self, playback, unit, item, target):
        if self._did_hit:
            pos = game.cursor.position
            region = None
            for reg in game.level.regions:
                if self._valid_region(reg) and reg.contains(pos):
                    region = reg
                    break
            if region:
                did_trigger = game.events.trigger(region.sub_nid, unit, position=pos, region=region)
                if did_trigger and region.only_once:
                    action.do(action.RemoveRegion(region))
        self._did_hit = False

class StoreUnit(ItemComponent):
    nid = 'store_unit'
    desc = "Item registers a unit on the map on hit"
    tag = 'special'

    def init(self, item):
        self.item.data['stored_unit'] = None

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode):
        if not skill_system.ignore_forced_movement(target):
            self.item.data['stored_unit'] = target.nid
            # actions.append(action.WarpOut(target))
            playback.append(('rescue_hit', unit, item, target))

class EmptyTileTargetRestrict(ItemComponent):
    nid = 'empty_tile_target_restrict'
    desc = "Item will only target tiles without units on them"
    tag = 'target'

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        if not game.board.get_unit(def_pos):
            return True
        return False

class UnloadUnit(ItemComponent):
    nid = 'unload_unit'
    desc = "Item takes stored unit and warps them to the new location on the map"
    tag = 'special'

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        if not game.board.get_unit(def_pos) and game.movement.check_simple_traversable(def_pos):
            return True
        return False
    
    def on_hit(self, actions, playback, unit, item, target, target_pos, mode):
        if self.item.data.get('stored_unit'):
            rescuee = game.get_unit(self.item.data['stored_unit'])
            if rescuee:
                actions.append(action.Warp(rescuee, target_pos))

class EventOnHit(ItemComponent):
    nid = 'event_on_hit'
    desc = "Calls event on hit"
    tag = 'special'

    expose = Type.Event

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode):
        event_prefab = DB.events.get_from_nid(self.value)
        if event_prefab:
            game.events.add_event(event_prefab.nid, event_prefab.commands, unit, target, item, target_pos)
