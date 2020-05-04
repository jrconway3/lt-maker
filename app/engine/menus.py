import math

from app.data.constants import TILEX, WINWIDTH, WINHEIGHT
from app.data import items
from app.data.database import DB
from app import utilities
from app.engine.sprites import SPRITES, FONT

from app.engine import engine, image_mods, icons, help_menu, text_funcs
from app.engine.base_surf import create_base_surf
from app.engine.game_state import game

class EmptyOption():
    def __init__(self, idx):
        self.idx = idx
        self.help_box = None
        self.color = None
        self.ignore = False

    def get(self):
        return None

    def width(self):
        return 104

    def height(self):
        return 16

    def draw(self, surf, x, y):
        pass

    def draw_highlight(self, surf, x, y, menu_width):
        highlight_surf = SPRITES.get('menu_highlight')
        width = highlight_surf.get_width()
        for slot in range((menu_width - 10)//width):
            left = x + 5 + slot*width
            top = y + 9
            surf.blit(highlight_surf, (left, top))
        return surf

class BasicOption():
    def __init__(self, idx, text):
        self.idx = idx
        self.text = text
        self.display_text = text_funcs.translate(text)
        self.help_box = None
        self.color = 'text_white'
        self.ignore = False

    def get(self):
        return self.text

    def width(self):
        return FONT[self.color].size(self.display_text)[0] + 24

    def height(self):
        return 16

    def draw(self, surf, x, y):
        font = FONT[self.color]
        font.blit(self.display_text, surf, (x + 6, y))

    def draw_highlight(self, surf, x, y, menu_width):
        highlight_surf = SPRITES.get('menu_highlight')
        width = highlight_surf.get_width()
        for slot in range((menu_width - 10)//width):
            left = x + 5 + slot*width
            top = y + 9
            surf.blit(highlight_surf, (left, top))
        return surf

class TitleOption():
    def __init__(self, idx, text, option_bg_name):
        self.idx = idx
        self.text = text
        self.display_text = text_funcs.translate(text)
        self.option_bg_name = option_bg_name

        self.color = 'chapter_grey'

    def get(self):
        return self.text

    def width(self):
        return SPRITES.get(self.option_bg_name).get_width()

    def height(self):
        return SPRITES.get(self.option_bg_name).get_height()

    def draw_text(self, surf, x, y):
        font = FONT[self.color]

        text = self.display_text
        text_size = font.size(text)
        position = (x - text_size[0]//2, y - text_size[1]//2)

        # Handle outline
        t = math.sin(math.radians((engine.get_time()//10) % 180))
        color_transition = image_mods.blend_colors((192, 248, 248), (56, 48, 40), t)
        outline_surf = engine.create_surface((text_size[0] + 4, text_size[1] + 2), transparent=True)
        font.blit(text, outline_surf, (1, 0))
        font.blit(text, outline_surf, (0, 1))
        font.blit(text, outline_surf, (1, 2))
        font.blit(text, outline_surf, (2, 1))
        outline_surf = image_mods.change_color(outline_surf, color_transition)

        surf.blit(outline_surf, (position[0] - 1, position[1] - 1))
        font.blit(text, surf, position)

    def draw(self, surf, x, y):
        left = x - self.width()//2
        surf.blit(SPRITES.get(self.option_bg_name), (left, y))

        self.draw_text(surf, left + self.width()//2, y + self.height()//2 + 1)

    def draw_highlight(self, surf, x, y):
        left = x - self.width()//2
        surf.blit(SPRITES.get(self.option_bg_name + '_highlight'), (left, y))

        self.draw_text(surf, left + self.width()//2, y + self.height()//2 + 1)

class ItemOption(BasicOption):
    def __init__(self, idx, item):
        self.idx = idx
        self.item = item
        self.help_box = None
        self.color = None
        self.ignore = False

    def get(self):
        return self.item

    def width(self):
        return 104

    def height(self):
        return 16

    def get_color(self):
        owner = game.get_unit(self.item.owner_nid)
        main_font = 'text_grey'
        uses_font = 'text_grey'
        if self.color:
            main_font = self.color
            uses_font = self.color
            if main_font == 'text_white':
                uses_font = 'text_blue'
        elif owner and owner.can_wield(self.item):
            main_font = 'text_white'
            uses_font = 'text_blue'
        return main_font, uses_font

    def get_help_box(self):
        if self.item.weapon or self.item.spell:
            return help_menu.ItemHelpDialog(self.item)
        else:
            return help_menu.HelpDialog(self.item.desc)

    def draw(self, surf, x, y):
        main_font = 'text_grey'
        uses_font = 'text_grey'
        icons.draw_item(surf, self.item, (x + 2, y))
        main_font, uses_font = self.get_color()
        FONT[main_font].blit(self.item.name, surf, (x + 20, y))
        uses_string = '--'
        if self.item.uses:
            uses_string = str(self.item.uses.value)
        elif self.item.c_uses:
            uses_string = str(self.item.c_uses.value)
        left = x + self.width() - 4 - FONT[uses_font].size(uses_string)[0] - 5
        FONT[uses_font].blit(uses_string, surf, (left, y))

class FullItemOption(ItemOption):
    def width(self):
        return 120

    def draw(self, surf, x, y):
        main_font = 'text_grey'
        uses_font = 'text_grey'
        icons.draw_item(surf, self.item, (x + 2, y))
        main_font, uses_font = self.get_color()
        FONT[main_font].blit(self.item.name, surf, (x + 20, y))
        uses_string = '--/--'
        if self.item.uses:
            prefab = DB.items.get(self.item.nid)
            total = prefab.uses.value
            uses_string = str(self.item.uses.value) + '/' + str(total)
        elif self.item.c_uses:
            prefab = DB.items.get(self.item.nid)
            total = prefab.uses.value
            uses_string = str(self.item.c_uses.value) + '/' + str(total)
        left = x + self.width() - 4 - FONT[uses_font].size(uses_string)[0] - 5
        FONT[uses_font].blit(uses_string, surf, (left, y))

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

    def set_cursor(self, val):
        self.draw_cursor = val

    def set_hard_limit(self, val):
        self.hard_limit = val
        self.update_options()

    def toggle_info(self):
        self.info_flag = not self.info_flag

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            option = BasicOption(idx, option)
            if info_descs:
                option.help_box = help_menu.HelpDialog(info_descs[idx])
            self.options.append(option)

    def get_current(self):
        return self.options[self.current_index].get()

    def get_current_index(self):
        return self.current_index

    def set_selection(self, option):
        for idx, opt in enumerate(self.options):
            if opt.get() == option:
                self.current_index = idx

    def move_to(self, idx):
        self.current_index = idx

    def move_down(self, first_push=True):
        if first_push:
            self.current_index += 1
            if self.current_index > self.scroll + self.limit - 2:
                self.scroll += 1
            if self.current_index > len(self.options) - 1:
                self.current_index = 0
                self.scroll = 0
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
            if self.current_index < self.scroll + 1:
                self.scroll -=1
            if self.current_index < 0:
                self.current_index = len(self.options) - 1
                self.scroll = self.current_index - self.limit + 1
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
        self.current_index = utilities.clamp(self.current_index, 0, len(self.options) - 1)

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

    # For mouse handling
    def get_rects(self):
        return NotImplementedError

    def handle_mouse(self):
        mouse_position = game.input_manager.get_mouse_position()
        if mouse_position:
            mouse_x, mouse_y = mouse_position
            idxs, option_rects = self.get_rects()
            for idx, option_rect in zip(idxs, option_rects):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.move_to(idx)

class Choice(Simple):
    def __init__(self, owner, options, topleft=None, background='menu_bg_base', info=None):
        super().__init__(owner, options, topleft, background, info)

        self.horizontal = False

        self.gem = True
        self.shimmer = 0

        self.stationary_cursor = Cursor()
        self.fake_cursor_idx = None

    def set_horizontal(self, val):
        self.horizontal = val

    def set_total_uses(self, val):
        self.display_total_uses = val
        self.update_options()

    def set_fake_cursor(self, val):
        self.fake_cursor_idx = val

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            if isinstance(option, items.Item):
                if self.display_total_uses:
                    option = FullItemOption(idx, option)
                else:
                    option = ItemOption(idx, option)
                option.help_box = option.get_help_box()
                self.options.append(option)
            else:
                option = BasicOption(idx, option)
                if info_descs:
                    option.help_box = help_menu.HelpDialog(info_descs[idx])
                self.options.append(option)

        if self.hard_limit:
            for num in range(self.limit - len(options)):
                option = EmptyOption(len(options) + num)
                self.options.append(option)

    def move_down(self, first_push=True):
        if all(option.ignore for option in self.options):
            return  # Skip

        if first_push:
            super().move_down(True)
            while self.options[self.current_index].ignore:
                super().move_down(True)

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
                super().move_up(True)

        else:
            if any(not option.ignore for option in self.options[:self.current_index]):
                super().move_up(False)
                while self.options[self.current_index].ignore:
                    super().move_up(False)

    def create_bg_surf(self):
        if self.horizontal:
            width = sum(option.width() for option in self.options) + 16
            return create_base_surf(width, 24, self.background)
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
            self.draw_scroll_bar(surf)

        start_index = self.scroll
        end_index = self.scroll + self.limit
        choices = self.options[start_index:end_index]
        running_height = 0
        menu_width = self.get_menu_width()
        if choices:
            for idx, choice in enumerate(choices):
                top = topleft[1] + 4 + running_height
                left = topleft[0]

                if idx == self.current_index and self.takes_input and self.draw_cursor:
                    choice.draw_highlight(surf, left, top, menu_width)
                if idx == self.fake_cursor_idx:
                    choice.draw_highlight(surf, left, top, menu_width)
                choice.draw(surf, left, top)
                if idx == self.fake_cursor_idx:
                    self.stationary_cursor.draw(surf, left, top)
                if idx == self.current_index and self.takes_input and self.draw_cursor:
                    self.cursor.draw(surf, left, top)
                    
                running_height += choice.height()
        else:
            FONT['text_grey'].blit("Nothing", bg_surf, (self.topleft[0] + 16, self.topleft[1] + 4))
        return surf

    def horiz_draw(self, surf):
        return surf

    def draw_scroll_bar(self, surf):
        return surf

    # For mouse handling
    def get_rects(self):
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

class Trade(Simple):
    """
    Menu used for trading items between two units
    Built from two choice menus
    """

    def __init__(self, initiator, partner, items1, items2):
        self.owner = initiator
        self.partner = partner

        self.menu1 = Choice(self.owner, items1, (11, 68))
        self.menu1.set_limit(DB.constants.max_items())
        self.menu1.set_hard_limit(True)  # Makes hard limit
        self.menu2 = Choice(self.partner, items2, (125, 68))
        self.menu2.set_limit(DB.constants.max_items())
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
        self.menu1.update_options(items1)
        self.menu2.update_options(items2)

    def move_down(self, first_push=True):
        if self.selecting_hand[0] == 0:
            self.menu1.current_index = self.selecting_hand[1]
            self.menu1.move_down(first_push)
            self.selecting_hand = (0, self.menu1.current_index)
        else:
            self.menu2.current_index = self.selecting_hand[1]
            self.menu2.move_down(first_push)
            self.selecting_hand = (1, self.menu2.current_index)

    def move_up(self, first_push=True):
        if self.selecting_hand[0] == 0:
            self.menu1.current_index = self.selecting_hand[1]
            self.menu1.move_up(first_push)
            self.selecting_hand = (0, self.menu1.current_index)
        else:
            self.menu2.current_index = self.selecting_hand[1]
            self.menu2.move_up(first_push)
            self.selecting_hand = (1, self.menu2.current_index)

    def cursor_left(self):
        self.menu1.set_cursor(1)
        self.menu2.set_cursor(0)

    def move_left(self):
        if self.selecting_hand[0] == 1:
            self.selecting_hand = (0, self.selecting_hand[1])
            self.menu1.move_to(self.selecting_hand[1])
            self.cursor_left()
            return True
        return False

    def cursor_right(self):
        self.menu2.set_cursor(1)
        self.menu1.set_cursor(0)

    def move_right(self):
        if self.selecting_hand[0] == 0:
            self.selecting_hand = (1, self.selecting_hand[1])
            self.menu2.move_to(self.selecting_hand[1])
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
        FONT['text_white'].blit(self.owner.name, surf, (24 - FONT['text_white'].width(self.owner.name)//2, 0))
        FONT['text_white'].blit(self.partner.name, surf, (WINWIDTH - 24 - FONT['text_white'].width(self.owner.name)//2, 0))

        # Draw Portraits
        # Owner
        owner_surf = engine.create_surface((96, 80), transparent=True)
        icons.draw_portrait(owner_surf, self.owner.nid, (0, 0))
        owner_surf = engine.subsurface(owner_surf, (0, 3, 96, 68))
        owner_surf = engine.flip_horiz(owner_surf)
        surf.blit(owner_surf, (11 + 52 - 48, 0))

        # Partner
        partner_surf = engine.create_surface((96, 80), transparent=True)
        icons.draw_portrait(partner_surf, self.partner.nid, (0, 0))
        partner_surf = engine.subsurface(partner_surf, (0, 3, 96, 68))
        surf.blit(partner_surf, (125 + 52 - 48, 0))

        self.menu1.draw(surf)
        self.menu2.draw(surf)

        return surf

    def handle_mouse(self):
        mouse_position = game.input_manager.get_mouse_position()
        if mouse_position:
            mouse_x, mouse_y = mouse_position
            idxs1, option_rects1 = self.menu1.get_rects()
            idxs2, option_rects2 = self.menu2.get_rects()
            # Menu1
            for idx, option_rect in zip(idxs1, option_rects1):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.menu1.move_to(idx)
                    if self.selecting_hand[0] == 1:
                        self.cursor_left()
                    self.selecting_hand = (0, idx)
            # Menu2
            for idx, option_rect in zip(idxs2, option_rects2):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.menu2.move_to(idx)
                    if self.selecting_hand[0] == 0:
                        self.cursor_right()
                    self.selecting_hand = (1, idx)

class Main(Simple):
    def __init__(self, options, option_bg):
        self.limit = 1000
        self.hard_limit = False
        self.scroll = 0

        self.cursor1 = Cursor(SPRITES.get('cursor_dragon'))
        self.cursor2 = Cursor(engine.flip_horiz(SPRITES.get('cursor_dragon')))
        self.option_bg = option_bg

        self.options = []
        self.options = self.create_options(options)
        self.current_index = 0

        self.center = WINWIDTH//2, WINHEIGHT//2

    def create_options(self, options):
        self.options.clear()
        for idx, option in enumerate(options):
            option = TitleOption(idx, option, self.option_bg)
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
            top = self.center[1] - (num_options/2.0 - idx) * (option.get_height() + 1)
            left = self.center[0] - option.get_width()//2
            rect = (left, top, option.width(), option.height())
            rects.append(rect)
            idxs.append(self.scroll + idx)
        return idxs, rects

class ChapterSelect(Main):
    def __init__(self, options, colors):
        super().__init__(options, 'chapter_select')
        self.colors = colors
        self.use_rel_y = len(options) > 3
        self.rel_pos_y = 0

    def set_color(self, idx, color):
        self.colors[idx] = color

    def create_options(self, options):
        self.options.clear()
        for idx, option in enumerate(options):
            option = TitleOption(idx, option, self.option_bg)
            self.options.append(option)

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

    def draw(self, surf, center=(WINWIDTH//2, WINHEIGHT//2), show_cursor=True):
        self.center = center
        num_options = len(self.options)
        start_index = max(0, self.current_index - 3)
        for idx, option in enumerate(self.options[start_index:self.current_index + 3], start_index):
            diff = idx - self.current_index
            if self.use_rel_y:
                top = center[1] + diff * (option.height() + 1) + self.rel_pos_y
            else:
                top = center[1] + idx * (option.height() + 1) - ((num_options - 1) * 15 - 4)
            if self.current_index == idx:
                option.draw_highlight(surf, center[0], top)
            else:
                option.draw(surf, center[0], top)
                
        if show_cursor:
            height = center[1] - 12 - (num_options/2.0 - self.current_index) * (option.height() + 1)
            self.cursor1.draw_vert(surf, (center[0] - option.width()//2 - 8 - 8, height))
            self.cursor2.draw_vert(surf, (center[0] + option.width()//2 - 8 + 8, height))

    def get_rects(self):
        idxs, rects = [], []
        num_options = len(self.options)
        start_index = max(0, self.current_index - 3)
        for idx, option in enumerate(self.options[start_index:self.current_index + 3], start_index):
            diff = idx - self.current_index
            if self.use_rel_y:
                top = self.center[1] + diff * (option.height() + 1) + self.rel_pos_y
            else:
                top = self.center[1] + idx * (option.height() + 1) - ((num_options - 1) * 15 - 4)
            left = self.center[0] - option.get_width()//2
            rect = (left, top, option.width(), option.height())
            rects.append(rect)
            idxs.append(self.scroll + idx)
        return idxs, rects
