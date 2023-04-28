from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Callable, Generic, Optional, TypeVar

from app.data.database.database import DB
from app.engine import (engine, help_menu, icons, image_mods, item_funcs,
                        item_system, text_funcs)
from app.engine.game_state import game
from app.engine.graphics.text.text_renderer import (anchor_align, render_text,
                                                    text_width)
from app.engine.objects.item import ItemObject
from app.sprites import SPRITES
from app.utilities.enums import HAlignment
from app.utilities.str_utils import is_int
from app.utilities.typing import NID, Protocol


T = TypeVar('T')

class IMenuOption(Protocol, Generic[T]):
    get: Callable[[], T]
    set: Callable[[T, str], None]
    height: Callable[[], int]
    width: Callable[[], int]
    set_width: Callable[[int], None]
    get_ignore: Callable[[], bool]
    set_ignore: Callable[[bool], None]
    set_help_box: Callable[[help_menu.HelpDialog], None]
    get_help_box: Callable[[], Optional[help_menu.HelpDialog]]
    @property
    def help_box(self) -> help_menu.HelpDialog:
        pass
    @property
    def ignore(self) -> bool:
        pass
    draw: Callable[[engine.Surface, int, int], None]
    draw_highlight: Callable[[engine.Surface, int, int, int], None]

