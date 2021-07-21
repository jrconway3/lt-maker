from app.engine.fluid_scroll import FluidScroll
from typing import Tuple
from app.engine.game_menus.menu_components.unit_menu.unit_menu import UnitMenuUI
from app.engine.objects.unit import UnitObject
import datetime
from app.constants import WINWIDTH

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.sound import SOUNDTHREAD
from app.engine.state import State
from app.engine import engine, background, base_surf, text_funcs, evaluate
from app.engine.game_state import game
from app.utilities.enums import Direction

class UnitMenuState(State):
    name = 'unit_menu'
    bg = None
    surfaces = []

    def start(self):
        self.fluid = FluidScroll()
        self.bg = background.create_background('settings_background')
        self.in_level = game.level is not None
        # if in level, all deploy units
        # else, all party units
        if self.in_level: # player is in a level, get deployed
            self.all_player_units = game.get_player_units()
        elif game.is_displaying_overworld() and game.overworld_controller.selected_entity: # overworld, get all party units
            self.all_player_units = game.get_units_in_party(game.overworld_controller.selected_entity.prefab.nid)
        else: # all player units, everywhere, who are playable
            self.all_player_units = []
            for party_nid in game.parties.keys():
                self.all_player_units += game.get_units_in_party(party_nid)

        self.ui_display = UnitMenuUI(self.all_player_units)

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.ui_display.move_cursor(Direction.DOWN)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.ui_display.move_cursor(Direction.UP)
        elif 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.ui_display.move_cursor(Direction.LEFT)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.ui_display.move_cursor(Direction.RIGHT)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.change('transition_pop')
        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 2')
            selected = self.ui_display.cursor_hover()
            if isinstance(selected, UnitObject):
                if self.in_level:
                    game.cursor.set_pos(selected.position)
                    game.state.back()
                    game.state.back()
            elif isinstance(selected, Tuple):
                self.ui_display.sort_data(selected)

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        self.ui_display.draw(surf)
        return surf
