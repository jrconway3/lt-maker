from app.data.database import DB

from app.engine.sound import SOUNDTHREAD
from app.engine.state import MapState
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

class EventState(MapState):
    name = 'event'
    event = None

    def begin(self):
        logger.info("Begin Event State")
        if not self.event:
            self.event = game.events.get()
            if self.event:
                game.cursor.hide()

    def take_input(self, event):
        if event == 'START' or event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            self.event.skip()

        elif event == 'SELECT' or event == 'RIGHT' or event == 'DOWN':
            if self.event.state == 'dialog':
                SOUNDTHREAD.play_sfx('Select 1')
                self.event.hurry_up()

    def update(self):
        super().update()
        if self.event:
            self.event.update()
        else:
            logger.info("Event complete")
            game.state.back()
            return 'repeat'

        if self.event.state == 'complete':
            game.state.back()
            return self.end_event()

    def draw(self, surf):
        surf = super().draw(surf)
        if self.event:
            self.event.draw(surf)

        return surf

    def end_event(self):
        logger.debug("Ending Event")
        if game.level_vars.get('_win_game'):
            logger.info("Player Wins!")
            current_level_index = DB.levels.index(game.level.nid)
            game.clean_up()
            if current_level_index < len(DB.levels) - 1:
                # Assumes no overworld
                next_level = DB.levels[current_level_index + 1]
                game.game_vars['_next_level_nid'] = next_level.nid
                game.state.clear()
                logger.info('Creating save...')
                game.memory['save_kind'] = 'start'
                game.state.change('title_save')
            else:
                logger.info('No more levels!')
                game.state.clear()
                game.state.change('title_start')
        elif game.level_vars.get('_lose_game'):
            game.state.clear()
            game.state.change('title_start')
            game.state.change('game_over')

        return 'repeat'
