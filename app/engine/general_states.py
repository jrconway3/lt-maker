from collections import OrderedDict

from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH
from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.sound import SOUNDTHREAD
from app.engine.state import State, MapState
import app.engine.config as cf
from app.engine.game_state import game
from app.engine import engine, action, menus, interaction, image_mods, \
    banner, save, phase, skill_system, target_system, item_system, \
    item_funcs, ui_view, info_menu, base_surf, gui, background, dialog, \
    text_funcs
from app.engine.selection_helper import SelectionHelper
from app.engine.abilities import ABILITIES

import logging
logger = logging.getLogger(__name__)

class TurnChangeState(MapState):
    name = 'turn_change'

    def begin(self):
        if game.phase.get_current() == 'player':
            # TODO Handle support increments
            game.memory['previous_cursor_position'] = game.cursor.position
        # Clear all previous states in state machine except me
        game.state.refresh()
        game.state.back()  # Turn Change should only last 1 frame

    def end(self):
        game.phase.next()  # Go to next phase
        # If entering player phase
        if game.phase.get_current() == 'player':
            action.do(action.IncrementTurn())
            game.state.change('free')
            game.state.change('status_upkeep') 
            game.state.change('phase_change')
            # EVENTS TRIGGER HERE
            game.events.trigger('turn_change')
            if game.turncount - 1 <= 0:  # Beginning of the level
                game.events.trigger('level_start')
        else:
            game.state.change('ai')
            game.state.change('status_upkeep')
            game.state.change('phase_change')
            # game.state.change('end_step')
            # EVENTS TRIGGER HERE
            if game.phase.get_current() == 'enemy':
                game.events.trigger('enemy_turn_change')

    def take_input(self, event):
        return 'repeat'

class PhaseChangeState(MapState):
    name = 'phase_change'

    def begin(self):
        self.save_state()
        logger.info("Phase Change Start")
        # These are done here instead of in turnchange because
        # introScript and other event scripts will have to go on the stack
        # in between this and turn change
        # And they technically happen before I want the player to have the turnwheel locked
        # units reset, etc.
        action.do(action.LockTurnwheel(game.phase.get_current() != 'player'))
        action.do(action.ResetAll([unit for unit in game.level.units if not unit.dead]))
        game.cursor.hide()
        game.phase.slide_in()

    def update(self):
        super().update()
        done = game.phase.update()
        if done:
            game.state.back()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = game.phase.draw(surf)
        return surf

    def end(self):
        logger.info("Phase Change End")
        phase.fade_in_phase_music()

    def save_state(self):
        if game.phase.get_current() == 'player':
            logger.info("Saving as we enter player phase!")
            name = game.level.nid + '_' + str(game.turncount)
            # TODO SUSPEND
        elif game.phase.get_current() == 'enemy':
            logger.info("Saving as we enter enemy phase!")
            name = game.level.nid + '_' + str(game.turncount) + 'b'
            # TODO SUSPEND

class FreeState(MapState):
    name = 'free'

    def begin(self):
        game.cursor.show()
        game.boundary.show()
        # The turnwheel will not be able to go before this moment
        phase.fade_in_phase_music()
        if game.turncount == 1:
            game.action_log.set_first_free_action()

    def take_input(self, event):
        game.cursor.take_input()
        
        if event == 'INFO':
            info_menu.handle_info()

        elif event == 'AUX':
            pass

        elif event == 'SELECT':
            cur_pos = game.cursor.position
            cur_unit = game.board.get_unit(cur_pos)
            if cur_unit and not cur_unit.finished:
                game.cursor.cur_unit = cur_unit
                if skill_system.can_select(cur_unit):
                    SOUNDTHREAD.play_sfx('Select 3')
                    game.state.change('move')
                else:
                    if cur_unit.team == 'enemy' or cur_unit.team == 'enemy2':
                        SOUNDTHREAD.play_sfx('Select 3')
                        game.boundary.toggle_unit(cur_unit)
                    else:
                        SOUNDTHREAD.play_sfx('Error')
            else:
                SOUNDTHREAD.play_sfx('Select 2')
                game.state.change('option_menu')

        elif event == 'BACK':
            pass

        elif event == 'START':
            SOUNDTHREAD.play_sfx('Select 5')

    def update(self):
        super().update()
        game.highlight.handle_hover()

        # Auto-end turn
        # Check to see if all ally units have completed their turns and no unit is active and the game is in the free state.
        if cf.SETTINGS['autoend_turn'] and any(unit.position for unit in game.level.units) and \
                all(unit.finished for unit in game.level.units if unit.position and unit.team == 'player'):
            # End the turn
            logger.info('Autoending turn.')
            game.state.change('turn_change')
            return 'repeat'

    def end(self):
        game.highlight.remove_highlights()

