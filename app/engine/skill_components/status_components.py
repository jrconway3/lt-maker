from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action, item_funcs
from app.engine.game_state import game

class Regeneration(SkillComponent):
    nid = 'regeneration'
    desc = "Unit restores %% of HP at beginning of turn"
    tag = "time"

    expose = Type.Float
    value = 0.2

    def on_upkeep(self, actions, playback, unit):
        max_hp = equations.parser.hitpoints(unit)
        if unit.get_hp() < max_hp:
            hp_change = max_hp * self.value
            actions.append(action.ChangeHP(unit, hp_change))
            # Playback
            playback.append(('hit_sound', 'MapHeal'))
            if hp_change >= 30:
                name = 'MapBigHealTrans'
            elif hp_change >= 15:
                name = 'MapMediumHealTrans'
            else:
                name = 'MapSmallHealTrans'
            playback.append(('cast_anim', name, unit))

class ResistStatus(SkillComponent):
    nid = 'resist_status'
    desc = "Unit is only affected by statuses for a turn"
    tag = "base"

    def on_add(self, unit, skill):
        for skill in unit.skills:
            if skill.time:
                action.do(action.SetObjData(skill, 'turns', min(skill.data['turns'], 1)))

    def on_gain_skill(self, unit, other_skill):
        if other_skill.time:
            action.do(action.SetObjData(other_skill, 'turns', min(other_skill.data['turns'], 1)))

class ImmuneStatus(SkillComponent):
    nid = 'immune_status'
    desc = "Unit is not affected by negative statuses"
    tag = 'base'

    def on_add(self, unit, skill):
        for skill in unit.skills:
            if skill.negative:
                action.do(action.RemoveSkill(unit, skill))

    def on_gain_skill(self, unit, other_skill):
        if other_skill.negative:
            action.do(action.RemoveSkill(unit, other_skill))

class Grounded(SkillComponent):
    nid = 'grounded'
    desc = "Unit cannot be forcibly moved"
    tag = 'base'

    def ignore_forced_movement(self, unit, skill):
        return True

class ReflectStatus(SkillComponent):
    nid = 'reflect_status'
    desc = "Unit reflects statuses back to initiator"
    tag = 'base'

    def on_gain_skill(self, unit, other_skill):
        if hasattr(other_skill, 'initiator'):
            other_unit = game.get_unit(other_skill.initiator)
            # Create a copy of other skill
            new_skill = item_funcs.create_skills(other_unit, [other_skill.nid])[0]
            game.register_skill(new_skill)
            action.do(action.AddSkill(other_unit, new_skill))
