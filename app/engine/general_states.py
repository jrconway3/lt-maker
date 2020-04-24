from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.state import MapState
from app.engine.game_state import game
from app.engine import action, menus, interaction, combat, image_mods

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
            # TODO
            # game.state.change('status_upkeep') 
            game.state.change('phase_change')
            # EVENTS TRIGGER HERE
        else:
            game.state.change('ai')
            # game.state.change('status_upkeep')
            game.state.change('phase_change')
            # game.state.change('end_step')

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
        # game.boundary.show()
        # The turnwheel will not be able to go before this moment
        if game.turncount == 1:
            game.action_log.set_first_free_action()

    def take_input(self, event):
        game.cursor.take_input()
        
        if event == 'INFO':
            if game.cursor.get_hover():
                # info_menu.start()
                pass
            else:
                # game.boundary.toggle_all_enemy_attacks()
                pass
        elif event == 'AUX':
            pass
        elif event == 'SELECT':
            cur_pos = game.cursor.position
            cur_unit = game.grid.get_unit(cur_pos)
            if cur_unit:
                game.cursor.cur_unit = cur_unit
                if cur_unit.team == 'player' and 'un_selectable' not in cur_unit.status_bundle:
                    game.state.change('move')
        elif event == 'BACK':
            pass
        elif event == 'START':
            pass

    def update(self):
        super().update()
        game.highlight.handle_hover()

    def end(self):
        game.highlight.remove_highlights()

class OptionChildState(MapState):
    name = 'option_child'

    def begin(self):
        selection = game.memory['option_owner']
        options = ['Yes', 'No']
        self.menu = menus.Choice(selection, options, game.memory['option_child'])

    def take_input(self, event):
        if event == 'DOWN':
            self.menu.move_down()
        elif event == 'UP':
            self.menu.move_up()

        elif event == 'BACK':
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            if selection == 'Yes':
                if self.menu.owner == 'End':
                    game.state.change('ai')
                elif self.menu.owner == 'Suspend':
                    game.state.back()
                    game.state.back()
                    logger.info('Suspending game...')
                    save.suspend_game(game, 'suspend')
                    game.state.clear()
                    game.state.change('title_start')
                elif self.menu.owner == 'Save':
                    game.state.back()
                    game.state.back()
                    logger.info('Creating battle save...')
                    game.memory['save_kind'] = 'battle'
                    game.state.change('title_save')
                    game.state.change('transition_out')
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
                game.state.back()

    def draw(self, surf):
        surf = super().draw(surf)
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
            game.state.clear()
            game.state.change('free')
            if cur_unit.has_attacked:
                action.do(action.Wait(self.cur_unit))
            else:
                cur_unit.sprite.change_state('normal')

        elif event == 'SELECT':
            if game.cursor.position == cur_unit.position:
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
                if game.grid.get_unit(game.cursor.position):
                    # ERROR!
                    pass
                else:
                    if cur_unit.has_attacked:
                        cur_unit.current_move = action.CantoMove(cur_unit, game.cursor.position)
                        game.state.change('canto_wait')
                    else:
                        cur_unit.current_move = action.Move(cur_unit, game.cursor.position)
                        game.state.change('menu')
                    game.state.change('movement')
                    action.do(cur_unit.current_move)
            else:
                # Error!
                pass

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

