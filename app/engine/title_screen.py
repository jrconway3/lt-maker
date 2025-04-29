import os

from app import autoupdate

from app.constants import TILEX, TILEY, WINHEIGHT, WINWIDTH
from app.data.database.database import DB
from app.data.database.difficulty_modes import GrowthOption, PermadeathOption

from app.engine import banner, base_surf
from app.engine import config as cf
from app.engine import (dialog, engine, gui, image_mods, menus, particles,
                        save, text_funcs)
from app.engine.background import PanoramaBackground
from app.engine.fluid_scroll import FluidScroll
from app.engine.fonts import FONT
from app.engine.game_state import game
from app.engine.objects.difficulty_mode import DifficultyModeObject
from app.engine.sound import get_sound_thread
from app.engine.sprites import SPRITES
from app.engine.state import State
from app.events.event import Event
from app.events import triggers

from app.engine.achievements import ACHIEVEMENTS
from app.engine.persistent_records import RECORDS

from app.data.resources.resources import RESOURCES
from app.utilities import utils

from app.constants import COLORKEY
from app.engine import icons
from app.engine.game_menus.menu_options import BasicOption, EmptyOption
from app.engine.graphics.text.text_renderer import render_text, text_width
from app.engine.info_menu.info_menu_portrait import InfoMenuPortrait
from app.engine.unit_sprite import MapSprite
from app.utilities.enums import HAlignment

import logging