def suspend():
    game.state.back()
    game.state.back()
    game.state.process_temp_state()
    logger.info('Suspending game...')
    save.suspend_game(game, 'suspend')
    game.state.clear()
    game.state.change('title_start')

def battle_save():
    game.state.back()
    game.state.back()
    logger.info('Creating battle save...')
    game.memory['save_kind'] = 'battle'
    game.state.change('title_save')
    game.state.change('transition_out')

class OptionMenuState(MapState):
    name = 'option_menu'

    def start(self):
        game.cursor.hide()
        options = ['Unit', 'Objective', 'Options']
        info_desc = ['Unit_desc', 'Objective_desc', 'Options_desc']
        ignore = [True, True, False]
        if DB.constants.get('permadeath').value:
            options.append('Suspend')
            info_desc.append('Suspend_desc')
            ignore.append(False)
        else:
            options.append('Save')
            info_desc.append('Save_desc')
            ignore.append(False)
        options.append('End')
        info_desc.append('End_desc')
        ignore.append(False)
        if DB.constants.get('turnwheel').value:
            options.insert(1, 'Turnwheel')
            info_desc.insert(1, 'Turnwheel_desc')
            ignore.insert(1, False)
        self.menu = menus.Choice(None, options, info=info_desc)
        self.menu.set_ignore(ignore)

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

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            if selection == 'End':
                if cf.SETTINGS['confirm_end']:
                    game.memory['option_owner'] = selection
                    game.memory['option_menu'] = self.menu
                    game.state.change('option_child')
                else:
                    game.state.change('ai')
            elif selection == 'Suspend' or selection == 'Save':
                if cf.SETTINGS['confirm_end']:
                    game.memory['option_owner'] = selection
                    game.memory['option_menu'] = self.menu
                    game.state.change('option_child')
                else:
                    if self.menu.owner == 'Suspend':
                        suspend()
                    elif self.menu.owner == 'Save':
                        battle_save()
            elif selection == 'Objective':
                game.state.change('objective')
                game.state.change('transition_out')
            elif selection == 'Options':
                game.memory['next_state'] = 'settings_menu'
                game.state.change('transition_to')
            elif selection == 'Unit':
                pass
                # game.state.change('unit_menu')
                # game.state.change('transition_out')
            elif selection == 'Turnwheel':
                if cf.SETTINGS['debug'] or game.game_vars.get('_current_turnwheel_uses', 1) > 0:
                    game.state.change('turnwheel')
                else:
                    alert = banner.Custom("Turnwheel_empty")
                    # Add banner sound
                    game.alerts.append(alert)
                    game.state.change('alert')

        elif event == 'INFO':
            self.menu.toggle_info()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        self.menu.draw(surf)
        return surf

class OptionChildState(State):
    name = 'option_child'
    transparent = True

    def begin(self):
        if 'option_owner' in game.memory:
            selection = game.memory['option_owner']
            topleft = game.memory['option_menu']
        else:
            selection = None
            topleft = None
        options = ['Yes', 'No']
        self.menu = menus.Choice(selection, options, topleft)

    def take_input(self, event):
        self.menu.handle_mouse()
        if event == 'DOWN':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down()
        elif event == 'UP':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            if selection == 'Yes':
                SOUNDTHREAD.play_sfx('Select 1')
                if self.menu.owner == 'End':
                    game.state.change('ai')
                elif self.menu.owner == 'Suspend':
                    suspend()
                elif self.menu.owner == 'Save':
                    battle_save()
                elif self.menu.owner == 'Discard' or self.menu.owner == 'Storage':
                    item = game.memory['option_item']
                    cur_unit = game.memory['option_unit']
                    if item in cur_unit.items:
                        action.do(action.DiscardItem(cur_unit, item))
                    if cur_unit.items:
                        game.state.back()
                        game.state.back()
                    else:  # If the unit has no more items, head all the way back to menu
                        game.state.back()
                        game.state.back()
                        game.state.back()
            else:
                SOUNDTHREAD.play_sfx('Select 4')
                game.state.back()

    def update(self):
        self.menu.update()

    def draw(self, surf):
        surf = self.menu.draw(surf)
        return surf

