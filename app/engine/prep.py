from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT

from app.resources.resources import RESOURCES
from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.sound import SOUNDTHREAD
from app.engine.fonts import FONT
from app.engine.state import State, MapState

from app.engine.background import PanoramaBackground
from app.engine import config as cf
from app.engine.game_state import game
from app.engine import menus, banner, action, base_surf, background, \
    info_menu, engine, equations, item_funcs, text_funcs, image_mods, \
    convoy_funcs, item_system, interaction

class PrepMainState(MapState):
    name = 'prep_main'

    def start(self):
        SOUNDTHREAD.fade_in(game.level.music['prep'])
        game.cursor.hide()
        game.cursor.autocursor()
        game.boundary.hide()

        imgs = RESOURCES.panoramas.get('focus_fade')
        self.bg = PanoramaBackground(imgs) if imgs else None

        options = ['Manage', 'Formation', 'Options', 'Save', 'Fight']
        if game.memory['prep_pick']:
            options.insert(0, 'Pick Units')
        self.menu = menus.Choice(None, options)

        # Force place any required units
        for unit in game.get_units_in_party():
            possible_position = game.get_next_formation_spot()
            if 'Required' in unit.tags and possible_position and not unit.position:
                action.ArriveOnMap(unit, possible_position).do()
                unit.reset()

        game.state.change('transition_in')
        return 'repeat'
        # game.events.trigger('prep_start')

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            if selection == 'Pick Units':
                game.memory['next_state'] = 'prep_pick_units'
                game.state.change('transition_to')
            elif selection == 'Manage':
                game.memory['next_state'] = 'prep_items'
                game.state.change('transition_to')
            elif selection == 'Formation':
                self.bg.fade_out()
                game.state.change('prep_formation')
            elif selection == 'Options':
                game.memory['next_state'] = 'settings_menu'
                game.state.change('transition_to')
            elif selection == 'Save':
                game.memory['save_kind'] = 'prep'
                game.memory['next_state'] = 'start_save'
                game.state.change('transition_to')
            elif selection == 'Fight':
                if any(unit.position for unit in game.level.units):
                    self.bg.fade_out()
                    game.state.back()
                else:
                    SOUNDTHREAD.play_sfx('Select 4')
                    alert = banner.Custom("Must select at least one unit!")
                    game.alerts.append(alert)
                    game.state.change('alert')

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        if self.bg:
            self.bg.draw(surf)
        self.menu.draw(surf)
        return surf

