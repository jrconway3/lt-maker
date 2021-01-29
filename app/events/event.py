from app.constants import WINWIDTH, WINHEIGHT, FRAMERATE
from app.resources.resources import RESOURCES
from app.engine.sound import SOUNDTHREAD
from app.data.database import DB
from app.events import event_commands, regions
from app.events.event_portrait import EventPortrait
from app.utilities import utils
from app.engine import dialog, engine, background, target_system, action, \
    interaction, item_funcs, item_system, banner, skill_system
from app.engine.objects.item import ItemObject
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

screen_positions = {'OffscreenLeft': -96, 
                    'FarLeft': -24,
                    'Left': 0,
                    'MidLeft': 24,
                    'CenterLeft': 24,
                    'CenterRight': 120,
                    'MidRight': 120,
                    'Right': 144,
                    'FarRight': 168,
                    'OffscreenRight': 240}

class Event():
    _transition_speed = 250
    _transition_color = (0, 0, 0)

    skippable = {"speak", "transition", "wait", "bop_portrait",
                 "sound", "location_card"}

    def __init__(self, commands, unit=None, unit2=None, position=None, region=None):
        self.commands = commands.copy()
        self.command_idx = 0

        self.background = None

        self.unit = self.unit1 = unit
        self.unit2 = unit2
        self.position = position
        self.region = region

        self.portraits = {}
        self.text_boxes = []
        self.other_boxes = []

        self.prev_state = None
        self.state = 'processing'

        self.wait_time = 0

        # Handles keeping the order that unit sprites should be drawn
        self.priority_counter = 1
        self.do_skip = False

        self.if_stack = [] # Keeps track of how many ifs we've encountered while searching for the bad ifs 'end'.
        self.parse_stack = [] # Keeps track of whether we've encountered a truth this level or not

        # For transition
        self.transition_state = None
        self.transition_progress = 0
        self.transition_update = 0
        self.transition_speed = self._transition_speed
        self.transition_color = self._transition_color

    def update(self):
        current_time = engine.get_time()
        # print(self.state)

        if self.state != self.prev_state:
            self.prev_state = self.state
            logger.debug("Event State: %s", self.state)

        if self.state == 'waiting':
            if current_time > self.wait_time:
                self.state = 'processing'

        elif self.state == 'processing':
            if self.command_idx >= len(self.commands):
                self.end()
            else:
                self.process()

        elif self.state == 'dialog':
            if self.text_boxes:
                if self.text_boxes[-1].is_done():
                    self.state = 'processing'

        elif self.state == 'paused':
            self.state = 'processing'

        # Handle transition
        if self.transition_state:
            perc = (current_time - self.transition_update) / self.transition_speed
            if self.transition_state == 'open':
                perc = 1 - perc
            self.transition_progress = utils.clamp(perc, 0, 1)
            if perc < 0:
                self.transition_state = None

    def draw(self, surf):
        if self.background:
            self.background.draw(surf)

        delete = [key for key, portrait in self.portraits.items() if portrait.update()]
        for key in delete:
            del self.portraits[key]

        sorted_portraits = sorted(self.portraits.values(), key=lambda x: x.priority)
        for portrait in sorted_portraits:
            portrait.draw(surf)

        # Draw other boxes
        self.other_boxes = [box for box in self.other_boxes if box.update()]
        for box in self.other_boxes:
            box.draw(surf)

        # Draw text/dialog boxes
        if self.state == 'dialog':
            to_draw = []
            for dialog_box in reversed(self.text_boxes):
                if not dialog_box.is_done():
                    to_draw.insert(0, dialog_box)
                if dialog_box.solo_flag:
                    break
            for dialog_box in to_draw:
                dialog_box.update()
                dialog_box.draw(surf)

        # Fade to black
        if self.transition_state:
            s = engine.create_surface((WINWIDTH, WINHEIGHT), transparent=True)
            s.fill((*self.transition_color, int(255 * self.transition_progress)))
            surf.blit(s, (0, 0))

        return surf   

    def end(self):
        self.state = 'complete'     

    def process(self):
        while self.command_idx < len(self.commands) and self.state == 'processing':
            command = self.commands[self.command_idx]
            if self.handle_conditional(command):
                if self.do_skip and command.nid in self.skippable:
                    pass
                else:
                    self.run_command(command)
            self.command_idx += 1

    def handle_conditional(self, command) -> bool:
        """
        Returns true if the processor should be processing this command
        """
        if command.nid == 'if':
            if not self.if_stack or self.if_stack[-1]:
                truth = eval(command.values[0])
                self.if_stack.append(truth)
                self.parse_stack.append(truth)
            else:
                self.if_stack.append(False)
                self.parse_stack.append(False)
            return False
        elif command.nid == 'elif':
            if not self.if_stack:
                logger.error("Syntax Error somewhere in script. 'elif' needs to be after if statement.")
                return False
            # If we haven't encountered a truth yet
            if not self.parse_stack[-1]:
                truth = eval(command.values[0])
                self.if_stack[-1] = truth
                self.parse_stack[-1] = truth
            else:
                self.if_stack[-1] = False
            return False
        elif command.nid == 'else':
            if not self.if_stack:
                logger.error("Syntax Error somewhere in script. 'else' needs to be after if statement.")
                return False
            # If the most recent is False but the rest below are non-existent or true
            if not self.parse_stack[-1]:
                self.if_stack[-1] = True
                self.parse_stack[-1] = True
            else:
                self.if_stack[-1] = False
            return False
        elif command.nid == 'end':
            self.if_stack.pop()
            self.parse_stack.pop()
            return False

        if self.if_stack and not self.if_stack[-1]:
            return False
        return True

    def skip(self):
        self.do_skip = True
        if self.state != 'paused':
            self.state = 'processing'
        self.transition_state = None
        # if self.text_boxes:
        #     self.text_boxes[-1].hurry_up()

    def hurry_up(self):
        if self.text_boxes:
            self.text_boxes[-1].hurry_up()

    def run_command(self, command):
        logger.info('%s: %s', command.nid, command.values)
        current_time = engine.get_time()

        if command.nid == 'break':
            self.end()
            
        elif command.nid == 'wait':
            self.wait_time = current_time + int(command.values[0])
            self.state = 'waiting'

        elif command.nid == 'end_skip':
            self.do_skip = False

        elif command.nid == 'music':
            music = command.values[0]
            if music == 'None':
                SOUNDTHREAD.fade_to_stop()
            else:
                SOUNDTHREAD.fade_in(music)

        elif command.nid == 'sound':
            sound = command.values[0]
            SOUNDTHREAD.play_sfx(sound)

        elif command.nid == 'change_music':
            phase = command.values[0]
            music = command.values[1]
            if music == 'None':
                action.do(action.ChangePhaseMusic(phase, None))
            else:
                action.do(action.ChangePhaseMusic(phase, music))

        elif command.nid == 'change_background':
            values, flags = event_commands.parse(command)
            if len(values) > 0 and values[0]:
                panorama = values[0]
                panorama = RESOURCES.panoramas.get(panorama)
                if not panorama:
                    return
                self.background = background.PanoramaBackground(panorama)
            else:
                self.background = None
            if 'keep_portraits' in flags:
                pass
            else:
                self.portraits.clear()

        elif command.nid == 'transition':
            values, flags = event_commands.parse(command)
            if len(values) > 0 and values[0]:
                self.transition_state = values[0].lower()
            elif self.transition_state == 'close':
                self.transition_state = 'open'
            else:
                self.transition_state = 'close'
            if len(values) > 1 and values[1]:
                self.transition_speed = max(1, int(values[1]))
            else:
                self.transition_speed = self._transition_speed
            if len(values) > 2 and values[2]:
                self.transition_color = tuple(int(_) for _ in values[2].split(','))
            else:
                self.transition_color = self._transition_color
            self.transition_update = current_time
            self.wait_time = current_time + int(self.transition_speed * 1.33)
            self.state = 'waiting'

        elif command.nid == 'speak':
            self.speak(command)

        elif command.nid == 'add_portrait':
            self.add_portrait(command)

        elif command.nid == 'remove_portrait':
            self.remove_portrait(command)

        elif command.nid == 'move_portrait':
            self.move_portrait(command)

        elif command.nid == 'bop_portrait':
            values, flags = event_commands.parse(command)
            name = values[0]
            portrait = self.portraits.get(name)
            if not portrait:
                return False
            portrait.bop()
            if 'no_block' in flags:
                pass
            else:
                self.wait_time = engine.get_time() + 666
                self.state = 'waiting'

        elif command.nid == 'expression':
            values, flags = event_commands.parse(command)
            name = values[0]
            portrait = self.portraits.get(name)
            if not portrait:
                return False
            expression_list = values[1].split(',')
            portrait.set_expression(expression_list)

        elif command.nid == 'disp_cursor':
            b = command.values[0]
            if b.lower() in ('1', 't', 'true', 'y', 'yes'):
                game.cursor.show()
            else:
                game.cursor.hide()

        elif command.nid == 'move_cursor':
            values, flags = event_commands.parse(command)
            position = self.parse_pos(values[0])
            game.cursor.set_pos(position)
            if 'immediate' in flags or self.do_skip:
                game.camera.force_xy(*position)
            else:
                game.camera.set_xy(*position)
                game.state.change('move_camera')
                self.state = 'paused'  # So that the message will leave the update loop

        elif command.nid == 'flicker_cursor':
            # This is a macro that just adds new commands to command list
            move_cursor_command = event_commands.MoveCursor(command.values)
            disp_cursor_command1 = event_commands.DispCursor(['1'])
            wait_command = event_commands.Wait(['1000'])
            disp_cursor_command2 = event_commands.DispCursor(['0'])
            # Done backwards to presever order upon insertion
            self.commands.insert(self.command_idx + 1, disp_cursor_command2)
            self.commands.insert(self.command_idx + 1, wait_command)
            self.commands.insert(self.command_idx + 1, disp_cursor_command1)
            self.commands.insert(self.command_idx + 1, move_cursor_command)
            
        elif command.nid == 'game_var':
            values, flags = event_commands.parse(command)
            nid = values[0]
            to_eval = values[1]
            try:
                val = eval(to_eval)
                game.game_vars[nid] = val
            except:
                logger.error("Could not evaluate {%s}" % to_eval)

        elif command.nid == 'level_var':
            values, flags = event_commands.parse(command)
            nid = values[0]
            to_eval = values[1]
            try:
                val = eval(to_eval)
                game.level_vars[nid] = val
            except:
                logger.error("Could not evaluate {%s}" % to_eval)

        elif command.nid == 'win_game':
            game.level_vars['_win_game'] = True

        elif command.nid == 'lose_game':
            game.level_vars['_lose_game'] = True

        elif command.nid == 'add_unit':
            self.add_unit(command)

        elif command.nid == 'remove_unit':
            self.remove_unit(command)

        elif command.nid == 'move_unit':
            self.move_unit(command)

        elif command.nid == 'interact_unit':
            self.interact_unit(command)

        elif command.nid == 'add_group':
            self.add_group(command)

        elif command.nid == 'spawn_group':
            self.spawn_group(command)

        elif command.nid == 'move_group':
            self.move_group(command)

        elif command.nid == 'remove_group':
            self.remove_group(command)

        elif command.nid == 'give_item':
            self.give_item(command)

        elif command.nid == 'give_money':
            self.give_money(command)

        elif command.nid == 'give_exp':
            self.give_exp(command)

        elif command.nid == 'give_skill':
            self.give_skill(command)

        elif command.nid == 'remove_skill':
            self.remove_skill(command)

        elif command.nid == 'change_ai':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return 
            if values[1] in DB.ai.keys():
                action.do(action.ChangeAI(unit, values[1]))
            else:
                print("Couldn't find AI %s" % values[1])
                return

        elif command.nid == 'change_team':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return 
            if values[1] in DB.teams:
                action.do(action.ChangeTeam(unit, values[1]))
            else:
                print("Not a valid team: %s" % values[1])
                return

        elif command.nid == 'change_portrait':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return 
            portrait = RESOURCES.portraits.get(values[1])
            if not portrait:
                print("Couldn't find portrat %s" % values[1])
                return 
            action.do(action.ChangePortrait(unit, values[1]))

        elif command.nid == 'change_stats':
            self.change_stats(command)

        elif command.nid == 'promote':
            self.promote(command)

        elif command.nid == 'change_class':
            self.class_change(command)

        elif command.nid == 'add_tag':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return 
            if values[1] in DB.tags.keys():
                action.do(action.AddTag(unit, values[1]))

        elif command.nid == 'remove_tag':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return 
            if values[1] in DB.tags.keys():
                action.do(action.RemoveTag(unit, values[1]))

        elif command.nid == 'set_current_hp':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return 
            hp = int(values[1])
            action.do(action.SetHP(unit, hp))

        elif command.nid == 'has_attacked':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return
            action.do(action.HasAttacked(unit))

        elif command.nid == 'has_traded':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit %s" % values[0])
                return
            action.do(action.HasTraded(unit))

        elif command.nid == 'add_talk':
            values, flags = event_commands.parse(command)
            action.do(action.AddTalk(values[0], values[1]))

        elif command.nid == 'remove_talk':
            values, flags = event_commands.parse(command)
            action.do(action.RemoveTalk(values[0], values[1]))

        elif command.nid == 'add_region':
            self.add_region(command)

        elif command.nid == 'region_condition':
            values, flags = event_commands.parse(command)
            nid = values[0]
            if nid in game.level.regions.keys():
                region = game.level.regions.get(nid)
                action.do(action.ChangeRegionCondition(region, values[1]))
            else:
                print("Couldn't find Region %s" % nid)

        elif command.nid == 'remove_region':
            values, flags = event_commands.parse(command)
            nid = values[0]
            if nid in game.level.regions.keys():
                region = game.level.regions.get(nid)
                action.do(action.RemoveRegion(region))
            else:
                print("Couldn't find Region %s" % nid)

        elif command.nid == 'show_layer':
            values, flags = event_commands.parse(command)
            nid = values[0]
            if nid not in game.level.tilemap.layers.keys():
                print("Could not find layer %s in tilemap" % nid)
                return
            if len(values) > 1 and values[1]:
                transition = values[1]
            else:
                transition = 'fade'
            
            action.do(action.ShowLayer(nid, transition))

        elif command.nid == 'hide_layer':
            values, flags = event_commands.parse(command)
            nid = values[0]
            if nid not in game.level.tilemap.layers.keys():
                print("Could not find layer %s in tilemap" % nid)
                return
            if len(values) > 1 and values[1]:
                transition = values[1]
            else:
                transition = 'fade'

            action.do(action.HideLayer(nid, transition))            

        elif command.nid == 'prep':
            values, flags = event_commands.parse(command)
            if values and values[0].lower() in ('1', 't', 'true', 'y', 'yes'):
                b = True
            else:
                b = False
            game.memory['prep_pick'] = b
            game.state.change('prep_main')
            self.state = 'paused'  # So that the message will leave the update loop

        elif command.nid == 'shop':
            values, flags = event_commands.parse(command)
            unit = self.get_unit(values[0])
            if not unit:
                print("Must have a unit visit the shop!")
                return
            game.memory['current_unit'] = unit
            item_list = values[1].split(',')
            shop_items = item_funcs.create_items(unit, item_list)
            game.memory['shop_items'] = shop_items
            
            if len(values) > 2 and values[2]:
                game.memory['shop_flavor'] = values[2].lower()
            else:
                game.memory['shop_flavor'] = 'armory'
            game.state.change('shop')
            self.state = 'paused'

        elif command.nid == 'chapter_title':
            values, flags = event_commands.parse(command)
            if len(values) > 0 and values[0]:
                music = values[0]
            else:
                music = None
            if len(values) > 1 and values[1]:
                custom_string = values[1]
            else:
                custom_string = None
            game.memory['chapter_title_music'] = music
            game.memory['chapter_title_title'] = custom_string
            game.state.change('chapter_title')
            self.state = 'paused'

        elif command.nid == 'alert':
            values, flags = event_commands.parse(command)
            custom_string = values[0]
            game.alerts.append(banner.Custom(custom_string))
            game.state.change('alert')
            self.state = 'paused'

        elif command.nid == 'location_card':
            values, flags = event_commands.parse(command)
            custom_string = values[0]

            new_location_card = dialog.LocationCard(custom_string)
            self.other_boxes.append(new_location_card)

            self.wait_time = engine.get_time() + new_location_card.exist_time
            self.state = 'waiting'

        elif command.nid == 'unlock':
            # This is a macro that just adds new commands to command list
            find_unlock_command = event_commands.FindUnlock(command.values)
            spend_unlock_command = event_commands.SpendUnlock(command.values)
            # Done backwards to presever order upon insertion
            self.commands.insert(self.command_idx + 1, spend_unlock_command)
            self.commands.insert(self.command_idx + 1, find_unlock_command)

        elif command.nid == 'find_unlock':
            self.find_unlock(command)

        elif command.nid == 'spend_unlock':
            self.spend_unlock(command)

    def add_portrait(self, command):
        values, flags = event_commands.parse(command)
        name = values[0]
        unit = self.get_unit(name)
        if unit:
            portrait = RESOURCES.portraits.get(unit.portrait_nid)
        else:
            portrait = RESOURCES.portraits.get(name)
        if not portrait:
            return False
        # If already present, don't add
        if name in self.portraits and not self.portraits[name].remove:
            return False

        pos = values[1]
        if pos in screen_positions:
            position = [screen_positions[pos], 80]
            mirror = 'Left' in pos
        else:
            position = [int(p) for p in pos.split(',')]
            mirror = False

        priority = self.priority_counter
        if 'low_priority' in flags:
            priority -= 1000
        self.priority_counter += 1

        if 'mirror' in flags:
            mirror = not mirror

        transition = True
        if 'immediate' in flags or self.do_skip:
            transition = False

        slide = None
        if len(values) > 2 and values[2]:
            slide = values[2]

        new_portrait = EventPortrait(portrait, position, priority, transition, slide, mirror)
        self.portraits[name] = new_portrait

        if 'immediate' in flags or 'no_block' in flags or self.do_skip:
            pass
        else:
            self.wait_time = engine.get_time() + new_portrait.transition_speed + 33  # 16 frames
            self.state = 'waiting'

        return True

    def remove_portrait(self, command):
        values, flags = event_commands.parse(command)
        name = values[0]
        if name not in self.portraits:
            return False

        if 'immediate' in flags or self.do_skip:
            portrait = self.portraits.pop(name)
        else:
            portrait = self.portraits[name]
            portrait.end()

        if 'immediate' in flags or 'no_block' in flags or self.do_skip:
            pass
        else:
            self.wait_time = engine.get_time() + portrait.transition_speed + 33
            self.state = 'waiting'

    def move_portrait(self, command):
        values, flags = event_commands.parse(command)
        name = values[0]
        portrait = self.portraits.get(name)
        if not portrait:
            return False

        pos = values[1]
        if pos in screen_positions:
            position = [screen_positions[pos], 80]
        else:
            position = [int(p) for p in pos.split(',')]

        if 'immediate' in flags or self.do_skip:
            portrait.quick_move(position)
        else:
            portrait.move(position)

        if 'immediate' in flags or 'no_block' in flags or self.do_skip:
            pass
        else:
            self.wait_time = engine.get_time() + portrait.travel_time + 66
            self.state = 'waiting'

    def speak(self, command):
        values, flags = event_commands.parse(command)

        speaker = values[0]
        text = values[1]

        if len(values) > 2 and values[2]:
            position = self.parse_pos(values[2])
        else:
            position = None
        if len(values) > 3 and values[3]:
            width = int(values[3])
        else:
            width = None

        portrait = self.portraits.get(speaker)
        new_dialog = dialog.Dialog(text, portrait, 'message_bg_base', position, width)
        self.text_boxes.append(new_dialog)
        self.state = 'dialog'
        # Bring portrait to forefront
        if portrait and 'low_priority' not in flags:
            portrait.priority = self.priority_counter
            self.priority_counter += 1

    def add_unit(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit %s" % values[0])
            return 
        if unit.position:
            print("Unit already on map!")
            return
        if unit.dead:
            print("Unit is dead!")
            return
        if len(values) > 1 and values[1]:
            position = self.parse_pos(values[1])
        else:
            position = unit.starting_position
        if not position:
            print("No position found!")
            return
        if len(values) > 2 and values[2]:
            entry_type = values[2]
        else:
            entry_type = 'fade'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        position = self.check_placement(position, placement)
        if not position:
            return None

        if self.do_skip:
            action.do(action.ArriveOnMap(unit, position))
        elif entry_type == 'warp':
            action.do(action.WarpIn(unit, position))
        elif entry_type == 'fade':
            action.do(action.FadeIn(unit, position))
        else:  # immediate
            action.do(action.ArriveOnMap(unit, position))

    def move_unit(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit.position:
            print("Unit not on map!")
            return

        if len(values) > 1 and values[1]:
            position = self.parse_pos(values[1])
        else:
            position = unit.starting_position
        if not position:
            print("No position found!")
            return

        if len(values) > 2 and values[2]:
            movement_type = values[2]
        else:
            movement_type = 'normal'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        follow = 'no_follow' not in flags

        position = self.check_placement(position, placement)
        if not position:
            print("Couldn't get a good position %s %s %s" % (position, movement_type, placement))
            return None

        if movement_type == 'immediate' or self.do_skip:
            action.do(action.Teleport(unit, position))
        elif movement_type == 'warp':
            action.do(action.Warp(unit, position))
        elif movement_type == 'fade':
            action.do(action.FadeMove(unit, position))
        elif movement_type == 'normal':
            path = target_system.get_path(unit, position)
            action.do(action.Move(unit, position, path, event=True, follow=follow))

        if 'no_block' in flags or self.do_skip:
            pass
        else:
            self.state = 'paused'
            game.state.change('movement')

    def remove_unit(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit %s" % values[0])
            return 
        if not unit.position:
            print("Unit not on map!")
            return
        if len(values) > 1 and values[1]:
            remove_type = values[1]
        else:
            remove_type = 'fade'

        if self.do_skip:
            action.do(action.LeaveMap(unit))
        elif remove_type == 'warp':
            action.do(action.WarpOut(unit))
        elif remove_type == 'fade':
            action.do(action.FadeOut(unit))
        else:  # immediate
            action.do(action.LeaveMap(unit))

    def interact_unit(self, command):
        values, flags = event_commands.parse(command)
        unit1 = self.get_unit(values[0])
        unit2 = self.get_unit(values[1])
        if not unit1 or not unit1.position:
            print("Couldn't find %s" % unit1)
            return 
        if not unit2 or not unit2.position:
            print("Couldn't find %s" % unit2)
            return 

        if len(values) > 2 and values[2]:
            script = values[2].split(',')
        else:
            script = None

        items = item_funcs.get_all_items(unit1)
        # Get item
        if len(values) > 3 and values[3]:
            item_nid = values[3]
            for i in items:
                if item_nid == i.nid:
                    item = i
                    break
        else:
            if items:
                item = items[0]
            else:
                print("Unit does not have item!")
                return

        interaction.start_combat(unit1, unit2.position, item, event_combat=True, script=script)
        self.state = "paused"

    def add_group(self, command):
        values, flags = event_commands.parse(command)
        group = game.level.unit_groups.get(values[0])
        if not group:
            print("Couldn't find group %s" % values[0])
            return
        if len(values) > 1 and values[1]:
            next_pos = values[1]
        else:
            next_pos = None
        if len(values) > 2 and values[2]:
            entry_type = values[2]
        else:
            entry_type = 'fade'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        create = 'create' in flags
        for unit_nid in group.units:
            unit = game.level.units.get(unit_nid)
            if create:
                unit = self.copy_unit(unit)
            elif unit.position or unit.dead:
                continue
            position = self._get_position(next_pos, unit, group)
            if not position:
                continue
            position = tuple(position)
            position = self.check_placement(position, placement)
            if self.do_skip:
                action.do(action.ArriveOnMap(unit, position))
            elif entry_type == 'warp':
                action.do(action.WarpIn(unit, position))
            elif entry_type == 'fade':
                action.do(action.FadeIn(unit, position))
            else:  # immediate
                action.do(action.ArriveOnMap(unit, position))

    def _move_unit(self, movement_type, placement, follow, unit, position):
        position = tuple(position)
        position = self.check_placement(position, placement)
        if not position:
            logger.warning("Couldn't determine valid position for %s?", unit.nid)
            return
        if movement_type == 'immediate' or self.do_skip:
            action.do(action.Teleport(unit, position))
        elif movement_type == 'warp':
            action.do(action.Warp(unit, position))
        elif movement_type == 'fade':
            action.do(action.FadeMove(unit, position))
        elif movement_type == 'normal':
            path = target_system.get_path(unit, position)
            action.do(action.Move(unit, position, path, event=True, follow=follow))

    def _add_unit(self, unit, position):
        position = tuple(position)
        action.do(action.ArriveOnMap(unit, position))

    def _get_position(self, next_pos, unit, group):
        if not next_pos:
            position = group.positions.get(unit.nid)
        elif next_pos.lower() == 'starting':
            position = unit.starting_position
        elif ',' in next_pos:
            position = self.parse_pos(next_pos)
        else:
            other_group = game.level.unit_groups.get(next_pos)
            position = other_group.positions.get(unit.nid)                
        return position

    def spawn_group(self, command):
        values, flags = event_commands.parse(command)
        group = game.level.unit_groups.get(values[0])
        if not group:
            print("Couldn't find group %s" % values[0])
            return
        cardinal_direction = values[1].lower()
        if cardinal_direction not in ('east', 'west', 'north', 'south'):
            print("Not a legal cardinal direction")
            return
        next_pos = values[2]
        if len(values) > 3 and values[3]:
            movement_type = values[3]
        else:
            movement_type = 'normal'
        if len(values) > 4 and values[4]:
            placement = values[4]
        else:
            placement = 'giveup'
        create = 'create' in flags
        follow = 'no_follow' not in flags

        for unit_nid in group.units:
            unit = game.level.units.get(unit_nid)
            if create:
                unit = self.copy_unit(unit)
            elif unit.position or unit.dead:
                continue
            position = self._get_position(next_pos, unit, group)
            if not position:
                continue
            
            if cardinal_direction == 'west':
                self._add_unit(unit, (0, position[1]))
            elif cardinal_direction == 'east':
                self._add_unit(unit, (game.tilemap.width - 1, position[1]))
            elif cardinal_direction == 'north':
                self._add_unit(unit, (position[0], 0))
            elif cardinal_direction == 'south':
                self._add_unit(unit, (position[0], game.tilemap.height - 1))
            self._move_unit(movement_type, placement, follow, unit, position)

        if 'no_block' in flags or self.do_skip:
            pass
        else:
            self.state = 'paused'
            game.state.change('movement')

    def move_group(self, command):
        values, flags = event_commands.parse(command)
        group = game.level.unit_groups.get(values[0])
        if not group:
            print("Couldn't find group %s" % values[0])
            return
        next_pos = values[1]
        if len(values) > 2 and values[2]:
            movement_type = values[2]
        else:
            movement_type = 'normal'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        follow = 'no_follow' not in flags

        for unit_nid in group.units:
            unit = game.level.units.get(unit_nid)
            if not unit.position:
                continue
            position = self._get_position(next_pos, unit, group)
            if not position:
                continue
            self._move_unit(movement_type, placement, follow, unit, position)

        if 'no_block' in flags or self.do_skip:
            pass
        else:
            self.state = 'paused'
            game.state.change('movement')

    def remove_group(self, command):
        values, flags = event_commands.parse(command)
        group = game.level.unit_groups.get(values[0])
        if not group:
            print("Couldn't find group %s" % values[0])
            return
        if len(values) > 1 and values[1]:
            remove_type = values[1]
        else:
            remove_type = 'fade'
        for unit_nid in group.units:
            unit = game.level.units.get(unit_nid)
            if unit.position:
                if self.do_skip:
                    action.do(action.LeaveMap(unit))
                elif remove_type == 'warp':
                    action.do(action.WarpOut(unit))
                elif remove_type == 'fade':
                    action.do(action.FadeOut(unit))
                else:  # immediate
                    action.do(action.LeaveMap(unit))

    def check_placement(self, position, placement):
        current_occupant = game.board.get_unit(position)
        if current_occupant:
            if placement == 'giveup':
                logger.info("Unit already present on tile %s", position)
                return None
            elif placement == 'stack':
                return position
            elif placement == 'closest':
                position = target_system.get_nearest_open_tile(current_occupant, position)
                if not position:
                    logger.info("Somehow wasn't able to find a nearby open tile")
                    return None
                return position
            elif placement == 'push':
                current_occupant = game.get_unit(current_occupant)
                new_pos = target_system.get_nearest_open_tile(current_occupant, position)
                action.do(action.Push(current_occupant, new_pos))
                return position
        else:
            return position

    def give_item(self, command):
        values, flags = event_commands.parse(command)
        if values[0].lower() == 'convoy':
            unit = None
        else:
            unit = self.get_unit(values[0])
            if not unit:
                print("Couldn't find unit with nid %s" % values[0])
                return
        item_nid = values[1]
        if item_nid in DB.items.keys():
            item_prefab = DB.items.get(item_nid)
            item = ItemObject.from_prefab(item_prefab)
            item_system.init(item)
            game.register_item(item)
        else:
            print("Couldn't find item with nid %s" % item_nid)
            return
        if 'no_banner' in flags:
            banner_flag = False
        else:
            banner_flag = True

        if unit:
            accessory = item_system.is_accessory(unit, item)
            if accessory and len(unit.accessories) >= DB.constants.value('num_accessories'):
                if 'no_choice' in flags:
                    action.do(action.PutItemInConvoy(item))
                    if banner_flag:
                        game.alerts.append(banner.SentToConvoy(item))
                        game.state.change('alert')
                        self.state = 'paused'
                else:
                    action.do(action.GiveItem(unit, item))
                    game.cursor.cur_unit = unit
                    game.state.change('item_discard')
                    self.state = 'paused'
                    if banner_flag:
                        game.alerts.append(banner.AcquiredItem(self.unit, self.item))
                        game.state.change('alert')
            elif not accessory and len(unit.nonaccessories) >= DB.constants.value('num_items'):
                if 'no_choice' in flags:
                    action.do(action.PutItemInConvoy(item))
                    if banner_flag:
                        game.alerts.append(banner.SentToConvoy(item))
                        game.state.change('alert')
                        self.state = 'paused'
                else:
                    action.do(action.GiveItem(unit, item))
                    game.cursor.cur_unit = unit
                    game.state.change('item_discard')
                    self.state = 'paused'
                    if banner_flag: 
                        game.alerts.append(banner.AcquiredItem(unit, item))
                        game.state.change('alert')
            else:
                action.do(action.GiveItem(unit, item))
                if banner_flag: 
                    game.alerts.append(banner.AcquiredItem(unit, item))
                    game.state.change('alert')
                    self.state = 'paused'
        else:
            action.do(action.PutItemInConvoy(item))
            if banner_flag:
                game.alerts.append(banner.SentToConvoy(item))
                game.state.change('alert')
                self.state = 'paused'

    def give_money(self, command):
        values, flags = event_commands.parse(command)
        money = int(values[0])
        if len(values) > 1 and values[1]:
            party_nid = values[1]
        else:
            party_nid = game.current_party
        banner_flag = 'no_banner' not in flags

        action.do(action.GainMoney(party_nid, money))
        if banner_flag:
            if money >= 0:
                b = banner.Advanced(['Got ', str(money), ' gold.'], ['text-white', 'text-blue', 'text-white'], 'Item')
            else:
                b = banner.Advanced(['Lost ', str(money), ' gold.'], ['text-white', 'text-blue', 'text-white'], 'ItemBreak')
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused'

    def give_exp(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit with nid %s" % values[0])
            return
        exp = utils.clamp(int(values[1]), 0, 100)
        game.exp_instance.append((unit, exp, None, 'init'))
        game.state.change('exp')
        self.state = 'paused'

    def give_skill(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit with nid %s" % values[0])
            return
        skill_nid = values[1]
        if skill_nid not in DB.skills.keys():
            print("Couldn't find skill with nid %s" % values[1])
            return
        banner_flag = 'no_banner' not in flags
        action.do(action.AddSkill(unit, skill_nid))
        if banner_flag:
            skill = DB.skills.get(skill_nid)
            b = banner.GiveSkill(unit, skill)
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused'

    def remove_skill(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit with nid %s" % values[0])
            return
        skill_nid = values[1]
        if skill_nid not in [skill.nid for skill in unit.skills]:
            print("Couldn't find skill with nid %s" % values[1])
            return
        banner_flag = 'no_banner' not in flags
        
        action.do(action.RemoveSkill(unit, skill_nid))
        if banner_flag:
            skill = DB.skills.get(skill_nid)
            b = banner.TakeSkill(unit, skill)
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused' 

    def change_stats(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit %s" % values[0])
            return

        s_list = values[1].split(',')
        stat_changes = {}
        for idx in range(len(s_list)//2):
            stat_nid = s_list[idx*2]
            stat_value = int(s_list[idx*2 + 1])
            stat_changes[stat_nid] = stat_value
        klass = DB.classes.get(unit.klass)
        # clamp stat changes
        stat_changes = {k: utils.clamp(v, -unit.stats[k], klass.max_stats.get(k).value - unit.stats[k]) for k, v in stat_changes.items()}

        immediate = 'immediate' in flags

        action.do(action.ApplyStatChanges(unit, stat_changes))
        if not immediate:
            game.memory['stat_changes'] = stat_changes
            game.exp_instance.append((unit, 0, None, 'stat_booster'))
            game.state.change('exp')
            self.state = 'paused'

    def promote(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit %s" % values[0])
            return
        new_klass = None
        if len(values) > 1 and values[1]:
            new_klass = values[1]
        else:
            klass = DB.classes.get(unit.klass)
            if len(klass.turns_into) == 0:
                print("No available promotions for %s" % klass)
                return
            elif len(klass.turns_into) == 1:
                new_klass = klass.turns_into[0]
            else:
                new_klass = None

        game.memory['current_unit'] = unit
        if new_klass:    
            game.memory['next_class'] = new_klass
            game.state.change('promotion')
            game.state.change('transition_out')
            self.state = 'paused'
        else:
            game.state.change('promotion_choice')
            game.state.change('transition_out')
            self.state = 'paused'

    def class_change(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit %s" % values[0])
            return
        new_klass = None
        if len(values) > 1 and values[1]:
            new_klass = values[1]
        elif not unit.generic:
            unit_prefab = DB.units.get(unit.nid)
            if not unit_prefab.alternate_classes:
                print("No available alternate classes for %s" % unit)
                return
            elif len(unit_prefab.alternate_classes) == 1:
                new_klass = unit_prefab.alternate_classes[0]
            else:
                new_klass = None

        game.memory['current_unit'] = unit
        if new_klass:    
            game.memory['next_class'] = new_klass
            game.state.change('class_change')
            game.state.change('transition_out')
            self.state = 'paused'
        else:
            game.state.change('class_change_choice')
            game.state.change('transition_out')
            self.state = 'paused'

    def add_region(self, command):
        values, flags = event_commands.parse(command)
        nid = values[0]
        if nid in game.level.regions.keys():
            print("Region nid %s already present!" % nid)
            return
        position = self.parse_pos(values[1])
        size = self.parse_pos(values[2])
        if not size:
            size = (1, 1)
        region_type = values[3].lower()
        if len(values) > 4 and values[4]:
            sub_region_type = values[4]
        else:
            sub_region_type = None

        new_region = regions.Region(nid)
        new_region.region_type = region_type
        new_region.position = position
        new_region.size = size
        new_region.sub_nid = sub_region_type

        if 'only_once' in flags:
            new_region.only_once = True

        action.do(action.AddRegion(new_region))

    def find_unlock(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit with nid %s" % values[0])
            return
        if not self.region:
            print("Can only find_unlock within a region's event script")
            return 
        if skill_system.can_unlock(unit, self.region):
            game.memory['unlock_item'] = None
            return  # We're done here

        all_items = []
        for item in item_funcs.get_all_items(unit):
            if item_funcs.available(unit, item) and \
                    item_system.can_unlock(unit, item, self.region):
                all_items.append(item)
        
        if len(all_items) > 1:
            game.memory['current_unit'] = unit
            game.memory['all_unlock_items'] = all_items
            game.state.change('unlock_select')
            self.state = 'paused'
        elif len(all_items) == 1:
            game.memory['unlock_item'] = all_items[0]
        else:
            logger.debug("Somehow unlocked event without being able to")
            game.memory['unlock_item'] = None

    def spend_unlock(self, command):
        values, flags = event_commands.parse(command)
        unit = self.get_unit(values[0])
        if not unit:
            print("Couldn't find unit with nid %s" % values[0])
            return

        chosen_item = game.memory.get('unlock_item')
        game.memory['unlock_item'] = None
        if not chosen_item:
            return

        actions, playback = [], []
        # In order to proc uses, c_uses etc.
        item_system.start_combat(playback, unit, chosen_item, None)
        item_system.on_hit(actions, playback, unit, chosen_item, None, None)
        for act in actions:
            action.do(act)
        item_system.end_combat(playback, unit, chosen_item, None)

        if unit.get_hp() <= 0:
            # Force can't die unlocking stuff, because I don't want to deal with that nonsense
            action.do(action.SetHP(unit, 1))

        # Check to see if we broke the item we were using
        if not item_funcs.available(unit, chosen_item):
            alert = item_system.on_not_usable(unit, chosen_item)
            if alert and unit.team == 'player':
                game.alerts.append(banner.BrokenItem(unit, chosen_item))
                game.state.change('alert')
                self.state = 'paused'

    def parse_pos(self, text):
        position = None
        if ',' in text:
            position = tuple(int(_) for _ in text.split(','))
        elif self.get_unit(text):
            position = self.get_unit(text).position
        return position

    def get_unit(self, text):
        if text in ('{unit}', '{unit1}'):
            return self.unit
        elif text == '{unit2}':
            return self.unit2
        else:
            return game.get_unit(text)
