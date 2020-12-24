from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action
from app.engine.game_state import game

class UnitAnim(SkillComponent):
    nid = 'unit_anim'
    desc = "Displays MapAnimation over unit"
    tag = 'aesthetic'

    expose = Type.MapAnimation

    def on_add(self, unit, skill):
        unit.sprite.add_animation(self.value)

    def on_remove(self, unit, skill):
        unit.sprite.remove_animation(self.value)

# Get proc skills working before bothering with this one
class DisplaySkillIconInCombat(SkillComponent):
    nid = 'display_skill_icon_in_combat'
    desc = "Displays the skill's icon in combat"
    tag = 'aesthetic'

    def display_skill_icon(self, unit) -> bool:
        return True

"""  # Need to wait for Combat Animations implementation
class PreCombatEffect(SkillComponent):
    nid = 'pre_combat_effect'
    desc = "Displays an effect before combat"

    def pre_combat_effect(self, unit):
        return None
"""