class MoveState(MapState):
    name = 'move'

    def begin(self):
        game.cursor.show()
        cur_unit = game.cursor.cur_unit
        cur_unit.sprite.change_state('selected')

        self.valid_moves = game.highlight.display_highlights(cur_unit)

        game.cursor.place_arrows()

    def take_input(self, event):
        game.cursor.take_input()
        cur_unit = game.cursor.cur_unit

        if event == 'INFO':
            pass
        elif event == 'AUX':
            pass

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.clear()
            game.state.change('free')
            if cur_unit.has_attacked:
                action.do(action.Wait(self.cur_unit))
            else:
                cur_unit.sprite.change_state('normal')

        elif event == 'SELECT':
            if game.cursor.position == cur_unit.position:
                SOUNDTHREAD.play_sfx('Select 2')
                if cur_unit.has_attacked:
                    game.state.clear()
                    game.state.change('free')
                    action.do(action.Wait(self.cur_unit))
                else:
                    # Just move in place
                    cur_unit.current_move = action.Move(cur_unit, game.cursor.position)
                    action.execute(cur_unit.current_move)
                    game.state.change('menu')

            elif game.cursor.position in self.valid_moves:
                if game.board.get_unit(game.cursor.position):
                    SOUNDTHREAD.play_sfx('Error')
                else:
                    # Sound -- ADD FOOTSTEP SOUNDS
                    if cur_unit.has_attacked:
                        cur_unit.current_move = action.CantoMove(cur_unit, game.cursor.position)
                        game.state.change('canto_wait')
                    else:
                        cur_unit.current_move = action.Move(cur_unit, game.cursor.position)
                        game.state.change('menu')
                    game.state.change('movement')
                    action.do(cur_unit.current_move)
            else:
                SOUNDTHREAD.play_sfx('Error')

    def end(self):
        game.cursor.remove_arrows()
        game.highlight.remove_highlights()

class MovementState(MapState):
    # Responsible for moving units that need to be moved
    name = 'movement'

    def begin(self):
        game.cursor.hide()

    def update(self):
        super().update()
        game.moving_units.update()
        if len(game.moving_units) <= 0:
            game.state.back()
            return 'repeat'

class WaitState(MapState):
    """
    State that forces all units that should have waited to wait
    """
    name = 'wait'

    def update(self):
        super().update()
        game.state.back()
        for unit in game.level.units:
            if unit.has_attacked and not unit.finished:
                action.do(action.Wait(unit))
        return 'repeat'

class CantoWaitState(MapState):
    name = 'canto_wait'

    def start(self):
        self.cur_unit = game.cursor.cur_unit
        self.menu = menus.Choice(self.cur_unit, ['Wait'])

    def begin(self):
        self.cur_unit.sprite.change_state('selected')

    def take_input(self, event):
        if event == 'INFO':
            pass

        elif event == 'SELECT':
            game.state.clear()
            game.state.change('free')
            action.do(action.Wait(self.cur_unit))

        elif event == 'BACK':
            if self.cur_unit.current_move:
                action.reverse(self.cur_unit.current_move)
                self.cur_unit.current_move = None

class MoveCameraState(MapState):
    name = 'move_camera'

    def update(self):
        super().update()
        if game.camera.at_rest():
            game.state.back()
            return 'repeat'

