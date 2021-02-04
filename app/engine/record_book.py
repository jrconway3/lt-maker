from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine import menus, menu_options, gui, base_surf, image_mods, text_funcs

from app.engine.game_state import game

class RecordOption(menu_options.BasicOption):
    def __init__(self, idx, text):
        self.idx = idx
        self.level, self.turncount, self.mvp = text
        self.help_box = None
        self.color = 'text-white'
        self.ignore = False

    def get(self):
        return self.level

    def width(self):
        return 224

    def height(self):
        return 16

    def draw(self, surf, x, y):
        level_prefab = DB.levels.get(self.level)
        if level_prefab:
            level_name = level_prefab.name
        else:
            level_name = "???"
        FONT['text-white'].blit(level_name, surf, (x + 4, y))
        FONT['text-blue'].blit_right(str(self.turncount), surf, (x + 120, y))
        unit_prefab = DB.units.get(self.mvp)
        if unit_prefab:
            unit_name = unit_prefab.name
        else:
            unit_name = "???"
        FONT['text-white'].blit_right(unit_name, surf, (x + 196, y))

class UnitRecordOption(RecordOption):
    def __init__(self, idx, text):
        self.idx = idx
        self.level, self.kills, self.damage, self.healing = text
        self.help_box = None
        self.color = 'text-white'
        self.ignore = False

    def get(self):
        return self.level

    def draw(self, surf, x, y):
        level_prefab = DB.levels.get(self.level)
        if level_prefab:
            level_name = level_prefab.name
        else:
            level_name = "???"
        FONT['text-white'].blit(level_name, surf, (x + 4, y))
        FONT['text-blue'].blit_right(str(self.kills), surf, (x + 114, y))
        FONT['text-blue'].blit_right(str(self.damage), surf, (x + 164, y))
        FONT['text-blue'].blit_right(str(self.healing), surf, (x + 210, y))

class LevelRecordOption(RecordOption):
    def __init__(self, idx, text):
        self.idx = idx
        self.unit_nid, self.kills, self.damage, self.healing = text
        self.help_box = None
        self.color = 'text-white'
        self.ignore = False

    def get(self):
        return self.unit_nid

    def draw(self, surf, x, y):
        unit_prefab = DB.units.get(self.level)
        if unit_prefab:
            unit_name = unit_prefab.name
        else:
            unit_name = "???"
        FONT['text-white'].blit(unit_name, surf, (x + 4, y))
        FONT['text-blue'].blit_right(str(self.kills), surf, (x + 114, y))
        FONT['text-blue'].blit_right(str(self.damage), surf, (x + 164, y))
        FONT['text-blue'].blit_right(str(self.healing), surf, (x + 210, y))

class RecordsDisplay(menus.Choice):
    """
    For each level, display turncount and mvp
    Level 1 - Turncount - MVP
    Level 2 - Turncount - MVP
    """

    option_type = RecordOption

    def __init__(self):
        options = self.get_options()
        super().__init__(None, options, 'center')
        self.shimmer = 2
        self.set_limit(6)
        self.set_hard_limit(True)
        self.y_offset = 16  # Make room for header

        self.top_banner = self.create_top_banner()

        self.left_arrow = gui.ScrollArrow('left', (2, 7))
        self.right_arrow = gui.ScrollArrow('right', (self.get_menu_width() - 8, 7), 0.5)

    def get_options(self):
        levels = game.records.get_levels()
        turncounts = game.records.get_turncounts(levels)
        mvps = [game.records.get_mvp(level_nid) for level_nid in levels]
        
        self.total_turns = sum(turncounts)
        unique_mvps = set(mvps)
        self.overall_mvp = None
        self.best_score = 0
        for mvp in unique_mvps:
            score = game.records.determine_score(mvp)
            if score > self.best_score:
                self.best_score = score
                self.overall_mvp = mvp

        return [(l, t, m) for (l, t, m) in zip(levels, turncounts, mvps)]

    def create_options(self, options, info_descs=None):
        self.options.clear()
        for idx, option in enumerate(options):
            option = self.option_type(idx, option)
            self.options.append(option)

        if self.hard_limit:
            for num in range(self.limit - len(options)):
                option = menu_options.EmptyOption(len(options) + num)
                option._width = 224
                self.options.append(option)

    def create_top_banner(self):
        bg = base_surf.create_base_surf(self.get_menu_width(), 24, 'menu_bg_white')
        bg = image_mods.make_translucent(bg, 0.25)
        FONT['text-yellow'].blit(text_funcs.translate('Total Turns'), bg, (4, 4))
        total_turns = str(self.total_turns)
        FONT['text-blue'].blit_right(total_turns, bg, (92, 4))
        FONT['text-yellow'].blit(text_funcs.translate('Overall MVP', bg, (100, 4)))
        unit = DB.units.get(self.overall_mvp)
        if unit:
            FONT['text-white'].blit_right(unit.name, bg, (216, 4))
        else:
            FONT['text-white'].blit_right('--', bg, (216, 4))
        return bg

    def draw(self, surf, offset=None):
        FONT['text-yellow'].blit(text_funcs.translate('Records Header'), surf, (4, 4))
        super().vert_draw(surf, offset)
        return surf

