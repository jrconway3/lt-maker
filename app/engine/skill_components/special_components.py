from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action, item_funcs, item_system, static_random
from app.engine.game_state import game

class Ability(SkillComponent):
    nid = 'ability'
    desc = "Give unit an item as an extra ability"
    tag = "advanced"

    expose = Type.Item

    def extra_ability(self, unit):
        # Find if any item already exists with the name we need
        for item in game.item_registry.values():
            if item.nid == self.value and item.owner_nid == unit.nid:
                new_item = item
                break
        else:
            new_item = item_funcs.create_item(unit, self.value)
            game.register_item(new_item)
        return new_item

    def end_combat(self, playback, unit, item, target):
        if item and item.nid == self.value:
            action.do(action.TriggerCharge(unit, self.skill))

class CombatArt(SkillComponent):
    nid = 'combat_art'
    desc = "Unit has the ability to apply an extra effect to next attack"
    tag = 'advanced'

    expose = Type.Skill

    def init(self, skill):
        self.skill.data['active'] = False
        self._action = None

    def combat_art(self, unit):
        return self.value

    def on_activation(self, unit):
        # I don't think this needs to use an action
        # because there will be no point in the turnwheel
        # where you could stop it at True
        self.skill.data['active'] = True
        self._action = action.AddSkill(unit, self.value)
        action.do(self._action)

    def on_deactivation(self, unit):
        self.skill.data['active'] = False
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

    def combat_art_weapon_filter(self, unit) -> list:
        from app.engine import evaluate
        good_weapons = []
        for item in item_funcs.get_all_items(unit):
            try:
                if bool(evaluate.evaluate(self.value, unit, item=item)):
                    good_weapons.append(item)
            except:
                print("Couldn't evaluate conditional: %s" % self.value)
        return good_weapons

def get_proc_rate(unit, skill) -> int:
    for component in skill.components:
        if component.defines('proc_rate'):
            return component.proc_rate(unit)
    return 100  # 100 is default
            
class AttackProc(SkillComponent):
    nid = 'attack_proc'
    desc = "Allows skill to proc when about to attack"
    tag = 'advanced'

    expose = Type.Skill

    def init(self, skill):
        self._did_action = False

    def start_sub_combat(self, unit, item, target, mode):
        proc_rate = get_proc_rate(unit, self.skill)
        if static_random.get_combat() < proc_rate:
            action.do(action.AddSkill(unit, self.value))
            self._did_action = True
        
    def end_sub_combat(self, unit, item, target, mode):
        if self._did_action:
            action.do(action.RemoveSkill(unit, self.value))

class DefenseProc(SkillComponent):
    nid = 'defense_proc'
    desc = "Allows skill to proc when defending"
    tag = 'advanced'

    expose = Type.Skill

    def init(self, skill):
        self._did_action = False

    def start_sub_combat(self, unit, item, target, mode):
        proc_rate = get_proc_rate(unit, self.skill)
        if static_random.get_combat() < proc_rate:
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

class DeathTether(SkillComponent):
    nid = 'death_tether'
    desc = "Remove all skills in the game that I initiated on my death"
    tag = 'advanced'

    def on_death(self, unit):
        for other_unit in game.units:
            for skill in other_unit.skills:
                if skill.initiator_nid == unit.nid:
                    action.do(action.RemoveSkill(other_unit, skill))

class Oversplash(SkillComponent):
    nid = 'oversplash'
    desc = "Grants unit +X area of effect for regular and blast items"
    tag = 'advanced'

    expose = Type.Int
    value = 1

    def empower_splash(self, unit):
        return self.value

    def alternate_splash(self, unit):
        from app.engine.item_components.aoe_components import BlastAOE
        return BlastAOE(self.value)

class Cleave(SkillComponent):
    nid = 'Cleave'
    desc = "Grants unit the ability to cleave with all their non-splash attacks"
    tag = 'advanced'

    def alternate_splash(self, unit):
        from app.engine.item_components.aoe_components import EnemyCleaveAOE
        return EnemyCleaveAOE()

class Aura(SkillComponent):
    nid = 'aura'
    desc = "Skill has an aura that gives off child skill"
    tag = 'advanced'
    paired_with = ('aura_range', 'aura_target')

    expose = Type.Skill

class AuraRange(SkillComponent):
    nid = 'aura_range'
    desc = "Set range of skill's aura"
    tag = 'advanced'
    paired_with = ('aura', 'aura_target')

    expose = Type.Int
    value = 3

class AuraTarget(SkillComponent):
    nid = 'aura_target'
    desc = "Set target of skill's aura (set to 'ally', 'enemy', or 'unit')"
    tag = 'advanced'
    paired_with = ('aura', 'aura_range')

    expose = Type.String
    value = 'unit'