class MenuState(MapState):
    name = 'menu'
    normal_options = {'Item', 'Wait', 'Take', 'Give', 'Rescue', 'Trade', 'Drop', 'Visit', 'Armory', 'Vendor', 'Spells', 'Attack', 'Steal', 'Shove'}

    def begin(self):
        # Play this here because there's a gap in sound while unit is moving
        SOUNDTHREAD.play_sfx('Select 2')
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit

        if not self.cur_unit.has_attacked:
            self.cur_unit.sprite.change_state('menu')
        else:
            self.cur_unit.sprite.change_state('selected')
        game.cursor.set_pos(self.cur_unit.position)

        options = []

        # Handle region event options
        self.valid_regions = []
        for region in game.level.regions:
            if region.region_type == 'Event' and region.contains(self.cur_unit.position):
                try:
                    unit = self.cur_unit  # For condition
                    logger.debug("Testing region: %s %s", region.condition, eval(region.condition))
                    # No duplicates
                    if eval(region.condition) and region.sub_nid not in options:
                        options.append(region.sub_nid)
                        self.valid_regions.append(region)
                except:
                    logger.error("Region condition {%s} could not be evaluated" % region.condition)

        # Handle regular ability options
        self.target_dict = OrderedDict()
        for ability in ABILITIES:
            t = ability.targets(self.cur_unit)
            self.target_dict[ability.name] = ability
            if t:
                options.append(ability.name)
        options.append("Wait")

        # Draw highlights
        for ability in ABILITIES:
            if ability.name in options:
                ability.highlights(self.cur_unit)
        if skill_system.has_canto(self.cur_unit):
            # Shows the canto moves in the menu
            moves = target_system.get_valid_moves(self.cur_unit)
            game.highlight.display_moves(moves)

        self.menu = menus.Choice(self.cur_unit, options)
        self.menu.set_limit(8)
        self.menu.set_color(['text-green' if option not in self.normal_options else 'text-white' for option in options])

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

        # Back, put unit back to where he/she started
        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            if self.cur_unit.has_traded:
                if skill_system.has_canto(self.cur_unit):
                    game.cursor.set_pos(self.cur_unit.position)
                    game.state.change('move')
                else:
                    game.state.clear()
                    game.state.change('free')
                    action.do(action.Wait(self.cur_unit))
            else:
                if self.cur_unit.current_move:
                    action.reverse(self.cur_unit.current_move)
                    self.cur_unit.current_move = None
                game.cursor.set_pos(self.cur_unit.position)
                game.state.change('move')

        elif event == 'INFO':
            pass

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            logger.info("Player selected %s", selection)
            game.highlight.remove_highlights()

            if selection == 'Item':
                game.state.change('item')
            elif selection in ('Attack', 'Spell'):
                game.memory['targets'] = self.target_dict[selection].targets(self.cur_unit)
                game.state.change('weapon_choice')
            elif selection == 'Wait':
                game.state.clear()
                game.state.change('free')
                action.do(action.Wait(self.cur_unit))
            # A region event
            elif selection in [region.sub_nid for region in self.valid_regions]:
                for region in self.valid_regions:
                    if region.sub_nid == selection:
                        did_trigger = game.events.trigger(selection, self.cur_unit, position=self.cur_unit.position, region=region)
                        if did_trigger and region.only_once:
                            # No longer exists
                            game.level.regions.delete(region)
                        if did_trigger:
                            action.do(action.HasAttacked(self.cur_unit))
            else:  # Selection is one of the other abilities
                game.memory['ability'] = self.target_dict[selection]
                game.state.change('targeting')

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        return surf

    def end(self):
        game.highlight.remove_highlights()

class ItemState(MapState):
    name = 'item'

    def start(self):
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit
        options = item_funcs.get_all_items(self.cur_unit)
        self.menu = menus.Choice(self.cur_unit, options)

    def begin(self):
        self.menu.update_options(item_funcs.get_all_items(self.cur_unit))

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

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            game.memory['parent_menu'] = self.menu
            game.state.change('item_child')

        elif event == 'INFO':
            self.menu.toggle_info()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        return surf

class ItemChildState(MapState):
    name = 'item_child'
    transparent = True

    def begin(self):
        parent_menu = game.memory['parent_menu']
        item = parent_menu.get_current()
        self.cur_unit = game.cursor.cur_unit

        options = []
        if item_system.equippable(self.cur_unit, item) and \
                item_system.available(self.cur_unit, item):
            options.append("Equip")
        if item_system.can_use(self.cur_unit, item) and \
                item_system.available(self.cur_unit, item):
            defender, splash = item_system.splash(self.cur_unit, item, self.cur_unit.position)
            if item_system.target_restrict(self.cur_unit, item, defender, splash):
                options.append("Use")
        if not item_system.locked(self.cur_unit, item):
            if 'convoy' in game.game_vars:
                options.append('Storage')
            else:
                options.append('Discard')

        self.menu = menus.Choice(item, options, parent_menu)

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

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            item = self.menu.owner
            if selection == 'Use':
                combat = interaction.engage(self.cur_unit, [self.cur_unit.position], item)
                game.combat_instance = combat
                game.state.change('combat')
            elif selection == 'Equip':
                action.do(action.EquipItem(self.cur_unit, item))
                game.memory['parent_menu'].current_index = 0  # Reset selection
                game.state.back()
            elif selection == 'Storage' or selection == 'Discard':
                game.memory['option_owner'] = selection
                game.memory['option_item'] = item
                game.memory['option_unit'] = self.cur_unit
                game.memory['option_menu'] = self.menu
                game.state.change('option_child')

    def update(self):
        self.menu.update()

    def draw(self, surf):
        surf = self.menu.draw(surf)
        return surf

