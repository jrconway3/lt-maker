from __future__ import annotations

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
        self.last_entry: DialogEntryComponent = None

    def append(self, dialog: Dialog):
        self.last_entry = self.ui.add_entry(dialog)

    def pop(self):
        ui.remove_entry(self.last_entry)
        self.last_entry = self.ui.get_last_entry()

    def clear(self):
        while self.last_entry:
            self.pop()
