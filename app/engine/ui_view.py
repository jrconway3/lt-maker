from app import utilities
from app.data.constants import WINWIDTH, WINHEIGHT, TILEX, TILEY
from app.data.item_components import SpellTarget
from app.data.database import DB

from app.engine.sprites import SPRITES, FONT
from app.engine import engine, base_surf, image_mods, text_funcs, icons, combat_calcs, unit_object
import app.engine.config as cf
from app.engine.game_state import game

class UIView():
    legal_states = ('free', 'prep_formation', 'prep_formation_select')
    x_positions = (0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 5, 4, 3, 2, 1)
    y_positions = (0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0, 0, 0, 0, 0)

    def __init__(self):
        self.unit_info_disp = None
        self.tile_info_disp = None
        self.obj_info_disp = None
        self.attack_info_disp = None
        self.spell_info_disp = None

        self.unit_info_offset = 0
        self.tile_info_offset = 0
        self.obj_info_offset = 0
        self.attack_info_offset = 0

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

    def create_attack_info(self, attacker, defender):
        def blit_num(surf, num, x_pos, y_pos):
            if not isinstance(num, str) and num >= 100:
                surf.blit(SPRITES.get('blue_100'), (x_pos - 16, y_pos))
            else:
                FONT['text_blue'].blit_right(str(num), surf, (x_pos, y_pos))

        grandmaster = DB.constants.get('rng').value == 'Grandmaster'
        crit = DB.constants.get('crit').value

        if grandmaster:
            surf = SPRITES.get('attack_info_grandmaster')
        elif cf.SETTINGS['crit']:
            surf = SPRITES.get('attack_info_crit')
        else:
            surf = SPRITES.get('attack_info')

        # Name
        width = FONT['text_white'].width(attacker.name)
        FONT['text_white'].blit(attacker.name, surf, (43 - width//2, 3))
        # Enemy name
        y_pos = 84
        if not crit:
            y_pos -= 16
        if grandmaster:
            y_pos -= 16
        position = 26 - FONT['text_white'].width(defender.name)//2, y_pos
        FONT['text_white'].blit(defender.name, surf, position)
        # Enemy Weapon
        if isinstance(defender, unit_object.UnitObject) and defender.get_weapon():
            width = FONT['text_white'].blit(defender.get_weapon().name)
            y_pos = 100
            if not crit:
                y_pos -= 16
            if grandmaster:
                y_pos -= 16
            position = 32 - width//2, y_pos
            FONT['text_white'].blit(defender.get_weapon().name, surf, position)
        # Self HP
        blit_num(surf, attacker.get_hp(), 64, 19)
        # Enemy HP
        blit_num(surf, defender.get_hp(), 20, 19)
        # Self MT
        mt = combat_calcs.compute_damage(attacker, defender, attacker.get_weapon(), 'Attack')
        if grandmaster:
            hit = combat_calcs.compute_hit(attacker, defender, attacker.get_weapon(), 'Attack')
            blit_num(surf, int(mt * float(hit) / 100), 64, 35)
        else:
            blit_num(surf, mt, 64, 35)
            hit = combat_calcs.compute_hit(attacker, defender, attacker.get_weapon(), 'Attack')
            blit_num(surf, hit, 64, 51)
            # Blit crit if applicable
            if crit:
                c = combat_calcs.compute_crit(attacker, defender, attacker.get_weapon(), 'Attack')
                blit_num(surf, c, 64, 67)
        # Enemy Hit and Mt
        if not attacker.get_weapon().cannot_be_countered and isinstance(defender, unit_object.UnitObject) and defender.get_weapon() and \
               utilities.calculate_distance(attacker.position, defender.position) in game.equations.get_range(defender, defender.get_weapon()):
            e_mt = combat_calcs.compute_damage(defender, attacker, defender.get_weapon(), 'Defense')
            e_hit = combat_calcs.compute_hit(defender, attacker, defender.get_weapon(), 'Defense')
            if crit:
                e_crit = combat_calcs.compute_crit(defender, attacker, defender.get_weapon(), 'Defense')
            else:
                e_crit = 0
        else:
            e_mt = '--'
            e_hit = '--'
            e_crit = '--'

        if grandmaster:
            if e_mt == '--' or e_hit == '--':
                blit_num(surf, e_mt, 20, 35)
            else:
                blit_num(surf, int(e_mt * float(e_hit) / 100), 20, 35)
        else:
            blit_num(surf, e_mt, 20, 35)
            blit_num(surf, e_hit, 20, 51)
            if crit:
                blit_num(surf, e_crit, 20, 67)

        return surf

    def draw_attack_info(self, surf, attacker, defender):
        if not self.attack_info_disp:
            self.attack_info_disp = self.create_attack_info(attacker, defender)

        grandmaster = DB.constants.get('rng').value == 'Grandmaster'
        crit = DB.constants.get('crit').value

        if game.cursor.position[0] > TILEX // 2 + game.camera.get_x() - 1:
            topleft = (8 - self.attack_info_offset, 4)
        else:
            topleft = (WINWIDTH - 77 + self.attack_info_offset, 4)
        if self.attack_info_offset > 0:
            self.attack_info_offset -= 20

        surf.blit(self.attack_info_disp, topleft)

        # Attacker Item
        white = False
        if isinstance(defender, unit_object.UnitObject):
            if combat_calcs.get_effective(attacker.get_weapon(), defender):
                white = True
        else:
            if attacker.get_weapon().extra_tile_damage:
                white = True
        icons.draw_item(surf, attacker.get_weapon(), (topleft[0] + 2, topleft[1] + 4), white)

        # Defender Item
        if isinstance(defender, unit_object.UnitObject) and defender.get_weapon():
            white = False
            if combat_calcs.get_effective(defender.get_weapon(), attacker):
                white = True
            y_pos = topleft[1] + 83
            if not crit:
                y_pos -= 16
            if grandmaster:
                y_pos -= 16
            icons.draw_item(surf, defender.get_weapon(), (topleft[0] + 50, y_pos), white)

        # Advantage arrows
        if isinstance(defender, unit_object.UnitObject) and game.target.check_enemy(attacker, defender):
            adv = combat_calcs.compute_advantage(attacker, attacker.get_weapon(), defender.get_weapon())
            disadv = combat_calcs.compute_advantage(attacker, attacker.get_weapon(), defender.get_weapon(), False)
            if adv:
                up_arrow = engine.subsurface(SPRITES.get('arrow_advantage'), (game.map_view.arrow_counter.count * 7, 0, 7, 10))
                surf.blit(up_arrow, (topleft[0] + 13, topleft[1] + 8))
            elif disadv:
                down_arrow = engine.subsurface(SPRITES.get('arrow_advantage'), (game.map_view.arrow_counter.count * 7, 10, 7, 10))
                surf.blit(down_arrow, (topleft[0] + 13, topleft[1] + 8))

            y_pos = topleft[1] + 89
            if not crit:
                y_pos -= 16
            if not grandmaster:
                y_pos -= 16
            adv = combat_calcs.compute_advantage(defender, defender.get_weapon(), attacker.get_weapon())
            disadv = combat_calcs.compute_advantage(defender, defender.get_weapon(), attacker.get_weapon(), False)
            if adv:
                up_arrow = engine.subsurface(SPRITES.get('arrow_advantage'), (game.map_view.arrow_counter.count * 7, 0, 7, 10))
                surf.blit(up_arrow, (topleft[0] + 61, y_pos))
            elif disadv:
                down_arrow = engine.subsurface(SPRITES.get('arrow_advantage'), (game.map_view.arrow_counter.count * 7, 10, 7, 10))
                surf.blit(down_arrow, (topleft[0] + 61, y_pos))

        # Doubling
        if isinstance(defender, unit_object.UnitObject):
            count = game.map_view.x2_counter.count
            x2_pos_player = (topleft[0] + 59 + self.x_positions[count], topleft[1] + 38 + self.y_positions[count])
            x2_pos_enemy = (topleft[0] + 20 + self.x_positions[count], topleft[1] + 38 + self.y_positions[count])
            weapon = attacker.get_weapon()
            my_num = 1
            if not weapon.no_double:
                if weapon.brave and weapon.brave.value != "Brave while defending":
                    my_num *= 2
                if combat_calcs.outspeed(attacker, defender, weapon, "Attack"):
                    my_num *= 2
                if weapon.uses or weapon.c_uses:
                    if weapon.uses:
                        my_num = min(my_num, weapon.uses.value)
                    if weapon.c_uses:
                        my_num = min(my_num, weapon.c_uses.value)

                if my_num == 2:
                    surf.blit(SPRITES.get('x2'), x2_pos_player)
                elif my_num == 3:
                    surf.blit(SPRITES.get('x3'), x2_pos_player)
                elif my_num == 4:
                    surf.blit(SPRITES.get('x4'), x2_pos_player)

                # ie if weapon can be countered
                if not weapon.cannot_be_countered:
                    eweapon = defender.get_weapon()

                    e_num = 1
                    if eweapon and not eweapon.no_double and \
                            utilities.calculate_distance(attacker.position, defender.position) in game.equations.get_range(eweapon, defender):
                        if eweapon.brave and eweapon.brave.value != 'Brave while attacking':
                            e_num *= 2
                        if DB.constants.get('def_double').value and \
                                combat_calcs.outspeed(defender, attacker, weapon, "Defense"):
                            e_num *= 2

                    if e_num == 2:
                        surf.blit(SPRITES.get('x2'), x2_pos_enemy)
                    elif e_num == 3:
                        surf.blit(SPRITES.get('x3'), x2_pos_enemy)
                    elif e_num == 4:
                        surf.blit(SPRITES.get('x4'), x2_pos_enemy)

        return surf

    def create_spell_info(self, attacker, defender):
        spell = attacker.get_spell()
        if spell.spell.targets in (SpellTarget.Ally, SpellTarget.Enemy, SpellTarget.Unit):
            height = 2
            if spell.might is not None:
                height += 1
            if spell.hit is not None:
                height += 1

            bg_surf = SPRITES.get('Spell_Window' + str(height))
            bg_surf = image_mods.make_translucent(bg_surf, .1)
            width, height = bg_surf.get_width(), bg_surf.get_height()

            running_height = 8

            FONT['text_white'].blit(defender.name, bg_surf, (30, running_height))

            running_height += 16
            # Blit HP
            FONT['text_yellow'].blit('HP', bg_surf, (9, running_height))
            # Blit /
            FONT['text_yellow'].blit('/', bg_surf, (width - 25, running_height))
            # Blit stats['HP']
            maxhp = str(game.equations.hitpoints(defender))
            maxhp_width = FONT['text_blue'].width(maxhp)
            FONT['text_blue'].blit(maxhp, bg_surf, (width - 5 - maxhp_width, running_height))
            # Blit currenthp
            currenthp = str(defender.get_hp())
            currenthp_width = FONT['text_blue'].width(currenthp)
            FONT['text_blue'].blit(currenthp, bg_surf, (width - 26 - currenthp_width, running_height))

            if spell.might is not None:
                running_height += 16
                mt = combat_calcs.compute_damage(attacker, defender, spell, 'Attack')
                FONT['text_yellow'].blit('Mt', bg_surf, (9, running_height))
                mt_width = FONT['text_blue'].width(str(mt))
                FONT['text_blue'].blit(str(mt), bg_surf, (width - 5 - mt_width, running_height))

            if spell.hit is not None:
                running_height += 16
                FONT['text_yellow'].blit('Hit', bg_surf, (9, running_height))
                hit = combat_calcs.compute_hit(attacker, defender, spell, 'Attack')
                if hit >= 100:
                    bg_surf.blit(SPRITES.get('blue_100'), (width - 21, running_height))
                else:
                    hit_width = FONT['text_blue'].width(str(hit))
                    position = width - 5 - hit_width, running_height
                    FONT['text_blue'].blit(str(hit), bg_surf, position)

            if DB.constants.get('crit').value and spell.crit is not None:
                running_height += 16
                FONT['text_yellow'].blit('Crit', bg_surf, (9, running_height))
                crit = combat_calcs.compute_crit(attacker, defender, spell, 'Attack')
                if crit >= 100:
                    bg_surf.blit(SPRITES.get('blue_100'), (width - 21, running_height))
                else:
                    crit_width = FONT['text_blue'].width(str(crit))
                    position = width - 5 - crit_width, running_height
                    FONT['text_blue'].blit(str(crit), bg_surf, position)

            # Blit name
            running_height += 16
            icons.draw_item(bg_surf, spell, (8, running_height))
            name_width = FONT['text_white'].width(spell.name)
            FONT['text_white'].blit(spell.name, bg_surf, (52 - name_width//2, running_height))

            return bg_surf

        else:
            height = 24
            if spell.might is not None:
                height += 16
            real_surf = base_surf.create_base_surf((80, height), 'menu_bg_base_opaque')
            bg_surf = engine.create_surface((real_surf.get_width() + 2, real_surf.get_height() + 4), transparent=True)
            bg_surf.blit(real_surf, (2, 4))
            bg_surf.blit(SPRITES.get('menu_gem_small'), (0, 0))
            shimmer = SPRITES.get('menu_shimmer1')
            bg_surf.blit(shimmer, (bg_surf.get_width() - shimmer.get_width() - 1, bg_surf.get_height() - shimmer.get_height() - 5))
            bg_surf = image_mods.make_transluenct(bg_surf, .1)
            width, height = bg_surf.get_width(), bg_surf.get_height()

            running_height = -10

            if spell.might is not None:
                running_height += 16
                mt = combat_calcs.damage(attacker, defender, spell, "Attack")
                FONT['text_yellow'].blit('Mt', bg_surf, (5, running_height))
                mt_size = FONT['text_blue'].width(str(mt))
                FONT['text_blue'].blit(str(mt), bg_surf, (width - 5 - mt_size, running_height))

            # Blit name
            running_height += 16
            icons.draw(bg_surf, spell, (4, running_height))
            name_width = FONT['text_white'].width(spell.name)
            FONT['text_white'].blit(spell.name, bg_surf, (52 - name_width//2, running_height))

            return bg_surf

    def draw_spell_info(self, surf, attacker, defender):
        if not self.spell_info_disp:
            self.spell_info_disp = self.create_spell_info(attacker, defender)
            if self.spell_info_disp:
                return

        width = self.spell_info_disp.get_width()
        if defender:
            unit_surf = defender.sprite.create_image('passive')

        if game.cursor.position[0] > TILEX // 2 + game.camera.get_x() - 1:
            topleft = (4, 4)
            if defender:
                u_topleft = (16 - max(0, (unit_surf.get_width() - 16)//2), 12 - max(0, (unit_surf.get_width() - 16)//2))
        else:
            topleft = (WINWIDTH - 4 - width, 4)
            if defender:
                u_topleft = (WINWIDTH - width + 8 - max(0, (unit_surf.get_width() - 16)//2), 12 - max(0, (unit_surf.get_width() - 16)//2))

        surf.blit(self.spell_info_disp, topleft)
        if defender:
            surf.blit(unit_surf, u_topleft)
        return surf