class ItemDiscardState(MapState):
    name = 'item_discard'

    def start(self):
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit
        options = self.cur_unit.items
        self.menu = menus.Choice(self.cur_unit, options)

        if 'convoy' in game.game_vars:
            self.pennant = banner.Pennant('Choose item to send to storage')
        else:
            self.pennant = banner.Pennant('Choose item to discard')

    def begin(self):
        self.menu.update_options(self.cur_unit.items)
        # Don't need to do this if we are under items
        if (len(self.cur_unit.accessories) <= DB.constants.value('max_accessories') and
                len(self.cur_unit.nonaccessories) <= DB.constants.value('max_items')):
            game.state.back()
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

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Error')

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            game.memory['option_owner'] = selection
            game.memory['option_item'] = selection
            game.memory['option_unit'] = self.cur_unit
            game.memory['option_menu'] = self.menu
            game.state.change('option_child')

        elif event == 'INFO':
            self.menu.toggle_info()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        if self.pennant:
            draw_on_top = game.cursor.position[1] >= game.tilemap.height - 1
            self.pennant.draw(surf, draw_on_top)
        surf = self.menu.draw(surf)
        return surf

class WeaponChoiceState(MapState):
    name = 'weapon_choice'

    def get_options(self, unit) -> list:
        options = target_system.get_all_weapons(unit)
        # Skill straining
        options = [option for option in options if target_system.get_valid_targets(unit, option)]
        return options

    def disp_attacks(self, unit, item):
        valid_attacks = target_system.get_attacks(unit, item)
        game.highlight.display_possible_attacks(valid_attacks)

    def begin(self):
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit
        self.cur_unit.sprite.change_state('chosen')
        options = self.get_options(self.cur_unit)
        self.menu = menus.Choice(self.cur_unit, options)
        self.item_desc_panel = ui_view.ItemDescriptionPanel(self.cur_unit, self.menu.get_current())
        self.disp_attacks(self.cur_unit, self.menu.get_current())

    def proceed(self):
        game.state.change('attack')

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
            current = self.menu.get_current()
            self.item_desc_panel.set_item(current)
            game.highlight.remove_highlights()
            self.disp_attacks(self.cur_unit, current)

        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)
            current = self.menu.get_current()
            self.item_desc_panel.set_item(current)
            game.highlight.remove_highlights()
            self.disp_attacks(self.cur_unit, current)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            action.do(action.EquipItem(self.cur_unit, selection))
            game.memory['item'] = selection
            game.state.change('combat_targeting')

        elif event == 'INFO':
            self.menu.toggle_info()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        surf = self.item_desc_panel.draw(surf)
        return surf

    def end(self):
        game.highlight.remove_highlights()

class SpellChoiceState(WeaponChoiceState):
    name = 'spell_choice'

    def get_options(self, unit) -> list:
        options = target_system.get_all_spells()
        # Skill straining
        options = [option for option in options if target_system.get_valid_targets(unit, option)]
        return options

    def disp_attacks(self, unit, item):
        spell_attacks = target_system.get_spell_attacks(unit, item)
        game.highlight.display_possible_spells(spell_attacks)

class TargetingState(MapState):
    name = 'targeting'

    def start(self):
        self.cur_unit = game.cursor.cur_unit

        # Should always come with associated ability
        self.ability = game.memory.get('ability')
        good_pos = self.ability.targets(self.cur_unit)
        
        self.selection = SelectionHelper(good_pos)
        closest_pos = self.selection.get_closest(self.cur_unit.position)
        game.cursor.set_pos(closest_pos)

        self.pennant = banner.Pennant(self.name)

    def begin(self):
        game.cursor.combat_show()
        self.cur_unit.sprite.change_state('chosen')

    def take_input(self, event):
        self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            new_position = self.selection.get_down(game.cursor.position)
            game.cursor.set_pos(new_position)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            new_position = self.selection.get_up(game.cursor.position)
            game.cursor.set_pos(new_position)
        if 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            new_position = self.selection.get_left(game.cursor.position)
            game.cursor.set_pos(new_position)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            new_position = self.selection.get_right(game.cursor.position)
            game.cursor.set_pos(new_position)

        new_position = self.selection.handle_mouse()
        if new_position:
            game.cursor.set_pos(new_position)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            self.ability.do(self.cur_unit)

    def draw(self, surf):
        surf = super().draw(surf)
        if self.pennant:
            draw_on_top = game.cursor.position[1] >= game.tilemap.height - 1
            self.pennant.draw(surf, draw_on_top)
        return surf