class MenuState(MapState):
    name = 'menu'
    normal_options = {'Item', 'Wait', 'Take', 'Give', 'Rescue', 'Trade', 'Drop', 'Visit', 'Armory', 'Vendor', 'Spells', 'Attack', 'Steal', 'Shove'}

    def begin(self):
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit

        valid_moves = {self.cur_unit.position}

        if not self.cur_unit.has_attacked:
            self.cur_unit.sprite.change_state('menu')
            spell_targets = game.targets.get_all_spell_targets(self.cur_unit)
            atk_targets = game.targets.get_all_weapon_targets(self.cur_unit)
        else:
            self.cur_unit.sprite.change_state('selected')
            spell_targets = set()
            atk_targets = set()

        if spell_targets:
            valid_attacks = game.targets.get_possible_spell_attacks(self.cur_unit, valid_moves)
            game.highlight.display_possible_spell_attacks(valid_attacks)
        if atk_targets:
            valid_attacks = game.targets.get_possible_attacks(self.cur_unit, valid_moves)
            game.highlight.display_possible_attacks(valid_attacks)
        if self.cur_unit.has_canto():
            # Shows the canto moves in the menu
            game.highlight.display_moves(game.targets.get_valid_moves(self.cur_unit))
        # Aura
        game.cursor.set_pos(self.cur_unit.position)

        options = []

        adj_positions = game.targets.get_adjacent_positions(self.cur_unit.position)
        adj_units = [game.grid.get_unit(pos) for pos in adj_positions]
        adj_units = [_ for _ in adj_units if _]  # Remove Nones
        adj_allies = [unit for unit in adj_units if game.targets.check_ally(self.cur_unit, unit)]

        # If the unit has valid targets
        if atk_targets:
            options.append("Attack")
        # If the unit has valid spell targets
        if spell_targets:
            options.append("Spell")
        # If the unit has a traveler
        if self.cur_unit.traveler and not self.cur_unit.has_attacked:
            for adj_pos in adj_positions:
                # If at least one adjacent, passable position is free of units
                tile = game.tilemap.tiles[adj_pos]
                terrain = DB.terrain.get(tile.terrain_nid)
                traveler = game.level.units.get(self.cur_unit.traveler)
                mgroup = DB.classes.get(traveler.klass).movement_group
                if not game.grid.get_unit(adj_pos) and DB.mcost.get_mcost(mgroup, terrain.mtype) < game.equations.movement(traveler):
                    options.append("Drop")
                    break
        if adj_allies:
            # If the unit does not have a travler
            if not self.cur_unit.traveler and not self.cur_unit.has_attacked:
                # If Rescue AID is higher than Rescue Weight
                if any(not ally.traveler and game.equations.rescue_aid(self.cur_unit) > game.equations.rescue_weight(ally) for ally in adj_allies):
                    options.append("Rescue")
                if any(ally.traveler and game.equations.rescue_aid(self.cur_unit) > game.equations.rescue_weight(game.level.units.get(ally.traveler)) for ally in adj_allies):
                    options.append("Take")
            # If the unit has a traveler
            if self.cur_unit.traveler and not self.cur_unit.has_attacked:
                if any(not ally.traveler and game.equations.rescue_aid(ally) > game.equations.rescue_weight(game.level.units.get(self.cur_unit.traveler)) for ally in adj_allies):
                    options.append("Give")
        # If the unit has an item
        if self.cur_unit.items:
            options.append("Item")
        if adj_allies:
            if any(ally.team == self.cur_unit.team for ally in adj_allies):
                options.append("Trade")
        options.append("Wait")

        self.menu = menus.Choice(self.cur_unit, options)
        self.menu.set_limit(8)
        self.menu.set_color(['text_green' if option not in self.normal_options else 'text_white' for option in options])

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            self.menu.move_up(first_push)

        # Back, put unit back to where he/she started
        if event == 'BACK':
            if self.cur_unit.has_traded:
                if self.cur_unit.has_canto():
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
            selection = self.menu.get_current()
            print(selection)
            logger.info("Player selected %s", selection)
            game.highlight.remove_highlights()

            if selection == 'Attack':
                game.state.change('weapon_choice')
            elif selection == 'Spells':
                game.state.change('spell_choice')
            elif selection == 'Item':
                game.state.change('item')
            elif selection == 'Trade':
                pass
            elif selection == 'Rescue':
                pass
            elif selection == 'Take':
                pass
            elif selection == 'Drop':
                pass
            elif selection == 'Give':
                pass
            elif selection == 'Wait':
                game.state.clear()
                game.state.change('free')
                action.do(action.Wait(self.cur_unit))

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
        options = [item for item in self.cur_unit.items]
        self.menu = menus.Choice(self.cur_unit, options)

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            self.menu.move_up(first_push)

        if event == 'BACK':
            game.state.back()

        elif event == 'SELECT':
            game.memory['parent_menu'] = self.menu
            game.state.change('item_child')

        elif event == 'INFO':
            pass

    def update(self):
        super().update()
        self.menu.update_options(self.cur_unit.items)

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        return surf

