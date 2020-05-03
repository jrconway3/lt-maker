import os

from app.data.constants import WINWIDTH, WINHEIGHT
from app.data.resources import RESOURCES
from app.data.database import DB

from app.engine import engine
from app.engine.sprites import SPRITES
from app.engine.state import State
from app.engine.background import PanoramaBackground
from app.engine import save, image_mods, banner, menus
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

class TitleStartState(State):
    name = "title_start"
    in_level = False
    show_map = False

    def start(self):
        self.logo = SPRITES.get('logo')
        imgs = RESOURCES.panoramas.get('title_background')
        self.bg = PanoramaBackground(imgs) if imgs else None
        game.memory['transition_speed'] = 0.01

        # Wait until saving thread has finished
        if save.SAVING_THREAD:
            save.SAVING_THREAD.join()

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        if event:
            game.state.change('title_main')
            game.state.change('transition_out')

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        engine.blit_center(surf, self.logo)
        return surf

class TitleMainState(State):
    name = 'title_main'
    in_level = False
    show_map = False

    def start(self):
        options = ['New Game', 'Extras']
        if any(ss.kind for ss in save.SAVE_SLOTS):
            options.insert(0, 'Restart Level')
            options.insert(0, 'Load Game')
        if os.path.exists(save.SUSPEND_LOC):
            options.insert(0, 'Continue')

        self.state = 'transition_in'
        self.position_x = -WINWIDTH//2

        # For fading out to load suspend
        self.background = SPRITES.get('black_background')
        self.transition = 100

        self.selection = None
        self.menu = menus.Main(options, "menu_dark")
        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        if self.state == 'normal':
            if event == 'DOWN':
                self.menu.move_down()
            elif event == 'UP':
                self.menu.move_up()

            elif event == 'BACK':
                game.state.change('title_start')
                game.state.change('transition_out')

            elif event == 'SELECT':
                self.selection = self.menu.get_current()
                if self.selection == 'Continue':
                    self.state = 'wait'
                elif os.path.exists(save.SUSPEND_LOC) and \
                        self.selection in ('Load Game', 'Restart Level', 'New Game'):
                    if self.selection == 'New Game':
                        text = 'Starting a new game will remove suspend!'
                    else:
                        text = 'Loading a game will remove suspend!'
                    game.alerts.append(banner.Custom(text))
                    game.state.change('alert_display')
                elif self.selection == 'New Game':
                    # game.state.change('title_mode')
                    game.state.change('title_new')
                    game.state.change('transition_out')
                else:
                    self.state = 'transition_out'

    def update(self):
        self.menu.update()

        if self.state == 'transition_in':
            self.position_x += 20
            if self.position_x >= WINWIDTH//2:
                self.position_x = WINWIDTH//2
                self.state = 'normal'

        elif self.state == 'transition_out':
            self.position_x -= 20
            if self.position_x <= -WINWIDTH//2:
                self.position_x = -WINWIDTH//2
                if self.selection == 'Load Game':
                    game.state.change('title_load')
                elif self.selection == 'Restart Level':
                    game.state.change('title_restart')
                elif self.selection == 'Extras':
                    game.state.change('title_extras')
                elif self.selection == 'New Game':
                    # game.state.change('title_mode')
                    game.state.change('title_new')
                    game.state.change('transition_out')
                self.state = 'transition_in'
                return 'repeat'

        elif self.state == 'wait':
            self.transition -= 5
            if self.transition <= 0:
                self.continue_suspend()
                return 'repeat'

    def continue_suspend(self):
        self.menu = None
        suspend = save.SaveSlot(save.SUSPEND_LOC, None)
        logger.info("Loading suspend...")
        save.load_game(game, suspend)

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.menu:
            self.menu.draw(surf, center=(self.position_x, WINHEIGHT//2), show_cursor=(self.state == 'normal'))

        bb = image_mods.make_translucent(self.background, self.transition/100.)
        surf.blit(bb, (0, 0))

        return surf

class TitleLoadState(State):
    name = 'title_load'
    in_level = False
    show_map = False

    def start(self):
        self.state = 'transition_in'
        self.position_x = int(WINWIDTH * 1.5)

        options, colors = save.get_save_title(save.SAVE_SLOTS)
        self.menu = menus.ChapterSelect(options, colors)
        most_recent = save.SAVE_SLOTS.index(max(save.SAVE_SLOTS, key=lambda x: x.realtime))
        self.menu.move_to(most_recent)

    def take_input(self, event):
        if event == 'DOWN':
            self.menu.move_down()
        elif event == 'UP':
            self.menu.move_up()

        elif event == 'BACK':
            self.state = 'transition_out'

        elif event == 'SELECT':
            selection = self.menu.current_index
            save_slot = save.SAVE_SLOTS[selection]
            if save_slot.kind:
                logger.info("Loading game...")
                save.load_game(game, save_slot)
                if save_slot.kind == 'Start':  # Restart
                    # Restart level
                    game.start_level(game.level.nid)
                game.memory['transition_from'] = 'Load Game'
                game.state.change('title_wait')
                game.state.process_temp_state()
                save.remove_suspend()
            else:
                # TODO Error sound
                pass

    def update(self):
        if self.menu:
            self.menu.update()

        if self.state == 'transition_in':
            self.position_x -= 20
            if self.position_x <= WINWIDTH//2:
                self.position_x = WINWIDTH//2
                self.state = 'normal'

        elif self.state == 'transition_out':
            self.position_x += 20
            if self.position_x >= int(WINWIDTH * 1.5):
                self.position_x = int(WINWIDTH * 1.5)
                game.state.back()
                self.state = 'transition_in'
                return 'repeat'

    def draw(self, surf):
        if self.menu:
            self.menu.draw(surf, center=(self.position_x, WINHEIGHT//2))
        return surf

class TitleRestartState(TitleLoadState):
    name = 'title_restart'

    def take_input(self, event):
        if event == 'DOWN':
            self.menu.move_down()
        elif event == 'UP':
            self.menu.move_up()

        elif event == 'BACK':
            self.state = 'transition_out'

        elif event == 'SELECT':
            selection = self.menu.current_index
            save_slot = save.RESTART_SLOTS[selection]
            if save_slot.kind:
                logger.info("Loading game...")
                save.load_game(game, save_slot)
                # Restart level
                game.start_level(game.level.nid)
                game.memory['transition_from'] = 'Restart Level'
                game.memory['title_menu'] = self.menu
                game.state.change('title_wait')
                game.state.process_temp_state()
                save.remove_suspend()
            else:
                # TODO Error sound
                pass

class TitleNewState(TitleLoadState):
    name = 'title_new'

    def take_input(self, event):
        if event == 'DOWN':
            self.menu.move_down()
        elif event == 'UP':
            self.menu.move_up()

        elif event == 'BACK':
            self.state = 'transition_out'

        elif event == 'SELECT':
            selection = self.menu.current_index
            save_slot = save.SAVE_SLOTS[selection]
            if save_slot.kind:
                game.state.change('title_new_child')
            else:
                # TODO Save Sound
                build_new_game()

class TitleNewChildState(State):
    name = 'title_new_child'
    transparent = True
    in_level = False
    show_map = False

    def start(self):
        selection = game.memory['option_owner']
        options = ['Overwrite', 'Back']
        self.menu = menus.Choice(selection, options, (8, WINHEIGHT - 24))
        self.menu.set_horizontal(True)

    def take_input(self, event):
        self.menu.handle_mouse()
        if event == 'RIGHT':
            self.menu.move_down()
        elif event == 'LEFT':
            self.menu.move_up()

        elif event == 'BACK':
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            if selection == 'Overwrite':
                build_new_game()
            elif selection == 'Back':
                game.state.back()

    def update(self):
        self.menu.update()

    def draw(self, surf):
        surf = self.menu.draw(surf)
        return surf

class TitleExtrasState(TitleLoadState):
    name = 'title_extras'
    in_level = False
    show_map = False

    def start(self):
        self.state = 'transition_in'
        options = ['Options', 'Credits']
        self.menu = menus.Main(options, 'menu_dark')

    def take_input(self, event):
        if event == 'DOWN':
            self.menu.move_down()
        elif event == 'UP':
            self.menu.move_up()

        elif event == 'BACK':
            self.state = 'transition_out'

        elif event == 'SELECT':
            selection = self.menu.get_current()
            if selection == 'Credits':
                game.state.change('credits')
                game.state.change('transition_out')
            elif selection == 'Options':
                game.state.change('config_menu')
                game.state.change('transition_out')

class TitleWaitState(State):
    name = 'title_wait'
    in_level = False
    show_map = False
    # NOT TRANSPARENT!!!

    def start(self):
        self.wait_flag = False
        self.wait_time = engine.get_time()
        self.menu = game.memory.get('title_menu')

    def update(self):
        if self.menu:
            self.menu.update()
        if not self.wait_flag and engine.get_time() - self.wait_time > 750:
            self.wait_flag = True
            game.state.change('transition_pop')

    def draw(self, surf):
        if self.menu:
            if 100 < engine.get_time() - self.wait_time > 200:
                self.menu.draw(surf, flicker=True)
            else:
                self.menu.draw(surf)
        return surf

class TitleSaveState(State):
    name = 'title_save'
    in_level = False
    show_map = False

    def start(self):
        self.leave_flag = False
        self.wait_time = 0

        save.check_save_slots()
        options, colors = save.get_save_title(save.SAVE_SLOTS)
        self.menu = menus.ChapterSelect(options, colors)
        most_recent = save.SAVE_SLOTS.index(max(save.SAVE_SLOTS, key=lambda x: x.realtime))
        self.menu.move_to(most_recent)

    def take_input(self, event):
        if self.wait_time > 0:
            return

        if event == 'DOWN':
            self.menu.move_down()
        elif event == 'UP':
            self.menu.move_up()

        elif event == 'BACK':
            # Proceed to next level anyway
            game.state.change('transition_pop')

        elif event == 'SELECT':
            # Rename selection
            self.wait_time = engine.get_time()
            if DB.constants.get('overworld').value:
                name = 'overworld'
                self.menu.set_name(self.menu.current_index, name)
            else:
                next_level_nid = game.memory['next_level_nid']
                name = DB.levels.get(next_level_nid).title
                self.menu.set_name(self.menu.current_index, name)
            self.menu.set_color(self.menu.current_index, 'green')
            
    def update(self):
        if self.menu:
            self.menu.update()

        if self.wait_time and engine.get_time() - self.wait_time > 1250 and not self.leave_flag:
            self.leave_flag = True

            current_state = game.state.state
            save.suspend_game(game, game.memory['save_kind'], slot=self.menu.current_index)
            game.state.state = current_state
            game.state.change('transition_pop')

    def draw(self, surf):
        if self.menu:
            if 100 < engine.get_time() - self.wait_time > 200:
                self.menu.draw(surf, flicker=True)
            else:
                self.menu.draw(surf)
        return surf