class CombatTargetingState(MapState):
    name = 'combat_targeting'

    def start(self):
        self.cur_unit = game.cursor.cur_unit
        self.item = game.memory['item']

        self.num_targets = item_system.num_targets(self.cur_unit, self.item)
        self.current_target_idx = 0
        self.prev_targets = []

        positions = target_system.get_valid_targets(self.cur_unit, self.item)
        self.selection = SelectionHelper(positions)
        closest_pos = self.selection.get_closest(game.cursor.position)
        game.cursor.set_pos(closest_pos)

        game.ui_view.prepare_attack_info()
        self.display_single_attack()

    def begin(self):
        game.cursor.combat_show()

    def display_single_attack(self):
        game.highlight.remove_highlights()
        splash_positions = item_system.splash_positions(self.cur_unit, self.item, game.cursor.position)
        game.highlight.display_possible_attacks({game.cursor.position})
        game.highlight.display_possible_attacks(splash_positions, light=True)

    def take_input(self, event):
        self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            new_position = self.selection.get_down(game.cursor.position)
            game.cursor.set_pos(new_position)
        elif 'UP' in directions:
            new_position = self.selection.get_up(game.cursor.position)
            game.cursor.set_pos(new_position)
        if 'LEFT' in directions:
            new_position = self.selection.get_left(game.cursor.position)
            game.cursor.set_pos(new_position)
        elif 'RIGHT' in directions:
            new_position = self.selection.get_right(game.cursor.position)
            game.cursor.set_pos(new_position)

        new_position = self.selection.handle_mouse()
        if new_position:
            game.cursor.set_pos(new_position)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            self.current_target_idx += 1
            self.prev_targets.append(game.cursor.position)
            if self.current_target_idx < self.num_targets and self.selection.count() > 1:
                if not item_system.allow_same_target(self.cur_unit, self.item):
                    self.selection.remove_target(game.cursor.position)
                    closest_pos = self.selection.get_closest(game.cursor.position)
                    game.cursor.set_pos(closest_pos)
                self.begin()
                self.display_single_attack()
            else:
                combat = interaction.engage(self.cur_unit, self.prev_targets, self.item)
                game.combat_instance = combat
                game.state.change('combat')

        if directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.display_single_attack()

    def draw(self, surf):
        surf = super().draw(surf)
        if self.cur_unit and game.cursor.get_hover():
            game.ui_view.draw_attack_info(surf, self.cur_unit, game.cursor.get_hover())
        return surf

    def end(self):
        game.highlight.remove_highlights()
        game.ui_view.attack_info_disp = None

# class SpellTargetingState(MapState):
#     name = 'spell_targeting'

#     def display_single_attack(self):
#         game.highlight.remove_highlights()
#         splash_positions = item_system.splash_positions(self.cur_unit, self.item, game.cursor.position)
#         game.highlight.display_possible_spells(splash_positions)

class CombatState(MapState):
    name = 'combat'
    fuzz_background = image_mods.make_translucent(SPRITES.get('bg_black'), 0.25)
    dark_fuzz_background = image_mods.make_translucent(SPRITES.get('bg_black'), 0.5)

    def start(self):
        game.cursor.hide()
        self.skip = False
        width = game.tilemap.width * TILEWIDTH
        height = game.tilemap.height * TILEHEIGHT
        self.combat = game.combat_instance
        self.unit_surf = engine.create_surface((width, height), transparent=True)
        self.is_animation_combat = isinstance(self.combat, interaction.AnimationCombat)

    def take_input(self, event):
        if event == 'START' and not self.skip:
            self.skip = True
            self.combat.skip()
        elif event == 'BACK':
            # Arena
            pass

    def update(self):
        super().update()
        done = self.combat.update()
        if self.skip and not self.is_animation_combat:
            while not done:
                done = self.combat.update()

    def draw(self, surf):
        if self.is_animation_combat:
            pass
        else:
            surf = super().draw(surf)
            self.combat.draw(surf)
        return surf

class DyingState(MapState):
    name = 'dying'

    def begin(self):
        game.cursor.hide()

    def update(self):
        super().update()

        done = game.death.update()
        if done:
            game.state.back()
            return 'repeat'

