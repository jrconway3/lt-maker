from app.engine.objects.item import ItemObject
from app.utilities import utils
from typing import List, Tuple
from app.engine.objects.skill import SkillObject
from app.utilities.typing import NID
from app.engine.objects.unit import UnitObject
from app.engine.game_state import GameState

import logging

class QueryType():
    SKILL = 'Skills'
    ITEM = 'Items'
    MAP = 'Map Functions'

def categorize(tag):
    def deco(func):
        func.tag = tag
        return func
    return deco

class GameQueryEngine():
    def __init__(self, logger: logging.Logger, game: GameState) -> None:
        self.logger = logger
        self.game = game

    def _resolve_obj(obj_or_nid):
        try:
            return obj_or_nid.uid
        except:
            try:
                return obj_or_nid.nid
            except:
                return obj_or_nid

    @categorize(QueryType.ITEM)
    def get_item(self, unit, item) -> ItemObject:
        """Returns a item object by nid.

        Args:
            unit: unit to check
            item: item to check

        Returns:
            ItemObject | None: Item if exists on unit, otherwise None
        """
        unit = self.game.get_unit(self._resolve_obj(unit))
        item = self._resolve_obj(item)
        found_items = [it for it in unit.items if it.uid == item or it.nid == item]
        if found_items:
            return found_items[0]
        return None

    @categorize(QueryType.ITEM)
    def has_item(self, unit, item) -> bool:
        """Check if unit has item.

        Args:
            unit: unit to check
            item: item to check

        Returns:
            bool: True if unit has item, else False
        """
        return bool(self.get_item(unit, item))

    @categorize(QueryType.SKILL)
    def get_skill(self, unit, skill) -> SkillObject:
        """Returns a skill object by nid.

        Args:
            unit: unit in question
            skill: nid of skill

        Returns:
            SkillObject | None: Skill, if exists on unit, else None.
        """
        unit = self.game.get_unit(self._resolve_obj(unit))
        skill = self._resolve_obj(skill)
        for sk in unit.skills:
            if sk.nid == skill:
                return sk
        return None

    @categorize(QueryType.SKILL)
    def has_skill(self, unit, skill) -> bool:
        """checks if unit has skill

        Args:
            unit: unit to check
            skill: skill to check

        Returns:
            bool: True if unit has skill, else false
        """
        return bool(self.get_skill(unit, skill))


    @categorize(QueryType.MAP)
    def get_closest_allies(self, position: Tuple[int, int], num: int = 1) -> List[Tuple[UnitObject, int]]:
        """Return a list containing the closest player units and their distances.

        Args:
            position (Tuple[int, int]): Position to query.
            num (int, optional): How many allies to search for. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns `num` pairs of `(unit, distance)` to the position.
            Will return fewer if there are fewer player units than `num`.
        """
        return sorted([(unit, utils.calculate_distance(unit.position, position)) for unit in self.game.get_player_units()],
                      key=lambda pair: pair[1])[:num]

    @categorize(QueryType.MAP)
    def get_allies_within_distance(self, position: Tuple[int, int], dist: int = 1) -> List[Tuple[UnitObject, int]]:
        """Return a list containing all player units within `dist` distance to the specific position.

        Args:
            position (Tuple[int, int]):  Position to query.
            dist (int, optional): How far to search. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns all pairs of `(unit, distance)`
            within the specified `dist`.
        """
        return [(unit, utils.calculate_distance(unit.position, position)) for unit in self.game.get_player_units() if utils.calculate_distance(unit.position, position) <= dist]

    @categorize(QueryType.MAP)
    def get_units_in_area(self, position_corner_1: Tuple[int, int], position_corner_2: Tuple[int, int]) -> List[UnitObject]:
        """Returns a list of units within a rectangular area.

        Args:
            position_corner_1 (Tuple[int, int]): (x, y) coordinates for one corner of the area
            position_corner_2 (Tuple[int, int]): (x, y) coordinates for the opposite corner

        Returns:
            List[UnitObject]: Returns all units with positions with values between those
            specified by the corners (inclusive), or an empty list if no units exist in that area
        """
        x1, y1 = position_corner_1
        x2, y2 = position_corner_2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        target_units = []
        for unit in self.game.get_all_units():
            ux, uy = unit.position
            if x1 <= ux <= x2 and y1 <= uy <= y2:
                target_units.append(unit)
        return target_units

    @categorize(QueryType.SKILL)
    def get_debuff_count(unit) -> int:
        """Checks how many negative skills the unit has.

        Args:
            unit: Unit in question

        Returns:
            int: Number of unique negative skills on the unit
        """
        return len([skill for skill in unit.skills if skill.negative])