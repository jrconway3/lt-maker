from app.data.skill_components import SkillComponent
from app.data.components import Type

class CombatCondition(SkillComponent):
    nid = 'combat_condition'
    desc = "Status is conditional based on combat properties"
    tag = "advanced"

    expose = Type.String
    value = 'False'

    def init(self, skill):
        self._condition = False

    def pre_combat(self, playback, unit, item, target):
        from app.engine import evaluate
        try:
            return bool(evaluate.evaluate(self.value, unit, target))
        except Exception as e:
            print("%s: Could not evaluate %s" % (e, self.value))

    def post_combat(self, playback, unit, item, target):
        self._condition = False

    def condition(self, unit):
        return self._condition

    def test_on(self, playback, unit, item, target):
        self.pre_combat(playback, unit, item, target)

    def test_off(self, playback, unit, item, target):
        self._condition = False

class Condition(SkillComponent):
    nid = 'condition'
    desc = "Status is conditional"
    tag = "advanced"

    expose = Type.String
    value = 'False'

    def condition(self, unit):
        from app.engine import evaluate
        try:
            return bool(evaluate.evaluate(self.value, unit))
        except Exception as e:
            print("%s: Could not evaluate %s" % (e, self.value))
