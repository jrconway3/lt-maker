from app.engine.state import MapState
from app.engine.game_state import game
from app.engine import action

import logging
logger = logging.getLogger(__name__)

class TurnChangeState(MapState):
    name = 'turn_change'

    def begin(self):
        if game.phase.get_current() == 'player':
            # TODO Handle support increments
            game.memory['previous_cursor_position'] = game.cursor.position
        # Clear all previous states in state machine except me
        game.state.refresh()
        game.state.back()  # Turn Change should only last 1 frame

    def end(self):
        game.phase.next()  # Go to next phase
        # If entering player phase
        if game.phase.get_current() == 'player':
            action.do(action.IncrementTurn())
            game.state.change('free')
            # TODO
            # game.state.change('status_upkeep') 
            # game.state.change('phase_change')
            # EVENTS TRIGGER HERE
        else:
            game.state.change('ai')
            # game.state.change('status_upkeep')
            # game.state.change('phase_change')
            # game.state.change('end_step')

    def take_input(self, event):
        return 'repeat'

class FreeState(MapState):
    name = 'free'

    def begin(self):
        game.cursor.show()
        # game.boundary.show()
        # The turnwheel will not be able to go before this moment
        if game.turncount == 1:
            game.action_log.set_first_free_action()

    def take_input(self, event):
        if event == 'INFO':
            if game.cursor.get_hover():
                # info_menu.start()
                pass
            else:
                # game.boundary.toggle_all_enemy_attacks()
                pass
        elif event == 'AUX':
            pass
        elif event == 'SELECT':
            pass
        elif event == 'BACK':
            pass
        elif event == 'START':
            pass
