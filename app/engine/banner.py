from app.engine.sprites import SPRITES, FONT
from app.engine import engine, base_surf, image_mods, icons

class Banner():
    def __init__(self):
        self.text = []
        self.item = None
        self.font = []
        self.update_flag = False
        self.time_to_wait = 300
        self.time_to_start = None
        self.surf = None

    def figure_out_size(self):
        self.length = FONT['text_white'].size(''.join(self.text))[0]
        self.length += (16 if self.item else 0)
        self.font_height = 16
        self.size = self.length + 18, 24

    def update(self):
        if not self.update_flag:
            self.update_flag = True
            self.time_to_start = engine.get_time()
            # play sound

    def draw(self, surf):
        if not self.surf:
            w, h = self.size
            bg_surf = base_surf.create_base_surf(w, h, 'menu_bg_base')
            self.surf = engine.create_surface((w + 2, h + 4), transparent=True)
            self.surf.blit(bg_surf, (2, 4))
            self.surf.blit(SPRITES.get('menu_gem_small'), (0, 0))
            self.surf = image_mods.make_translucent(self.surf, .1)

        bg_surf = self.surf.copy()

        left = 6
        for idx, word in enumerate(self.text):
            word_width = FONT[self.font[idx]].size(word)[0]
            FONT[self.font[idx]].blit(word, bg_surf, (left, self.size[1]//2 - self.font_height//2 + 4))
            left += word_width

        if self.item:
            icons.draw_item(bg_surf, self.item, (self.size[0] - 24, 8), cooldown=False)
        surf.blit(bg_surf)
        return surf

class AcquiredItem(Banner):
    allows_choice = True

    def __init__(self, unit, item):
        super().__init__()
        self.unit = unit
        self.item = item
        article = 'an' if self.item.name.lower()[0] in ('a', 'e', 'i', 'o', 'u') else 'a'
        if "'" in self.item.name:
            # No article for things like Prim's Charm, Ophie's Blade, etc.
            self.text = [unit.name, ' got ', item.name, '.']
            self.font = ['text_blue', 'text_white', 'text_blue', 'text_white']
        else:
            self.text = [unit.name, ' got ', article, ' ', item.name, '.']
            self.font = ['text_blue', 'text_white', 'text_white', 'text_white', 'text_blue', 'text_white']
        self.figure_out_size()

class NoChoiceAcquiredItem(AcquiredItem):
    allows_choice = False

class SentToConvoy(Banner):
    def __init__(self, item):
        super().__init__()
        self.item = item
        self.text = [item.name, ' sent to convoy.']
        self.font = ['text_blue', 'txt_white']
        self.figure_out_size()

class BrokenItem(Banner):
    def __init__(self, unit, item):
        super().__init__()
        self.unit = unit
        self.item = item
        if item.booster:
            self.text = [unit.name, ' used ', item.name, '.']
            # self.sound = GC.SOUNDDICT['Item']
        else:
            self.text = [unit.name, ' broke ', item.name, '.']
            # self.sound = GC.SOUNDDICT['ItemBreak']
        self.font = ['text_blue', 'text_white', 'text_blue', 'text_blue']
        self.figure_out_size()
