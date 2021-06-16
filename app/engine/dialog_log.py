import re
from pygame import Color

from app.constants import WINWIDTH, WINHEIGHT

from app.engine import engine
from app.engine.fonts import FONT
from app.engine.graphics.ui_framework.ui_framework import UIComponent
from app.engine.graphics.ui_framework.ui_framework_layout import UILayoutType, VAlignment, ListLayoutStyle
from app.engine.graphics.ui_framework.premade_components import TextComponent

def clean_speak_text(s):
    """Returns a copy of the "speak" command text without any commands

    >>> s = 'This is a test| with{w}{br} commands.'
    >>> clean_text(s)
    >>> 'This is a test with commands.'
    """
    return re.sub(r'({\w*})|(\|)|(;)/', ' ', s)


class DialogEntryComponent(UIComponent):
    def __init__(self, name, dialog, parent=None):
        super().__init__(name=name, parent=parent)

        self.horizontal_padding = 5
        self.vertical_padding = 10

        self.props.layout = UILayoutType.LIST

        self.props.list_style = ListLayoutStyle.COLUMN
        self.speaker = TextComponent("speaker", dialog.speaker, self)
        self.speaker.padding = (self.horizontal_padding, 0, 0, 0)
        self.speaker.set_font(FONT['text-yellow'])

        text = clean_speak_text(dialog.plain_text)

        self.text = TextComponent("dialog text", text, self)
        self.text.padding = (self.horizontal_padding, self.horizontal_padding, 0, self.vertical_padding)
        self.text.set_num_lines(0)
        self.size = self.calculate_size()

        self.add_child(self.speaker)
        self.add_child(self.text)

    def calculate_size(self):
        width = self.parent.width
        height = self.text.height + self.speaker.height
        return (width, height)


class DialogLogContainer(UIComponent):
    def __init__(self, name, parent=None):
        super().__init__(name=name, parent=parent)
        self.props.layout = UILayoutType.LIST
        self.props.bg_color = Color(33,33,33, 225)
        self.props.list_style = ListLayoutStyle.COLUMN
        self.text_objects: List[TextComponent] = []

    def scroll_up_down(self, dist):
        self.scroll = (self.scroll[0], self.scroll[1] + dist)

    def _reset(self, reason):
        if reason == 'height':
            return
        # Recalculates our own height
        # this automatically triggers whenever we add a child
        self_height = 0
        for text in self.text_objects:
            text_height = text.height
            self_height += text_height
        self.height = max(self_height, self.parent.height)

    def add_entry(self, dialog_entry: DialogEntryComponent):
        self.add_child(dialog_entry)
        self.text_objects.append(dialog_entry)

    def get_last_entry(self):
        if self.text_objects:
            return self.text_objects[-1]
        else:
            return None


class DialogLogUI:
    entry_count = 0

    def __init__(self):
        self.base_component = UIComponent.create_base_component(WINWIDTH, WINHEIGHT)
        self.base_component.name = "base"

        self.log_container = DialogLogContainer('container', parent=self.base_component) # Component contains all the dialog log entries.
        self.base_component.add_child(self.log_container)

    def add_entry(self, dialog):
        # Create and add new entry to ui.
        entry = DialogEntryComponent(f"entry no. {self.entry_count}", dialog, parent=self.log_container)
        self.entry_count += 1
        self.log_container.add_entry(entry)

    def extend_entry(self, dialog, entry=None):
        """Append this dialog string to the previous entry's graphics object.

        Precondition: if entry is None then self.log_container.get_last_entry()
                      is not None
        """

        if entry is None:
            entry = self.log_container.get_last_entry()

        # Append this dialog string to the previous entry's graphics object.
        dialog_text = clean_speak_text(dialog.plain_text)
        old_text = last_entry.text.text  # Get's the string of text component.
        last_entry.text.set_text(old_text + ' ' + dialog_text)
        last_entry.size = last_entry.calculate_size()
        self.log_container._reset("height")

    def scroll_up(self):
        self.log_container.scroll_up_down(-10)

    def scroll_down(self):
        self.log_container.scroll_up_down(10)

    def draw(self, surf):
        ui_surf = self.base_component.to_surf()
        surf.blit(ui_surf, (0, 0))
        return surf


class DialogLog:
    ui = DialogLogUI()
    last_dialog = None

    def log_dialog(self, dialog):
        self.ui.add_entry(dialog)

    def update(self, dialog):
        if dialog == last_dialog:
            pass

        self.last_dialog = dialog

    def scroll_up(self):
        self.ui.scroll_up()

    def scroll_down(self):
        self.ui.scroll_down()

    def draw(self, surf):
        surf = self.ui.draw(surf)
        return surf
