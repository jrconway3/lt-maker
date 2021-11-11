from app.constants import WINWIDTH, WINHEIGHT
from app.engine.sound import SOUNDTHREAD
from app.engine.fonts import FONT
from app.engine.state import MapState

from app.engine import menus, action, base_surf
from app.engine.game_state import game

class TextEntryState(MapState):
    name = 'text_entry'
    transparent = True

    def start(self):
        self.constant_id, self.header, self.character_limit, illegal_characters, self.force_entry = game.memory['text_entry']
        self.menu = menus.KeyboardMenu(self.header, self.character_limit, illegal_characters)
        self.bg_surf, self.topleft = self.create_bg_surf()

    def begin(self):
        #Did we say yes to text confirmation?
        if game.memory.get('entered_text'):
            #We did, so reset this variable and finish processing this state. Update game vars with the provided info.
            action.do(action.SetGameVar(self.constant_id, self.menu.name))
            action.do(action.SetGameVar('last_response_entered', self.menu.name))
            game.memory['entered_text'] = False
            game.state.back()
    
    def create_bg_surf(self):
        width_of_header = FONT['text-white'].width(self.header) + 16
        menu_width = self.menu.get_menu_width()
        width = max(width_of_header, menu_width)
        menu_height = self.menu.get_menu_height()
        height = menu_height + FONT['text-white'].height
        bg_surf = base_surf.create_base_surf(width, height, 'menu_bg_base')
        topleft = (9, 42)
        return bg_surf, topleft
    
    def take_input(self, event):
        self.menu.handle_mouse()
        if event == 'RIGHT':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_right()
        elif event == 'LEFT':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_left()
        elif event == 'DOWN':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down()
        elif event == 'UP':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            if len(self.menu.name) > 0:
                self.menu.updateName('back')
                SOUNDTHREAD.play_sfx('Select 4')
            else:
                SOUNDTHREAD.play_sfx('Error')

        elif event == 'SELECT':
            selection = self.menu.get_current()
            if len(self.menu.name) < self.menu.character_limit:
                self.menu.updateName(selection)
                SOUNDTHREAD.play_sfx('Select 1')
            else:
                SOUNDTHREAD.play_sfx('Error')

        elif event == 'START':
            game.state.change('text_confirm')
            SOUNDTHREAD.play_sfx('Select 2')
            
        #Exits text entry without saving a value. Dev must dictate whether this is available by setting the flag in the event.
        elif event == 'AUX' and not self.force_entry:
            game.state.back()

    def update(self):
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        surf.blit(self.bg_surf, self.topleft)
        if self.menu:
            self.menu.draw(surf)
        return surf

class TextConfirmState(MapState):
    name = 'text_confirm'
    transparent = True

    def start(self):
        self.header = 'Finish text entry?'
        options_list = ['Yes','No']
        self.orientation = 'vertical'
        self.menu = menus.Choice(None, options_list, 'center', None)
        self.bg_surf, self.topleft = self.create_bg_surf()
        self.menu.topleft = (self.topleft[0], self.topleft[1] + FONT['text-white'].height)

    def create_bg_surf(self):
        width_of_header = FONT['text-white'].width(self.header) + 16
        menu_width = self.menu.get_menu_width()
        width = max(width_of_header, menu_width)
        menu_height = self.menu.get_menu_height() if self.orientation == 'vertical' else FONT['text-white'].height + 8
        height = menu_height + FONT['text-white'].height
        bg_surf = base_surf.create_base_surf(width, height, 'menu_bg_base')
        topleft = (WINWIDTH//2 - width//2, WINHEIGHT//2 - height//2)
        return bg_surf, topleft

    def take_input(self, event):
        self.menu.handle_mouse()
        if (event == 'RIGHT' and self.orientation == 'horizontal') or \
                (event == 'DOWN' and self.orientation == 'vertical'):
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down()
        elif (event == 'LEFT' and self.orientation == 'horizontal') or \
                (event == 'UP' and self.orientation == 'vertical'):
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Error')

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            if selection == 'Yes':
                game.memory['entered_text'] = True
                game.state.back()
            else:
                game.memory['entered_text'] = False
                game.state.back()

    def update(self):
        self.menu.update()

    def draw(self, surf):
        surf.blit(self.bg_surf, self.topleft)
        FONT['text-white'].blit(self.header, surf, (self.topleft[0] + 4, self.topleft[1] + 4))

        # Place Menu on background
        self.menu.draw(surf)
        return surf
