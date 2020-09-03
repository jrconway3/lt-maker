from app.data.skill_components import SkillComponent

from app.engine import equations
from app.engine.game_state import game

# status plugins
class Unselectable(SkillComponent):
    nid = 'unselectable'
    desc = "Unit cannot be selected"

    def can_select(unit) -> bool:
        return False

class IgnoreAlliances(SkillComponent):
    nid = 'ignore_alliances'
    desc = "Unit will treat all units as enemies"

    def check_ally(unit1, unit2) -> bool:
        return False

    def check_enemy(unit1, unit2) -> bool:
        return True

class Canto(SkillComponent):
    nid = 'canto'
    desc = "Unit can move again after certain actions"

    def has_canto(unit) -> bool:
        return not unit.has_attacked

class CantoPlus(SkillComponent):
    nid = 'canto_plus'
    desc = "Unit can move again even after attacking"

    def has_canto(unit) -> bool:
        return True

class CantoSharp(SkillComponent):
    nid = 'canto_sharp'
    desc = "Unit can move and attack in either order"

    def has_canto(unit) -> bool:
        return not unit.has_attacked or unit.movement_left >= equations.parser.movement(unit)