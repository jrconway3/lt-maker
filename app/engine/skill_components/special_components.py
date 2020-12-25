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
            new_item = item_funcs.create_items(unit, [self.value])
            game.register_item(new_item)
        return new_item

    def end_combat(self, playback, unit, item, target):
        if item.nid == self.value:
            action.do(action.TriggerCharge(unit, self.skill))

class CombatArt(SkillComponent):
    nid = 'combat_art'
    desc = "Unit has the ability to apply an extra effect to next attack"
    tag = 'advanced'

    expose = Type.Skill

    def init(self):
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
        good_weapons = []
        for item in item_funcs.get_all_items(unit):
            try:
                if bool(eval(self.value)):
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

    def init(self):
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

    def init(self):
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
