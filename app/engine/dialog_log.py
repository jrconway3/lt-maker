from __future__ import annotations

import re

from app.engine.state import State
from app.engine.fluid_scroll import FluidScroll
from app.engine.game_state import game

from app.engine.graphics.dialog.dialog_log_ui import DialogLogUI

class DialogLogState(State):
    name = 'dialog_log'
    transparent = True

    def start(self):
        self.ui = game.dialog_log.ui
        self.fluid = FluidScroll()

    def begin(self):
        self.ui.scroll_all() # Set scroll to bottom.

    def take_input(self, event):
        self.fluid.update()
        directions = self.fluid.get_directions()

        if 'UP' in directions:
            self.ui.scroll_up()
        elif 'DOWN' in directions:
            self.ui.scroll_down()
        elif event == 'INFO' or event == 'BACK':
            game.state.back()

    def draw(self, surf):
        surf = self.ui.draw(surf)
        return surf

class DialogLog:
    def __init__(self):
        self.ui = DialogLogUI()
        self.entries: List[Tuple[str, str]] = []
        self.last_entry: DialogEntryComponent = None

    def append(self, *args):
        if isinstance(args[0], list):
            self._append_tuple(args[0])
        else:
            self._append_dialog(args[0])

    def _append_tuple(self, t: Tuple[str, str]):
        speaker, text = t[0], t[1]
        self.last_entry = self.ui.add_entry(speaker, text)
        self.entries.append((speaker, text))

    def _append_dialog(self, dialog: Dialog):
        speaker = dialog.speaker
        text = self.clean_speak_text(dialog.plain_text)
        self.last_entry = self.ui.add_entry(speaker, text)
        self.entries.append((speaker, text))

    def pop(self):
        self.ui.remove_entry(self.last_entry)
        self.last_entry = self.ui.get_last_entry()
        self.entries.pop()
        return self.last_entry

    def clear(self):
        while self.last_entry:
            self.pop()
        self.entries.clear()

    def save(self):
        return self.entries

    def load(self, entries: List[Tuple[str, str]]):
        for entry in entries:
            self.append(entry)

    def clean_speak_text(self, s):
        """Returns a copy of the "speak" command text without any commands

        >>> s = 'This is a test| with{w}{br} commands.'
        >>> clean_text(s)
        >>> 'This is a test with commands.'
        """
        return re.sub(r'({\w*})|(\|)|(;)/', ' ', s)

# Shorthand creating and loading from tuple.
def load_from_entries(entries: List[Tuple[str, str]]):
    d = DialogLog()
    d.load(entries)
    return d
