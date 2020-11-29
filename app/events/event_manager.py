from app.data.database import DB
from app.events.event import Event
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

class EventManager():
    def __init__(self):
        self.events = []  # A stack of events

    def trigger(self, trigger, unit=None, unit2=None, position=None, region=None):
        unit1 = unit
        triggered_events = []
        for event_prefab in DB.events.get(trigger, game.level.nid):
            try:
                logger.debug("%s %s %s", event_prefab.trigger, event_prefab.condition, eval(event_prefab.condition))
                if event_prefab.nid not in game.already_triggered_events and eval(event_prefab.condition):
                    triggered_events.append(event_prefab)
            except:
                logger.error("Condition {%s} could not be evaluated" % event_prefab.condition)

        for event_prefab in triggered_events:
            new_event = Event(event_prefab.commands, unit, unit2, position, region)
            self.events.append(new_event)
            game.state.change('event')
            if event_prefab.only_once:
                game.already_triggered_events.append(event_prefab.nid)

    def get(self):
        if self.events:
            return self.events.pop()
        return None
