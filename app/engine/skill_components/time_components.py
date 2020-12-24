from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action
from app.engine.game_state import game

class Time(SkillComponent):
    nid = 'time'
    desc = "Lasts for some number of turns"
    tag = "time"

    expose = Type.Int
    value = 2

    def init(self, skill):
        self.skill.data['turns'] = self.value
        self.skill.data['starting_turns'] = self.value

    def on_upkeep(self, actions, playback, unit):
        val = self.skill.data['turns'] - 1
        action.do(action.SetObjData(self.skill, 'turns', val))
        if self.skill.data['turns'] <= 0:
            actions.append(action.RemoveSkill(unit, self.skill))

    def text(self) -> str:
        return str(self.skill.data['turns'])

class LostOnEndstep(SkillComponent):
    nid = 'lost_on_endstep'
    desc = "Remove on next endstep"
    tag = "time"

    def on_endstep(self, actions, playback, unit):
        actions.append(action.RemoveSkill(unit, self.skill))

class EventOnRemove(SkillComponent):
    nid = 'event_on_remove'
    desc = "Calls event when removed"
    tag = "time"

    expose = Type.Event

    def on_remove(self, unit, skill):
        did_something = game.events.trigger(self.value, unit)
        if did_something:
            game.state.change('event')
