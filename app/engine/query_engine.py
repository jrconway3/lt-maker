from app.utilities import utils
from typing import List, Tuple
from app.engine.objects.skill import SkillObject
from app.utilities.typing import NID
from app.engine.objects.unit import UnitObject
from app.engine.game_state import GameState

import logging

class QueryType():
    SKILL = 'Skills'
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

    @categorize(QueryType.SKILL)
    def get_skill_by_nid(self, unit: UnitObject, skill_nid: NID) -> SkillObject:
        """Returns a skill object by nid.

        Args:
            unit (UnitObject): Unit in question
            skill_nid (NID): NID of skill

        Returns:
            SkillObject | None: Skill, if exists on unit, else None.
        """
        for skill in unit.skills:
            if skill.nid == skill_nid:
                return skill
        return None

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