class ItemChildState(MapState):
    name = 'item_child'

    def begin(self):
        parent_menu = game.memory['parent_menu']
        item = parent_menu.get_current()
        self.cur_unit = game.cursor.cur_unit

        options = []
        if item.weapon and self.cur_unit.can_wield(item):
            options.append("Equip")
        if item.usable and self.cur_unit.can_use(item):
            options.append("Use")
        if not item.locked:
            if 'convoy' in game.game_constants:
                options.append('Storage')
            else:
                options.append('Discard')

        self.menu = menus.Choice(item, options, parent_menu)

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            self.menu.move_up(first_push)

        if event == 'BACK':
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            item = self.menu.owner
            if selection == 'Use':
                if item.booster:  # Does not use interact object
                    game.state.clear()
                    game.state.change('free')
                    game.state.change('wait')
                    interaction.handle_booster(self.cur_unit, item)
                else:
                    game.combat = interaction.start_combat(self.cur_unit, self.cur_unit, self.cur_unit.position, [], item)
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
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        return surf

class WeaponChoiceState(MapState):
    name = 'weapon_choice'

    def get_options(self, unit):
        options = [item for item in unit.items if item.weapon and unit.can_wield(item)]
        # Skill straining
        options = [item for item in options if game.targets.get_valid_weapon_targets(unit, item)]
        return options

    def disp_attacks(self, unit, item):
        valid_attacks, valid_splash = game.targets.get_attacks(unit, item)
        game.highlight.display_possible_attacks(valid_attacks)
        game.highlight.display_possible_attacks(valid_splash, light=True)

    def begin(self):
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit
        self.cur_unit.sprite.change_state('chosen')
        options = self.get_options(self.cur_unit)
        self.menu = menus.Choice(self.cur_unit, options)
        self.disp_attacks(self.cur_unit, self.menu.get_current())

    def proceed(self):
        game.state.change('attack')

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            self.menu.move_down(first_push)
            game.highlight.remove_highlights()
            self.disp_attacks(self.cur_unit, self.menu.get_current())
        elif 'UP' in directions:
            self.menu.move_up(first_push)
            game.highlight.remove_highlights()

        if event == 'BACK':
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            action.do(action.EquipItem(self.cur_unit, selection))
            self.proceed()

        elif event == 'INFO':
            pass

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        return surf

    def end(self):
        game.highlight.remove_highlights()

class SpellChoiceState(WeaponChoiceState):
    name = 'spell_choice'

    def get_options(self, unit):
        options = [item for item in unit.items if item.spell and unit.can_wield(item)]
        # Skill straining
        options = [item for item in options if game.targets.get_valid_spell_targets(unit, item)]
        return options

    def disp_attacks(self, unit, item):
        spell_attacks = game.targets.get_spell_attacks(unit, item)
        game.highlight.display_possible_spells(spell_attacks)

    def proceed(self):
        game.state.change('spell')