class PrepPickUnitsState(State):
    name = 'prep_pick_units'

    def start(self):
        player_units = game.get_units_in_party()
        stuck_units = [unit for unit in player_units if unit.position and game.check_for_region(unit.position, 'Formation')]
        unstuck_units = [unit for unit in player_units if unit not in stuck_units]

        units = stuck_units + unstuck_units
        self.menu = menus.UnitSelect(units, (6, 2), (110, 24))

        self.bg = background.create_background('rune_background')
        game.memory['prep_bg'] = self.bg

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_up(first_push)
        elif 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_left(first_push)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_right(first_push)

        if event == 'SELECT':
            unit = self.menu.get_current()
            if unit.position and game.check_for_region(unit.position, 'Formation'):
                SOUNDTHREAD.play_sfx('Select 4')  # Locked/Lord character
            elif unit.position and 'Required' in unit.tags:
                SOUNDTHREAD.play_sfx('Select 4')  # Required unit, can't be removed
            elif unit.position:
                SOUNDTHREAD.play_sfx('Select 1')
                action.LeaveMap(unit).do()
            else:
                possible_position = game.get_next_formation_spot()
                is_fatigued = False
                if DB.constants.value('fatigue') and game.game_vars['fatigue'] == 1:
                    if unit.current_fatigue >= equations.parser.max_fatigue(unit):
                        is_fatigued = True  
                if possible_position and not is_fatigued:
                    SOUNDTHREAD.play_sfx('Select 1')
                    action.ArriveOnMap(unit, possible_position).do()
                    unit.reset()
                elif is_fatigued:
                    SOUNDTHREAD.play_sfx('Select 4')

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.change('transition_pop')

        elif event == 'INFO':
            game.memory['scroll_units'] = game.get_units_in_party()
            game.memory['next_state'] = 'info_menu'
            game.memory['current_unit'] = self.menu.get_current()
            game.state.change('transition_to')

    def update(self):
        self.menu.update()

    def draw_pick_units_card(self, surf):
        bg_surf = base_surf.create_base_surf((132, 24), 'menu_bg_white')
        player_units = game.get_units_in_party()
        on_map = [unit for unit in game.level.units if unit.position and unit in player_units]
        num_slots = game.level_vars.get('prep_slots')
        if num_slots is None:
            num_slots = len(game.get_all_formation_spots())
        pick_s = ['Pick ', str(num_slots - len(on_map), 'units  ', str(on_map), '/', str(num_slots))]
        pick_f = ['text-white', 'text-blue', 'text-white', 'text-blue', 'text-white', 'text-blue']
        left_justify = 8
        for word, font in zip(pick_s, pick_f):
            FONT[pick_f].blit(word, bg_surf, (left_justify, 4))
            left_justify += FONT[pick_f].width(word)
        surf.blit(bg_surf, (110, 4))

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        menus.draw_items(surf, (4, 44), self.menu.get_current(), include_top=True)

        self.draw_pick_units_card(surf)

        self.menu.draw(surf)
        return surf

class PrepFormationState(MapState):
    name = 'prep_formation'

    def begin(self):
        game.cursor.show()
        game.boundary.show()

    def take_input(self, event):
        game.cursor.take_input()

        if event == 'INFO':
            info_menu.handle_info()

        elif event == 'AUX':
            pass

        elif event == 'SELECT':
            cur_unit = game.cursor.get_hover()
            if cur_unit:
                if game.check_for_region(game.cursor.position, 'Formation'):
                    SOUNDTHREAD.play_sfx('Select 3')
                    game.state.change('prep_formation_select')
                else:
                    SOUNDTHREAD.play_sfx('Select 2')
                    if cur_unit.team == 'enemy' or cur_unit.team == 'enemy2':
                        SOUNDTHREAD.play_sfx('Select 3')
                        game.boundary.toggle_unit(cur_unit)
                    else:
                        SOUNDTHREAD.play_sfx('Error')

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 1')
            game.state.back()

        elif event == 'START':
            SOUNDTHREAD.play_sfx('Select 5')
            game.state.change('minimap')

        def update(self):
            super().update()
            game.highlight.handle_hover()

        def finish(self):
            game.highlight.remove_highlights()

class PrepFormationSelectState(MapState):
    name = 'prep_formation_select'
    marker = SPRITES.get('menu_hand_rotated')
    marker_offset = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1]

    def start(self):
        self.last_update = engine.get_time()
        self.counter = 0
        self.unit = game.cursor.get_hover()

    def take_input(self, event):
        game.cursor.take_input()

        if event == 'SELECT':
            if game.check_for_region(game.cursor.position, 'Formation'):
                SOUNDTHREAD.play_sfx('FormationSelect')
                cur_unit = game.cursor.get_hover()
                if cur_unit.team != 'player':
                    pass
                elif cur_unit:
                    game.leave(cur_unit)
                    game.leave(self.unit)
                    cur_unit.position, self.unit.position = self.unit.position, cur_unit.position
                    game.arrive(cur_unit)
                    game.arrive(self.unit)
                else:
                    game.leave(self.unit)
                    self.unit.position = game.cursor.position
                    game.arrive(self.unit)
                game.state.back()
                game.ui_view.remove_unit_display()
            else:
                SOUNDTHREAD.play_sfx('Error')

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'AUX':
            game.cursor.set_pos(self.unit.position)

        elif event == 'INFO':
            info_menu.handle_info()

    def draw(self, surf):
        surf = super().draw(surf)

        # Draw static hand
        if self.unit:
            pos = self.unit.position
            x = (pos[0] - game.camera.get_x()) * TILEWIDTH + 2
            y = (pos[1] - game.camera.get_y() - 1) * TILEHEIGHT
            surf.blit(self.marker, (x, y))

        if game.check_for_region(game.cursor.position, 'Formation'):
            pos = game.cursor.position
            while engine.get_time() - 50 > self.last_update:
                self.last_update += 50
                self.counter = self.counter % len(self.marker_offset)
            x = (pos[0] - game.camera.get_x()) * TILEWIDTH + 2
            y = (pos[1] - game.camera.get_y() - 1) * TILEHEIGHT + self.marker_offset[self.counter]
            surf.blit(self.marker, (x, y))

        return surf

