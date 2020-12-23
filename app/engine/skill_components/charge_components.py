from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action
from app.engine.game_state import game

class BuildCharge(SkillComponent):
    nid = 'build_charge'
    desc = "Skill will gain charges after each combat until full"
    tag = "advanced"

    expose = Type.Int
    value = 10

    def init(self, skill):
        self.skill.data['charge'] = 0
        self.skill.data['total_charge'] = self.value

    def condition(self, unit, skill):
        return self.skill.data['charge'] >= self.skill.data['charge']

    def on_end_chapter(self, unit, skill):
        self.skill.data['charge'] = 0

    def trigger_charge(self, unit, skill):
        self.skill.data['charge'] = 0

    def text(self) -> str:
        return str(self.skill.data['charge'])

class DrainCharge(SkillComponent):
    nid = 'drain_charge'
    desc = "Skill will have a number of charges that are drained by 1 when activated"
    tag = "advanced"

    expose = Type.Int
    value = 1

    def init(self, skill):
        self.skill.data['charge'] = self.value
        self.skill.data['total_charge'] = self.value

    def condition(self, unit, skill):
        return self.skill.data['charge'] > 0

    def on_end_chapter(self, unit, skill):
        self.skill.data['charge'] = self.skill.data['total_charge']

    def trigger_charge(self, unit, skill):
        self.skill.data['charge'] -= 1

    def text(self) -> str:
        return str(self.skill.data['charge'])

class CombatChargeIncrease(SkillComponent):
    nid = 'combat_charge_increase'
    desc = "Increases charge of skill each combat"
    tag = "advanced"

    expose = Type.Int
    value = 5

    def end_combat(self, playback, unit, item, target):
        action.SetObjData(self.skill, 'charge', self.skill.data['charge'] + self.value)

class CombatChargeIncreaseByStat(SkillComponent):
    nid = 'combat_charge_increase_by_stat'
    desc = "Increases charge of skill each combat"
    tag = "advanced"

    expose = Type.Stat

    def end_combat(self, playback, unit, item, target):
        new_value = self.skill.data['charge'] + unit.stats[self.value] + unit.stat_bonus(self.value)
        action.SetObjData(self.skill, 'charge', new_value)
