from app.engine.item_system.item_component import ItemComponent, Type

from app.engine import targets
from app.engine.item_system import item_system
from app.engine.game_state import game 

class BlastAOE(ItemComponent):
    nid = 'aoe_blast'
    desc = "Gives Blast AOE"
    expose = Type.Int  # Radius

    def splash(self, unit, item, position) -> tuple:
        ranges = set(range(self.value + 1))
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
