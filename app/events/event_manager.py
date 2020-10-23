from app.data.database import DB
from app.events.event import Event
from app.engine.game_state import game

class EventManager():
    def __init__(self):
        self.events = []  # A stack of events

    def trigger(self, trigger):
        triggered_events = []
        for event_prefab in DB.events.get(trigger, game.level.nid):
            print(event_prefab.trigger, event_prefab.condition)
            if eval(event_prefab.condition):
                triggered_events.append(event_prefab)

        for event_prefab in triggered_events:
            new_event = Event(event_prefab.commands)
            self.events.append(new_event)
            game.state.change('event')

    def get(self):
        if self.events:
            return self.events.pop()
        return None
