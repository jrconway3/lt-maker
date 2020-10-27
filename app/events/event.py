from app.constants import WINWIDTH, WINHEIGHT, FRAMERATE
from app.resources.resources import RESOURCES
from app.engine.sound import SOUNDTHREAD
from app.events.event_portrait import EventPortrait
from app.utilities import utils
from app.engine import dialog, engine, background
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

screen_positions = {'OffscreenLeft': -96, 'FarLeft': -24, 'Left': 0, 'MidLeft': 24, 'MidRight': 120, 'Right': 144, 'FarRight': 168, 'OffscreenRight': 240}

class Event():
    _transition_speed = 15 * FRAMERATE
    _transition_color = (0, 0, 0)

    def __init__(self, commands, unit=None, unit2=None, position=None):
        self.commands = commands
        self.command_idx = 0

        self.background = None

        self.unit = self.unit1 = unit
        self.unit2 = unit2
        self.position = position

        self.portraits = {}
        self.text_boxes = []

        self.prev_state = None
        self.state = 'processing'

        self.wait_time = 0

        # Handles keeping the order that unit sprites should be drawn
        self.priority_counter = 1

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
            self.reset_portraits()
            if self.command_idx >= len(self.commands):
                self.end()
            else:
                self.process()

        elif self.state == 'dialog':
            if self.text_boxes:
                if self.text_boxes[-1].is_done():
                    self.state = 'processing'
                if not self.text_boxes[-1].processing:
                    self.reset_portraits()

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

        # Draw text/dialog boxes
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

            self.run_command(command)
            self.command_idx += 1

    def reset_portraits(self):
        for portrait in self.portraits.values():
            portrait.stop_talking()

    def skip(self):
        pass

    def hurry_up(self):
        if self.text_boxes:
            if self.text_boxes[-1].processing:
                self.text_boxes[-1].hurry_up()
            else:
                SOUNDTHREAD.play_sfx('Select 1')
                self.text_boxes[-1].unpause()

    def parse(self, command):
        values = command.values
        num_keywords = len(command.keywords)
        true_values = values[:num_keywords]
        flags = {v for v in values[num_keywords:] if v in command.flags}
        optional_keywords = [v for v in values[num_keywords:] if v not in flags]
        true_values += optional_keywords
        return true_values, flags

    def run_command(self, command):
        logger.info('Command %s', command.nid)
        logger.info('Command Values %s', command.values)
        current_time = engine.get_time()

        if command.nid == 'wait':
            self.wait_time = current_time + int(command.values[0])
            self.state = 'waiting'

        elif command.nid == 'music':
            music = command.values[0]
            SOUNDTHREAD.fade_in(music)

        elif command.nid == 'sound':
            sound = command.values[0]
            SOUNDTHREAD.play_sfx(sound)

        elif command.nid == 'change_background':
            panorama = command.values[0]
            panorama = RESOURCES.panoramas.get(panorama)
            if not panorama:
                return
            self.background = background.PanoramaBackground(panorama)
            if 'keep_portraits' in command.values:
                pass
            else:
                self.portraits.clear()

        elif command.nid == 'transition':
            values, flags = self.parse(command)
            if len(values) > 0:
                self.transition_state = values[0].lower()
            elif self.transition_state == 'close':
                self.transition_state = 'open'
            else:
                self.transition_state = 'close'
            if len(values) > 1:
                self.transition_speed = max(1, int(values[1]))
            else:
                self.transition_speed = self._transition_speed
            if len(values) > 2:
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
            values, flags = self.parse(command)
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

    def add_portrait(self, command):
        values, flags = self.parse(command)
        name = values[0]
        unit = game.get_unit(name)
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
            mirror = pos in ('OffscreenLeft', 'FarLeft', 'Left', 'CenterLeft')
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
        if 'immediate' in flags:
            transition = False

        slide = None
        if len(values) > 2:
            slide = values[2]

        new_portrait = EventPortrait(portrait, position, priority, transition, slide, mirror)
        self.portraits[name] = new_portrait

        if 'immediate' in flags or 'no_block' in flags:
            pass
        else:
            self.wait_time = engine.get_time() + new_portrait.transition_speed + 33  # 16 frames
            self.state = 'waiting'

        return True

    def remove_portrait(self, command):
        values, flags = self.parse(command)
        name = values[0]
        if name not in self.portraits:
            return False

        if 'immediate' in flags:
            portrait = self.portraits.pop(name)
        else:
            portrait = self.portraits[name]
            portrait.end()

        if 'immediate' in flags or 'no_block' in flags:
            pass
        else:
            self.wait_time = engine.get_time() + portrait.transition_speed + 33
            self.state = 'waiting'

    def move_portrait(self, command):
        values, flags = self.parse(command)
        name = values[0]
        portrait = self.portraits.get(name)
        if not portrait:
            return False

        pos = values[1]
        if pos in screen_positions:
            position = [screen_positions[pos], 80]
        else:
            position = [int(p) for p in pos.split(',')]

        if 'immediate' in flags:
            portrait.quick_move(position)
        else:
            portrait.move(position)

        if 'immediate' in flags or 'no_block' in flags:
            pass
        else:
            self.wait_time = engine.get_time() + portrait.travel_mag * portrait.movement_speed + 33
            self.state = 'waiting'

    def speak(self, command):
        values, flags = self.parse(command)

        speaker = values[0]
        text = values[1]

        new_dialog = dialog.Dialog(text, portrait=self.portraits.get(speaker), background='message_bg_base')
        self.text_boxes.append(new_dialog)
        self.state = 'dialog'