class AttackState(MapState):
    name = 'attack'

    def display_single_attack(self, weapon):
        game.highlight.remove_highlights()
        attack_position, splash_positions = \
            interaction.get_aoe(weapon, self.attacker, self.attacker.position, game.cursor.position)
        game.highlight.display_possible_attacks({attack_position})
        game.highlight.display_possible_attacks(splash_positions, light=True)

    def begin(self):
        game.cursor.combat_show()
        self.attacker = game.cursor.cur_unit
        weapon = self.attacker.get_weapon()
        targets = game.targets.get_valid_weapon_targets(self.attacker, weapon)
        self.selection = SelectionHelper(targets)
        closest_position = self.selection.get_closest(game.cursor.position)
        game.cursor.set_pos(closest_position)
        self.display_single_attack(weapon)

        self.fluid.update_speed(cf.SETTINGS['cursor_speed'])

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

        if event == 'BACK':
            game.state.back()

        elif event == 'SELECT':
            weapon = self.attacker.get_weapon()
            defender, splash = interaction.convert_positions(self.attacker, self.attacker.position, game.cursor.position, weapon)
            game.combat_instance = interaction.start_combat(self.attacker, defender, game.cursor.position, splash, weapon)
            game.state.change('combat')

        if directions:
            self.display_single_attack()

    def draw(self, surf):
        surf = super().draw(surf)
        # TODO Draw attack info
        return surf

    def end(self):
        game.highlight.remove_highlights()

class SpellState(MapState):
    name = 'spell'

    def display_single_attack(self, item):
        game.highlight.remove_highlights()
        attack_position, splash_positions = \
            interaction.get_aoe(item, self.attacker, self.attacker.position, game.cursor.position)
        if attack_position:
            game.highlight.display_possible_spells({attack_position})
        game.highlight.display_possible_spells(splash_positions)

    def begin(self):
        game.cursor.combat_show()
        self.attacker = game.cursor.cur_unit
        spell = self.attacker.get_spell()
        targets = game.targets.get_valid_spell_targets(self.attacker, spell)
        self.selection = SelectionHelper(targets)
        if spell.heal:
            units = [game.level.units.get(game.grid.get_unit(pos)) for pos in targets]
            units = sorted(units, key=lambda unit: unit.get_hp())
            closest_position = units[0].position
        else:
            closest_position = self.selection.get_closest(game.cursor.position)
        game.cursor.set_pos(closest_position)
        
        # spell_attacks = game.target.get_spell_attacks(self.attacker, spell)
        # game.highlight.display_possible_spells(spell_attacks)
        self.display_single_attack(spell)

        self.fluid.update_speed(cf.SETTINGS['cursor_speed'])

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

        if event == 'BACK':
            game.state.back()

        elif event == 'SELECT':
            spell = self.attacker.get_spell()
            defender, splash = interaction.convert_positions(self.attacker, self.attacker.position, game.cursor.position, spell)
            game.combat_instance = interaction.start_combat(self.attacker, defender, game.cursor.position, splash, spell)
            game.state.change('combat')

        if directions:
            self.display_single_attack()

    def draw(self, surf):
        surf = super().draw(surf)
        # TODO Draw attack info
        return surf

    def end(self):
        game.highlight.remove_highlights()

class CombatState(MapState):
    name = 'combat'
    fuzz_background = image_mods.make_translucent(SPRITES.get('BlackBackground'), 0.25)
    dark_fuzz_background = image_mods.make_translucent(SPRITES.get('BlackBackground'), 0.5)

    def start(self):
        self.skip = False
        width = game.tilemap.width * TILEWIDTH
        height = game.tilemap.height * TILEHEIGHT
        self.unit_surf = engine.create_surface((width, height), transparent=True)
        self.is_animation_combat = isinstance(game.combat_instance, combat.AnimationCombat)

    def begin(self):
        game.cursor.hide()

    def take_input(self, event):
        if event == 'START' and not self.skip:
            self.skip = True
            game.combat_instance.skip()
        elif event == 'BACK':
            # Arena
            pass

    def update(self):
        super().update()
        done = game.combat_instance.update()
        if self.skip and not self.is_animation_combat:
            while not done:
                done = game.combat_instance.update()

    def draw(self, surf):
        if self.is_animation_combat:
            pass
        else:
            surf = super().draw(surf)
            surf = game.combat_instance.draw(surf)
        return surf
