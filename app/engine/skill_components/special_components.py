from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action
from app.engine.game_state import game

class Ability(SkillComponent):
    nid = 'ability'
    desc = "Give unit an item as an extra ability"
    tag = "advanced"

    expose = Type.Item

    def extra_ability(self, unit):
        return self.value

    def end_combat(self, actions, playback, unit, item, target):
        if item.nid == self.value:
            actions.append(action.TriggerCharge(unit, self.skill))

class CombatArt(SkillComponent):
    nid = 'combat_art'
    desc = "Unit has the ability to apply an extra effect to next attack"
    tag = 'advanced'

    expose = Type.Skill

    def extra_ability(self, unit):
        return self.value

    def on_activation(self, unit):
        self._action = action.AddSkill(unit, self.value)
        action.do(self._action)

    def on_deactivation(self, unit):
        action.reverse(self._action)

    def end_combat(self, actions, playback, unit, item, target):
        self.on_deactivation(unit)
        actions.append(action.TriggerCharge(unit, self.skill))

class AutomaticCombatArt(SkillComponent):
    nid = 'automatic_combat_art'
    desc = "Unit will be given skill on upkeep and removed on endstep"
    tag = 'advanced'

    expose = Type.Skill

    def on_upkeep(self, actions, playback, unit):
        actions.append(action.AddSkill(unit, self.value))
        actions.append(action.TriggerCharge(unit, self.skill))

    def on_endstep(self, actions, playback, unit):
        actions.append(action.RemoveSkill(unit, self.value))

class CombatArtAllowedWeapons(SkillComponent):
    nid = 'combat_art_allowed_weapons'
    desc = "Defines what weapons are actually allowed"
    tag = 'advanced'
    paired_with = ('combat_art', )

    expose = Type.String

    def combat_art_weapon_filter(self, unit, item):
        return eval(self.value)

class AttackProc(SkillComponent):
    nid = 'attack_proc'
    desc = "Allows skill to proc when about to attack"
    tag = 'advanced'

    expose = Type.Skill

    def init(self):
        self._did_action = False

    def start_sub_combat(self, unit, item, target, mode):
        proc_rate = skill_system.get_proc_rate(unit, self.skill)
        if proc_rate > static_random.get_combat():
            action.do(action.AddSkill(unit, self.value))
            self._did_action = True
        
    def end_sub_combat(self, unit, item, target, mode):
        if self._did_action:
            action.do(action.RemoveSkill(unit, self.value))

class DefenseProc(SkillComponent):
    nid = 'attack_proc'
    desc = "Allows skill to proc when defending"
    tag = 'advanced'

    expose = Type.Skill

    def init(self):
        self._did_action = False

    def start_sub_combat(self, unit, item, target, mode):
        proc_rate = skill_system.get_proc_rate(unit, self.skill)
        if proc_rate > static_random.get_combat():
            action.do(action.AddSkill(unit, self.value))
            self._did_action = True
        
    def end_sub_combat(self, unit, item, target, mode):
        if self._did_action:
            action.do(action.RemoveSkill(unit, self.value))

class ProcRate(SkillComponent):
    nid = 'proc_rate'
    desc = "Set the proc rate"
    tag = 'advanced'

    expose = Type.Equation

    def proc_rate(self, unit):
        return equations.parser.get(self.value, unit)
