from app.engine import engine
from app.engine.graphics.ui_framework.ui_framework import UIComponent
from app.engine.graphics.ui_framework.ui_framework_layout import UILayoutType, VAlignment, ListLayoutStyle
from app.engine.graphics.ui_framework.premade_components import TextComponent
from app.constants import WINWIDTH, WINHEIGHT
from pygame import Color
import re

class DialogEntryComponent(UIComponent):
    def __init__(self, name, parent, dialog):
        super().__init__(name=name, parent=parent)

        self.props.layout = UILayoutType.LIST

        self.mini_portrait = UIComponent.from_existing_surf(dialog.portrait.mini_portrait)
        self.props.list_style = ListLayoutStyle.COLUMN
        self.speaker = TextComponent("speaker", dialog.speaker, self)
        self.speaker.props.max_width = WINWIDTH

        # Remove any instances of commands from dialog text.
        text = re.sub(r'({\w*})|(\|)|(;)/', ' ', dialog.plain_text)
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
        self._init_scroll_animations()

    def _init_scroll_animations(self):
        pass

    def add_entry(self, dialog):
        entry = DialogEntryComponent(f"entry no. {self.entry_num}", self.base_component, dialog)
        self.entries.append(entry)
        self.entry_num += 1
        self.base_component.add_child(entry)

    def draw(self, surf):
        ui_surf = self.base_component.to_surf()
        surf.blit(ui_surf, (0, 0))
        return surf


class DialogLog:
    ui = DialogLogUI()
    entry_log = []

    def log_dialog(self, dialog):
        print(dialog.plain_text)
        self.entry_log.append(dialog)
        self.ui.add_entry(dialog)

    def scroll_up(self):
        pass

    def scroll_down(self):
        pass

    def draw(self, surf):
        surf = self.ui.draw(surf)
        return surf
