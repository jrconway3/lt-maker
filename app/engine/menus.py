from app.constants import TILEX, WINWIDTH, WINHEIGHT
from app.data.database import DB
from app.utilities import utils

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.input_manager import INPUT
from app.engine import engine, image_mods, icons, help_menu, menu_options, \
    item_system, gui, item_funcs
from app.engine.gui import ScrollBar
from app.engine.base_surf import create_base_surf
from app.engine.objects.item import ItemObject
from app.engine.objects.unit import UnitObject
from app.engine.game_state import game

def draw_unit_items(surf, topleft, unit, include_top=False, include_bottom=True, include_face=False, right=True, shimmer=0):
    x, y = topleft
    if include_top:
        white_surf = SPRITES.get('prep_top')
        surf.blit(white_surf, (x - 6, y - white_surf.get_height()))
        icons.draw_chibi(surf, unit.portrait_nid, (x + 3, y - 35))
        FONT['text-white'].blit_center(unit.name, surf, (x + 68, y - 35))
        FONT['text-blue'].blit_right(str(unit.level), surf, (x + 72, y - 19))
        FONT['text-blue'].blit_right(str(unit.exp), surf, (x + 97, y - 19))

    if include_bottom:
        bg_surf = create_base_surf(104, 16 * DB.constants.total_items() + 8, 'menu_bg_base')
        if shimmer:
            img = SPRITES.get('menu_shimmer%d' % shimmer)
            bg_surf.blit(img, (bg_surf.get_width() - img.get_width() - 1, bg_surf.get_height() - img.get_height() - 5))
        bg_surf = image_mods.make_translucent(bg_surf, 0.1)
        # if include_top:
        #     y -= 4
        surf.blit(bg_surf, (x, y))

        if include_face:
            face_image = icons.get_portrait(unit)
            if right:
                face_image = engine.flip_horiz(face_image)
            face_image = face_image.convert_alpha()
            face_image = engine.subsurface(face_image, (0, 0, 96, 76))
            face_image = image_mods.make_translucent(face_image, 0.5)
            left = x + bg_surf.get_width()//2 + 1
            top = y + bg_surf.get_height()//2 - 1 + 2
            engine.blit_center(surf, face_image, (left, top))
        
        # Blit items
        for idx, item in enumerate(unit.nonaccessories):
            item_option = menu_options.ItemOption(idx, item)
            item_option.draw(surf, topleft[0] + 2, topleft[1] + idx * 16 + 4)
        for idx, item in enumerate(unit.accessories):
            item_option = menu_options.ItemOption(idx, item)
            item_option.draw(surf, topleft[0] + 2, topleft[1] + DB.constants.value('num_items') * 16 + idx * 16 + 4)

