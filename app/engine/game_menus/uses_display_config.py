from __future__ import annotations

from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass


from app.engine import item_funcs, item_system
from app.engine.game_state import game

from app.engine.objects.unit import UnitObject
from app.engine.objects.item import ItemObject

class ItemOptionModes(Enum):
    NO_USES = 0
    USES = 1
    FULL_USES = 2
    FULL_USES_AND_REPAIR = 3
    VALUE = 4
    STOCK_AND_VALUE = 5
    CUSTOM = 6

@dataclass
class UsesDisplayConfig:
    get_curr_uses: Callable[[ItemObject, UnitObject], str] = None
    delim: str = ''
    get_max_uses: Callable[[ItemObject, UnitObject], str] = None
    get_uses_color: Callable[[ItemObject, UnitObject], str] = None
    override_unavailable_color: bool = None
    override_droppable_color: bool = None

    unit: Optional[UnitObject] = None
    item: Optional[ItemObject] = None

    def __add__(self, other: UsesDisplayConfig) -> UsesDisplayConfig:
        return UsesDisplayConfig(
            get_curr_uses=other.get_curr_uses if other.get_curr_uses is not None else self.get_curr_uses,
            delim=other.delim if other.delim is not None else self.delim,
            get_max_uses=other.get_max_uses if other.get_max_uses is not None else self.get_max_uses,
            get_uses_color=other.get_uses_color if other.get_uses_color is not None else self.get_uses_color,
            override_unavailable_color=other.override_unavailable_color if other.override_unavailable_color is not None else self.override_unavailable_color,
            override_droppable_color=other.override_droppable_color if other.override_droppable_color is not None else self.override_droppable_color,
            unit=self.unit,
            item=self.item
        )

    def get_uses(self) -> str:
        curr_uses = self.get_curr_uses(self.unit, self.item) if self.get_curr_uses else None
        return str(curr_uses) if curr_uses is not None else None

    def get_max(self) -> str:
        max_uses = self.get_max_uses(self.unit, self.item) if self.get_max_uses else None
        return str(max_uses) if max_uses is not None else None

    def get_color(self) -> str:
        # Grab Custom Color If It Exists
        custom_color = self.item.custom_uses_color._font_color(self.unit, self.item) if self.item and self.item.custom_uses_color else None
        if not custom_color:
            custom_color = self.get_uses_color(self.unit, self.item) if self.get_uses_color else None

        # Set Custom Color to 'grey' by Default
        uses_color = custom_color if self._override_unavailable() else 'grey'
        if self.item:
            if not self.unit or item_funcs.available(self.unit, self.item):
                uses_color = custom_color or 'blue'

            # Item is Droppable?
            if self.item.droppable and not self._override_droppable():
                uses_color = 'green'
        return uses_color

    # If true, also overrides the grey color for unavailable items.
    def _override_unavailable(self) -> bool:
        return self.override_unavailable_color or False

    # If true, also overrides the green color for droppable items.
    def _override_droppable(self) -> bool:
        return self.override_droppable_color or False

    @staticmethod
    def from_item(item: ItemObject):
        if item:
            owner = game.get_unit(item.owner_nid)
            if owner:
                custom_uses = item_system.item_uses_display(owner, item)
                if custom_uses:
                    return custom_uses
                return UsesDisplayConfig(unit=owner, item=item)
        return UsesDisplayConfig(item=item)