def draw_funds(surf):
    # Draw R: Info display
    helper = engine.get_key_name(cf.SETTINGS['key_INFO']).upper()
    FONT['text-yellow'].blit(helper, surf, (123, 143))
    FONT['text-white'].blit(': Info', surf, (123 + FONT['text-blue'].width(helper), 143))
    # Draw Funds display
    surf.blit(SPRITES.get('FundsDisplay'), (168, 137))
    money = str(game.get_money())
    FONT['text-blue'].blit_right(money, surf, (219, 141))

class PrepManageState(State):
    name = 'prep_manage'

    def start(self):
        units = game.get_units_in_party()
        units = sorted(units, key=lambda unit: bool(unit.position), reverse=True)
        self.menu = menus.UnitSelect(units, (4, 3), 'center')       

        # Display
        self.quick_disp = self.create_quick_disp()

        self.bg = background.create_background('rune_background')
        game.memory['prep_bg'] = self.bg
        game.memory['manage_menu'] = self.menu

        game.state.change('transition_in')
        return 'repeat'

    def create_quick_disp(self):
        buttons = [SPRITES.get('Buttons').subsurface(0, 165, 33, 9), SPRITES.get('Buttons').subsurface(0, 66, 14, 13)]
        font = FONT['text-white']
        commands = ['Manage', 'Optimize All']
        commands = [text_funcs.translate(c) for c in commands]
        size = (49 + max(font.width(c) for c in commands), 40)
        bg_surf = base_surf.create_base_surf(size[0], size[1], 'menu_bg_brown')
        bg_surf = image_mods.make_translucent(bg_surf, 0.1)
        for idx, button in enumerate(buttons):
            bg_surf.blit(button, (20 - button.get_width()//2, idx * 16 + 12 - button.get_height()))
        for idx, command in enumerate(commands):
            font.blit(command, bg_surf, (38, idx * 16 + 4))
        return bg_surf

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_up(first_push)
        elif 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_left(first_push)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_right(first_push)

        if event == 'SELECT':
            unit = self.menu.get_current()
            game.memory['current_unit'] = unit
            game.state.change('prep_manage_select')
        elif event == 'BACK':
            game.state.change('transition_pop')
        elif event == 'INFO':
            game.memory['scroll_units'] = game.get_units_in_party()
            game.memory['next_state'] = 'info_menu'
            game.memory['current_unit'] = self.menu.get_current()
            game.state.change('transition_to')
        elif event == 'START':
            game.optimize_all()

    def update(self):
        self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        self.menu.draw(surf)
        menus.draw_items(surf, (6, 72), self.menu.get_current(), include_face=True, shimmer=2)
        surf.blit(self.quick_disp, (WINWIDTH//2 + 10, WINHEIGHT//2 + 9))
        draw_funds(surf)
        return surf

class PrepManageSelectState(State):
    name = 'prep_manage_select'

    def start(self):
        self.bg = game.memory['prep_bg']
        self.menu = game.memory['manage_menu']
        self.unit = game.memory['current_unit']

        options = ['Trade', 'Restock', 'Give all', 'Optimize', 'Items', 'Market']
        ignore = [False, True, True, True, True, True]
        if 'convoy' in game.game_vars:
            ignore = [False, True, True, False, False, True]
            tradeable_items = item_funcs.get_all_tradeable_items(self.unit)
            if tradeable_items:
                ignore[2] = False
            if any(convoy_funcs.can_restock(item) for item in tradeable_items):
                ignore[1] = False
        if 'prep_market' in game.game_vars:
            ignore[5] = False
        self.select_menu = menus.Choice(self.unit, options, (128, 80))
        self.select_menu.set_ignore(ignore)
        self.select_menu.set_tabling(3, 2)

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.select_menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.select_menu.moveDown(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.select_menu.moveUp(first_push)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.select_menu.moveRight(first_push)
        elif 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.select_menu.moveLeft(first_push)

        if event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            choice = self.select_menu.get_current()
            if choice == 'Trade':
                game.state.change('prep_trade_select')
            elif choice == 'Give all':
                tradeable_items = item_funcs.get_all_tradeable_items(self.unit)
                for item in tradeable_items:
                    convoy_funcs.store_item(item, self.unit)
            elif choice == 'Items':
                game.memory['next_state'] = 'prep_items'
                game.state.change('transition_to')
            elif choice == 'Restock':
                game.state.change('prep_restock')
            elif choice == 'Optimize':
                game.optimize(self.unit)
            elif choice == 'Market':
                game.memory['next_state'] = 'prep_market'
                game.state.change('transition_to')

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

    def update(self):
        self.menu.update()
        self.select_menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        self.menu.draw(surf)
        self.select_menu.draw(surf)
        menus.draw_items(surf, (6, 72), self.unit, include_face=True, include_top=True, shimmer=2)
        draw_funds(surf)
        return surf

class PrepTradeSelectState(State):
    name = 'prep_trade_select'

    def start(self):
        self.menu = game.memory['manage_menu']
        self.bg = game.memory['prep_bg']
        self.unit = game.memory['current_unit']
        self.menu.set_extra_marker()

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_up(first_push)
        elif 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_left(first_push)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 5')
            self.menu.move_right(first_push)

        if event == 'SELECT':
            unit2 = self.menu.get_current()
            game.memory['unit1'] = self.unit
            game.memory['unit2'] = unit2
            game.memory['next_state'] = 'prep_trade'
            game.state.change('transition_to')

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.change('transition_pop')

        elif event == 'INFO':
            game.memory['scroll_units'] = game.get_units_in_party()
            game.memory['next_state'] = 'info_menu'
            game.memory['current_unit'] = self.menu.get_current()
            game.state.change('transition_to')

    def update(self):
        self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        menus.draw_items(surf, (6, 72), self.unit, include_face=True, shimmer=2)
        menus.draw_items(surf, (126, 72), self.menu.get_current(), include_face=True, right=False, shimmer=2)
        
        self.menu.draw(surf)

        return surf

class PrepItemsState(State):
    name = 'prep_items'

    trade_name_surf = SPRITES.get('trade_name')

    def start(self):
        self.unit = game.memory['current_unit']
        self.menu = menus.Convoy(self.unit, (WINWIDTH - 124, 40))
        
        self.state = 'free'
        self.sub_menu = None

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)
        elif 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('TradeRight')
            self.menu.move_left(first_push)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('TradeRight')
            self.menu.move_right(first_push)

        if event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            if self.state == 'free':
                current = self.menu.get_current()
                context = self.menu.get_context()
                if context == 'inventory':
                    if current:
                        self.state = 'owner_item'
                        topleft = (0, 0)
                        options = ['Store', 'Trade']
                        if item_system.can_use(self.unit, current) and \
                                item_system.available(self.unit, current) and \
                                item_system.can_use_in_base(self.unit, current):
                            options.append('Use')
                        if convoy_funcs.can_restock(current):
                            options.append('Restock')
                        self.sub_menu = menus.Choice(current, options, topleft)
                    else:
                        self.menu.move_to_convoy()
                elif context == 'convoy':
                    if current:
                        if item_system.can_use(self.unit, current) and \
                                item_system.available(self.unit, current) and \
                                item_system.can_use_in_base(self.unit, current):
                            self.state = 'convoy_item'
                            topleft = (0, 0)
                            if item_funcs.inventory_full(self.unit, current):
                                options = ['Trade', 'Use']
                            else:
                                options = ['Take', 'Use']
                            self.sub_menu = menus.Choice(current, options, topleft)
                        else:
                            if item_funcs.inventory_full(self.unit, current):
                                self.state = 'trade_inventory'
                                self.menu.move_to_inventory()
                            else:
                                convoy_funcs.take_item(current, self.unit)
                    else:
                        pass  # Nothing happens
            elif self.state == 'owner_item':
                current = self.sub_menu.get_current()
                item = self.menu.get_current()
                if current == 'Store':
                    convoy_funcs.store_item(item, self.unit)
                elif current == 'Trade':
                    self.state = 'trade_convoy'
                    self.menu.move_to_convoy()
                elif current == 'Use':
                    combat = interaction.engage(self.unit, None, item)
                    game.combat_instance = combat
                    game.state.change('combat')
                elif current == 'Restock':
                    convoy_funcs.restock(item)
            elif self.state == 'convoy_item':
                current = self.sub_menu.get_current()
                item = self.menu.get_current()
                if current == 'Take':
                    convoy_funcs.take_item(item, self.unit)
                elif current == 'Trade':
                    self.state = 'trade_inventory'
                    self.menu.move_to_inventory()
                elif current == 'Use':
                    combat = interaction.engage(self.unit, None, item)
                    game.combat_instance = combat
                    game.state.change('combat')
            elif self.state == 'trade_convoy':
                unit_item = self.menu.get_inventory()
                convoy_item = self.menu.get_current()
                convoy_funcs.trade_items(convoy_item, unit_item, self.unit)
                self.menu.unlock()
            elif self.state == 'trade_inventory':
                convoy_item = self.menu.get_convoy()
                unit_item = self.menu.get_current()
                convoy_funcs.trade_items(convoy_item, unit_item, self.unit)
                self.menu.unlock()

        elif event == 'BACK':
            if self.menu.info_flag:
                self.menu.toggle_info()
                SOUNDTHREAD.play_sfx('Info Out')
            elif self.state == 'free':
                SOUNDTHREAD.play_sfx('Select 4')
                game.state.change('transition_pop')
            elif self.state == 'owner_item':
                self.sub_menu = None
                self.state = 'free'
            elif self.state == 'convoy_item':
                self.sub_menu = None
                self.state = 'free'
            elif self.state == 'trade_convoy':
                self.menu.move_to_inventory()
                self.menu.unlock()
                self.state = 'free'
            elif self.state == 'trade_inventory':
                self.menu.move_to_convoy()
                self.menu.unlock()
                self.state = 'free'

        elif event == 'INFO':
            if self.state in ('free', 'trade_convoy', 'trade_inventory'):
                self.menu.toggle_info()
                if self.menu.info_flag:
                    SOUNDTHREAD.play_sfx('Info In')
                else:
                    SOUNDTHREAD.play_sfx('Info Out')

    def update(self):
        self.menu.update()
        if self.sub_menu:
            self.sub_menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        self.menu.draw(surf)
        if self.sub_menu:
            self.sub_menu.draw(surf)
        return surf

class PrepRestockState(State):
    name = 'prep_restock'

class PrepMarketState(State):
    name = 'prep_market'
