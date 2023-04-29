from app.engine.game_state import game
from app.engine.state import MapState
from app.engine.movement.rationalize_movement_component import RationalizeMovementComponent
from app.utilities import utils

class FreeRoamRationalizeState(MapState):
    name = 'free_roam_rationalize'

    def begin(self):
        # Check for any units that have a good position but aren't on the board
        for unit in game.get_all_units():
            if utils.round_pos(unit.position) == unit.position and not game.board.get_unit(unit.position):
                game.arrive(unit)

        self.movement_components = self._get_units_to_rationalize()
        for mc in self.movement_components:
            game.movement.add(mc)

    def _get_units_to_rationalize(self):
        movement_components = []
        for unit in game.get_all_units():
            if utils.round_pos(unit.position) != unit.position:
                new_movement_component = RationalizeMovementComponent(unit)
                movement_components.append(new_movement_component)

    def update(self):
        super().update()
        game.movement.update()
        if len(game.movement) <= 0:
            game.state.back()
            return 'repeat'
