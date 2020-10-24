from app.utilities.data import Data, Prefab
from app.events import event_commands

all_triggers = ['level_start', 'turn_change']

class EventPrefab(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.trigger = None
        self.level_nid = None
        self.condition: str = "True"
        self.commands = []

    def save_attr(self, name, value):
        if name == 'commands':
            value = [c.save() for c in value]
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'commands':
            value = [event_commands.restore_command(c) for c in value]
        else:
            value = super().restore_attr(name, value)
        return value

    @classmethod
    def default(cls):
        return cls('None')

class EventCatalog(Data):
    datatype = EventPrefab

    def get(self, trigger, level_nid):
        # For now just returns events
        # Ignores level_nid
        return [event for event in self._list if event.trigger == trigger and
                (not event.level_nid or event.level_nid == level_nid)]
