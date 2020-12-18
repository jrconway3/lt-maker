from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import target_system
from app.engine.game_state import game 

class BlastAOE(ItemComponent):
    nid = 'aoe_blast'
    desc = "Gives Blast AOE"
    tag = 'aoe'

    expose = Type.Int  # Radius
    value = 1

    def splash(self, unit, item, position) -> tuple:
        ranges = set(range(self.value + 1))
        splash = target_system.find_manhattan_spheres(ranges, position[0], position[1])
        from app.engine import item_system
        if item_system.is_spell(unit, item):
            # spell blast
            splash = [game.board.get_unit(s) for s in splash]
            splash = [s for s in splash if s]
            return None, splash
        else:
            # regular blast
            splash = [game.board.get_unit(s) for s in splash if s != position]
            splash = [s for s in splash if s]
            return game.board.get_unit(position), splash

    def splash_positions(self, unit, item, position) -> set:
        ranges = set(range(self.value + 1))
        splash = target_system.find_manhattan_spheres(ranges, position[0], position[1])
        return splash
