from app import utilities
from app.data.constants import WINWIDTH, WINHEIGHT, TILEX, TILEY
from app.data.database import DB

from app.engine.sprites import SPRITES, FONT
from app.engine import engine, base_surf, image_mods, text_funcs, icons
import app.engine.config as cf
from app.engine.game_state import game

class UIView():
    legal_states = ('free', 'prep_formation', 'prep_formation_select')

    def __init__(self):
        self.unit_info_disp = None
        self.tile_info_disp = None
        self.obj_info_disp = None

        self.unit_info_offset = 0
        self.tile_info_offset = 0
        self.obj_info_offset = 0

        self.remove_unit_info = True
        self.expected_coord = None
        self.tile_left = False
        self.obj_top = False

    def remove_unit_display(self):
        self.remove_unit_info = True

    def draw(self, surf):
        # Unit info handling
        if self.remove_unit_info:
            hover = game.cursor.get_hover()
            if game.state.get_state() in self.legal_states and hover:
                self.remove_unit_info = False
                self.unit_info_disp = self.create_unit_info(hover)
                self.unit_info_offset = min(self.unit_info_disp.get_width(), self.unit_info_offset)
            elif self.unit_info_disp:
                self.unit_info_offset += 20
                if self.unit_info_offset >= 200:
                    self.unit_info_disp = None
        else:
            self.unit_info_offset -= 20
            self.unit_info_offset = max(0, self.unit_info_offset)

        # Tile info handling
        if game.state.get_state() in self.legal_states and cf.SETTINGS['show_terrain']:
            if game.cursor.position != self.expected_coord:
                self.tile_info_disp = self.create_tile_info(game.cursor.position)
            if self.tile_info_disp:
                self.tile_info_offset = min(self.tile_info_disp.get_width(), self.tile_info_offset)
            self.tile_info_offset -= 20
            self.tile_info_offset = max(0, self.tile_info_offset)
        elif self.tile_info_disp:
            self.tile_info_offset += 20
            if self.tile_info_offset >= 200:
                self.tile_info_disp = None

        # Objective info handling
        if game.state.get_state() in self.legal_states and cf.SETTINGS['show_objective']:
            self.obj_info_disp = self.create_obj_info()
            self.obj_info_offset -= 20
            self.obj_info_offset = max(0, self.obj_info_offset)
        elif self.obj_info_disp:
            self.obj_info_offset += 20
            if self.obj_info_offset >= 200:
                self.obj_info_disp = None

        # === Final drawing
        # Should be in topleft, unless cursor is in topleft, in which case it should be in bottomleft
        if self.unit_info_disp:
            if game.cursor.position[1] < TILEY // 2 + game.camera.get_y() and \
                    not (game.cursor.position[1] > TILEX // 2 + game.camera.get_x() - 1):
                surf.blit(self.unit_info_disp, (-self.unit_info_offset, WINHEIGHT - self.unit_info_disp.get_height()))
            else:
                surf.blit(self.unit_info_disp, (-self.unit_info_offset, 0))

        if self.tile_info_disp:
            # Should be in bottom, no matter what. Can be in bottomleft or bottomright, depending on where cursor is
            if game.cursor.position[0] > TILEX // 2 + game.camera.get_x() - 1: # If cursor is right
                if self.tile_left:
                    self.tile_left = False
                    self.tile_info_offset = self.tile_info_disp.get_width()
                surf.blit(self.tile_info_disp, (5 - self.tile_info_offset, WINHEIGHT - self.tile_info_disp.get_height() - 3)) # Bottomleft
            else:
                if not self.tile_left:
                    self.tile_left = True
                    self.tile_info_offset = self.tile_info_disp.get_width()
                xpos = WINWIDTH - self.tile_info_disp.get_width() - 5 + self.tile_info_offset
                ypos = WINHEIGHT - self.tile_info_disp.get_height() - 3
                surf.blit(self.tile_info_disp, (xpos, ypos)) # Bottomright

        if self.obj_info_disp:
            # Should be in topright, unless the cursor is in the topright
            # TopRight - I believe this has RIGHT precedence
            if game.cursor.position[1] < TILEY // 2 + game.camera.get_y() and \
                    game.cursor.position[0] > TILEX // 2 + game.camera.get_x() - 1:
                # Gotta place in bottomright, because cursor is in topright
                if self.obj_top:
                    self.obj_top = False
                    self.obj_info_offset = self.obj_info_disp.get_width()
                pos = (WINWIDTH - 4 + self.obj_info_offset - self.obj_info_disp.get_width(), 
                       WINHEIGHT - 4 - self.obj_info_disp.get_height())
                surf.blit(self.obj_info_disp, pos) # Should be bottom right
            else:
                # Place in topright
                if not self.obj_top:
                    self.obj_top = True
                    self.obj_info_offset = self.obj_info_disp.get_width()
                surf.blit(self.obj_info_disp, (WINWIDTH - 4 + self.obj_info_offset - self.obj_info_disp.get_width(), 1))
        
        return surf

    def create_unit_info(self, unit):
        font = FONT['info_grey']
        dimensions = (112, 40)
        width, height = dimensions
        surf = SPRITES.get('unit_info_bg').copy()
        top, left = 4, 6
        if unit.generic:
            icons.draw_faction(surf, DB.factions.get(unit.faction), (left + 1, top + 4))
        else:
            icons.draw_chibi(surf, unit.nid, (left + 1, top + 4))

        name = unit.name
        if unit.generic:
            short_name = DB.classes.get(unit.klass).short_name
            name = short_name + ' ' + str(unit.level)
        pos = (left + width//2 + 6 - font.width(name)//2, top + 4)
        font.blit(name, surf, pos)

        # Health text
        surf.blit(SPRITES.get('unit_info_hp'), (left + 34, top + height - 20))
        surf.blit(SPRITES.get('unit_info_slash'), (left + 68, top + height - 19))
        current_hp = unit.get_hp()
        max_hp = game.equations.hitpoints(unit)
        font.blit_right(str(current_hp), surf, (left + 66, top + 16))
        font.blit_right(str(max_hp), surf, (left + 90, top + 16))

        # Health BG
        bg_surf = SPRITES.get('health_bar2_bg')
        surf.blit(bg_surf, (left + 36, top + height - 10))

        # Health Bar
        hp_ratio = utilities.clamp(current_hp / float(max_hp), 0, 1)
        if hp_ratio > 0:
            hp_surf = SPRITES.get('health_bar2')
            idx = int(hp_ratio * hp_surf.get_width())
            hp_surf = engine.subsurface(hp_surf, (0, 0, idx, 2))
            surf.blit(hp_surf, (left + 37, top + height - 9))

        # Weapon Icon
        weapon = unit.get_weapon()
        if weapon:
            pos = (left + width - 20, top + height//2 - 8)
            icons.draw_item(surf, weapon, pos)
        return surf

    def create_tile_info(self, coord):
        tile = game.tilemap.tiles[coord]
        terrain = DB.terrain.get(tile.terrain_nid)
        if tile.current_hp > 0:
            self.expected_coord = None
            bg_surf = SPRITES.get('tile_info_destructible').copy()
            at_icon = SPRITES.get('icon_attackable_terrain')
            bg_surf.blit(at_icon, (7, bg_surf.get_height() - 7 - at_icon.get_height()))
            cur = str(tile.current_hp)
            FONT['small_white'].blit_right(cur, bg_surf, bg_surf.get_width() - 9, 24)
        else:
            self.expected_coord = coord
            bg_surf = SPRITES.get('tile_info_quick').copy()
        name = terrain.name
        width, height = FONT['text_white'].size(name)
        pos = (bg_surf.get_width()//2 - width//2, 22 - height)
        FONT['text_white'].blit(name, bg_surf, pos)
        return bg_surf

    def eval_string(self, string):
        return string

    def create_obj_info(self):
        font = FONT['text_white']
        obj = game.level.objective['simple']
        text_lines = self.eval_string(obj).split(',')
        longest_surf_width = text_funcs.get_max_width(font, text_lines)
        bg_surf = base_surf.create_base_surf(longest_surf_width + 16, 16 * len(text_lines) + 8, 'menu_bg_base_opaque')

        if len(text_lines) == 1:
            shimmer = SPRITES.get('menu_shimmer1')
        else:
            shimmer = SPRITES.get('menu_shimmer2')
        bg_surf.blit(shimmer, (bg_surf.get_width() - 1 - shimmer.get_width(), 4))
        surf = engine.create_surface((bg_surf.get_width(), bg_surf.get_height() + 3), transparent=True)
        surf.blit(bg_surf, (0, 3))
        gem = SPRITES.get('combat_gem_blue')
        surf.blit(gem, (bg_surf.get_width()//2 - gem.get_width()//2, 0))
        surf = image_mods.make_translucent(surf, .1)

        for idx, line in enumerate(text_lines):
            pos = (surf.get_width()//2 - font.width(line)//2, 16 * idx + 6)
            font.blit(line, surf, pos)

        return surf
