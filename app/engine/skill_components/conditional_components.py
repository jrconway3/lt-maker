from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine.game_state import game

class CombatCondition(SkillComponent):
    nid = 'combat_condition'
    desc = "Status is conditional based on combat properties"
    tag = "advanced"

    expose = Type.String
    value = 'False'

    def init(self, skill):
        self._condition = False

    def pre_combat(self, playback, unit, item, target):
        try:
            self._condition = bool(eval(self.value))
        except:
            print("Could not evaluate %s" % self.value)

    def post_combat(self, playback, unit, item, target):
        self._condition = False

    def condition(self, unit):
        return self._condition

    def test_on(self, unit, item, target):
        self.pre_combat([], unit, item, target)

    def test_off(self, unit, item, target):
        self._condition = False

class Condition(SkillComponent):
    nid = 'condition'
    desc = "Status is conditional"
    tag = "advanced"

    expose = Type.String
    value = 'False'

    def condition(self, unit):
        try:
            return bool(eval(self.value))
        except:
            print("Could not evaluate %s" % self.value)
