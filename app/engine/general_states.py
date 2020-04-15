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
            game.state.change('phase_change')
            # EVENTS TRIGGER HERE
        else:
            game.state.change('ai')
            # game.state.change('status_upkeep')
            game.state.change('phase_change')
            # game.state.change('end_step')

    def take_input(self, event):
        return 'repeat'

class PhaseChangeState(MapState):
    name = 'phase_change'

    def begin(self):
        self.save_state()
        logger.info("Phase Change Start")
        # These are done here instead of in turnchange because
        # introScript and other event scripts will have to go on the stack
        # in between this and turn change
        # And they technically happen before I want the player to have the turnwheel locked
        # units reset, etc.
        action.do(action.LockTurnwheel(game.phase.get_current() != 'player'))
        action.do(action.ResetAll([unit for unit in game.level.units if not unit.dead]))
        game.cursor.hide()
        game.phase.slide_in()

    def update(self):
        super().update()
        done = game.phase.update()
        if done:
            game.state.back()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = game.phase.draw(surf)
        return surf

    def end(self):
        logger.info("Phase Change End")

    def save_state(self):
        if game.phase.get_current() == 'player':
            logger.info("Saving as we enter player phase!")
            name = game.level.nid + '_' + str(game.turncount)
            # TODO SUSPEND
        elif game.phase.get_current() == 'enemy':
            logger.info("Saving as we enter enemy phase!")
            name = game.level.nid + '_' + str(game.turncount) + 'b'
            # TODO SUSPEND

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
        game.cursor.take_input()
