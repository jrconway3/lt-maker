from app.engine import config as cf
from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine import text_funcs, menus, image_mods, \
    gui_objects, base_surf, help_menu

class ControlOption(menus.BasicOption):
    def __init__(self, idx, name, icon):
        self.idx = idx
        self.name = name
        self.display_name = text_funcs.translate(name)
        self.icon = icon
        self.help_box = None

    def get(self):
        return self.name

    def width(self):
        return 216

    def height(self):
        return 16

    def draw(self, surf, x, y, active=False):
        name_font = 'text_white'
        key_font = 'text_blue'
        surf.blit(self.icon, (x + 16, y))
        FONT[name_font].blit(self.display_name, surf, (x + 56, y))
        FONT[key_font].blit(cf.SETTINGS[self.name], surf, (x + 128, y))

class ConfigOption(menus.BasicOption):
    def __init__(self, idx, name, values, icon):
        self.idx = idx
        self.name = name
        self.display_name = text_funcs.translate(name)
        self.icon = icon
        self.help_box = None
        self.values = values

    def get(self):
        return self.name

    def width(self):
        return 216

    def height(self):
        return 16

class SliderOption(ConfigOption):
    def __init__(self, idx, name, values, icon):
        super().__init__(idx, name, values, icon)
        self.counter = 0
        self.anim = [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

    def draw(self, surf, x, y, active=False):
        self.counter = (self.counter + 1) % len(self.anim)
        surf.blit(self.icon, (x + 16, y))
        name_font = 'text_white'
        FONT[name_font].blit(self.display_name, surf, (x + 32, y))
        slider_bar = SPRITES.get('health_bar_bg')
        if not slider_bar:
            return
        surf.blit(slider_bar, (x + 112, y + 4))
        slider_cursor = SPRITES.get('waiting_cursor')
        if not slider_cursor:
            return
        value = cf.SETTINGS[self.name]
        if value in self.values:
            slider_fraction = self.values.index(value) / float(len(self.values) - 1)
        else:
            slider_fraction = value - self.values[0] / float(self.values[-1] - self.values[0])
        offset = slider_fraction * (slider_bar.get_width() - 6)
        if active:
            slider_bop = self.anim[self.counter] // 2 - 1
        else:
            slider_bop = 0
        surf.blit(slider_cursor, (x + 112 + offset, y + 4 + slider_bop))

class ChoiceOption(ConfigOption):
    def __init__(self, idx, name, values, icon):
        super().__init__(idx, name, values, icon)
        self.left_arrow = gui_objects.ScrollArrow('left', (0, 0), 0)
        self.right_arrow = gui_objects.ScrollArrow('right', (0, 0), 0.5)

    def draw(self, surf, x, y, active=False):
        surf.blit(self.icon, (x + 16, y))
        name_font = FONT['text_white']
        name_font.blit(self.display_name, surf, (x + 32, y))
        value_font = FONT['text_blue']
        value = cf.SETTINGS[self.name]
        display_value = text_funcs.translate(value)
        value_font.center_blit(display_value, surf, (x + 164, y))
        self.draw_side_arrows(surf, x, y, active)

    def draw_side_arrows(self, surf, x, y, active):
        self.left_arrow.x = x + 112
        self.right_arrow.x = x + 216 - 8 # To account for right
        self.left_arrow.y = self.right_arrow.y = y
        self.left_arrow.draw(surf)
        self.right_arrow.draw(surf)

class SimpleOption(ConfigOption):
    def draw(self, surf, x, y, active=False):
        surf.blit(self.icon, (x + 16, y))
        name_font = FONT['text_white']
        name_font.blit(self.display_name, surf, (x + 32, y))
        value = cf.SETTINGS[self.name]
        if isinstance(self.values, bool):
            if value:
                on_font = FONT['text_blue']
                off_font = FONT['text_grey']
            else:
                on_font = FONT['text_grey']
                off_font = FONT['text_blue']
                on_str = text_funcs.translate('ON') + '    '
            on_font.blit(on_str, surf, (x + 112, y))
            off_font.blit(text_funcs.translate('OFF'), surf, (x + 112 + on_font.width(on_str)))
        else:
            running_width = 0
            for choice in self.values:
                if choice == value:
                    font = FONT['text_blue']
                else:
                    font = FONT['text_grey']
                text = text_funcs.translate(choice) + '    '
                font.blit(text, surf, (x + 112 + running_width, y))
                width = font.width(text)
                running_width += width

class Controls(menus.Simple):
    def __init__(self, owner, options, background, icons, info=None):
        super().__init__(owner, options, None, background, info)
        self.icons = icons
        self.set_limit(5)

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            option = ControlOption(idx, option, self.icons[idx])
            if info_descs:
                option.help_box = help_menu.HelpDialog(info_descs[idx])
            self.options.append(option)

    def draw(self, surf):
        topleft = (0, 32)
        bg_surf = base_surf.create_base_surf(self.get_menu_width(), self.get_menu_height(), self.background)
        bg_surf = image_mods.make_translucent(bg_surf, .1)
        surf.blit(bg_surf, topleft)

        if len(self.options) > self.limit:
            self.draw_scroll_bar(surf)

        end_index = self.scroll + self.limit
        choices = self.options[self.scroll:end_index]
        running_height = 0

        for idx, choice in enumerate(choices):
            top = topleft[1] + 4 + running_height
            left = topleft[0]

            active = (idx == self.current_index and self.takes_input)
            choice.draw(surf, left, top, active)
            if active:
                self.cursor.draw(surf, left, top)

            running_height += choice.height()

        return surf

    def get_rects(self):
        topleft = (0, 32)
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

class Config(Controls):
    def __init__(self, owner, options, background, icons, info):
        super().__init__(self, owner, options, None, background, info)

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            if isinstance(option[1][0], int) or isinstance(option[1][0], float):
                option = SliderOption(idx, option[0], option[1], self.icons[idx])
            else:  # Is a list of options
                if len(' '.join([text_funcs.translate(o) for o in option[1]])) > 16:  # Long list
                    option = ChoiceOption(idx, option[0], option[1], self.icons[idx])
                else:  # Short list
                    option = SimpleOption(idx, option[0], option[1], self.icons[idx])
            if info_descs:
                option.help_box = help_menu.HelpDialog(info_descs[idx])
            self.options.append(option)
