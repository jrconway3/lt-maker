from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT

from app.resources.resources import RESOURCES
from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.sound import SOUNDTHREAD
from app.engine.fonts import FONT
from app.engine.state import State, MapState

from app.engine.background import SpriteBackground
from app.engine import config as cf
from app.engine.game_state import game
from app.engine import menus, banner, action, base_surf, background, \
    info_menu, engine, equations, item_funcs, text_funcs, image_mods, \
    convoy_funcs, item_system, interaction, gui, icons, prep
from app.engine.fluid_scroll import FluidScroll

class BaseMainState(State):
    name = 'base_main'

    def __init__(self, name=None):
        super().__init__(name)
        self.fluid = FluidScroll()

    def start(self):
        SOUNDTHREAD.fade_in(game.level.music['base'])
        game.cursor.hide()
        game.cursor.autocursor()
        game.boundary.hide()
        # build background
        bg_name = game.memory.get('base_bg_name')
        panorama = None
        if bg_name:
            panorama = RESOURCES.panoramas.get(bg_name)
        if panorama:
            panorama = RESOURCES.panoramas.get(bg_name)
            self.bg = background.PanoramaBackground(panorama)
        else:
            panorama = RESOURCES.panoramas.get('default_background')
            self.bg = background.ScrollingBackground(panorama)
            self.bg.scroll_speed = 50
        game.memory['base_bg'] = self.bg

        options = ['Manage', 'Convos', 'Codex', 'Options', 'Save', 'Continue']
        ignore = [False, True, False, False, False, False]
        if game.base_convos:
            ignore[1] = False
        # TODO: Supports
        if game.game_vars.get('_base_market'):
            options.insert(1, 'Market')
            if game.market_items:
                ignore.insert(1, False)
            else:
                ignore.insert(1, True)
        
        topleft = 4, WINHEIGHT//2 - (len(options) * 16 + 8)//2
        self.menu = menus.Choice(None, options, topleft=topleft)
        self.menu.set_ignore(ignore)

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            if selection == 'Manage':
                game.memory['next_state'] = 'prep_manage'
                game.state.change('transition_to')
            elif selection == 'Market':
                game.memory['next_state'] = 'base_market_select'
                game.state.change('transition_to')
            elif selection == 'Convos':
                game.memory['option_owner'] = selection
                game.memory['option_menu'] = self.menu
                game.state.change('base_convos_child')
            elif selection == 'Codex':
                game.memory['option_owner'] = selection
                game.memory['option_menu'] = self.menu
                game.state.change('base_codex_child')
            elif selection == 'Options':
                game.memory['next_state'] = 'settings_menu'
                game.state.change('transition_to')
            elif selection == 'Save':
                game.memory['save_kind'] = 'base'
                game.memory['next_state'] = 'in_chapter_save'
                game.state.change('transition_to')
            elif selection == 'Continue':
                game.state.change('transition_pop')

    def update(self):
        super().update()
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        if self.bg:
            self.bg.draw(surf)
        if self.menu:
            self.menu.draw(surf)
        return surf

