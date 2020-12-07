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

class Defense(SkillComponent):
    nid = 'defense'
    desc = "Gives +X defense"
    tag = 'combat'

    expose = Type.Int
    value = 1

    def stat_change(self, unit):
        return {'DEF': self.value}

class Avoid(SkillComponent):
    nid = 'avoid'
    desc = "Gives +X avoid"
    tag = 'combat'

    expose = Type.Int
    value = 20

    def modify_avoid(self, unit, item_to_avoid):
        return self.value

class IgnoreTerrain(SkillComponent):
    nid = 'ignore_terrain'
    desc = "Unit will not be affected by terrain"
    tag = 'base'

    def ignore_terrain(self, unit):
        return True

    def ignore_region_status(self, unit):
        return True

class Hidden(SkillComponent):
    nid = 'hidden'
    desc = "Skill will not show up on screen"
    tag = "base"

class ClassSkill(SkillComponent):
    nid = 'class_skill'
    desc = "Skill will show up on first page of info menu"
    tag = "base"

class Stack(SkillComponent):
    nid = 'stack'
    desc = "Skill can be applied to a unit multiple times"
    tag = "base"

class Time(SkillComponent):
    nid = 'time'
    desc = "Lasts for some number of turns"
    tag = "base"

    expose = Type.Int
    value = 2

    def init(self, unit):
        self.skill.data['turns'] = self.value
        self.skill.data['starting_turns'] = self.value

    def on_upkeep(self, actions, playback, unit):
        self.skill.data['turns'] -= 1
        if self.skill.data['turns'] <= 0:
            action.do(action.RemoveSkill(unit, self.skill))

    def text(self) -> str:
        return str(self.skill.data['turns'])
