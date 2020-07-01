from app.resources.resources import RESOURCES

from app.engine import config as cf
from app.engine.sprites import SPRITES
from app.engine.sound import SOUNDTHREAD
from app.engine.state import State
from app.engine import engine, background, banner, menus, settings_menu
from app.engine.game_state import game

controls = {'key_SELECT': engine.subsurface(SPRITES.get('buttons'), (0, 66, 14, 13)),
            'key_BACK': engine.subsurface(SPRITES.get('buttons'), (0, 82, 14, 13)),
            'key_INFO': engine.subsurface(SPRITES.get('buttons'), (1, 149, 16, 9)),
            'key_AUX': engine.subsurface(SPRITES.get('buttons'), (1, 133, 16, 9)),
            'key_START': engine.subsurface(SPRITES.get('buttons'), (0, 165, 33, 9)),
            'key_LEFT': engine.subsurface(SPRITES.get('buttons'), (1, 4, 13, 12)),
            'key_RIGHT': engine.subsurface(SPRITES.get('buttons'), (1, 19, 13, 12)),
            'key_DOWN': engine.subsurface(SPRITES.get('buttons'), (1, 34, 12, 13)),
            'key_UP': engine.subsurface(SPRITES.get('buttons'), (1, 50, 12, 13))}
control_order = ('key_SELECT', 'key_BACK', 'key_INFO', 'key_AUX', 'key_LEFT', 'key_RIGHT', 'key_UP', 'key_DOWN', 'key_START')

config = [('Animation', ['Always', 'Your Turn', 'Combat Only', 'Never'], 'Animation_desc', 0),
          ('temp_Screen Size', ['1', '2', '3', '4', '5'], 'temp_Screen Size_desc', 18),
          ('Unit Speed', list(reversed(range(15, 180, 15))), 'Unit Speed_desc', 1),
          ('Text Speed', cf.text_speed_options, 'Text Speed_desc', 2),
          ('Cursor Speed', list(reversed(range(32, 160, 16))), 'Cursor Speed_desc', 8),
          ('Show Terrain', bool, 'Show Terrain_desc', 7),
          ('Show Objective', bool, 'Show Objective_desc', 6),
          ('Autocursor', bool, 'Autocursor_desc', 13),
          ('HP Map Team', ['All', 'Ally', 'Enemy'], 'HP Map Team_desc', 10),
          ('HP Map Cull', ['None', 'Wounded', 'All'], 'HP Map Cull_desc', 10),
          ('Music Volume', [x/10.0 for x in range(0, 11, 1)], 'Music Volume_desc', 15),
          ('Sound Volume', [x/10.0 for x in range(0, 11, 1)], 'Sound Volume_desc', 16),
          ('Autoend Turn', bool, 'Autoend Turn_desc', 14),
          ('Confirm End', bool, 'Confirm End_desc', 14),
          ('Display Hints', bool, 'Display Hints_desc', 3)]

config_icons = [engine.subsurface(SPRITES.get('settings_icons'), (0, c[3] * 16, 16, 16)) for c in config]

class SettingsMenuState(State):
    name = 'settings_menu'
    in_level = False
    show_map = False

    def create_background(self):
        panorama = RESOURCES.panoramas.get('settings_background')
        if not panorama:
            panorama = RESOURCES.panoramas.get('default_background')
        if panorama:
            if panorama.num_frames > 1:
                self.bg = background.PanoramaBackground(panorama)
            else:
                self.bg = background.ScrollingBackground(panorama)
        else:
            self.bg = None

    def start(self):
        self.create_background()
        self.state = 'config'

        top_options = ('Config', 'Controls')
        top_info = ('Config_desc', 'Controls_desc')
        self.top_menu = menus.Choice(None, top_options, ('center', 0), 'menu_bg_clear', top_info)
        self.top_menu.set_horizontal(True)

        control_options = control_order
        control_icons = [controls[c] for c in control_options]
        self.control_menu = settings_menu.Controls(None, control_options, 'menu_bg_clear', control_icons)

        config_options = [(c[0], c[1]) for c in config]
        config_info = [c[2] for c in config]
        self.config_menu = settings_menu.Config(None, config_options, 'menu_bg_clear', config_icons, config_info)
        
        self.current_menu = self.top_menu

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        if self.state == 'get_input':
            if event == 'BACK':
                SOUNDTHREAD.play_sfx('Select 4')
                self.state = 'controls'
                game.input_manager.set_change_keymap(False)
            elif event == 'NEW':
                SOUNDTHREAD.play_sfx('Select 1')
                self.state = 'controls'
                selection = self.current_menu.get_current()
                cf.SETTINGS[selection] = game.input_manager.unavailable_button
                game.input_manager.set_change_keymap(False)
                game.input_manager.update_key_map()
            elif event:
                SOUNDTHREAD.play_sfx('Select 4')
                self.state = 'invalid'
                game.input_manager.set_change_keymap(False)
                text = 'Invalid Choice!'
                game.alerts.append(banner.Custom(text))
                game.state.change('alert')
        else:
            self.current_menu.handle_mouse()
            if event == 'DOWN':
                SOUNDTHREAD.play_sfx('Select 6')
                self.current_menu.move_down()
            elif event == 'UP':
                SOUNDTHREAD.play_sfx('Select 6')
                self.current_menu.move_up()
            elif event == 'LEFT':
                SOUNDTHREAD.play_sfx('Select 6')
                self.current_menu.move_left()
            elif event == 'RIGHT':
                SOUNDTHREAD.play_sfx('Select 6')
                self.current_menu.move_right()

            elif event == 'BACK':
                self.back()

            elif event == 'SELECT':
                selection = self.current_menu.get_current()
                if self.current_menu is self.top_menu:
                    SOUNDTHREAD.play_sfx('Select 1')
                    if selection == 'config':
                        # Transition to config menu state
                        self.current_menu = self.config_menu
                        self.state = 'config'
                    elif selection == 'controls':
                        self.current_menu = self.controls_menu
                        self.state = 'controls'
                elif self.state == 'controls':
                    self.state = 'get_input'
                    game.input_manager.set_change_keymap(True)

    def back(self):
        SOUNDTHREAD.play_sfx('Select 4')
        cf.save_settings()
        game.state.change('transition_pop')

    def update(self):
        self.top_menu.update()
        if self.state == 'config':
            self.config_menu.update()
        else:
            self.controls_menu.update()
    
    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)

        if self.state == 'config':
            self.top_menu.draw(surf)
            self.config_menu.draw(surf)
        else:
            self.top_menu.draw(surf)
            self.controls_menu.draw(surf)

        return surf

    def finish(self):
        # Just to make sure!
        game.input_manager.set_change_keymap(False)