class AlertState(State):
    name = 'alert'
    transparent = True

    def begin(self):
        if game.cursor:
            game.cursor.hide()

    def take_input(self, event):
        if game.alerts:
            alert = game.alerts[-1]

        if event and alert and alert.time_to_start and \
                engine.get_time() - alert.time_to_start > alert.time_to_wait:
            alert = game.alerts.pop()
            game.state.back()
            return 'repeat'

    def update(self):
        if game.alerts:
            alert = game.alerts[-1]
            alert.update()

    def draw(self, surf):
        if game.alerts:
            alert = game.alerts[-1]
            alert.draw(surf)
        return surf

class AIState(MapState):
    name = 'ai'

    def start(self):
        logger.info("Starting AI State")
        game.cursor.hide()
        self.unit_list = [unit for unit in game.level.units if unit.position and 
                          not unit.finished and unit.team == game.phase.get_current()]
        # Sort by distance to closest enemy (ascending)
        self.unit_list = sorted(self.unit_list, key=lambda unit: target_system.distance_to_closest_enemy(unit))
        # Sort ai groups together
        self.unit_list = sorted(self.unit_list, key=lambda unit: unit.get_group() or '')
        # Sort by ai priority
        self.unit_list = sorted(self.unit_list, key=lambda unit: DB.ai.get(unit.ai).priority)
        # Reverse, because we will be popping them off at the end
        self.unit_list.reverse()

        self.cur_unit = None

    def update(self):
        super().update()

        # Don't bother if someone is dying!!!
        if any(unit.is_dying for unit in game.level.units):
            return

        if (not self.cur_unit or not self.cur_unit.position) and self.unit_list:
            self.cur_unit = self.unit_list.pop()
            # also resets AI
            game.ai.load_unit(self.cur_unit)

        logger.info("Current AI: %s", self.cur_unit.nid if self.cur_unit else None)
        
        if self.cur_unit:
            did_something = game.ai.act()
            # Center camera on current unit
            if did_something and self.cur_unit.position:
                game.cursor.set_pos(self.cur_unit.position)
                game.state.change('move_camera')

            if game.ai.is_done():
                logger.info("Current AI %s is done with turn.", self.cur_unit.nid)
                action.do(action.Wait(self.cur_unit))
                game.ai.reset()
                self.cur_unit = None
        else:
            logger.info("AI Phase complete")
            game.ai.reset()
            self.unit_list.clear()
            self.cur_unit = None
            game.state.change('turn_change')
            return 'repeat'

