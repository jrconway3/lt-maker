from __future__ import annotations

from typing import Callable, List, Tuple

from app.data.database import DB
from app.data.items import ItemPrefab
from app.data.klass import Klass
from app.data.skills import SkillPrefab
from app.engine import engine
from app.engine.game_menus.menu_components.generic_menu.simple_menu import \
    ChoiceTable
from app.engine.game_state import game
from app.engine.graphics.ui_framework.ui_framework import UIComponent
from app.engine.graphics.ui_framework.ui_framework_layout import convert_align
from app.engine.icons import get_icon, get_icon_by_nid
from app.engine.objects.unit import UnitObject
from app.utilities.enums import Alignments
from app.utilities.typing import NID


class ChoiceMenuUI():
    def __init__(self, data: List[str] | Callable[[], List] = None, data_type: str = 'str',
                 title: str = None, rows: int = 0, cols: int = 1, row_width: int = -1,
                 alignment: Alignments = Alignments.CENTER, bg: str = 'menu_bg_base'):
        self._data_type = data_type
        self._data: List = None
        self._get_data: Callable[[], List] = None

        # UI stuff
        self.base_component = UIComponent.create_base_component()
        self.table = ChoiceTable('table', self.base_component, num_rows=rows, num_columns=cols, title=title, row_width=row_width, background=bg)
        halign, valign = convert_align(alignment)
        self.table.props.h_alignment = halign
        self.table.props.v_alignment = valign
        self.table.margin = (10, 10, 10, 10)
        self.base_component.add_child(self.table)

        if callable(data):
            self._get_data = data
            self.set_data(self._get_data())
        else:
            self.set_data(data)

    def set_data(self, raw_data):
        if self._data == raw_data and not self._data_type == 'type_unit': # units need to be refreshed
            return
        self._data = raw_data
        parsed_data = self.parse_data(raw_data)
        self.table.set_data(parsed_data)

    def parse_data(self, data: List[str]) -> List[str] | List[Tuple[engine.Surface, str, NID]]:
        if self._data_type == 'type_item':
            return [self.parse_item(DB.items.get(item_nid)) for item_nid in data]
        elif self._data_type == 'type_skill':
            return [self.parse_skill(DB.skills.get(skill_nid)) for skill_nid in data]
        elif self._data_type == 'type_unit':
            return [self.parse_unit(game.unit_registry.get(unit_nid)) for unit_nid in data]
        elif self._data_type == 'type_class':
            return [self.parse_klass(DB.classes.get(klass_nid)) for klass_nid in data]
        elif self._data_type == 'type_icon':
            parsed_data = [datum.split('-') for datum in data]
            return [self.parse_custom_icon_data(tup) for tup in parsed_data]
        else:
            return data

    def parse_klass(self, klass: Klass):
        raise NotImplementedError()

    def parse_custom_icon_data(self, tup: Tuple[NID, str, str, str]) -> Tuple[engine.Surface, str]:
        icon_sheet_nid = tup[0]
        icon_x = int(tup[1])
        icon_y = int(tup[2])
        text = tup[3]
        icon = get_icon_by_nid(icon_sheet_nid, icon_x, icon_y)
        return (icon, text)

    def parse_skill(self, skill: SkillPrefab) -> Tuple[engine.Surface, str]:
        if skill:
            return (get_icon(skill), skill.name, skill.nid)
        else:
            return (get_icon(skill), "ERR", "ERR")

    def parse_item(self, item: ItemPrefab) -> Tuple[engine.Surface, str]:
        if item:
            return (get_icon(item), item.name, item.nid)
        else:
            return (get_icon(item), "ERR", "ERR")

    def parse_unit(self, unit: UnitObject) -> Tuple[engine.Surface, str]:
        if unit:
            unit_sprite = unit.sprite.create_image('passive')
            unit_icon = UIComponent()
            unit_icon.size = (16, 16)
            unit_icon.overflow = (12, 0, 12, 0) # the unit sprites are kind of enormous
            unit_icon.add_surf(unit_sprite, (-24, -24))
            return (unit_icon, unit.name, unit.nid)
        else:
            return (get_icon(None), "ERR", "ERR")

    def update(self):
        if self._get_data:
            new_data = self._get_data()
            self.set_data(new_data)
        elif self._data_type == 'type_unit':
            # elif because while not mutually exclusive, we only ever need one call of "set_data"
            self.set_data(self._data)
        return True

    def get_selected(self):
        return self.table.get_selected()

    def move_up(self):
        self.table.move_up()

    def move_down(self):
        self.table.move_down()

    def move_right(self):
        self.table.move_right()

    def move_left(self):
        self.table.move_left()

    def draw(self, surf, should_draw_cursor = 1): # should_draw_cursor allows us to stop updating the cursor
        self.table.set_draw_cursor(should_draw_cursor)
        ui_surf = self.base_component.to_surf()
        surf.blit(ui_surf, (0, 0))
        return surf
