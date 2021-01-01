import re

from app.utilities import utils
from app.constants import WINWIDTH
from app.engine.fonts import FONT
from app.engine.sprites import SPRITES
from app.engine.sound import SOUNDTHREAD
from app.engine.base_surf import create_base_surf
from app.engine import text_funcs, engine, image_mods
from app.engine import config as cf

class Dialog():
    num_lines = 2
    solo_flag = True
    cursor = SPRITES.get('waiting_cursor')
    cursor_offset = [0]*20 + [1]*2 + [2]*8 + [1]*2
    transition_speed = 166  # 10 frames

    def __init__(self, text, portrait=None, background=None, position=None, width=None):
        self.plain_text = text
        self.portrait = portrait
        self.font = FONT['convo-black']

        self.processing = True
        self.text_commands = self.format_text(text)
        self.text_lines = []
        
        # Size
        if width:
            self.width = width
            self.width -= self.width%8
            self.text_width = self.width - 24
            self.determine_height()
        elif self.portrait:
            self.determine_size()
        else:
            self.text_width, self.text_height = (WINWIDTH - 24, self.num_lines * 16)
            self.width, self.height = self.text_width + 16, self.text_height + 8

        # Position
        if position:
            pos_x = position[0]
            pos_y = position[1]
        elif self.portrait:
            desired_center = self.determine_desired_center(self.portrait)
            pos_x = utils.clamp(desired_center - self.width//2, 8, WINWIDTH - 8 - self.width)
            if pos_x % 8 != 0:
                pos_x += 4
            pos_y = 24
        else:
            pos_x = 4
            pos_y = 110
        self.position = pos_x, pos_y

        if background:
            self.background = self.make_background(background)
            self.tail = SPRITES.get('message_bg_tail')
        else:
            self.background = None
            self.tail = None

        # For drawing
        self.cursor_offset_index = 0
        self.text_index = 0
        self.total_num_updates = 0
        self.y_offset = 0 # How much to move lines (for when a new line is spawned)

        # For transition
        self.transition = True
        self.transition_progress = 0
        self.transition_update = engine.get_time()

        # For sound
        self.last_sound_update = 0

        self._next_line()

    def format_text(self, text):
        # Pipe character replacement
        text = text.replace('|', '{w}{br}')
        if text.endswith('{no_wait}'):
            text = text[:-4]
        elif not text.endswith('{w}'):
            text += '{w}'
        command = None
        processed_text = []
        for character in text:
            if character == '{' and command is None:
                command = '{'
            elif character == '}' and command is not None:
                command += '}'
                processed_text.append(command)
                command = None
            elif command is not None:
                command += character
            else:
                processed_text.append(character)
        processed_text = [';' if char == '{semicolon}' else char for char in processed_text]

        return processed_text

    def determine_desired_center(self, portrait):
        x = self.portrait.position[0] + self.portrait.get_width()//2
        if x < 48:  # FarLeft
            return 8
        elif x < 72:  # Left
            return 80
        elif x < 104:  # MidLeft
            return 104
        elif x > 192:  # FarRight
            return 232
        elif x > 168:  # Right
            return 152
        elif x > 144:  # MidRight
            return 128
        else:
            return 120

    def determine_width(self):
        width = 0
        current_line = ''
        preceded_by_wait: bool = False
        for command in self.text_commands:
            if command in ('{br}', '{break}', '{clear}'):
                if not preceded_by_wait:
                    # Force it to be only one line
                    split_lines = self.get_lines_from_block(current_line, 1)
                else:
                    split_lines = self.get_lines_from_block(current_line)
                width = max(width, max(self.font.width(s) for s in split_lines))
                if len(split_lines) == 1:
                    width += 16
                current_line = ''
                preceded_by_wait = False
            elif command in ('{w}', '{wait}'):
                preceded_by_wait = True
            elif command.startswith('{'):
                pass
            else:
                current_line += command
        if current_line:
            split_lines = self.get_lines_from_block(current_line)
            width = max(width, max(self.font.width(s) for s in split_lines))
            # Account for "waiting cursor"
            if len(split_lines) == 1:
                width += 16
        return width

    def determine_height(self):
        self.text_height = self.font.height * self.num_lines
        self.text_height = max(self.text_height, 16)
        self.height = self.text_height + 16

    def determine_size(self):
        self.text_width = self.determine_width()
        self.text_width = utils.clamp(self.text_width, 48, WINWIDTH - 32)
        self.width = self.text_width + 24 - self.text_width%8
        if self.width < 200:
            self.width += 8
        self.determine_height()

    def get_lines_from_block(self, block, force_lines=None):
        if force_lines:
            num_lines = force_lines
        else:
            num_lines = self.num_lines
            if len(block) <= 24:
                num_lines = 1
        lines = text_funcs.split(self.font, block, num_lines, WINWIDTH - 16)
        return lines

    def _next_line(self):
        self.text_lines.append('')
        self.y_offset = 16

    def _add_letter(self, letter):
        self.text_lines[-1] += letter

    def _next_char(self, sound=True):  # Add the next character to the text_lines list
        if self.text_index >= len(self.text_commands):
            self.processing = False
            return
        command = self.text_commands[self.text_index]
        if command == '{br}' or command == '{break}':
            self._next_line()
        elif command == '{w}' or command == '{wait}':
            self.processing = False
        elif command == '{clear}':
            self.text_lines.clear()
            self._next_line()
        elif command == ' ':  # Check to see if we should move to next line
            current_line = self.text_lines[-1]
            # Remove any commands from line
            current_line = re.sub(r'\{[^}]*\}', ' ', current_line)
            next_word = self._get_next_word(self.text_index)
            if self.font.width(current_line + ' ' + next_word) > self.text_width:
                self._next_line()
            else:
                self._add_letter(' ')
                if sound:
                    self.play_talk_boop()
        else:
            self._add_letter(command)
            if sound:
                self.play_talk_boop()
        self.text_index += 1

    def _get_next_word(self, text_index):
        word = ''
        for letter in self.text_commands[self.text_index + 1:]:
            if letter == ' ' or len(letter) > 1:  # Command
                break
            else:
                word += letter
        return word

    def is_done(self):
        return self.text_index >= len(self.text_commands)

    def make_background(self, background):
        surf = create_base_surf(self.width, self.height, background)
        return surf

    def hurry_up(self):
        self.transition = False
        self.transition_progress = 0
        while self.processing:
            self._next_char(sound=False)

    def unpause(self):
        self.processing = True
        if self.portrait and not self.is_done():
            self.portrait.talk()

    def play_talk_boop(self):
        # SOUNDTHREAD.stop_sfx('Talk_Boop')
        if cf.SETTINGS['talk_boop'] and engine.get_true_time() - self.last_sound_update > 32:
            self.last_sound_update = engine.get_true_time()
            SOUNDTHREAD.play_sfx('Talk_Boop')

    def update(self):
        current_time = engine.get_time()

        if self.transition:
            perc = (current_time - self.transition_update) / self.transition_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                self.transition = False
                if self.portrait:
                    self.portrait.talk()
        elif self.processing:
            if cf.SETTINGS['text_speed'] > 0:
                num_updates = engine.get_delta() / float(cf.SETTINGS['text_speed'])
                self.total_num_updates += num_updates
                while self.total_num_updates >= 1 and self.processing:
                    self.total_num_updates -= 1
                    self._next_char(sound=self.total_num_updates < 2)
                    if not self.processing:
                        self.total_num_updates = 0
            else:
                self.hurry_up()
                self.play_talk_boop()

        self.cursor_offset_index = (self.cursor_offset_index + 1) % len(self.cursor_offset)

    def draw_text(self, surf):
        end_x_pos, end_y_pos = 0, 0
        text_surf = engine.create_surface((self.text_width, self.text_height), transparent=True)

        display_lines = self.text_lines[-self.num_lines:]
        for idx, line in enumerate(display_lines):
            x_pos = 0
            y_pos = 16 * idx
            if len(self.text_lines) > self.num_lines:
                y_set = y_pos + self.y_offset
            else:
                y_set = y_pos
            self.font.blit(line, text_surf, (x_pos, y_set))
            end_x_pos = self.position[0] + 8 + x_pos + self.font.width(line)
            end_y_pos = self.position[1] + 8 + y_pos

        # Draw line that's disappearing
        if self.y_offset and len(self.text_lines) > self.num_lines:
            x_pos = 0
            y_pos = -16 + self.y_offset
            line = self.text_lines[-self.num_lines - 1]
            self.font.blit(line, text_surf, (x_pos, y_pos))

        # Update y_offset
        self.y_offset = max(0, self.y_offset - 2)
        surf.blit(text_surf, (self.position[0] + 8, self.position[1] + 8))

        return end_x_pos, end_y_pos

    def draw_tail(self, surf, portrait):
        portrait_pos = portrait.position[0] + portrait.get_width()//2
        mirror = portrait_pos < WINWIDTH//2
        if mirror:
            tail_surf = engine.flip_horiz(self.tail)
        else:
            tail_surf = self.tail
        y_pos = self.position[1] + self.background.get_height() - 2
        x_pos = portrait_pos + 20 if mirror else portrait_pos - 36
        # If we wouldn't actually be on the dialog box
        if x_pos > self.background.get_width() + self.position[0] - 24:
            x_pos = self.position[0] + self.background.get_width() - 24
        elif x_pos < self.position[0] + 8:
            x_pos = self.position + 8

        tail_surf = image_mods.make_translucent(tail_surf, .05)
        surf.blit(tail_surf, (x_pos, y_pos))

    def draw(self, surf):
        if self.background:
            if self.transition:
                # bg = image_mods.resize(self.background, (1, .5 + self.transition_progress/2.))
                new_width = self.background.get_width() - 10 + int(10*self.transition_progress)
                new_height = self.background.get_height() - 10 + int(10*self.transition_progress)
                bg = engine.transform_scale(self.background, (new_width, new_height))
                bg = image_mods.make_translucent(bg, .05 + .7 * (1 - self.transition_progress))
                surf.blit(bg, (self.position[0], self.position[1] + self.height - bg.get_height()))
            else:
                bg = image_mods.make_translucent(self.background, .05)
                surf.blit(bg, self.position)

        if not self.transition:
            # Draw message tail
            if self.portrait and self.background and self.tail:
                self.draw_tail(surf, self.portrait)
            # Draw text
            end_pos = self.draw_text(surf)

            if not self.processing:
                cursor_pos = 4 + end_pos[0], \
                    6 + end_pos[1] + self.cursor_offset[self.cursor_offset_index]
                surf.blit(self.cursor, cursor_pos)

        return surf

class LocationCard():
    exist_time = 2000
    transition_speed = 166  # 10 frames

    def __init__(self, text, background='menu_bg_brown'):
        self.plain_text = text
        self.font = FONT['text-white']

        self.text_lines = self.format_text(text)
        self.determine_size()
        self.position = (10, 1)

        if background:
            self.background = self.make_background(background)
        else:
            self.background = engine.create_surface((self.width, self.height), transparent=True)

        # For transition
        self.transition = True
        self.transition_progress = 0
        self.transition_update = engine.get_time()

    def format_text(self, text):
        return [text]

    def determine_size(self):
        self.width = max(self.font.width(line) for line in self.text_lines) + 16
        self.height = len(self.text_lines) * self.font.height

    def make_background(self, background):
        surf = create_base_surf(self.width, self.height, background)
        return surf

    def update(self):
        current_time = engine.get_time()

        if self.transition:
            perc = (current_time - self.transition_update) / self.transition_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                if self.transition == 'end':
                    return False
                self.transition = False

        if current_time - self.start_time > self.exist_time:
            self.transition = 'end'

        return True

    def draw(self, surf):
        bg = self.background.copy()
        # Draw text
        for idx, line in enumerate(self.text_lines):
            self.font.blit_center(line, bg, (bg.get_width()//2, idx * self.font.height + 4))

        if self.transition == 'start':
            bg = image_mods.make_translucent(bg, 1.1 - self.transition_progress)
        elif self.transition == 'end':
            bg = image_mods.make_translucent(bg, .1 + (self.transition_progress * .9))
        else:
            bg = image_mods.make_translucent(bg, .1)
        surf.blit(bg, self.position)

        return surf
