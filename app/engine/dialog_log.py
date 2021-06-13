import re
from pygame import Color

from app.constants import WINWIDTH, WINHEIGHT

from app.engine import engine
from app.engine.graphics.ui_framework.ui_framework import UIComponent
from app.engine.graphics.ui_framework.ui_framework_layout import UILayoutType, VAlignment, ListLayoutStyle
from app.engine.graphics.ui_framework.premade_animations.animation_templates import *
from app.engine.graphics.ui_framework.premade_components import TextComponent

def clean_speak_text(s):
    """Returns a copy of the "speak" command text without any commands

    >>> s = 'This is a test| with{w}{br} commands.'
    >>> clean_text(s)
    >>> 'This is a test with commands.'
    """
    return re.sub(r'({\w*})|(\|)|(;)/', ' ', s)

class DialogEntryComponent(UIComponent):
    def __init__(self, name, parent, dialog):
        super().__init__(name=name, parent=parent)

        self.props.layout = UILayoutType.LIST

        # self.mini_portrait = UIComponent.from_existing_surf(dialog.portrait.mini_portrait)
        self.props.list_style = ListLayoutStyle.COLUMN
        self.speaker = TextComponent("speaker", dialog.speaker, self)
        self.speaker.props.max_width = WINWIDTH

        text = clean_speak_text(dialog.plain_text)
        self.text = TextComponent("dialog text", text, self)
        self.text.props.max_width = WINWIDTH
        self.size = (self.parent.width, self.text.height + self.speaker.height)

        self.add_child(self.speaker)
        self.add_child(self.text)


class DialogLogUI:
    entries = []
    entry_num = 0

    def __init__(self):
        self.base_component = UIComponent.create_base_component(WINWIDTH, WINHEIGHT)
        self.base_component.props.layout = UILayoutType.LIST
        self.base_component.props.bg_color = Color(33,33,33, 175)
        self.base_component.props.list_style = ListLayoutStyle.COLUMN
        translate_onscreen_down = translate_anim((0, -WINHEIGHT/2), (0, 0), duration=3000, interp_mode=InterpolationType.LOGARITHMIC, skew=3)
        self.base_component.save_animation(translate_onscreen_down, '!enter')

    def add_entry(self, dialog):

        # If the current speaker is also the last logged speaker...
        if self.entries and self.entries[-1].speaker == dialog.speaker:
            # Append this dialog string to the previous entry's graphics object.
            dialog_text = clean_speak_text(dialog.plain_text)
            old_text = self.entries[-1].text.text  # Get's the string of text component.
            self.entries[-1].text.set_text(old_text + ' ' + dialog_text)
        else:
            # Create and add new entry to ui.
            entry = DialogEntryComponent(f"entry no. {self.entry_num}", self.base_component, dialog)
            self.entries.append(entry)
            self.entry_num += 1
            self.base_component.add_child(entry)

    def enter(self):
        self.base_component.enter()

    def draw(self, surf):
        ui_surf = self.base_component.to_surf()
        surf.blit(ui_surf, (0, 0))
        return surf


class DialogLog:
    ui = DialogLogUI()
    entry_log = []

    def log_dialog(self, dialog):
        self.entry_log.append(dialog)
        self.ui.add_entry(dialog)

    def scroll_up(self):
        pass

    def scroll_down(self):
        pass

    def draw(self, surf):
        surf = self.ui.draw(surf)
        return surf