class TitleStartState(State):
    name = "title_start"
    in_level = False
    show_map = False

    def start(self):
        logo = SPRITES.get('logo')
        imgs = RESOURCES.panoramas.get('title_background')
        self.bg = PanoramaBackground(imgs) if imgs else None
        game.memory['title_bg'] = self.bg
        press_start_sprite = SPRITES.get('press_start')
        if press_start_sprite:
            self.press_start = gui.Logo(press_start_sprite, (WINWIDTH//2, 4*WINHEIGHT//5))
        else:
            self.press_start = None

        if logo:
            num_frames = 1
            speed = 64
            height = utils.clamp(WINHEIGHT//2 - 40, logo.get_height()//2, WINHEIGHT//2)
            self.logo = gui.Logo(logo, (WINWIDTH//2, height), num_frames, speed)
        else:
            self.logo = None

        self.particles = None
        if DB.constants.value('title_particles'):
            bounds = (-WINHEIGHT, WINWIDTH, WINHEIGHT, WINHEIGHT + 16)
            self.particles = particles.MapParticleSystem('title', particles.Smoke, .075, bounds, (TILEX, TILEY))
            self.particles.prefill()
        game.memory['title_particles'] = self.particles
        game.memory['transition_speed'] = 0.5

        # Wait until saving thread has finished
        if save.SAVE_THREAD:
            save.SAVE_THREAD.join()

        game.state.refresh()

        # Title Screen Intro Cinematic
        if game.memory.get('title_intro_already_played'):
            game.state.change('transition_in')
        else:
            game.sweep()
            game.events.trigger(triggers.OnTitleScreen())
            # On startup occurs before on title_screen
            game.events.trigger(triggers.OnStartup())
            game.memory['title_intro_already_played'] = True

        get_sound_thread().clear()
        if RECORDS.get('_music_title_screen'):
            get_sound_thread().fade_in(RECORDS.get('_music_title_screen'), fade_in=50)
        elif DB.constants.value('music_main'):
            get_sound_thread().fade_in(DB.constants.value('music_main'), fade_in=50)

        return 'repeat'

    def begin(self):
        if game.state.from_transition():
            game.state.change('transition_in')
            return 'repeat'

    def take_input(self, event):
        if event:
            get_sound_thread().play_sfx('Start')
            game.memory['next_state'] = 'title_main'
            game.memory['transition_speed'] = 4
            game.state.change('transition_to')

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.particles:
            self.particles.update()
            self.particles.draw(surf)
        if self.logo:
            self.logo.update()
            self.logo.draw(surf)
        if self.press_start:
            self.press_start.update()
            self.press_start.draw(surf)
        FONT['text'].blit(text_funcs.translate('_attribution'), surf, (4, WINHEIGHT - 16))
        return surf

class TitleMainState(State):
    name = 'title_main'
    in_level = False
    show_map = False

    menu = None
    bg = None

    def start(self):
        save.check_save_slots()
        options = ['New Game', 'Extras']
        if any(ss.kind for ss in save.SAVE_SLOTS):
            options.insert(0, 'Restart Level')
            options.insert(0, 'Load Game')
        if os.path.exists(save.SUSPEND_LOC):
            options.insert(0, 'Continue')
        # Only check for updates in frozen version
        # if hasattr(sys, 'frozen') and autoupdate.check_for_update():
        #    options.append('Update')

        self.fluid = FluidScroll(128)
        self.bg = game.memory['title_bg']
        self.particles = game.memory['title_particles']

        self.state = 'transition_in'
        self.position_x = -WINWIDTH//2

        # For fading out to load suspend
        self.background = SPRITES.get('bg_black')
        self.transition = 100

        self.banner_flag = False

        self.selection = None
        self.menu = menus.Main(options, "title_menu_dark")
        game.state.change('transition_in')
        return 'repeat'

    def begin(self):
        self.fluid.reset_on_change_state()

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if self.state == 'alert':
            self.state = 'transition_out'
        if self.state == 'normal':
            self.menu.handle_mouse()
            if 'DOWN' in directions:
                if self.menu.move_down(first_push):
                    get_sound_thread().play_sfx('Select 6')
            elif 'UP' in directions:
                if self.menu.move_up(first_push):
                    get_sound_thread().play_sfx('Select 6')

            if event == 'BACK':
                get_sound_thread().play_sfx('Select 4')
                # game.memory['next_state'] = 'title_start'
                # game.state.change('transition_to')
                game.memory['transition_speed'] = 4
                game.state.change('transition_pop')

            elif event == 'SELECT':
                get_sound_thread().play_sfx('Select 1')
                self.selection = self.menu.get_current()
                if self.selection == 'Continue':
                    self.state = 'wait'
                elif os.path.exists(save.SUSPEND_LOC) and not self.banner_flag and \
                        self.selection in ('Load Game', 'Restart Level', 'New Game'):
                    if self.selection == 'New Game':
                        text = 'Starting a new game will remove suspend!'
                    elif self.selection == 'Load Game':
                        text = 'Loading a game will remove suspend!'
                    else:
                        text = 'Restarting a game will remove suspend!'
                    game.alerts.append(banner.Custom(text))
                    game.state.change('alert')
                    self.state = 'alert'
                    self.banner_flag = True
                elif self.selection == 'Update':
                    updating = autoupdate.update()
                    if updating:
                        engine.terminate()
                    else:
                        print("Failed to update?")
                else:
                    self.state = 'transition_out'

    def update(self):
        if self.menu:
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
                    available_difficulties = [difficulty for difficulty in DB.difficulty_modes if (not difficulty.start_locked or RECORDS.check_difficulty_unlocked(difficulty.nid))]
                    if not available_difficulties:
                        logging.error("All difficulties are locked. Using default Difficulty Level.")
                        available_difficulties = [DB.difficulty_modes[0]]
                    # Check if more than one mode or the only mode requires a choice
                    if len(available_difficulties) > 1 or \
                        (available_difficulties and
                         (available_difficulties[0].permadeath_choice == PermadeathOption.PLAYER_CHOICE or
                          available_difficulties[0].growths_choice == GrowthOption.PLAYER_CHOICE)):
                        game.memory['next_state'] = 'title_mode'
                        game.memory['transition_speed'] = 4
                        game.state.change('transition_to')
                    else:  # Wow, no need for choice
                        mode = available_difficulties[0]
                        game.current_mode = DifficultyModeObject.from_prefab(mode)
                        game.state.change('title_new')
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
        logging.info("Loading suspend...")
        save.load_game(game, suspend)
        save.remove_suspend()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.particles:
            self.particles.update()
            self.particles.draw(surf)
        if self.menu:
            self.menu.draw(surf, center=(self.position_x, WINHEIGHT//2), show_cursor=(self.state == 'normal'))

        bb = image_mods.make_translucent(self.background, self.transition/100.)
        surf.blit(bb, (0, 0))

        return surf

class TitleModeState(State):
    name = 'title_mode'
    in_level = False
    show_map = False

    menu = None
    bg = None
    dialog = None
    label = None

    def difficulty_choice(self):
        return len(self.available_difficulties) > 1

    def start(self):
        self.fluid = FluidScroll(128)
        self.bg = game.memory['title_bg']
        self.particles = game.memory['title_particles']

        self.state = 'difficulty_setup'
        self.permadeath_choice: bool = True
        self.growths_choice: bool = True

        self.label = base_surf.create_base_surf(96, 88)
        shimmer = SPRITES.get('menu_shimmer2')
        self.label.blit(shimmer, (95 - shimmer.get_width(), 83 - shimmer.get_height()))
        self.label = image_mods.make_translucent(self.label, .1)

        self.available_difficulties = [difficulty for difficulty in DB.difficulty_modes if (not difficulty.start_locked or RECORDS.check_difficulty_unlocked(difficulty.nid))]

    def begin(self):
        if self.state == 'difficulty_setup':
            if self.difficulty_choice():
                options = [mode.name for mode in self.available_difficulties]
                self.menu = menus.ModeSelect(options)
                self.state = 'difficulty_wait'
                game.state.change('transition_in')
            else:
                if len(self.available_difficulties) == 0:
                    mode = DB.difficulty_modes[0]
                else:
                    mode = self.available_difficulties[0]
                game.current_mode = DifficultyModeObject.from_prefab(mode)
                self.permadeath_choice = mode.permadeath_choice == PermadeathOption.PLAYER_CHOICE
                self.growths_choice = mode.growths_choice == GrowthOption.PLAYER_CHOICE
                self.state = 'death_setup'
                return self.begin()  # Call again to continue setting it up

        elif self.state == 'death_setup':
            if self.permadeath_choice:
                options = [perma.value for perma in PermadeathOption if perma != PermadeathOption.PLAYER_CHOICE]
                self.menu = menus.ModeSelect(options)
                self.menu.current_index = 1
                self.state = 'death_wait'
                game.state.change('transition_in')
            else:
                self.state = 'growth_setup'
                return self.begin()

        elif self.state == 'growth_setup':
            if self.growths_choice:
                options = [growth.value for growth in GrowthOption if growth != GrowthOption.PLAYER_CHOICE]
                self.menu = menus.ModeSelect(options)
                self.state = 'growth_wait'
                game.state.change('transition_in')
            else:
                game.memory['next_state'] = 'title_new'
                game.state.change('transition_to')

        self.update_dialog()
        self.fluid.reset_on_change_state()

        return 'repeat'

    def update_dialog(self):
        if self.menu:
            option = self.menu.get_current()
            text = option + '_desc'
            text = text_funcs.translate_and_text_evaluate(text, self=option)
            self.dialog = dialog.Dialog(text, num_lines=4, draw_cursor=False)
            self.dialog.position = (140, 34)
            self.dialog.text_width = WINWIDTH - 142 - 12
            self.dialog.font = FONT['text']
            self.dialog.font_type = 'text'
            self.dialog.font_color = 'white'
            self.dialog.reformat()

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        old_current_index = self.menu.get_current_index()
        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')

        if self.menu.get_current_index() != old_current_index:
            self.update_dialog()

        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            if self.state == 'difficulty_wait':
                game.state.change('transition_pop')
            elif self.state == 'death_wait':
                if self.difficulty_choice():
                    self.state = 'difficulty_setup'
                    game.state.change('transition_out')
                else:
                    game.state.change('transition_pop')
            elif self.state == 'growth_wait':
                if self.permadeath_choice:
                    self.state = 'death_setup'
                    game.state.change('transition_out')
                elif self.difficulty_choice():
                    self.state = 'difficulty_setup'
                    game.state.change('transition_out')
                else:
                    game.state.change('transition_pop')
            else:
                game.state.change('transition_pop')
            return 'repeat'

        elif event == 'SELECT':
            get_sound_thread().play_sfx('Select 1')
            if self.state == 'growth_wait':
                game.current_mode.growths = self.menu.get_current()
                game.memory['next_state'] = 'title_new'
                game.state.change('transition_to')
            elif self.state == 'death_wait':
                game.current_mode.permadeath = self.menu.get_current() == PermadeathOption.CLASSIC
                if self.growths_choice:
                    self.state = 'growth_setup'
                    game.state.change('transition_out')
                else:
                    game.memory['next_state'] = 'title_new'
                    game.state.change('transition_to')
            elif self.state == 'difficulty_wait':
                mode = self.available_difficulties[self.menu.get_current_index()]
                game.current_mode = DifficultyModeObject.from_prefab(mode)
                self.permadeath_choice = mode.permadeath_choice == PermadeathOption.PLAYER_CHOICE
                self.growths_choice = mode.growths_choice == GrowthOption.PLAYER_CHOICE
                if self.permadeath_choice:
                    self.state = 'death_setup'
                    game.state.change('transition_out')
                elif self.growths_choice:
                    self.state = 'growth_setup'
                    game.state.change('transition_out')
                else:
                    game.memory['next_state'] = 'title_new'
                    game.memory['transition_speed'] = 4
                    game.state.change('transition_to')
            return 'repeat'

    def update(self):
        if self.menu:
            self.menu.update()
        if self.dialog:
            self.dialog.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.particles:
            self.particles.update()
            self.particles.draw(surf)
        if self.label:
            surf.blit(self.label, (142, 36))
        if self.dialog:
            self.dialog.draw(surf)
        if self.menu:
            self.menu.draw(surf)
        return surf

class TitleLoadState(State):
    name = 'title_load'
    in_level = False
    show_map = False

    menu = None
    bg = None

    def get_slots(self):
        return save.SAVE_SLOTS

    def start(self):
        self.fluid = FluidScroll(128)
        self.state = 'transition_in'
        self.position_x = int(WINWIDTH * 1.5)

        self.bg = game.memory['title_bg']
        self.particles = game.memory['title_particles']

        save.check_save_slots()
        self.save_slots = self.get_slots()
        options, colors = save.get_save_title(self.save_slots)
        self.menu = menus.ChapterSelect(options, colors)
        most_recent = self.save_slots.index(max(self.save_slots, key=lambda x: x.realtime))
        self.menu.move_to(most_recent)

    def begin(self):
        self.fluid.reset_on_change_state()

    def take_input(self, event):
        # Only take input in normal state
        if self.state != 'normal':
            return

        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')

        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            self.state = 'transition_out'

        elif event == 'SELECT':
            selection = self.menu.current_index
            save_slot = self.save_slots[selection]
            if save_slot.kind:
                get_sound_thread().play_sfx('Save')
                logging.info("Loading save of kind %s...", save_slot.kind)
                game.state.clear()
                game.state.process_temp_state()
                game.build_new()
                save.load_game(game, save_slot)
                if save_slot.kind == 'start':  # Restart
                    # Restart level
                    next_level_nid = game.game_vars['_next_level_nid']
                    game.load_states(['start_level_asset_loading'])
                    game.start_level(next_level_nid)
                elif save_slot.kind == 'overworld': # load overworld
                    game.load_states(['overworld'])
                game.memory['transition_from'] = 'Load Game'
                game.memory['title_menu'] = self.menu
                game.state.change('title_wait')
                game.state.process_temp_state()
                save.remove_suspend()
            else:
                get_sound_thread().play_sfx('Error')

    def back(self):
        game.state.back()

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
                self.back()
                self.state = 'transition_in'
                return 'repeat'

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.particles:
            self.particles.update()
            self.particles.draw(surf)
        if self.menu:
            self.menu.draw(surf, center=(self.position_x, WINHEIGHT//2))
        return surf

class TitleRestartState(TitleLoadState):
    name = 'title_restart'

    def get_slots(self):
        return save.RESTART_SLOTS

    def take_input(self, event):
        # Only take input in normal state
        if self.state != 'normal':
            return

        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')

        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            self.state = 'transition_out'

        elif event == 'SELECT':
            selection = self.menu.current_index
            save_slot = save.RESTART_SLOTS[selection]
            save_slot_main = save.SAVE_SLOTS[selection]
            if save_slot.kind:
                get_sound_thread().play_sfx('Save')
                logging.info("Loading game...")
                game.build_new()
                # Restart level
                if save_slot_main.kind == 'overworld':
                    save.load_game(game, save_slot_main)
                    game.load_states(['overworld'])
                else:
                    save.load_game(game, save_slot)
                    next_level_nid = game.game_vars['_next_level_nid']
                    game.start_level(next_level_nid)
                game.memory['transition_from'] = 'Restart Level'
                game.memory['title_menu'] = self.menu
                game.state.change('title_wait')
                game.state.process_temp_state()
                save.remove_suspend()
            else:
                get_sound_thread().play_sfx('Error')

def build_new_game(slot: int):
    # Make sure to keep the current mode
    assert isinstance(slot, int)
    old_mode = game.current_mode
    game.build_new()
    game.current_mode = old_mode

    game.state.clear()
    game.current_save_slot = slot

    if DB.constants.value('overworld_start'):
        game.state.change('overworld')
        game.state.process_temp_state()

        first_overworld_nid = DB.overworlds[0].nid
        game.game_vars['_next_overworld_nid'] = first_overworld_nid
    else:
        game.state.change('start_level_asset_loading')
        game.state.process_temp_state()

        first_level_nid = DB.levels[0].nid
        # Skip DEBUG if it's the first level
        if first_level_nid == 'DEBUG' and len(DB.levels) > 1:
            first_level_nid = DB.levels[1].nid
        game.start_level(first_level_nid)
        # Just for displaying the correct information on the title menu
        game.game_vars['_next_level_nid'] = first_level_nid

    save.suspend_game(game, 'start', slot)
    save.remove_suspend()

class TitleNewState(TitleLoadState):
    name = 'title_new'

    def take_input(self, event):
        # Only take input in normal state
        if self.state != 'normal':
            return

        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')

        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            self.state = 'transition_out'

        elif event == 'SELECT':
            selection = self.menu.current_index
            save_slot = self.save_slots[selection]
            if save_slot.kind:
                get_sound_thread().play_sfx('Select 1')
                game.memory['option_owner'] = selection
                game.memory['option_menu'] = self.menu
                game.memory['transition_from'] = 'New Game'
                game.memory['title_menu'] = self.menu
                game.state.change('title_new_child')
            else:
                get_sound_thread().play_sfx('Save')
                build_new_game(selection)
                save.SAVE_THREAD.join()
                save.check_save_slots()
                options, color = save.get_save_title(save.SAVE_SLOTS)
                self.menu.set_colors(color)
                self.menu.update_options(options)
                game.memory['transition_from'] = 'New Game'
                game.memory['title_menu'] = self.menu
                game.state.change('title_wait')

    def back(self):
        if game.state.get_prev_state().name == 'title_mode':
            game.state.back()
        game.state.back()

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
            if self.menu.move_down():
                get_sound_thread().play_sfx('Select 6')
        elif event == 'LEFT':
            if self.menu.move_up():
                get_sound_thread().play_sfx('Select 6')

        elif event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            if selection == 'Overwrite':
                get_sound_thread().play_sfx('Save')
                build_new_game(self.menu.owner)  # game.memory['option_owner']
                save.SAVE_THREAD.join()
                save.check_save_slots()
                options, color = save.get_save_title(save.SAVE_SLOTS)
                game.memory['title_menu'].set_colors(color)
                game.memory['title_menu'].update_options(options)
                game.state.change('title_wait')
                game.state.process_temp_state()
            elif selection == 'Back':
                get_sound_thread().play_sfx('Select 4')
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
        self.fluid = FluidScroll(128)
        self.position_x = int(WINWIDTH * 1.5)
        self.state = 'transition_in'

        self.bg = game.memory['title_bg']
        self.particles = game.memory['title_particles']

        options = ['Options', 'Credits']
        if DB.constants.value('title_sound'):
            options.append('Sound Room')
        if ACHIEVEMENTS:
            options.insert(1, 'Achievements')
        if (cf.SETTINGS['debug'] or cf.SETTINGS['all_saves']) and save.get_all_saves():
            options.insert(0, 'All Saves')
        self.menu = menus.Main(options, 'title_menu_dark')

    def begin(self):
        super().begin()
        # If we came back from the credits event, fade in
        if game.state.prev_state == 'event':
            game.state.change('transition_in')
            return 'repeat'

    def take_input(self, event):
        # Only take input in normal state
        if self.state != 'normal':
            return

        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')

        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            self.state = 'transition_out'

        elif event == 'SELECT':
            get_sound_thread().play_sfx('Select 1')
            selection = self.menu.get_current()
            if selection == 'Credits':
                game.memory['next_state'] = 'title_credit'
                game.state.change('transition_to')
            elif selection == 'Options':
                game.memory['next_state'] = 'settings_menu'
                game.state.change('transition_to')
            elif selection == 'All Saves':
                game.memory['next_state'] = 'title_all_saves'
                game.state.change('transition_to')
            elif selection == 'Sound Room':
                game.memory['next_state'] = 'extras_sound_room'
                game.memory['base_bg'] = self.bg
                game.state.change('transition_to')
            elif selection == 'Achievements':
                game.memory['next_state'] = 'base_achievement'
                game.memory['base_bg'] = self.bg
                game.state.change('transition_to')

class TitleAllSavesState(TitleLoadState):
    name = 'title_all_saves'
    in_level = False
    show_map = False

    def start(self):
        self.fluid = FluidScroll(128)
        self.state = 'transition_in'
        self.position_x = int(WINWIDTH * 1.5)

        self.bg = game.memory['title_bg']
        self.particles = game.memory['title_particles']

        self.save_slots = save.get_all_saves()
        options, colors = save.get_save_title(self.save_slots)
        self.menu = menus.ChapterSelect(options, colors)

class TitleWaitState(State):
    name = 'title_wait'
    in_level = False
    show_map = False
    # NOT TRANSPARENT!!!
    bg = None
    particles = []
    menu = None

    def start(self):
        self.bg = game.memory['title_bg']
        self.particles = game.memory['title_particles']

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
        if self.bg:
            self.bg.draw(surf)
        if self.particles:
            self.particles.update()
            self.particles.draw(surf)
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

    bg = None
    particles = None
    menu = None

    wait_time = 0
    fluid = None

    def start(self):
        if game.memory.get('_skip_save', False):
            game.memory['_skip_save'] = False
            if game.game_vars['_should_go_to_overworld']:
                self.go_to_overworld(make_save=False)
            else:
                self.go_to_next_level(make_save=False)
            return 'repeat'
        self.fluid = FluidScroll(128)
        imgs = RESOURCES.panoramas.get('title_background')
        self.bg = PanoramaBackground(imgs) if imgs else None
        game.memory['title_bg'] = self.bg

        self.particles = None
        if DB.constants.value('title_particles'):
            bounds = (-WINHEIGHT, WINWIDTH, WINHEIGHT, WINHEIGHT + 16)
            self.particles = particles.MapParticleSystem('title', particles.Smoke, .075, bounds, (TILEX, TILEY))
            self.particles.prefill()
        game.memory['title_particles'] = self.particles

        game.memory['transition_speed'] = 0.5

        self.leave_flag = False
        self.wait_time = 0

        save.check_save_slots()
        options, colors = save.get_save_title(save.SAVE_SLOTS)
        self.menu = menus.ChapterSelect(options, colors)
        most_recent = save.SAVE_SLOTS.index(max(save.SAVE_SLOTS, key=lambda x: x.realtime))
        self.menu.move_to(most_recent)

        game.state.change('transition_in')
        return 'repeat'

    def begin(self):
        if self.fluid:
            self.fluid.reset_on_change_state()

    def go_to_next_level(self, make_save=True):
        current_state = game.state.state[-1]
        next_level_nid = game.game_vars['_next_level_nid']

        game.load_states(['start_level_asset_loading'])
        if make_save:
            save.suspend_game(game, game.memory['save_kind'], slot=self.menu.current_index)

        game.start_level(next_level_nid)

        game.state.state.append(current_state)
        game.state.change('transition_pop')

    def go_to_overworld(self, make_save=True):
        current_state = game.state.state[-1]

        game.load_states(['overworld'])
        if make_save:
            save.suspend_game(game, game.memory['save_kind'], slot=self.menu.current_index)

        game.state.state.append(current_state)
        game.state.change('transition_pop')

    def take_input(self, event):
        if self.wait_time > 0:
            return

        if not self.fluid:
            return
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')

        if event == 'BACK':
            # Proceed to next level anyway
            get_sound_thread().play_sfx('Select 4')
            if self.name == 'in_chapter_save':
                game.state.change('transition_pop')
            elif game.game_vars['_should_go_to_overworld']:
                self.go_to_overworld(make_save=False)
            else:
                self.go_to_next_level(make_save=False)

        elif event == 'SELECT':
            get_sound_thread().play_sfx('Save')
            # Rename selection
            self.wait_time = engine.get_time()
            if self.name == 'in_chapter_save':
                name = game.level.name
                self.menu.set_text(self.menu.current_index, name)
            else:
                next_level_nid = game.game_vars['_next_level_nid']
                level = DB.levels.get(next_level_nid)
                if level:
                    name = level.name
                    self.menu.set_text(self.menu.current_index, name)
            self.menu.set_color(self.menu.current_index, game.mode.color)

    def update(self):
        if self.menu:
            self.menu.update()

        if self.wait_time and engine.get_time() - self.wait_time > 1250 and not self.leave_flag:
            self.leave_flag = True

            if self.name == 'in_chapter_save':
                saved_state = game.state.state[:]
                game.state.state = game.state.state[:-1]  # All except this one
                save.suspend_game(game, game.memory['save_kind'], slot=self.menu.current_index)
                # Put states back
                game.state.state = saved_state
                game.state.change('transition_pop')
            elif game.game_vars['_should_go_to_overworld']:
                self.go_to_overworld(make_save=True)
            else:
                self.go_to_next_level(make_save=True)

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.particles:
            self.particles.update()
            self.particles.draw(surf)
        if self.menu:
            if 100 < engine.get_time() - self.wait_time < 200:
                self.menu.draw(surf, flicker=True)
            else:
                self.menu.draw(surf)
        return surf

class TitleCreditState(State):
    name = 'title_credit'

    def __init__(self, name=None):
        super().__init__(name)
        self.fluid = FluidScroll()

    def start(self):
        self.bg = game.memory['title_bg']

        credits = sorted(DB.credit, key=lambda x: (x.category, x.sub_nid if x.type in ['List', 'Text'] else x.type))
        self.categories = []
        options = []
        ignore = []

        ordered_credits = []
        temp_list = None
        for credit in credits:
            curr_option = credit.sub_nid \
                            if credit.type in ['List', 'Text'] \
                            else credit.type
            curr_option = curr_option.replace('_', ' ')

            if credit.category not in self.categories:
                self.categories.append(credit.category)
                if temp_list:
                    ordered_credits.append(temp_list)
                options.append(credit.category)
                ignore.append(True)

                ordered_credits.append([])
                options.append(curr_option)
                ignore.append(False)

                prev_option = curr_option
                temp_list = [credit]
                continue

            if prev_option == curr_option:
                temp_list.append(credit)
                continue

            ordered_credits.append(temp_list)
            options.append(curr_option)
            ignore.append(False)
            prev_option = curr_option
            temp_list = [credit]
        ordered_credits.append(temp_list)

        self.menu = CreditMenu(options, ignore)
        self.display = CreditDisplay(ordered_credits)
        self.display.update_entry(self.menu.get_current_index())

        game.state.change('transition_in')
        return 'repeat'

    def begin(self):
        self.fluid.reset_on_change_state()

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if not self.display.current or self.display.current != self.menu.get_current_index():
            self.display.update_entry(self.menu.get_current_index())

        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
            self.display.update_entry(self.menu.get_current_index())

        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')
            self.display.update_entry(self.menu.get_current_index())

        elif 'RIGHT' in directions:
            if self.display.page_right():
                get_sound_thread().play_sfx('Status_Page_Change')

        elif 'LEFT' in directions:
            if self.display.page_left():
                get_sound_thread().play_sfx('Status_Page_Change')

        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            game.state.change('transition_pop')

        elif event == 'SELECT':
            if self.display.page_right(True):
                get_sound_thread().play_sfx('Status_Page_Change')

    def update(self):
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.display:
            self.display.draw(surf)
        if self.menu:
            self.menu.draw(surf)
        return surf

class CreditDisplay():
    icon_size_dict = {"16x16_Icons": 16, "32x32_Icons": 32, "Map_Icons": 32, "Map_Sprites": 16}

    def __init__(self, credits):
        self.credits = credits
        self.current = None
        self.pages = []
        self.font = 'text'

        self.topleft = (84, 4)
        self.width = WINWIDTH - 84
        self.height = WINHEIGHT - 8

        self.bg_surf = base_surf.create_base_surf(self.width, self.height, 'menu_bg_brown')
        shimmer = SPRITES.get('menu_shimmer3')
        self.bg_surf.blit(shimmer, (
            self.bg_surf.get_width() - shimmer.get_width() - 1, self.bg_surf.get_height() - shimmer.get_height() - 5))
        self.bg_surf = image_mods.make_translucent(self.bg_surf, .1)

        self.left_arrow = gui.ScrollArrow('left', (self.topleft[0] + 4, 8))
        self.right_arrow = gui.ScrollArrow('right', (self.topleft[0] + self.width - 11, 8), 0.5)

        self.clear_display()

    def clear_display(self):       
        self.bg = None
        self.dlg = None
        self.portrait = None
        self.static_surf = None

    def update_entry(self, idx):
        from app.engine import dialog

        if self.current == idx:
            return  # No need to update

        self.current = idx
        self.page_num = 0
        self.pages = []

        lst = self.credits[idx]
        if lst:
            if lst[0].type in ('16x16_Icons', '32x32_Icons', 'Map_Icons', 'Map_Sprites'):
                limit = self.height - 24
                icon_height = self.icon_size_dict.get(lst[0].type) + 4
                font_height = FONT[self.font].height
                page_height = 0
                page = []

                for credit in lst:
                    line = len(text_funcs.line_wrap(self.font, "by %s" % credit.contrib[0][0], self.width - 16))
                    credit_height = max(line * font_height, icon_height)
                    if page_height + credit_height <= limit:
                        page_height += credit_height
                        page.append(credit)
                        continue
                    self.pages.append(page)
                    page_height = credit_height
                    page = [credit]
                self.pages.append(page)
            else:
                self.pages = [[credit] for credit in lst]
        self.num_pages = len(self.pages)

        self.clear_display()

    def page_right(self, first_push=False) -> bool:
        if self.page_num < self.num_pages - 1:
            self.page_num += 1
            self.right_arrow.pulse()
            self.clear_display()
            return True
        elif first_push:
            self.page_num = (self.page_num + 1) % self.num_pages
            self.right_arrow.pulse()
            self.clear_display()
            return True
        return False

    def page_left(self, first_push=False) -> bool:
        if self.page_num > 0:
            self.page_num -= 1
            self.left_arrow.pulse()
            self.clear_display()
            return True
        elif first_push:
            self.page_num = (self.page_num - 1) % self.num_pages
            self.left_arrow.pulse()
            self.clear_display()
            return True
        return False

    def draw(self, surf):
        if self.pages:
            lst = self.pages[self.page_num]
            credit = lst[0]

            if credit.type == 'Panoramas':
                if not self.bg:
                    imgs = RESOURCES.panoramas.get(credit.sub_nid)
                    self.bg = PanoramaBackground(imgs) if imgs else None
                self.bg.draw(surf)

                c = credit.contrib[0]
                lines = text_funcs.line_wrap(self.font, "%s by %s" % (c[1], c[0]), self.width - 16)
                temp_menu = base_surf.create_base_surf(self.width, 28 + len(lines) * FONT[self.font].height, 'menu_bg_clear')
                surf.blit(temp_menu, self.topleft)
            else:
                surf.blit(self.bg_surf, self.topleft)

            if credit.type == 'Portraits':
                if not self.portrait:
                    portrait = RESOURCES.portraits.get(credit.sub_nid)
                    self.portrait = InfoMenuPortrait(portrait, DB.constants.value('info_menu_blink'))

                self.portrait.update()
                im = self.portrait.create_image()
                surf.blit(im, utils.tuple_add((self.width - 96, WINHEIGHT - 12 - 80), self.topleft))

            elif credit.type == 'Map_Sprites':
                y_pos = 20
                icon_size = self.icon_size_dict.get(credit.type) + 4
                for c in lst:
                    res = RESOURCES.map_sprites.get(c.sub_nid)
                    map_sprite = game.map_sprite_registry.get("%s_player" % res.nid)
                    if not map_sprite:
                        map_sprite = MapSprite(res, "player")
                        game.map_sprite_registry["%s_player" % map_sprite.nid] = map_sprite
                    im = map_sprite.create_image('passive')
                    surf.blit(im, utils.tuple_add((8 - 24, y_pos - 24), self.topleft))

                    lines = text_funcs.line_wrap(self.font, "by %s" % c.contrib[0][0], self.width - 16 - icon_size)
                    for idx, line in enumerate(lines):
                        render_text(surf, [self.font], [line], [], utils.tuple_add((8 + icon_size, y_pos + idx * FONT[self.font].height), self.topleft))
                    y_pos += max(len(lines) * FONT[self.font].height, icon_size)

            elif credit.type == 'Text':
                if not self.dlg:
                    self.dlg = dialog.Dialog(credit.contrib[0][1], font_type=self.font, font_color="white", num_lines=8, draw_cursor=False)
                    self.dlg.position = self.topleft[0], self.topleft[1] + 12
                    self.dlg.text_width = WINWIDTH - 100
                    self.dlg.reformat()

                self.dlg.update()
                self.dlg.draw(surf)

            if self.num_pages > 1:
                self.left_arrow.draw(surf)
                self.right_arrow.draw(surf)

            if not self.static_surf:
                self.static_surf = self.create_static_surf(lst)
            surf.blit(self.static_surf, (0, 0))

        return surf

    def create_static_surf(self, lst):
        credit = lst[0]
        surf = engine.create_surface((WINWIDTH, WINHEIGHT), transparent=True)

        header = credit.sub_nid if credit.type in ['List', 'Text'] else credit.type
        render_text(surf, ['text'], [header.replace('_', ' ')], ['blue'], utils.tuple_add((self.width // 2, 4), self.topleft), HAlignment.CENTER)
        if self.num_pages > 1:
            text = '%d / %d' % (self.page_num + 1, self.num_pages)
            render_text(surf, ['text'], [text], ['yellow'], utils.tuple_add((self.width - 8, WINHEIGHT - 12 - 16), self.topleft), HAlignment.RIGHT)

        if credit.type == '80x72_Icons':
            im = self.get_icon_by_credit(credit)
            surf.blit(im, utils.tuple_add((self.width - 96, WINHEIGHT - 12 - 72), self.topleft))

        lines = []
        if credit.type in ('16x16_Icons', '32x32_Icons', 'Map_Icons'):
            y_pos = 20
            icon_size = self.icon_size_dict.get(credit.type) + 4
            for c in lst:
                im = self.get_icon_by_credit(c)
                surf.blit(im, utils.tuple_add((8, y_pos), self.topleft))
                lines = text_funcs.line_wrap(self.font, "by %s" % c.contrib[0][0], self.width - 16 - icon_size)
                for idx, line in enumerate(lines):
                    render_text(surf, [self.font], [line], [], utils.tuple_add((8 + icon_size, y_pos + idx * FONT[self.font].height), self.topleft))
                y_pos += max(len(lines) * FONT[self.font].height, icon_size)

        elif credit.type in ('80x72_Icons', 'Portraits', 'Panoramas'):
            c = credit.contrib[0]
            lines = text_funcs.line_wrap(self.font, c[1], self.width - 16)
            st = lines.pop()
            highlight_lines = range(len(lines))

            lines += text_funcs.line_wrap(self.font, "<orange>%s</> by %s" % (st, c[0]), self.width - 16)
            for idx, line in enumerate(lines):
                render_text(surf, [self.font], [line], ['orange' if idx in highlight_lines else None], 
                            utils.tuple_add((8, 20 + idx * FONT[self.font].height), self.topleft))


        elif credit.type == 'List':
            highlight_lines = []
            for c in credit.contrib:
                start = len(lines)
                lines += text_funcs.line_wrap(self.font, c[1], self.width - 16)
                st = lines.pop()
                end = len(lines)
                highlight_lines += range(start, end)

                lines += text_funcs.line_wrap(self.font, "<orange>%s</> by %s" % (st, c[0]), self.width - 16)
            for idx, line in enumerate(lines):
                render_text(surf, [self.font], [line], ['orange' if idx in highlight_lines else None], 
                            utils.tuple_add((8, 20 + idx * FONT[self.font].height), self.topleft))

        return surf

    def get_icon_by_credit(self, credit):
        if credit.type == '16x16_Icons':
            database = RESOURCES.icons16
            width, height = 16, 16
        elif credit.type == '32x32_Icons':
            database = RESOURCES.icons32
            width, height = 32, 32
        elif credit.type == '80x72_Icons':
            database = RESOURCES.icons80
            width, height = 80, 72
        elif credit.type == 'Map_Icons':
            database = RESOURCES.map_icons

            image = database.get(credit.sub_nid)
            if not image.image:
                image.image = engine.image_load(image.full_path)
            im = image.image.copy()
            return im
        else:
            return None

        image = database.get(credit.sub_nid)
        if not image.image:
            image.image = engine.image_load(image.full_path)
        im = engine.subsurface(image.image, (credit.icon_index[0] * width, credit.icon_index[1] * height, width, height))
        im = im.convert()
        engine.set_colorkey(im, COLORKEY, rleaccel=True)
        return im

class CreditMenu(menus.Choice):
    def __init__(self, options, ignore=None):
        topleft = (4, 4)
        background = 'menu_bg_brown'

        super().__init__(None, options, topleft, background, info=None)

        self.shimmer = 3
        self.gem = 'brown'
        self.set_limit(9)
        if ignore:
            self.set_ignore(ignore)

    def create_options(self, options, info_descs=None):
        self.set_limit(9)
        self.options.clear()
        for idx, option in enumerate(options):
            option = CreditOption(idx, option)
            self.options.append(option)

        buffer = self.limit - len(options)
        for num in range(buffer):
            option = EmptyOption(len(options) + num)
            self.options.append(option)

class CreditOption(BasicOption):
    def width(self):
        return 84

    def height(self):
        return 16

    def get_color(self):
        if self.ignore:
            return 'yellow'
        return self.color

    def draw(self, surf, x, y):
        main_color = self.get_color()
        main_font = self.font

        s = self.display_text
        width = text_width(main_font, s)
        if width > 70:
            main_font = 'narrow'

        render_text(surf, [main_font], s, [main_color], (x + 6, y))