class ShopState(State):
    name = 'shop'

    def start(self):
        self.unit = game.memory['current_unit']
        self.flavor = game.memory['shop_flavor']
        if self.flavor == 'vendor':
            self.portrait = SPRITES.get('vendor_portrait')
            self.opening_message = 'vendor_opener'
            self.buy_message = 'vendor_buy'
            self.back_message = 'vendor_back'
            self.leave_message = 'vendor_leave'
        else:
            self.portrait = SPRITES.get('armory_portrait')
            self.opening_message = 'armory_opener'
            self.buy_message = 'armory_buy'
            self.back_message = 'armory_back'
            self.leave_message = 'armory_leave'

        items = game.memory['shop_items']
        my_items = item_funcs.get_all_tradeable_items(self.unit)
        topleft = (44, 14)
        self.sell_menu = menus.Shop(self.unit, my_items, topleft, disp_value='sell')
        self.sell_menu.set_limit(5)
        self.sell_menu.set_hard_limit(True)
        self.sell_menu.gem = False
        self.sell_menu.shimmer = 2
        self.buy_menu = menus.Shop(self.unit, items, topleft, disp_value='buy')
        self.buy_menu.set_limit(5)
        self.buy_menu.set_hard_limit(True)
        self.buy_menu.gem = False
        self.buy_menu.shimmer = 2

        self.choice_menu = menus.Choice(self.unit, ["Buy", "Sell"], (80, 32), background=None)
        self.choice_menu.set_horizontal(True)
        self.menu = None  # For input

        self.state = 'open'
        self.current_msg = self.get_dialog(self.opening_message)

        self.message_bg = base_surf.create_base_surf((WINWIDTH + 8, 48), 'menu_bg_clear')
        self.money_counter_disp = gui.PopUpDisplay((223, 32))

        self.bg = background.create_background('rune_background')

        game.state.change('transition_in')
        return 'repeat'

    def get_dialog(self, text):
        return dialog.Dialog(text_funcs.translate(text))

    def update_options(self):
        self.sell_menu.update_options(item_funcs.get_all_tradeable_items(self.unit))

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions or 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions or 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        if event == 'SELECT':
            if self.state == 'open':
                SOUNDTHREAD.play_sfx('Select 1')
                if self.current_msg.is_done():
                    self.state = 'choice'
                    self.menu = self.choice_menu
                else:
                    self.current_msg.hurry_up()

            elif self.state == 'choice':
                SOUNDTHREAD.play_sfx('Select 1')
                current = self.choice_menu.get_current()
                if current == 'buy':
                    self.menu = self.buy_menu
                    self.state = 'buy'
                    self.current_msg = self.get_dialog(self.buy_message)
                elif current == 'sell' and item_funcs.get_all_tradeable_items(self.unit):
                    self.menu = self.sell_menu
                    self.state = 'sell'

            elif self.state == 'buy':
                item = self.buy_menu.get_current()
                if item:
                    value = item_system.buy_price(self.unit, item)
                    if game.get_money() - value >= 0:
                        SOUNDTHREAD.play_sfx('GoldExchange')
                        game.set_money(game.get_money() - value)
                        self.money_counter_disp.start(-value)
                        new_item = item_funcs.create_items(self.unit, item.nid)[0]
                        game.register_item(new_item)
                        if not item_funcs.inventory_full(self.unit, new_item):
                            self.unit.add_item(new_item)
                            self.current_msg = self.get_dialog('shop_buy_again')
                        elif 'convoy' in game.game_vars:
                            new_item.owner_nid = None
                            game.party.convoy.append(new_item)
                            self.current_msg = self.get_dialog('shop_convoy')
                        else:
                            self.current_msg = self.get_dialog('shop_max')
                            self.state = 'choice'
                            self.menu = self.choice_menu

                        self.update_options()
                    else:
                        # You don't have enough money
                        SOUNDTHREAD.play_sfx('Select 4')
                        self.current_msg = self.get_dialog('shop_no_money')

            elif self.state == 'sell':
                item = self.sell_menu.get_current()
                if item:
                    value = item_system.sell_price(self.unit, item)
                    if value:
                        SOUNDTHREAD.play_sfx('GoldExchange')
                        game.set_money(game.get_money() + value)
                        self.money_counter_disp.start(value)
                        self.unit.remove_item(item)
                        self.current_msg = self.get_dialog('shop_sell_again')
                        self.update_options()
                    else:
                        # No value, can't be sold
                        SOUNDTHREAD.play_sfx('Select 4')
                        self.current_msg = self.get_dialog('shop_no_value')
                else:
                    # You didn't choose anything to sell
                    SOUNDTHREAD.play_sfx('Select 4')

            elif self.state == 'close':
                SOUNDTHREAD.play_sfx('Select 1')
                if self.current_msg.is_done():
                    game.state.change('transition_pop')
                else:
                    self.current_msg.hurry_up()

        elif event == 'BACK':
            if self.state == 'open' or self.state == 'close':
                SOUNDTHREAD.play_sfx('Select 4')
                game.state.change('transition_pop')
            elif self.state == 'choice':
                SOUNDTHREAD.play_sfx('Select 4')
                self.state = 'close'
                self.current_msg = self.get_dialog(self.leave_message)
            elif self.state == 'buy' or self.state == 'sell':
                if self.menu.info_flag:
                    self.menu.toggle_info()
                    SOUNDTHREAD.play_sfx('Info Out')
                else:
                    SOUNDTHREAD.play_sfx('Select 4')
                    self.state = 'choice'
                    self.menu = self.choice_menu
                    self.current_msg = self.get_dialog('shop_again')

        elif event == 'INFO':
            if self.state == 'buy' or self.state == 'sell':
                self.menu.toggle_info()
                if self.menu.info_flag:
                    SOUNDTHREAD.play_sfx('Info In')
                else:
                    SOUNDTHREAD.play_sfx('Info Out')

    def update(self):
        self.current_msg.update()
        self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        surf.blit(self.message_bg, (-4, 8))
        if self.current_msg:
            self.current_msg.draw(surf)
        if self.state == 'sell':
            self.sell_menu.draw(surf)
        else:
            self.buy_menu.draw(surf)
        if self.state == 'choice' and self.current_msg.is_done():
            self.choice_menu.draw(surf)
        surf.blit(self.portrait, (3, 0))
        
        surf.blit(SPRITES.get('money_bg'), (172, 48))
        FONT['text-blue'].blit_right(str(game.get_money()), surf, (223, 48))
        self.money_counter_disp.draw(surf)