class Cursor():
    def __init__(self, sprite=None):
        self.counter = 0
        self.anim = [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        if not sprite:
            self.sprite = SPRITES.get('menu_hand')
        else:
            self.sprite = sprite
        self.y_offset = 0

    def update(self):
        self.counter = (self.counter + 1) % len(self.anim)

    def draw(self, surf, x, y):
        surf.blit(self.sprite, (x - 12 + self.anim[self.counter], y + 3 + self.y_offset * 8))
        self.y_offset = 0
        return surf

    def draw_vert(self, surf, x, y):
        surf.blit(self.sprite, (x - 12, y + 3 + self.y_offset * 8 + self.anim[self.counter]))
        self.y_offset = 0
        return surf

class Simple():
    """
    Abstract menu class. Must implement personal draw function
    """

    trade_name_surf = SPRITES.get('trade_name')

    def __init__(self, owner, options, topleft=None, background='menu_bg_base', info=None):
        self.owner = owner
        self.topleft = topleft
        self.background = background

        self.current_index = 0

        self.display_total_uses = False
        self.limit = 1000
        self.hard_limit = False
        self.scroll = 0

        self.options = []
        self.create_options(options, info)

        self.cursor = Cursor()
        self.scroll_bar = ScrollBar()
        self.next_scroll_time = 0
        self.draw_cursor = 1  # 0 No draw, 1 Regular, 2 Draw but no move

        self.takes_input = True
        self.info_flag = False

    def set_limit(self, val):
        self.limit = max(2, val)

    def set_color(self, colors):
        for idx, option in enumerate(self.options):
            option.color = colors[idx]

    def set_ignore(self, ignores):
        for idx, option in enumerate(self.options):
            option.ignore = ignores[idx]
        self.current_index = self.get_first_option().idx

    def set_cursor(self, val):
        self.draw_cursor = val

    def set_hard_limit(self, val):
        self.hard_limit = val
        self.update_options()

    def set_text(self, idx, text):
        self.options[idx].set_text(text)

    def toggle_info(self):
        self.info_flag = not self.info_flag

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            option = menu_options.BasicOption(idx, option)
            if info_descs:
                option.help_box = help_menu.HelpDialog(info_descs[idx])
            self.options.append(option)

    def get_current(self):
        if self.options:
            return self.options[self.current_index].get()

    def get_current_option(self):
        if self.options:
            return self.options[self.current_index]

    def get_first_option(self):
        for option in self.options:
            if not option.ignore:
                return option

    def get_last_option(self):
        for option in reversed(self.options):
            if not option.ignore:
                return option

    def get_current_index(self):
        return self.current_index

    def set_selection(self, option):
        for idx, opt in enumerate(self.options):
            if opt.get() == option:
                self.current_index = idx

    def mouse_move(self, idx):
        if engine.get_time() > self.next_scroll_time:
            did_scroll = self.move_to(idx)
            if did_scroll:
                self.next_scroll_time = engine.get_time() + 50

    def move_to(self, idx):    
        scroll = self.scroll
        idx = utils.clamp(idx, 0, len(self.options) - 1)
        if self.options[idx].ignore:
            return
        while self.current_index < idx:
            self.move_down(True)  # Higher idxs
        while self.current_index > idx:
            self.move_up(True)
        # If we did scroll
        return scroll != self.scroll

    def move_down(self, first_push=True):
        if first_push:
            self.current_index += 1
            if self.current_index > len(self.options) - 1:
                self.current_index = 0
                self.scroll = 0
            elif self.current_index > self.scroll + self.limit - 2:
                self.scroll += 1
            else:
                self.cursor.y_offset -= 1
        else:
            if self.current_index < len(self.options) - 1:
                self.current_index += 1
                if self.current_index > self.scroll + self.limit - 2:
                    self.scroll += 1
                self.cursor.y_offset -= 1
        if self.hard_limit:
            self.scroll = 0
        elif self.limit < len(self.options):
            self.scroll = min(len(self.options) - self.limit, self.scroll)

    def move_up(self, first_push=True):
        if first_push:
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.options) - 1
                self.scroll = self.current_index - self.limit + 1
            elif self.current_index < self.scroll + 1:
                self.scroll -= 1
            else:
                self.cursor.y_offset += 1
        else:
            if self.current_index > 0:
                self.current_index -= 1
                if self.current_index < self.scroll + 1:
                    self.scroll -= 1
                self.cursor.y_offset += 1
        if self.hard_limit:
            self.scroll = 0
        else:
            self.scroll = max(0, self.scroll)

    def update_options(self, options=None):
        if options is not None:
            bare_options = options
        else:
            bare_options = [option.get() for option in self.options]
        self.create_options(bare_options)
        self.current_index = utils.clamp(self.current_index, 0, len(self.options) - 1)

    def get_menu_width(self):
        max_width = max(option.width() for option in self.options)
        return max_width - max_width%8

    def get_menu_height(self):
        return sum(option.height() for option in self.options[:self.limit]) + 8

    def get_topleft(self):
        if not self.topleft:
            if game.cursor.position[0] > TILEX//2 + game.camera.get_x():
                return (8, 8)
            else:
                return (WINWIDTH - self.get_menu_width() - 8, 8)
        elif self.topleft == 'center':
            return (WINWIDTH//2 - self.get_menu_width()//2, WINHEIGHT//2 - self.get_menu_height()//2)
        elif isinstance(self.topleft, tuple):
            if self.topleft[0] == 'center':
                return (WINWIDTH//2 - self.get_menu_width()//2, self.topleft[1])
            elif self.topleft[1] == 'center':
                return (self.topleft[0], WINHEIGHT//2 - self.get_menu_height()//2)
            else:
                return self.topleft
        elif isinstance(self.topleft, Simple):
            if game.cursor.position[0] > TILEX//2 + game.camera.get_x():
                return (24 + self.topleft.get_menu_width(), self.topleft.current_index * 16 + 8)
            else:
                return (WINWIDTH - 40 - self.topleft.get_menu_width(), self.topleft.current_index * 16 + 8)
        else:
            return self.topleft

    def update(self):
        if self.draw_cursor == 1:
            self.cursor.update()

    def draw_scroll_bar(self, surf, topleft):
        right = topleft[0] + self.get_menu_width()
        topright = (right, topleft[1])
        self.scroll_bar.draw(surf, topright, self.scroll, self.limit, len(self.options))

    # For mouse handling
    def get_rects(self):
        return NotImplementedError

    def handle_mouse(self):
        mouse_position = INPUT.get_mouse_position()
        if mouse_position:
            mouse_x, mouse_y = mouse_position
            idxs, option_rects = self.get_rects()
            for idx, option_rect in zip(idxs, option_rects):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.mouse_move(idx)

class Choice(Simple):
    def __init__(self, owner, options, topleft=None, background='menu_bg_base', info=None):
        self.horizontal = False
        super().__init__(owner, options, topleft, background, info)

        self.gem = True
        self.shimmer = 0

        self.stationary_cursor = Cursor()
        self.fake_cursor_idx = None

    def set_horizontal(self, val):
        self.horizontal = val
        self.update_options()

    def set_total_uses(self, val):
        self.display_total_uses = val
        self.update_options()

    def set_fake_cursor(self, val):
        self.fake_cursor_idx = val

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            if isinstance(option, ItemObject):
                if self.display_total_uses:
                    option = menu_options.FullItemOption(idx, option)
                else:
                    option = menu_options.ItemOption(idx, option)
                option.help_box = option.get_help_box()
                self.options.append(option)
            else:
                if self.horizontal:
                    option = menu_options.HorizOption(idx, option)
                else:
                    option = menu_options.BasicOption(idx, option)
                if info_descs:
                    option.help_box = help_menu.HelpDialog(info_descs[idx])
                self.options.append(option)

        if self.hard_limit:
            for num in range(self.limit - len(options)):
                option = menu_options.EmptyOption(len(options) + num)
                self.options.append(option)

    def move_down(self, first_push=True):
        if all(option.ignore for option in self.options):
            return  # Skip

        if first_push:
            super().move_down(True)
            while self.options[self.current_index].ignore:
                self.cursor.y_offset = 0  # Reset y offset
                super().move_down(True)
            if self.get_current_option() == self.get_first_option():
                self.cursor.y_offset = 0
        else:
            if any(not option.ignore for option in self.options[self.current_index+1:]):
                super().move_down(False)
                while self.options[self.current_index].ignore:
                    super().move_down(False)

    def move_up(self, first_push=True):
        if all(option.ignore for option in self.options):
            return  # Skip

        if first_push:
            super().move_up(True)
            while self.options[self.current_index].ignore:
                self.cursor.y_offset = 0
                super().move_up(True)
            if self.get_current_option() == self.get_last_option():
                self.cursor.y_offset = 0

        else:
            if any(not option.ignore for option in self.options[:self.current_index]):
                super().move_up(False)
                while self.options[self.current_index].ignore:
                    super().move_up(False)

    def create_bg_surf(self):
        if self.horizontal:
            width = sum(option.width() + 8 for option in self.options) + 16
            surf = create_base_surf(width, 24, self.background)
            surf = image_mods.make_translucent(surf, .5)
            return surf
        else:
            bg_surf = create_base_surf(self.get_menu_width(), self.get_menu_height(), self.background)
            surf = engine.create_surface((bg_surf.get_width() + 2, bg_surf.get_height() + 4), transparent=True)
            surf.blit(bg_surf, (2, 4))
            if self.gem:
                surf.blit(SPRITES.get('menu_gem_small'), (0, 0))
            if self.shimmer != 0:
                sprite = SPRITES.get('menu_shimmer%d' % self.shimmer)
                surf.blit(sprite, (surf.get_width() - 1 - sprite.get_width(), surf.get_height() - 5 - sprite.get_height()))
            surf = image_mods.make_translucent(surf, .1)
            return surf

    def draw(self, surf):
        if self.horizontal:
            surf = self.horiz_draw(surf)
        else:
            surf = self.vert_draw(surf)
            if self.info_flag:
                surf = self.vert_draw_info(surf)
        return surf

    def vert_draw_info(self, surf):
        help_box = self.options[self.current_index].help_box
        if not help_box:
            return surf
        topleft = self.get_topleft()
        idxs, rects = self.get_rects()
        rect = rects[self.current_index - self.scroll]
        if topleft[0] < WINWIDTH // 2:
            help_box.draw(surf, (rect[0], rect[1]))
        else:
            help_box.draw(surf, (rect[0] + self.get_menu_width(), rect[1]), right=True)
        return surf

    def vert_draw(self, surf):
        topleft = self.get_topleft()

        bg_surf = self.create_bg_surf()
        surf.blit(bg_surf, (topleft[0] - 2, topleft[1] - 4))

        if len(self.options) > self.limit:
            self.draw_scroll_bar(surf, topleft)

        start_index = self.scroll
        end_index = self.scroll + self.limit
        choices = self.options[start_index:end_index]
        running_height = 0
        menu_width = self.get_menu_width()
        if choices:
            for idx, choice in enumerate(choices):
                top = topleft[1] + 4 + running_height
                left = topleft[0]

                if idx + self.scroll == self.current_index and self.takes_input and self.draw_cursor:
                    choice.draw_highlight(surf, left, top, menu_width)
                elif idx + self.scroll == self.fake_cursor_idx:
                    choice.draw_highlight(surf, left, top, menu_width)
                else:
                    choice.draw(surf, left, top)
                if idx + self.scroll == self.fake_cursor_idx:
                    self.stationary_cursor.draw(surf, left, top)
                if idx + self.scroll == self.current_index and self.takes_input and self.draw_cursor:
                    self.cursor.draw(surf, left, top)
                    
                running_height += choice.height()
        else:
            FONT['text-grey'].blit("Nothing", bg_surf, (self.topleft[0] + 16, self.topleft[1] + 4))
        return surf

    def horiz_draw(self, surf):
        topleft = self.get_topleft()

        bg_surf = self.create_bg_surf()
        surf.blit(bg_surf, topleft)

        start_index = self.scroll
        end_index = self.scroll + self.limit
        choices = self.options[start_index:end_index]
        running_width = 0
        if choices:
            for idx, choice in enumerate(choices):
                top = topleft[1] + 4
                left = topleft[0] + running_width
                width = choice.width()

                if idx == self.current_index and self.takes_input and self.draw_cursor:
                    choice.draw_highlight(surf, left, top, width + 14)
                elif idx == self.fake_cursor_idx:
                    choice.draw_highlight(surf, left, top, width + 14)
                else:
                    choice.draw(surf, left, top)
                if idx == self.fake_cursor_idx:
                    self.stationary_cursor.draw(surf, left, top)
                if idx == self.current_index and self.takes_input and self.draw_cursor:
                    self.cursor.draw(surf, left, top)
                    
                running_width += choice.width() + 8
        else:
            FONT['text-grey'].blit("Nothing", bg_surf, (self.topleft[0] + 8, self.topleft[1] + 4))
        return surf

    # For mouse handling
    def get_rects(self):
        if self.horizontal:
            return self.get_horiz_rects()
        else:
            return self.get_vert_rects()

    def get_vert_rects(self):
        topleft = self.get_topleft()
        end_index = self.scroll + self.limit
        choices = self.options[self.scroll:end_index]
        running_height = 0
        idxs, rects = [], []
        for idx, choice in enumerate(choices):
            top = topleft[1] + 4 + running_height
            left = topleft[0]
            rect = (left, top, choice.width(), choice.height())
            rects.append(rect)
            idxs.append(self.scroll + idx)

            running_height += choice.height()
        return idxs, rects

    def get_horiz_rects(self):
        topleft = self.get_topleft()
        choices = self.options
        running_width = 0
        idxs, rects = [], []
        for idx, choice in enumerate(choices):
            top = topleft[1] + 4
            left = topleft[0] + running_width
            rect = (left, top, choice.width(), choice.height())
            rects.append(rect)
            idxs.append(idx)

            running_width += choice.width() + 8
        return idxs, rects

class Inventory(Choice):
    def create_options(self, options, info_desc=None):
        self.options.clear()
        # Assumes all options are Item Objects
        accessories = [option for option in options if item_system.is_accessory(self.owner, option)]
        items = [option for option in options if option not in accessories]
        num_items = DB.constants.value('num_items')
        num_accessories = DB.constants.value('num_accessories')
        # Get items
        for idx, item in enumerate(items):
            option = menu_options.FullItemOption(idx, item)
            option.help_box = option.get_help_box()
            self.options.append(option)
        # Get empty options in the middle
        for num in range(num_items - len(items)):
            option = menu_options.EmptyOption(len(self.options) + num)
            self.options.append(option)
        # Get accessories
        for idx, item in enumerate(accessories):
            option = menu_options.FullItemOption(idx, item)
            option.help_box = option.get_help_box()
            self.options.append(option)
        # Get empty options at the end
        for num in range(num_accessories - len(accessories)):
            option = menu_options.EmptyOption(len(self.options) + num)
            self.options.append(option)

class Shop(Choice):
    def __init__(self, owner, options, topleft=None, disp_value='sell', background='menu_bg_base', info=None):
        super().__init__(owner, options, topleft, background, info)
        self.disp_value = disp_value

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            option = menu_options.ValueItemOption(idx, option, self.disp_value)
            option.help_box = option.get_help_box()
            self.options.append(option)

class Trade(Simple):
    """
    Menu used for trading items between two units
    Built from two choice menus
    """

    def __init__(self, initiator, partner, items1, items2):
        self.owner = initiator
        self.partner = partner

        if len(items1) < DB.constants.total_items():
            items1 = items1[:] + ['']
        if len(items2) < DB.constants.total_items():
            items2 = items2[:] + ['']
        self.menu1 = Choice(self.owner, items1, (11, 68))
        self.menu1.set_limit(DB.constants.total_items())
        self.menu1.set_hard_limit(True)  # Makes hard limit
        self.menu2 = Choice(self.partner, items2 , (125, 68))
        self.menu2.set_limit(DB.constants.total_items())
        self.menu2.set_hard_limit(True)  # Makes hard limit
        self.menu2.set_cursor(0)

        self.selecting_hand = (0, 0)
        self.other_hand = None

        self._selected_option = None

    def selected_option(self):
        return self._selected_option

    def unset_selected_option(self):
        self._selected_option = None
        self.selecting_hand = self.other_hand
        self.other_hand = None
        self.menu1.set_fake_cursor(None)
        self.menu2.set_fake_cursor(None)
        # handle cursor
        if self.selecting_hand[0] == 0:
            self.menu1.move_to(self.selecting_hand[1])
            self.menu1.set_cursor(1)
            self.menu2.set_cursor(0)
        else:
            self.menu2.move_to(self.selecting_hand[1])
            self.menu1.set_cursor(0)
            self.menu2.set_cursor(1)

    def set_selected_option(self):
        self.other_hand = self.selecting_hand
        if self.selecting_hand[0] == 0:
            self._selected_option = self.menu1.options[self.selecting_hand[1]]
            self.selecting_hand = (1, self.selecting_hand[1])
            self.menu2.move_to(self.selecting_hand[1])
            self.menu1.set_fake_cursor(self.other_hand[1])
            self.menu2.set_cursor(1)
            self.menu1.set_cursor(0)
        else:
            self._selected_option = self.menu2.options[self.selecting_hand[1]]
            self.selecting_hand = (0, self.selecting_hand[1])
            self.menu1.move_to(self.selecting_hand[1])
            self.menu2.set_fake_cursor(self.other_hand[1])
            self.menu1.set_cursor(1)
            self.menu2.set_cursor(0)

    def get_current_option(self):
        if self.selecting_hand[0] == 0:
            return self.menu1.options[self.selecting_hand[1]]
        else:
            return self.menu2.options[self.selecting_hand[1]]

    def update_options(self, items1, items2):
        if len(items1) < DB.constants.total_items():
            items1 = items1[:] + ['']
        if len(items2) < DB.constants.total_items():
            items2 = items2[:] + ['']
        self.menu1.update_options(items1)
        self.menu2.update_options(items2)

    def move_down(self, first_push=True):
        old_index = self.selecting_hand[1]
        if self.selecting_hand[0] == 0:
            self.menu1.current_index = self.selecting_hand[1]
            self.menu1.move_down(first_push)
            self.selecting_hand = (0, self.menu1.current_index)
        else:
            self.menu2.current_index = self.selecting_hand[1]
            self.menu2.move_down(first_push)
            self.selecting_hand = (1, self.menu2.current_index)
        return self.selecting_hand[1] != old_index

    def move_up(self, first_push=True):
        old_index = self.selecting_hand[1]
        if self.selecting_hand[0] == 0:
            self.menu1.current_index = self.selecting_hand[1]
            self.menu1.move_up(first_push)
            self.selecting_hand = (0, self.menu1.current_index)
        else:
            self.menu2.current_index = self.selecting_hand[1]
            self.menu2.move_up(first_push)
            self.selecting_hand = (1, self.menu2.current_index)
        return self.selecting_hand[1] != old_index

    def cursor_left(self):
        self.menu1.set_cursor(1)
        self.menu1.cursor.y_offset = 0
        self.menu2.set_cursor(0)

    def move_left(self):
        if self.selecting_hand[0] == 1:
            idx = utils.clamp(self.selecting_hand[1], 0, len([option for option in self.menu1.options if not option.ignore]) - 1)
            self.menu1.move_to(idx)
            self.selecting_hand = (0, self.menu1.current_index)
            self.cursor_left()
            return True
        return False

    def cursor_right(self):
        self.menu2.set_cursor(1)
        self.menu2.cursor.y_offset = 0
        self.menu1.set_cursor(0)

    def move_right(self):
        if self.selecting_hand[0] == 0:
            idx = utils.clamp(self.selecting_hand[1], 0, len([option for option in self.menu2.options if not option.ignore]) - 1)
            self.menu2.move_to(idx)
            self.selecting_hand = (1, self.menu2.current_index)
            self.cursor_right()
            return True
        return False

    def update(self):
        self.menu1.update()
        self.menu2.update()

    def draw(self, surf):
        # Draw trade names
        surf.blit(self.trade_name_surf, (-4, -1))
        surf.blit(self.trade_name_surf, (WINWIDTH - self.trade_name_surf.get_width() + 4, -1))
        FONT['text-white'].blit(self.owner.name, surf, (24 - FONT['text-white'].width(self.owner.name)//2, 0))
        FONT['text-white'].blit(self.partner.name, surf, (WINWIDTH - 24 - FONT['text-white'].width(self.owner.name)//2, 0))

        # Draw Portraits
        # Owner
        owner_surf = engine.create_surface((96, 80), transparent=True)
        icons.draw_portrait(owner_surf, self.owner, (0, 0))
        owner_surf = engine.subsurface(owner_surf, (0, 3, 96, 68))
        owner_surf = engine.flip_horiz(owner_surf)
        surf.blit(owner_surf, (11 + 52 - 48, 0))

        # Partner
        partner_surf = engine.create_surface((96, 80), transparent=True)
        icons.draw_portrait(partner_surf, self.partner, (0, 0))
        partner_surf = engine.subsurface(partner_surf, (0, 3, 96, 68))
        surf.blit(partner_surf, (125 + 52 - 48, 0))

        self.menu1.draw(surf)
        self.menu2.draw(surf)

        return surf

    def handle_mouse(self):
        mouse_position = INPUT.get_mouse_position()
        if mouse_position:
            mouse_x, mouse_y = mouse_position
            idxs1, option_rects1 = self.menu1.get_rects()
            idxs2, option_rects2 = self.menu2.get_rects()
            # Menu1
            for idx, option_rect in zip(idxs1, option_rects1):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.menu1.mouse_move(idx)
                    if self.selecting_hand[0] == 1:
                        self.cursor_left()
                    self.selecting_hand = (0, idx)
            # Menu2
            for idx, option_rect in zip(idxs2, option_rects2):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.menu2.mouse_move(idx)
                    if self.selecting_hand[0] == 0:
                        self.cursor_right()
                    self.selecting_hand = (1, idx)

class Table(Simple):
    def __init__(self, owner, options, layout, topleft=None, background='menu_bg_base', info=None):
        self.mode = None
        super().__init__(owner, options, topleft, background, info)
        
        self.rows, self.columns = layout
        self.limit = self.rows
        self.gem = False
        self.shimmer = 0

        self.stationary_cursor = Cursor()
        self.fake_cursor_idx = None

    def set_mode(self, mode):
        self.mode = mode
        self.update_options()

    def set_fake_cursor(self, val):
        self.fake_cursor_idx = val

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            if isinstance(option, UnitObject):
                option = menu_options.UnitOption(idx, option)
                option.set_mode(self.mode)
            else:
                option = menu_options.BasicOption(idx, option)
            self.options.append(option)

    def mouse_move(self, idx):
        if engine.get_time() > self.next_scroll_time:
            did_scroll = self.move_to(idx)
            if did_scroll:
                self.next_scroll_time = engine.get_time() + 50

    def move_to(self, idx):
        scroll = self.scroll
        idx = utils.clamp(idx, 0, len(self.options) - 1)
        if self.options[idx].ignore:
            return
        while self.current_index < idx:
            self.move_right(True)
        while self.current_index > idx:
            self.move_left(True)
        # If we did scroll
        return scroll != self.scroll

    def _move_down(self, first_push=True):
        if first_push:
            self.current_index += self.columns
            if self.current_index > len(self.options) - 1:
                # If there is an option to the left
                # If odd number of options and we are on the same row as it
                if len(self.options) % self.columns and self.current_index // self.columns == len(self.options) // self.columns:
                    self.current_index = len(self.options) - 1
                else:
                    self.current_index = self.current_index % self.columns
                    self.scroll = 0
            elif self.current_index > (self.scroll + self.limit - 2) * self.columns:
                self.scroll += 1
            else:
                self.cursor.y_offset -= 1
        else:
            if self.current_index < len(self.options) - self.columns:
                self.current_index += self.columns
                if self.current_index > (self.scroll + self.limit - 2) * self.columns:
                    self.scroll += 1
                self.cursor.y_offset -= 1
        if self.limit < len(self.options):
            self.scroll = min(len(self.options) - self.limit, self.scroll)

    def _move_up(self, first_push=True):
        if first_push:
            self.current_index -= self.columns
            if self.current_index < 0:
                column_idx = self.current_index % self.columns
                self.current_index = len(self.options) - 1
                while self.current_index % self.columns != column_idx:
                    self.current_index -= 1
                self.scroll = self.current_index // self.columns - self.limit + 1
            elif self.current_index < self.scroll * self.columns + 1:
                self.scroll -= 1
            else:
                self.cursor.y_offset += 1
        else:
            if self.current_index > 0:
                self.current_index -= self.columns
                if self.current_index < self.scroll * self.columns + 1:
                    self.scroll -= 1
                self.cursor.y_offset += 1
        self.scroll = max(0, self.scroll)

    def _move_left(self, first_push=True):
        if first_push:
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.options) - 1
                self.scroll = self.current_index // self.columns - self.limit + 1
            elif self.current_index < self.scroll * self.columns + 1:
                self.scroll -= 1
            else:
                self.cursor.y_offset += 1
        else:
            if self.current_index > 0:
                self.current_index -= 1
                if self.current_index < self.scroll * self.columns + 1:
                    self.scroll -= 1
                self.cursor.y_offset += 1
        self.scroll = max(0, self.scroll)

    def _move_right(self, first_push=True):
        if first_push:
            self.current_index += 1
            if self.current_index > len(self.options) - 1:
                self.current_index = 0
                self.scroll = 0
            elif self.current_index > (self.scroll + self.limit - 2) * self.columns:
                self.scroll += 1
            else:
                self.cursor.y_offset -= 1
        else:
            if self.current_index < len(self.options) - 1:
                self.current_index += 1
                if self.current_index > (self.scroll + self.limit - 2) * self.columns:
                    self.scroll += 1
                self.cursor.y_offset -= 1
        if self.limit < len(self.options):
            self.scroll = min(len(self.options) - self.limit, self.scroll)

    def move_down(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        if first_push:
            self._move_down(True)
            while self.options[self.current_index].ignore:
                self._move_down(True)

        else:
            if any(not option.ignore for option in self.options[self.current_index + 1:]):
                self._move_down(False)
                while self.options[self.current_index].ignore:
                    self._move_down(False)

        if old_index == self.current_index:
            self.cursor.y_offset = 0
        return old_index != self.current_index

    def move_up(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        if first_push:
            self._move_up(True)
            while self.options[self.current_index].ignore:
                self._move_up(True)

        else:
            if any(not option.ignore for option in self.options[:self.current_index]):
                self._move_up(False)
                while self.options[self.current_index].ignore:
                    self._move_up(False)

        if old_index == self.current_index:
            self.cursor.y_offset = 0
        return old_index != self.current_index

    def move_right(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        if first_push:
            self._move_right(True)
            while self.options[self.current_index].ignore:
                self._move_right(True)

        else:
            if any(not option.ignore for option in self.options[self.current_index + 1:]):
                self._move_right(False)
                while self.options[self.current_index].ignore:
                    self._move_right(False)

        if old_index == self.current_index:
            self.cursor.y_offset = 0
        return old_index != self.current_index

    def move_left(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        if first_push:
            self._move_left(True)
            while self.options[self.current_index].ignore:
                self._move_left(True)

        else:
            if any(not option.ignore for option in self.options[:self.current_index]):
                self._move_left(False)
                while self.options[self.current_index].ignore:
                    self._move_left(False)

        if old_index == self.current_index:
            self.cursor.y_offset = 0
        return old_index != self.current_index

    def get_menu_width(self):
        max_width = max(option.width() for option in self.options)
        total_width = (max_width - max_width%8) * self.columns
        if self.mode in ('unit', 'position'):
            total_width += 32
        return total_width

    def get_menu_height(self):
        max_height = max(option.height() for option in self.options)
        return (max_height - max_height%8) * self.rows + 8

    def create_bg_surf(self):
        bg_surf = create_base_surf(self.get_menu_width(), self.get_menu_height(), self.background)
        surf = engine.create_surface((bg_surf.get_width() + 2, bg_surf.get_height() + 4), transparent=True)
        surf.blit(bg_surf, (2, 4))
        if self.gem:
            surf.blit(SPRITES.get('menu_gem_small'), (0, 0))
        if self.shimmer != 0:
            sprite = SPRITES.get('menu_shimmer%d' % self.shimmer)
            surf.blit(sprite, (surf.get_width() - sprite.get_width() - 1, surf.get_height() - sprite.get_height() - 5))
        surf = image_mods.make_translucent(surf, .1)
        return surf

    def draw(self, surf):
        topleft = self.get_topleft()
        bg_surf = self.create_bg_surf()
        surf.blit(bg_surf, (topleft[0] - 2, topleft[1] - 4))

        if len(self.options) > self.rows * self.columns:
            self.draw_scroll_bar(surf, topleft)

        start_index = self.scroll * self.columns
        end_index = (self.scroll + self.limit) * self.columns
        choices = self.options[start_index:end_index]
        width = max(option.width() for option in self.options)
        height = max(option.height() for option in self.options)
        if choices:
            for idx, choice in enumerate(choices):
                top = topleft[1] + 4 + (idx // self.columns * height)
                left = topleft[0] + (idx % self.columns * width)
                if self.mode in ('unit', 'position'):
                    left += 16

                if idx + (self.scroll * self.columns) == self.current_index and self.takes_input and self.draw_cursor:
                    choice.draw_highlight(surf, left, top, width)
                elif idx + (self.scroll * self.columns) == self.fake_cursor_idx:
                    choice.draw_highlight(surf, left, top, width)
                else:
                    choice.draw(surf, left, top)
                if idx + (self.scroll * self.columns) == self.fake_cursor_idx:
                    self.stationary_cursor.draw(surf, left, top)
                if idx + (self.scroll * self.columns) == self.current_index and self.takes_input and self.draw_cursor:
                    self.cursor.draw(surf, left, top)

        else:
            FONT['text-grey'].blit("Nothing", bg_surf, (topleft[0] + 16, topleft[1] + 4))

    # For mouse handling
    def get_rects(self):
        topleft = self.get_topleft()

        start_index = self.scroll * self.columns
        end_index = (self.scroll + self.limit) * self.columns
        choices = self.options[start_index:end_index]
        width = max(option.width() for option in self.options)
        height = max(option.height() for option in self.options)

        idxs, rects = [], []
        for idx, choice in enumerate(choices):
            top = topleft[1] + 4 + (idx // self.columns * height)
            left = topleft[0] + (idx % self.columns * width)
            if self.mode in ('unit', 'position'):
                left += 16
            rect = (left, top, width, height)
            rects.append(rect)
            idxs.append(start_index + idx)
        return idxs, rects

class Convoy():
    def __init__(self, owner, topleft):
        self.owner = owner  # Unit that's at the convoy
        self.topleft = topleft

        self.order = [w.nid for w in DB.weapons]
        self.build_menus()

        self.selection_index = 0  # 0 is inventory, 1+ is convoy
        self.menu_index = 0  # Position for convoy
        self.locked = False  # Whether you are locked to convoy or inventory

        # Handle arrows
        x, y = self.topleft
        menu_width = 160 if self.disp_value else 120
        self.left_arrow = gui.ScrollArrow('left', (x - 4, y - 14))
        self.right_arrow = gui.ScrollArrow('right', (x + menu_width - 4, y - 14), 0.5)

    def build_menus(self):
        sorted_dict = self.get_sorted_dict()
        self.menus = {}
        for w_type in self.order:
            new_menu = Choice(self.owner, sorted_dict[w_type], self.topleft)
            new_menu.set_limit(7)
            new_menu.set_hard_limit(True)
            new_menu.gem = False
            new_menu.shimmer = 2
            self.menus[w_type] = new_menu

        self.inventory = Inventory(self.owner, self.owner.items, (0, 0))
        self.inventory.gem = False
        self.inventory.shimmer = 2

    def get_sorted_dict(self):
        convoy = game.party.convoy
        all_items = []
        all_items += convoy
        for unit in self.unit_registry.values():
            if not unit.dead and unit.party == game.party.nid:
                items = item_funcs.get_all_tradeable_items(unit)
                all_items += items                

        sorted_dict = {}
        for w_type in self.order:
            sorted_dict[w_type] = [item for item in all_items if item_system.weapon_type(self.unit, item) == w_type] 
        sorted_dict['Consumable'] = [item for item in all_items if item_system.weapon_type(self.unit, item) is None]
        for key, value in sorted_dict.items():
            value.sort(key=lambda item: item_system.special_sort(self.unit, item))
            value.sort(key=lambda item: item.name)
            value.sort(key=lambda item: item_system.sell_price(self.unit, item))

        return sorted_dict

    def update_options(self):
        sorted_dict = self.get_sorted_dict()
        for name, menu in self.menus.items():
            menu.update_options(sorted_dict[name])

    def get_current(self):
        if self.selection_index == 0:
            return self.inventory.get_current()
        else:
            return self.menus[self.order[self.selection_index - 1]].get_current()

    def get_current_index(self):
        if self.selection_index == 0:
            return self.inventory.get_current_index()
        else:
            return self.menus[self.order[self.selection_index - 1]].get_current_index()

    def get_context(self):
        if self.selection_index == 0:
            return 'inventory'
        else:
            return 'convoy'

    def move_to_inventory(self):
        self.selection_index = 0
        self.locked = True

    def move_to_convoy(self):
        self.selection_index = self.menu_index + 1
        self.locked = True

    def unlock(self):
        self.locked = False

    def move_down(self, first_push=True):
        if self.selection_index == 0:
            self.inventory.move_down(first_push)
        else:
            self.menus[self.order[self.selection_index - 1]].move_down(first_push)

    def move_up(self, first_push=True):
        if self.selection_index == 0:
            self.inventory.move_up(first_push)
        else:
            self.menus[self.order[self.selection_index - 1]].move_up(first_push)

    def move_left(self, first_push=True):
        if self.selection_index == 0:
            if self.locked:
                return
            if first_push:
                self.selection_index = len(self.order)
                self.menu_index = len(self.order) - 1
        elif self.selection_index == 1:
            if self.locked:
                self.selection_index = len(self.order)
                self.menu_index = len(self.order) - 1
            else:
                self.selection_index = 0
        else:
            self.selection_index -= 1
            self.menu_index = self.selection_index - 1
            self.left_arrow.pulse()

    def move_right(self, first_push=True):
        if self.selection_index == 0:
            if self.locked:
                return
            if first_push:
                self.selection_index = 1
                self.menu_index = 0
        elif self.selection_index == len(self.order):
            if self.locked:
                self.selection_index = 1
                self.menu_index = 0
            else:
                self.selection_index = 0
        else:
            self.selection_index += 1
            self.menu_index = self.selection_index - 1
            self.right_arrow.pulse()

    def toggle_info(self):
        if self.selection_index == 0:
            self.inventory.toggle_info()
        else:
            self.menus[self.order[self.selection_index - 1]].toggle_info()

    def set_take_input(self, val):
        self.inventory.takes_input = val
        for menu in self.menus.values():
            menu.takes_input = val

    def update(self):
        self.menus[self.order[self.menu_index]].update()
        if self.inventory:
            self.inventory.update()

    def draw(self, surf):
        self.menus[self.order[self.menu_index]].draw(surf)
        if self.inventory:
            self.inventory.draw(surf)

        # Draw item icons
        dist = 120//len(self.order) - 1
        for idx, weapon_nid in enumerate(self.order):
            if idx == self.selection_index - 1:
                pass
            else:
                weapon_type = DB.weapons.get(weapon_nid)
                topleft = self.topleft[0] + (len(self.order) - 1 - idx) * dist + 4, self.topleft[1] - 14
                icons.draw_weapon(surf, weapon_type, topleft, gray=True)
        for idx, weapon_nid in enumerate(self.order):
            if idx == self.selection_index - 1:
                weapon_type = DB.weapons.get(weapon_nid)
                icons.draw_weapon(surf, weapon_type, topleft)
                surf.blit(SPRITES.get('weapon_shine'), (self.topleft[0] + idx * dist + 4, self.topelft[1] - 14))
                
        self.left_arrow.draw(surf)
        self.right_arrow.draw(surf)
        return surf

class Market(Convoy):
    def __init__(self, owner, options, topleft, disp_value=None):
        self.disp_value = disp_value
        self.options = options
        super().__init__(owner, topleft)
        self.selection_index = 1
        self.menu_index = 0
        self.inventory = None

    def build_menus(self):
        sorted_dict = self.get_sorted_dict()
        self.menus = {}
        for w_type in self.order:
            new_menu = Shop(self.owner, sorted_dict[w_type], self.topelft, self.disp_value)
            new_menu.set_limit(7)
            new_menu.set_hard_limit(True)
            new_menu.gem = False
            new_menu.shimmer = 2
            self.menus[w_type] = new_menu

    def get_sorted_dict(self):
        if self.options:
            all_items = self.options
        else:
            convoy = game.party.convoy
            all_items = []
            all_items += convoy
            for unit in self.unit_registry.values():
                if not unit.dead and unit.party == game.party.nid:
                    items = item_funcs.get_all_tradeable_items(unit)
                    all_items += items 
        
        sorted_dict = {}
        for w_type in self.order:
            sorted_dict[w_type] = [item for item in all_items if item_system.weapon_type(self.unit, item) == w_type] 
        sorted_dict['Consumable'] = [item for item in all_items if item_system.weapon_type(self.unit, item) is None]
        for key, value in sorted_dict.items():
            value.sort(key=lambda item: item_system.special_sort(self.unit, item))
            value.sort(key=lambda item: item.name)
            value.sort(key=lambda item: item_system.sell_price(self.unit, item))

        return sorted_dict

    def get_current(self):
        return self.menus[self.order[self.selection_index - 1]].get_current()

    def get_current_index(self):
        return self.menus[self.order[self.selection_index - 1]].get_current_index()

    def get_context(self):
        return 'convoy'

    def move_down(self, first_push=True):
        self.menus[self.order[self.selection_index - 1]].move_down(first_push)

    def move_up(self, first_push=True):
        self.menus[self.order[self.selection_index - 1]].move_up(first_push)

    def move_left(self, first_push=True):
        if self.selection_index == 1:
            if first_push:
                self.selection_index = len(self.order)
                self.menu_index = len(self.order) - 1
            else:
                self.selection_index = 1
        else:
            self.selection_index -= 1
            self.menu_index = self.selection_index - 1
            self.left_arrow.pulse()

    def move_right(self, first_push=True):
        if self.selection_index == len(self.order):
            if first_push:
                self.selection_index = 1
                self.menu_index = 0
            else:
                self.selection_index = len(self.order)
        else:
            self.selection_index += 1
            self.menu_index = self.selection_index - 1
            self.right_arrow.pulse()

    def toggle_info(self):
        self.menus[self.order[self.selection_index - 1]].toggle_info()

    def set_take_input(self, val):
        for menu in self.menus.values():
            menu.takes_input = val

class Main(Simple):
    def __init__(self, options, option_bg):
        self.limit = 1000
        self.hard_limit = False
        self.scroll = 0

        self.cursor1 = Cursor(SPRITES.get('cursor_dragon'))
        self.cursor2 = Cursor(engine.flip_horiz(SPRITES.get('cursor_dragon')))
        self.next_scroll_time = 0
        self.option_bg = option_bg

        self.options = []
        self.options = self.create_options(options)
        self.current_index = 0

        self.center = WINWIDTH//2, WINHEIGHT//2

    @property
    def cursor(self):
        return self.cursor1

    def create_options(self, options):
        self.options.clear()
        for idx, option in enumerate(options):
            option = menu_options.TitleOption(idx, option, self.option_bg)
            self.options.append(option)
        return self.options

    def update(self):
        self.cursor1.update()
        self.cursor2.update()

    def draw(self, surf, center=(WINWIDTH//2, WINHEIGHT//2), show_cursor=True):
        self.center = center
        num_options = len(self.options)
        for idx, option in enumerate(self.options):
            top = center[1] - (num_options/2.0 - idx) * (option.height() + 1)
            if self.current_index == idx:
                option.draw_highlight(surf, center[0], top)
            else:
                option.draw(surf, center[0], top)
                
        if show_cursor:
            height = center[1] - 12 - (num_options/2.0 - self.current_index) * (option.height() + 1)
            self.cursor1.draw_vert(surf, center[0] - option.width()//2 - 8 - 8, height)
            self.cursor2.draw_vert(surf, center[0] + option.width()//2 - 8 + 8, height)

    def get_rects(self):
        idxs, rects = [], []
        num_options = len(self.options)
        for idx, option in enumerate(self.options):
            top = self.center[1] - (num_options/2.0 - idx) * (option.height() + 1)
            left = self.center[0] - option.width()//2
            rect = (left, top, option.width(), option.height())
            rects.append(rect)
            idxs.append(self.scroll + idx)
        return idxs, rects

class ChapterSelect(Main):
    def __init__(self, options, colors):
        self.colors = colors
        super().__init__(options, 'chapter_select')
        self.use_rel_y = len(options) > 3
        self.rel_pos_y = 0

    def set_color(self, idx, color):
        self.colors[idx] = color

    def set_colors(self, colors):
        self.colors = colors

    def create_options(self, options):
        self.options.clear()
        for idx, option in enumerate(options):
            option = menu_options.ChapterSelectOption(idx, option, self.option_bg, self.colors[idx])
            self.options.append(option)
        return self.options

    def move_down(self, first_push=True):
        super().move_down(first_push)
        if self.use_rel_y:
            self.rel_pos_y -= 30

    def move_up(self, first_push=True):
        super().move_up(first_push)
        if self.use_rel_y:
            self.rel_pos_y += 30

    def update(self):
        super().update()
        if self.use_rel_y:
            if self.rel_pos_y > 0:
                self.rel_pos_y = max(0, self.rel_pos_y - 4)
            elif self.rel_pos_y < 0:
                self.rel_pos_y = min(0, self.rel_pos_y + 4)

    def draw(self, surf, center=(WINWIDTH//2, WINHEIGHT//2), show_cursor=True, flicker=False):
        self.center = center
        num_options = len(self.options)
        start_index = max(0, self.current_index - 3)
        for idx, option in enumerate(self.options[start_index:self.current_index + 3], start_index):
            diff = idx - self.current_index
            if self.use_rel_y:
                top = center[1] + diff * (option.height() + 1) + self.rel_pos_y
            else:
                top = center[1] + idx * (option.height() + 1) - (num_options * (option.height() + 1)//2)
            if self.current_index == idx:
                if flicker:
                    option.draw_flicker(surf, center[0], top)
                else:
                    option.draw_highlight(surf, center[0], top)
            else:
                option.draw(surf, center[0], top)
                
        if show_cursor:
            height = center[1] - 12 - (num_options/2.0 - self.current_index) * (option.height() + 1)
            self.cursor1.draw_vert(surf, center[0] - option.width()//2 - 8 - 8, height)
            self.cursor2.draw_vert(surf, center[0] + option.width()//2 - 8 + 8, height)

    def get_rects(self):
        idxs, rects = [], []
        num_options = len(self.options)
        start_index = max(0, self.current_index - 3)
        for idx, option in enumerate(self.options[start_index:self.current_index + 3], start_index):
            diff = idx - self.current_index
            if self.use_rel_y:
                top = self.center[1] + diff * (option.height() + 1) + self.rel_pos_y
            else:
                top = self.center[1] + idx * (option.height() + 1) - (num_options * (option.height() + 1)//2)
            left = self.center[0] - option.width()//2
            rect = (left, top, option.width(), option.height())
            rects.append(rect)
            idxs.append(self.scroll + idx)
        return idxs, rects