class BaseOption(IMenuOption[T]):
    def __init__(self, idx: int, value: T, display_value: Optional[str] = None, width: int = 0,
                 height: int = 0, ignore: bool = False):
        self.idx: int = idx
        self._value: T = value
        self._disp_value: str = display_value or ""
        self._width: int = width
        self._height: int = height
        self._ignore: bool = ignore
        self._help_box: Optional[help_menu.HelpDialog] = None

    def get(self):
        return self._value

    def set(self, val: T, disp_val: Optional[str]=None):
        raise NotImplementedError()

    def height(self):
        # 16 is standard text height
        return self._height or 16

    def width(self):
        # arbitrarily chosen
        return self._width or 80

    def set_width(self, width: int):
        self._width = width

    def get_ignore(self):
        return self._ignore

    def set_ignore(self, ignore: bool):
        self._ignore = ignore

    def set_help_box(self, help_box: help_menu.HelpDialog):
        self._help_box = help_box

    def get_help_box(self):
        return self._help_box

    @property
    def help_box(self) -> Optional[help_menu.HelpDialog]:
        return self.get_help_box()

    @help_box.setter
    def help_box(self, help_box: help_menu.HelpDialog):
        self.set_help_box(help_box)

    @property
    def ignore(self) -> bool:
        return self.get_ignore()

    @ignore.setter
    def ignore(self, ig: bool):
        self.set_ignore(ig)

    def draw(self, surf, x, y):
        raise NotImplementedError()

    def draw_highlight(self, surf, x, y, menu_width):
        highlight_surf = SPRITES.get('menu_highlight')
        width = highlight_surf.get_width()
        for slot in range((menu_width - 10)//width):
            left = x + 5 + slot*width
            top = y + 9
            surf.blit(highlight_surf, (left, top))
        self.draw(surf, x, y)
        return surf

class TextOption(BaseOption[str]):
    def __init__(self, idx: int, value: str, display_value: str | None = None, width: int = 0,
                 height: int = 0, ignore: bool = False, font: NID = 'text', text_color: NID = 'white',
                 align: HAlignment = HAlignment.LEFT):
        super().__init__(idx, value, display_value, width, height, ignore)
        self._disp_value = text_funcs.translate(display_value or value)
        self._align = align
        self._color = text_color
        self._font = font

    def set(self, val: str, disp_val: Optional[str]=None):
        self._value = val
        self._disp_value = text_funcs.translate(disp_val or val)

    def width(self):
        return self._width or text_width(self._font, self._disp_value) + 24

    def get_color(self):
        if self.get_ignore():
            return 'grey'
        return self._color

    def set_color(self, color: NID):
        self._color = color

    def draw(self, surf, x, y):
        blit_loc = anchor_align(x, self.width(), self._align, (5, 5)), y
        render_text(surf, [self._font], [self._disp_value], [self.get_color()], blit_loc, self._align)

class NarrowOption(TextOption):
    def __init__(self, idx: int, value: str, display_value: str | None = None, width: int = 0, height: int = 0, ignore: bool = False, font: NID = 'text', text_color: NID = 'white', align: HAlignment = HAlignment.LEFT):
        super().__init__(idx, value, display_value, width, height, ignore, font, text_color, align)

    def width(self):
        return self._width or text_width(self._font, self._disp_value)

class NullOption(BaseOption[None]):
    def __init__(self, idx: int, display_text: str = 'Nothing', width: int = 0, font: NID = 'text', text_color: NID = 'white', align: HAlignment = HAlignment.LEFT):
        super().__init__(idx, None, display_text, width)
        self._align = align
        self._color = text_color
        self._font = font

    def set(self, val, disp_val):
        return

    def draw(self, surf, x, y):
        blit_loc = anchor_align(x, self.width(), self._align, (5, 5)), y
        render_text(surf, [self._font], [self._disp_value], [self._color], blit_loc, self._align)

class ItemOptionUtils():
    @staticmethod
    def draw_icon(surf, x, y, item: ItemObject):
        icon = icons.get_icon(item)
        if icon:
            surf.blit(icon, (x + 2, y))

    @staticmethod
    def draw_without_uses(surf, x, y, item: ItemObject, font: NID, color: NID, width: int,
                          align: HAlignment = HAlignment.LEFT, disp_text: Optional[str] = None):
        ItemOptionUtils.draw_icon(surf, x, y, item)
        display_text = disp_text or item.name
        if text_width(font, display_text) > width - 20:
            font = 'narrow'
        blit_loc = anchor_align(x, width, align, (20, 5)), y

        render_text(surf, [font], [display_text], [color], blit_loc)

    @staticmethod
    def draw_with_uses(surf, x, y, item: ItemObject, font: NID, color: NID, uses_color: NID,
                       width: int, align: HAlignment = HAlignment.LEFT,
                       disp_text: Optional[str] = None):
        ItemOptionUtils.draw_icon(surf, x, y, item)
        display_text = disp_text or item.name
        uses_font = font
        if text_width(font, display_text) > width - 36:
            font = 'narrow'
        blit_loc = anchor_align(x, width, align, (20, 16)), y
        render_text(surf, [font], [display_text], [color], blit_loc, align)
        uses_string = '--'
        if item.uses:
            uses_string = str(item.data['uses'])
        elif item.parent_item and item.parent_item.uses and item.parent_item.data['uses']:
            uses_string = str(item.parent_item.data['uses'])
        elif item.c_uses:
            uses_string = str(item.data['c_uses'])
        elif item.parent_item and item.parent_item.c_uses and item.parent_item.data['c_uses']:
            uses_string = str(item.parent_item.data['c_uses'])
        elif item.cooldown:
            uses_string = str(item.data['cooldown'])
        uses_loc = anchor_align(x, width, HAlignment.RIGHT, (0, 5)), y
        render_text(surf, [uses_font], [uses_string], [uses_color], uses_loc, HAlignment.RIGHT)

    @staticmethod
    def draw_with_full_uses(surf, x, y, item: ItemObject, font: NID, color: NID, uses_color: NID,
                       width: int, align: HAlignment = HAlignment.LEFT,
                       disp_text: Optional[str] = None):
        ItemOptionUtils.draw_icon(surf, x, y, item)
        main_font = font
        display_text = disp_text or item.name
        if text_width(main_font, display_text) > width - 56:
            main_font = 'narrow'
        uses_font = font
        blit_loc = anchor_align(x, width, align, (20, 36)), y
        render_text(surf, [main_font], [display_text], [color], blit_loc, align)

        uses_string_a = '--'
        uses_string_b = '--'
        if item.data.get('uses') is not None:
            uses_string_a = str(item.data['uses'])
            uses_string_b = str(item.data['starting_uses'])
        elif item.data.get('c_uses') is not None:
            uses_string_a = str(item.data['c_uses'])
            uses_string_b = str(item.data['starting_c_uses'])
        elif item.parent_item and item.parent_item.data.get('uses') is not None:
            uses_string_a = str(item.parent_item.data['uses'])
            uses_string_b = str(item.parent_item.data['starting_uses'])
        elif item.parent_item and item.parent_item.data.get('c_uses') is not None:
            uses_string_a = str(item.parent_item.data['c_uses'])
            uses_string_b = str(item.parent_item.data['starting_c_uses'])
        elif item.data.get('cooldown') is not None:
            uses_string_a = str(item.data['cooldown'])
            uses_string_b = str(item.data['starting_cooldown'])
        uses_string_a_loc = anchor_align(x, width, HAlignment.RIGHT, (0, 24)), y
        uses_string_b_loc = anchor_align(x, width, HAlignment.RIGHT, (0, 0)), y
        slash_loc = anchor_align(x, width, HAlignment.RIGHT, (0, 16)), y
        render_text(surf, [uses_font], [uses_string_a], [uses_color], uses_string_a_loc, HAlignment.RIGHT)
        render_text(surf, [uses_font], ["/"], [], slash_loc, HAlignment.RIGHT)
        render_text(surf, [uses_font], [uses_string_b], [uses_color], uses_string_b_loc, HAlignment.RIGHT)


class ItemOptionModes(Enum):
    NO_USES = 0
    USES = 1
    FULL_USES = 2
    FULL_USES_AND_REPAIR = 3
    VALUE = 4
    STOCK_AND_VALUE = 5


class BasicItemOption(BaseOption[ItemObject]):
    def __init__(self, idx: int, item: ItemObject, display_value: str | None = None,  width: int = 0,
                 height: int = 0, ignore: bool = False, font: NID = 'text', text_color: NID = 'white',
                 align: HAlignment = HAlignment.LEFT, mode: ItemOptionModes = ItemOptionModes.NO_USES):
        super().__init__(idx, item, display_value, width, height, ignore)
        self._disp_value = text_funcs.translate(display_value or self._value.name)
        self._align = align
        self._color = text_color
        self._font = font
        self._mode = mode

    @classmethod
    def from_nid(cls, idx, item_nid: NID, display_value: str | None = None, width: int = 0,
                 height: int = 0, ignore: bool = False, font: NID = 'text', text_color: NID = 'white',
                 align: HAlignment = HAlignment.LEFT, mode: ItemOptionModes = ItemOptionModes.NO_USES):
        item_prefab = DB.items.get(item_nid, None)
        if not item_prefab:
            raise ValueError("%s is not an item" % item_nid)
        as_item = ItemObject.from_prefab(item_prefab)
        return cls(idx, as_item, display_value, width, height, ignore, font, text_color, align, mode)

    @classmethod
    def from_uid(cls, idx, item_uid: int, display_value: str | None = None, width: int = 0,
                 height: int = 0, ignore: bool = False, font: NID = 'text', text_color: NID = 'white',
                 align: HAlignment = HAlignment.LEFT, mode: ItemOptionModes = ItemOptionModes.NO_USES):
        item_object = game.item_registry.get(item_uid)
        if not item_object:
            raise ValueError("%s is not a valid item uid" % item_uid)
        return cls(idx, item_object, display_value, width, height, ignore, font, text_color, align, mode)

    @classmethod
    def from_item(cls, idx, value: ItemObject, display_value: str | None = None, width: int = 0,
                 height: int = 0, ignore: bool = False, font: NID = 'text', text_color: NID = 'white',
                 align: HAlignment = HAlignment.LEFT, mode: ItemOptionModes = ItemOptionModes.NO_USES):
        return cls(idx, value, display_value, width, height, ignore, font, text_color, align, mode)

    def width(self):
        return self._width or 104

    def set(self, val: ItemObject, disp_val: Optional[str]=None):
        self._value = val
        self._disp_value = text_funcs.translate(disp_val or self._value.name)

    def get_color(self):
        owner = game.get_unit(self._value.owner_nid)
        main_color = 'grey'
        uses_color = 'grey'
        if self.get_ignore():
            pass
        elif self._color:
            main_color = self._color
            if owner and not item_funcs.available(owner, self._value):
                pass
            else:
                uses_color = 'blue'
        elif self._value.droppable:
            main_color = 'green'
            uses_color = 'green'
        elif not owner or item_funcs.available(owner, self._value):
            main_color = 'white'
            uses_color = 'blue'
        return main_color, uses_color

    def get_help_box(self):
        if not self._help_box:
            if item_system.is_weapon(None, self._value) or item_system.is_spell(None, self._value):
                self._help_box = help_menu.ItemHelpDialog(self._value)
            else:
                self._help_box = help_menu.HelpDialog(self._value.desc)
        return self._help_box

    def draw(self, surf, x, y):
        main_color, uses_color = self.get_color()
        if self._mode == ItemOptionModes.NO_USES:
            ItemOptionUtils.draw_without_uses(surf, x, y, self._value, self._font, main_color, self.width(), self._align, self._disp_value)
        elif self._mode == ItemOptionModes.USES:
            ItemOptionUtils.draw_with_uses(surf, x, y, self._value, self._font, main_color, uses_color, self.width(), self._align, self._disp_value)
        elif self._mode == ItemOptionModes.FULL_USES:
            ItemOptionUtils.draw_with_full_uses(surf, x, y, self._value, self._font, main_color, uses_color, self.width(), self._align, self._disp_value)
