from app.data.constants import TILEX, WINWIDTH, WINHEIGHT
from app.data.database import DB
from app import utilities
from app.engine.sprites import SPRITES, FONT

from app.engine import engine, image_mods, icons
from app.engine.base_surf import create_base_surf
from app.engine.game_state import game

class BasicOption():
    def __init__(self, idx, text):
        self.idx = idx
        self.text = text
        self.help_box = None
        self.color = 'text_width'
        self.ignore = False

    def get(self):
        return self.text

    def width(self):
        return FONT[self.color].size(self.text)[0] + 24

    def height(self):
        return 16

    def draw(self, surf, x, y):
        font = FONT[self.color]
        font.blit(self.text, surf, (x + 6, y))

    def draw_highlight(self, surf, x, y, menu_width):
        highlight_surf = SPRITES.get('menu_highlight')
        width = highlight_surf.get_width()
        for slot in range((menu_width - 10)//width):
            left = x + 5 + slot*width
            top = y + 9
            surf.blit(highlight_surf, (left, top))
        return surf

class ItemOption(BasicOption):
    def __init__(self, idx, item):
        self.idx = idx
        self.item = item
        self.help_box = None
        self.color = 'text_grey'
        self.ignore = False

    def get(self):
        return self.item

    def width(self):
        return 104

    def height(self):
        return 16

    def get_color(self):
        owner = game.get_unit(self.item.owner)
        if self.color:
            main_font = self.color
            uses_font = self.color
            if main_font == 'text_white':
                uses_font = 'text_blue'
        elif owner.can_wield(self.item):
            main_font = 'text_white'
            uses_font = 'text_blue'
        return main_font, uses_font

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
    def __init__(self):
        self.counter = 0
        self.anim = [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        self.sprite = SPRITES.get('menu_hand')
        self.y_offset = 0

    def update(self):
        self.counter = (self.counter + 1) % len(self.anim)

    def draw(self, surf, x, y):
        surf.blit(self.sprite, (x - 12 + self.anim[self.counter], y + 3 + self.y_offset * 8))
        self.y_offset = 0
        return surf

class Simple():
    """
    Abstract menu class. Must implement personal draw function
    """
    def __init__(self, owner, options, topleft=None, background='menu_bg_base'):
        self.owner = owner
        self.topleft = topleft
        self.background = background

        self.current_index = 0

        self.options = []
        self.create_options(options)

        self.cursor = Cursor()

        self.limit = 1000
        self.scroll = 0

        self.takes_input = True

    def set_limit(self, val):
        self.limit = max(2, val)

    def set_color(self, colors):
        for idx, option in enumerate(self.options):
            option.color = colors[idx]

    def set_ignore(self, ignores):
        for idx, option in enumerate(self.options):
            option.ignore = ignores[idx]

    def create_options(self, options):
        self.options.clear()
        for idx, option in enumerate(options):
            self.options.append(BasicOption(idx, option))

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
        if self.limit < len(self.options):
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
        self.scroll = max(0, self.scroll)

    def update_options(self, options):
        self.create_items(options)
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
        self.cursor.update()

class Choice(Simple):
    def __init__(self, owner, options, topleft=None, background='menu_bg_base'):
        super().__init__(owner, options, topleft, background)

        self.horizontal = False
        self.display_total_uses = False
        self.gem = True
        self.shimmer = 0

    def set_horizontal(self, val):
        self.horizontal = val

    def set_total_uses(self, val):
        self.display_total_uses = val
        self.update_options()

    def create_options(self, options):
        self.options.clear()
        for idx, option in enumerate(options):
            if isinstance(option, items.Item):
                if self.display_total_uses:
                    self.options.append(FullItemOption(idx, option))
                else:
                    self.options.append(ItemOption(idx, option))
            else:
                self.options.append(BasicOption(idx, option))

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
            return self.horiz_draw(surf)
        else:
            return self.vert_draw(surf)

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

                if idx == self.current_index and self.takes_input:
                    choice.draw_highlight(surf, left, top, menu_width)
                choice.draw(surf, left, top)
                if idx == self.current_index and self.takes_input:
                    self.cursor.draw(surf, left, top)
                    
                running_height += choice.height()
        else:
            FONT['text_grey'].blit("Nothing", bg_surf, (self.topleft[0] + 16, self.topleft[1] + 4))
        return surf

    def horiz_draw(self, surf):
        return surf
