import logging
from app.engine.text_evaluator import TextEvaluator
import datetime
from app.constants import WINWIDTH, WINHEIGHT

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.sound import get_sound_thread
from app.engine.state import State
from app.engine import engine, background, base_surf, text_funcs, evaluate, icons, menus
from app.engine.game_state import game
from app.engine.fluid_scroll import FluidScroll

class ObjectiveMenuState(State):
    name = 'objective_menu'
    bg = None
    surfaces = []

    def start(self):
        self.bg = background.create_background('settings_background')
        self.surfaces = self.get_surfaces()
        self.fluid = FluidScroll()

        game.state.change('transition_in')
        return 'repeat'

    def get_surfaces(self) -> list:
        surfaces = []

        name_back_surf = SPRITES.get('chapter_select_green')
        # Text
        big_font = FONT['chapter-green']
        center = (name_back_surf.get_width()//2, name_back_surf.get_height()//2 - big_font.height//2)
        big_font.blit_center(game.level.name, name_back_surf, center)
        surfaces.append((name_back_surf, (24, 2)))

        # Background
        back_surf = base_surf.create_base_surf(WINWIDTH - 8, 24, 'menu_bg_white')
        surfaces.append((back_surf, (4, 34)))

        # Get words
        golden_words_surf = SPRITES.get('golden_words')

        # Get Turn
        turn_surf = engine.subsurface(golden_words_surf, (0, 17, 26, 10))
        surfaces.append((turn_surf, (10, 42)))
        # Get Funds
        funds_surf = engine.subsurface(golden_words_surf, (0, 33, 32, 10))
        surfaces.append((funds_surf, (WINWIDTH//3 - 8, 42)))
        # Get PlayTime
        playtime_surf = engine.subsurface(golden_words_surf, (32, 15, 17, 13))
        surfaces.append((playtime_surf, (2*WINWIDTH//3 + 6, 39)))
        # Get G
        g_surf = engine.subsurface(golden_words_surf, (40, 47, 9, 12))
        surfaces.append((g_surf, (2*WINWIDTH//3 - 8 - 1, 40)))
        # TurnCountSurf
        turn_count_size = FONT['text-blue'].width(str(game.turncount)) + 1, FONT['text-blue'].height
        turn_count_surf = engine.create_surface(turn_count_size, transparent=True)
        FONT['text-blue'].blit(str(game.turncount), turn_count_surf, (0, 0))
        surfaces.append((turn_count_surf, (WINWIDTH//3 - 16 - turn_count_surf.get_width(), 38)))
        # MoneySurf
        money = str(game.get_money())
        money_size = FONT['text-blue'].width(money) + 1, FONT['text-blue'].height
        money_surf = engine.create_surface(money_size, transparent=True)
        FONT['text-blue'].blit(money, money_surf, (0, 0))
        surfaces.append((money_surf, (2*WINWIDTH//3 - 12 - money_surf.get_width(), 38)))

        # Get win and loss conditions
        win_con = game.level.objective['win']
        text_parser = TextEvaluator(logging.getLogger(), game)
        win_lines = text_parser._evaluate_all(','+win_con).split(',')
        win_lines = [w.replace('{comma}', ',') for w in win_lines]

        loss_con = game.level.objective['loss']
        text_parser = TextEvaluator(logging.getLogger(), game)
        loss_lines = text_parser._evaluate_all(','+loss_con).split(',')
        loss_lines = [line.replace('{comma}', ',') for line in loss_lines]

        self.topleft = (4, 60)
        self.menu = menus.ObjMenu(None, win_lines+loss_lines, (6, 1), self.topleft)

        """hold_surf = base_surf.create_base_surf(WINWIDTH - 16, 40 + 16*len(win_lines) + 16 * len(loss_lines))
        shimmer = SPRITES.get('menu_shimmer2')
        hold_surf.blit(shimmer, (hold_surf.get_width() - 1 - shimmer.get_width(), hold_surf.get_height() - shimmer.get_height() - 5))

        # Win cons
        hold_surf.blit(SPRITES.get('lowlight'), (2, 12))

        FONT['text-yellow'].blit(text_funcs.translate('Win Conditions'), hold_surf, (4, 4))

        for idx, win_con in enumerate(win_lines):
            FONT['text'].blit(win_con, hold_surf, (8, 20 + 16*idx))

        hold_surf.blit(SPRITES.get('lowlight'), (2, 28 + 16*len(win_lines)))

        FONT['text-yellow'].blit(text_funcs.translate('Loss Conditions'), hold_surf, (4, 20 + 16*len(win_lines)))

        for idx, loss_con in enumerate(loss_lines):
            FONT['text'].blit(loss_con, hold_surf, (8, 36 + 16*len(win_lines) + idx*16))

        surfaces.append((hold_surf, (8, 34 + back_surf.get_height() + 2)))"""

        seed = str(game.game_vars['_random_seed'])
        seed_surf = engine.create_surface((28, 16), transparent=True)
        FONT['text-numbers'].blit_center(seed, seed_surf, (14, 0))
        surfaces.append((seed_surf, (WINWIDTH - 28, 4)))

        # PlayerUnits
        playerbg_surf = base_surf.create_base_surf(WINWIDTH - 192, 24)
        shimmerp = SPRITES.get('menu_shimmer1')
        playerbg_surf.blit(shimmerp, (playerbg_surf.get_width() - 1 - shimmerp.get_width(), playerbg_surf.get_height() - shimmerp.get_height() - 5))
        surfaces.append((playerbg_surf, (132, 60)))
        player_surf = engine.subsurface(golden_words_surf, (56, 12, 40, 8))
        surfaces.append((player_surf, (WINWIDTH - 104, 57)))
        p_count_size = FONT['text-blue'].width(str(len(game.get_player_units()))) + 1, FONT['text-blue'].height
        p_count_surf = engine.create_surface(p_count_size, transparent=True)
        FONT['text-blue'].blit(str(len(game.get_player_units())), p_count_surf, (0, 0))
        surfaces.append((p_count_surf, (WINWIDTH - 75 - p_count_surf.get_width(), 62)))

        # OtherUnits
        otherbg_surf = base_surf.create_base_surf(WINWIDTH - 192, 24, 'menu_bg_green')
        shimmero = SPRITES.get('menu_shimmer_green')
        otherbg_surf.blit(shimmero, (otherbg_surf.get_width() - 1 - shimmero.get_width(), otherbg_surf.get_height() - shimmero.get_height() - 5))
        surfaces.append((otherbg_surf, (132, 80)))
        other_surf = engine.subsurface(golden_words_surf, (56, 36, 40, 8))
        surfaces.append((other_surf, (WINWIDTH - 104, 77)))
        o_count_size = FONT['text-blue'].width(str(len(game.get_other_units()))) + 6, FONT['text-blue'].height
        o_count_surf = engine.create_surface(o_count_size, transparent=True)
        if len(game.get_other_units()) > 0:
            FONT['text-blue'].blit(str(len(game.get_other_units())), o_count_surf, (5, 0))
        else:
            FONT['text-blue'].blit("--", o_count_surf, (0, 0))
        surfaces.append((o_count_surf, (WINWIDTH - 75 - o_count_surf.get_width(), 82)))

        # EnemyUnits
        enemyu = len(game.get_enemy_units())
        enemy2u = len(game.get_enemy2_units())
        redunits = enemyu - enemy2u

        enemybg_surf = base_surf.create_base_surf(WINWIDTH - 192, 24, 'menu_bg_red')
        shimmere = SPRITES.get('menu_shimmer_red')
        enemybg_surf.blit(shimmere, (enemybg_surf.get_width() - 1 - shimmere.get_width(), enemybg_surf.get_height() - shimmere.get_height() - 5))
        surfaces.append((enemybg_surf, (188, 60)))
        enemy_surf = engine.subsurface(golden_words_surf, (56, 20, 40, 8))
        surfaces.append((enemy_surf, (WINWIDTH - 48, 57)))
        e_count_size = FONT['text-blue'].width(str(redunits)) + 6, FONT['text-blue'].height
        e_count_surf = engine.create_surface(e_count_size, transparent=True)
        if redunits > 0:
            FONT['text-blue'].blit(str(redunits), e_count_surf, (5, 0))
        else:
            FONT['text-blue'].blit("--", e_count_surf, (0, 0))
        surfaces.append((e_count_surf, (WINWIDTH - 16 - e_count_surf.get_width(), 62)))

        # Enemy2Units
        enemy2bg_surf = base_surf.create_base_surf(WINWIDTH - 192, 24, 'menu_bg_purple')
        shimmere2 = SPRITES.get('menu_shimmer_purple')
        enemy2bg_surf.blit(shimmere2, (enemy2bg_surf.get_width() - 1 - shimmere2.get_width(), enemy2bg_surf.get_height() - shimmere2.get_height() - 5))
        surfaces.append((enemy2bg_surf, (188, 80)))
        e2_count_size = FONT['text-blue'].width(str(len(game.get_enemy2_units()))) + 6, FONT['text-blue'].height
        e2_count_surf = engine.create_surface(e2_count_size, transparent=True)
        if len(game.get_enemy2_units()) > 0:
            FONT['text-blue'].blit(str(len(game.get_enemy2_units())), e2_count_surf, (5, 0))
        else:
            FONT['text-blue'].blit("--", e2_count_surf, (0, 0))
        surfaces.append((e2_count_surf, (WINWIDTH - 16 - e2_count_surf.get_width(), 82)))

        # Unit info bg
        back_surf = base_surf.create_base_surf(WINWIDTH - 136, 62, 'menu_bg_white')
        surfaces.append((back_surf, (132, 100)))

        # ChibiPortraitSurf
        chibi = engine.create_surface((96, WINHEIGHT + 24), transparent=True)
        icons.draw_chibi(chibi, game.get_unit(game.get_party().leader_nid).portrait_nid, (7, 8))
        surfaces.append((chibi, (WINWIDTH - 44, 111)))

        # UnitStatSurf
        Name_size = FONT['text-white'].width(str(game.get_unit(game.get_party().leader_nid).name)) + 1, FONT['text-white'].height
        Name_surf = engine.create_surface(Name_size, transparent=True)
        FONT['text-white'].blit(str(game.get_unit(game.get_party().leader_nid).name), Name_surf, (0, 0))
        surfaces.append((Name_surf, (WINWIDTH - 42 - Name_surf.get_width(), 104)))

        LV_surf = engine.subsurface(golden_words_surf, (0, 48, 16, 24))
        surfaces.append((LV_surf, (140, 122)))
        level_size = FONT['text-blue'].width(str(game.get_unit(game.get_party().leader_nid).level)) + 1, FONT['text-blue'].height
        level_surf = engine.create_surface(level_size, transparent=True)
        FONT['text-blue'].blit(str(game.get_unit(game.get_party().leader_nid).level), level_surf, (0, 0))
        surfaces.append((level_surf, (WINWIDTH - 42 - level_surf.get_width(), 120)))

        HP_surf = engine.subsurface(golden_words_surf, (16, 48, 20, 24))
        surfaces.append((HP_surf, (140, 136)))
        HitPoints_size = FONT['text-blue'].width(str(game.get_unit(game.get_party().leader_nid).get_hp())) + 20, FONT['text-blue'].height
        HitPoints_surf = engine.create_surface(HitPoints_size, transparent=True)
        FONT['text-blue'].blit(str(game.get_unit(game.get_party().leader_nid).get_max_hp()) + '/' + str(game.get_unit(game.get_party().leader_nid).get_hp()), HitPoints_surf, (0, 0))
        surfaces.append((HitPoints_surf, (WINWIDTH - 42 - HitPoints_surf.get_width(), 134)))

        return surfaces

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            self.menu.move_down(first_push)
            get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            get_sound_thread().play_sfx('Select 6')
            self.menu.move_up(first_push)
        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            game.state.back()

    def update(self):
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)

        self.menu.draw(surf)

        # Non moving surfaces
        for surface, pos in self.surfaces:
            surf.blit(surface, pos)

        # Map Sprite
        mapsprite = game.get_unit(game.get_party().leader_nid).sprite.create_image('passive')
        surf.blit(mapsprite, (124, 82))

        # Playtime
        time = datetime.timedelta(milliseconds=game.playtime)
        seconds = int(time.total_seconds())
        hours = min(seconds//3600, 99)
        minutes = str((seconds%3600)//60)
        if len(minutes) < 2:
            minutes = '0' + minutes
        seconds = str(seconds%60)
        if len(seconds) < 2:
            seconds = '0' + seconds

        formatted_time = ':'.join([str(hours), minutes, seconds])
        FONT['text-blue'].blit_right(formatted_time, surf, (WINWIDTH - 8, 38))

        return surf
