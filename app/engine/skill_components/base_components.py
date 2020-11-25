from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action
from app.engine.game_state import game

# status plugins
class Unselectable(SkillComponent):
    nid = 'unselectable'
    desc = "Unit cannot be selected"
    tag = 'base'

    def can_select(self, unit) -> bool:
        return False

class IgnoreAlliances(SkillComponent):
    nid = 'ignore_alliances'
    desc = "Unit will treat all units as enemies"
    tag = 'base'

    def check_ally(self, unit1, unit2) -> bool:
        return False

    def check_enemy(self, unit1, unit2) -> bool:
        return True

class Canto(SkillComponent):
    nid = 'canto'
    desc = "Unit can move again after certain actions"
    tag = 'movement'

    def has_canto(self, unit) -> bool:
        return not unit.has_attacked

class CantoPlus(SkillComponent):
    nid = 'canto_plus'
    desc = "Unit can move again even after attacking"
    tag = 'movement'

    def has_canto(self, unit) -> bool:
        return True

class CantoSharp(SkillComponent):
    nid = 'canto_sharp'
    desc = "Unit can move and attack in either order"
    tag = 'movement'

    def has_canto(self, unit) -> bool:
        return not unit.has_attacked or unit.movement_left >= equations.parser.movement(unit)

class Regeneration(SkillComponent):
    nid = 'regeneration'
    desc = "Unit restores %% of HP at beginning of turn"
    tag = "status"

    expose = Type.Float
    value = 0.2

    def on_upkeep(self, unit):
        max_hp = equations.parser.hitpoints(unit)
        hp_change = max_hp * self.value
        action.do(action.ChangeHP(unit, hp_change))

class Time(SkillComponent):
    nid = 'time'
    desc = "Lasts for some number of turns"
    tag = "base"

    expose = Type.Int
    value = 2

    def init(self, unit):
        self.skill.data['turns'] = self.value
        self.skill.data['starting_turns'] = self.value

    def on_upkeep(self, unit):
        self.skill.data['turns'] -= 1
        if self.skill.data['turns'] <= 0:
            action.do(action.RemoveSkill(unit, self.skill))