class UnitStats(RecordsDisplay):
    """
    For a unit, get it's stats on each level
    Level 1 - Kills - Damage - Healing
    Level 2 - Kills - Damage - Healing
    """
    option_type = UnitRecordOption

    def __init__(self, unit_nid):
        self.unit_nid = unit_nid
        super().__init__()

    def get_options(self):
        levels = game.records.get_levels()
        kills = [game.records.get_kills(self.unit_nid, level) for level in levels]
        damage = [game.records.get_damage(self.unit_nid, level) for level in levels]
        healing = [game.records.get_healing(self.unit_nid, level) for level in levels]

        return [(l, k, d, h) for (l, k, d, h) in zip(levels, kills, damage, healing)]

    def create_top_banner(self):
        bg = SPRITES.get('purple_background').copy()
        unit_prefab = DB.units.get(self.unit_nid)
        if unit_prefab:
            unit_name = unit_prefab.name
        else:
            unit_name = "???"
        FONT['chapter-grey'].blit_center(unit_name, bg, (bg.get_width()//2, 4))
        return bg

    def draw(self, surf, offset=None):
        FONT['text-yellow'].blit(text_funcs.translate('Unit Records Header'), surf, (4, 4))
        super().vert_draw(surf, offset)
        return surf

class MVPDisplay(RecordsDisplay):
    """
    For each unit, display stats
    Unit5 - Kills - Damage - Healing
    Unit2 - Kills - Damage - Healing
    """
    option = LevelRecordOption

    def get_options(self):
        units = game.get_all_units_in_party()
        units = list(sorted(units, key=lambda x: game.records.determine_score(x)))
        kills = [game.records.get_kills(unit_nid) for unit_nid in units]
        damage = [game.records.get_damage(unit_nid) for unit_nid in units]
        healing = [game.records.get_healing(unit_nid) for unit_nid in units]

        return [(u, k, d, h) for (u, k, d, h) in zip(units, kills, damage, healing)]

class ChapterStats(RecordsDisplay):
    """
    For a given level, display each unit in mvp order
    Unit5 - Kills - Damage - Healing
    Unit2 - Kills - Damage - Healing
    """
    option = LevelRecordOption

    def __init__(self, level_nid):
        self.level_nid = level_nid
        super().__init__()

    def get_options(self):
        units = game.get_all_units_in_party()
        units = list(sorted(units, key=lambda x: game.records.determine_score(x, self.level_nid)))
        kills = [game.records.get_kills(unit_nid, self.level_nid) for unit_nid in units]
        damage = [game.records.get_damage(unit_nid, self.level_nid) for unit_nid in units]
        healing = [game.records.get_healing(unit_nid, self.level_nid) for unit_nid in units]

        return [(u, k, d, h) for (u, k, d, h) in zip(units, kills, damage, healing)]

    def create_top_banner(self):
        bg = SPRITES.get('purple_background').copy()
        level_prefab = DB.units.get(self.level_nid)
        if level_prefab:
            level_name = level_prefab.name
        else:
            level_name = "???"
        FONT['chapter-grey'].blit_center(level_name, bg, (bg.get_width()//2, 4))
        return bg
