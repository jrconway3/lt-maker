from app.utilities import utils

from app.data.item_components import ItemComponent

from app.engine import action
from app.engine import item_funcs
from app.engine.game_state import game

class UnlockStaff(ItemComponent):
    nid = 'unlock_staff'
    desc = "Item allows user to unlock locked regions. Doesn't work with other splash/aoe components"
    tag = 'advanced'

    def init(self, item):
        self._did_hit = False

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

    def on_hit(self, actions, playback, unit, item, target, mode):
        self._did_hit = True

    def end_combat(self, playback, unit, item, target):
        if self._did_hit or True:
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