class BaseMarketSelectState(prep.PrepManageState):
    name = 'base_market_select'

    def create_quick_disp(self):
        sprite = SPRITES.get('buttons')
        buttons = [sprite.subsurface(0, 66, 14, 13)]
        font = FONT['text-white']
        commands = ['Market']
        commands = [text_funcs.translate(c) for c in commands]
        size = (49 + max(font.width(c) for c in commands), 40)
        bg_surf = base_surf.create_base_surf(size[0], size[1], 'menu_bg_brown')
        bg_surf = image_mods.make_translucent(bg_surf, 0.1)
        bg_surf.blit(buttons[0], (20 - buttons[0].get_width()//2, 18 - buttons[0].get_height()))
        for idx, command in enumerate(commands):
            font.blit(command, bg_surf, (38, idx * 16 + 3))
        return bg_surf

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                SOUNDTHREAD.play_sfx('Select 5')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                SOUNDTHREAD.play_sfx('Select 5')
        elif 'LEFT' in directions:
            if self.menu.move_left(first_push):
                SOUNDTHREAD.play_sfx('Select 5')
        elif 'RIGHT' in directions:
            if self.menu.move_right(first_push):
                SOUNDTHREAD.play_sfx('Select 5')

        if event == 'SELECT':
            unit = self.menu.get_current()
            game.memory['current_unit'] = unit
            game.memory['next_state'] = 'prep_market'
            game.state.change('transition_to')
            SOUNDTHREAD.play_sfx('Select 1')
        elif event == 'BACK':
            game.state.change('transition_pop')
            SOUNDTHREAD.play_sfx('Select 4')
        elif event == 'INFO':
            SOUNDTHREAD.play_sfx('Select 1')
            game.memory['scroll_units'] = game.get_units_in_party()
            game.memory['next_state'] = 'info_menu'
            game.memory['current_unit'] = self.menu.get_current()
            game.state.change('transition_to')

class BaseConvosChildState(State):
    name = 'base_convos_child'
    transparent = True

    def start(self):
        options = [event_nid for event_nid in game.base_convos]
        ignore = [bool(game.memory.get('_ignore_' + event_nid)) for event_nid in game.base_convos]

        selection = game.memory['option_owner']
        topleft = game.memory['option_menu']

        self.menu = menus.Choice(selection, options, topleft)
        color = ['text-grey' if i else 'text-white' for i in ignore]
        self.menu.set_color(color)

    def begin(self):
        ignore = [bool(game.memory.get('_ignore_' + event_nid)) for event_nid in game.base_convos]
        color = ['text-grey' if i else 'text-white' for i in ignore]
        self.menu.set_color(color)

    def take_input(self, event):
        self.menu.handle_mouse()
        if event == 'DOWN':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down()
        elif event == 'UP':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            SOUNDTHREAD.play_sfx('Select 1')
            game.memory['_ignore_' + selection] = True
            game.events.trigger('on_base_convo', selection)

    def update(self):
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.menu:
            self.menu.draw(surf)
        return surf

class BaseCodexChildState(State):
    name = 'base_codex_child'
    transparent = True
    
    def start(self):
        options = ['Library']
        if game.game_vars['_show_world_map']:
            options.append('Map')
        # TODO Records
        # TODO Achievements?
        # TODO Tactics?
        # TODO Guide

        selection = game.memory['option_owner']
        topleft = game.memory['option_menu']

        self.menu = menus.Choice(selection, options, topleft)

    def begin(self):
        ignore = [bool(game.memory.get('_ignore_' + event_nid)) for event_nid in game.base_convos]
        color = ['text-grey' if i else 'text-white' for i in ignore]
        self.menu.set_color(color)

    def take_input(self, event):
        self.menu.handle_mouse()
        if event == 'DOWN':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down()
        elif event == 'UP':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            SOUNDTHREAD.play_sfx('Select 1')

            if selection == 'Library':
                game.memory['next_state'] = 'base_library'
                game.state.change('transition_to')
            elif selection == 'Map':
                game.memory['next_state'] = 'base_world_map'
                game.state.change('transition_to')

    def update(self):
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        if self.menu:
            self.menu.draw(surf)
        return surf

class LoreDisplay():
    def __init__(self):
        self.lore = None
        self.topleft = (72, 4)
        self.width = WINWIDTH - 76
        self.bg_surf = base_surf.create_base_surf(self.width, WINHEIGHT - 8)

    def update_entry(self, lore_nid):
        self.lore = DB.lore.get(lore_nid)
        self.page_num = 0
        self.lines = self.lore.text.split('{br}')
        self.num_pages = len(self.lines)

    def page_right(self, first_push=False) -> bool:
        if self.page_num < self.num_pages:
            self.page_num += 1
            return True
        elif first_push:
            self.page_num = (self.page_num + 1) % self.num_pages
            return True
        return False

    def page_left(self, first_push=False) -> bool:
        if self.page_num > 0:
            self.page_num -= 1
            return True
        elif first_push:
            self.page_num = (self.page_num - 1) % self.num_pages
            return True
        return False

    def draw(self, surf):
        if self.lore:
            if game.get_unit(self.lore.nid):
                unit = game.get_unit(self.lore.nid)
                icons.draw_portrait(surf, unit, (self.width - 96, WINHEIGHT - 12 - 80))

            FONT['text-yellow'].blit_center(self.lore.title, surf, (self.width//2, 4))

            text = self.lines[self.page_num]
            lines = text_funcs.line_wrap(FONT['text-white'], text, self.width - 8)
            for idx, line in enumerate(lines):
                FONT['text-white'].blit(line, surf, (4, FONT['text-white'].height * idx + 20))

        return surf

class BaseLibraryState(State):
    name = 'base_library'

    def __init__(self, name=None):
        super().__init__(name)
        self.fluid = FluidScroll()

    def start(self):
        self.bg = game.memory['base_bg']

        unlocked_lore = [lore for lore in DB.lore if lore.nid in game.unlocked_lore]
        sorted_lore = sorted(unlocked_lore, key=lambda x: x.category)
        self.categories = []
        options = []
        ignore = []
        for lore in sorted_lore:
            if lore.category not in self.categories:
                self.categories.append(lore.category)
                options.append(lore.category)
                ignore.append(True)
                continue
            options.append(lore)
            ignore.append(False)

        topleft = 4, 4
        self.options = options
        self.menu = menus.Choice(None, self.options, topleft=topleft)
        self.menu.set_limit(9)
        self.menu.set_hard_limit(True)
        self.menu.set_ignore(ignore)

        self.display = LoreDisplay()

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                SOUNDTHREAD.play_sfx('Select 6')
                self.display.update_entry(self.menu.get_current().nid)
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                SOUNDTHREAD.play_sfx('Select 6')
                self.display.update_entry(self.menu.get_current().nid)
        elif 'RIGHT' in directions:
            if self.display.page_right():
                SOUNDTHREAD.play_sfx('TradeRight')
        elif 'LEFT' in directions:
            if self.display.page_left():
                SOUNDTHREAD.play_sfx('TradeRight')

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.change('transition_pop')

        elif event == 'SELECT':
            if self.display.page_right(True):
                SOUNDTHREAD.play_sfx('TradeRight')

        elif event == 'AUX':
            SOUNDTHREAD.play_sfx('Info')
            lore = self.menu.get_current()
            # Go to previous category
            cidx = self.categories.index(lore.category)
            new_category = self.categories[(cidx + 1) % len(self.categories)]
            idx = self.options.index(new_category)
            option = self.options[idx + 1]
            
            self.display.update_entry(option.nid)

        elif event == 'INFO':
            SOUNDTHREAD.play_sfx('Info')
            lore = self.menu.get_current()
            # Go to next category
            cidx = self.categories.index(lore.category)
            new_category = self.categories[(cidx - 1) % len(self.categories)]
            idx = self.options.index(new_category)
            option = self.options[idx + 1]

            self.display.update_entry(option.nid)

    def update(self):
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        if self.menu:
            self.menu.draw(surf)
        if self.display:
            self.display.draw(surf)
        return surf
