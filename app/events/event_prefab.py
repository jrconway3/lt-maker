from app.utilities.data import Data, Prefab
from app.events import event_commands

class Trigger(object):
    def __init__(self, nid, unit1=False, unit2=False, position=False):
        self.nid: str = nid
        self.unit1: bool = unit1
        self.unit2: bool = unit2
        self.position: bool = position

all_triggers = Data([
    Trigger('level_start'),
    Trigger('turn_change'),
    Trigger('enemy_turn_change'),
    Trigger('unit_death'),
    Trigger('unit_wait'),
    Trigger('unit_level_up'),
    Trigger('combat_start'),
    Trigger('combat_end'),
    Trigger('on_talk'),
    Trigger('end_level'),
    Trigger('before_base'),
    Trigger('on_title_screen'),
])

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
