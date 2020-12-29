from app.utilities.data import Data, Prefab
from app.events import event_commands

class Trigger(object):
    def __init__(self, nid, unit1=False, unit2=False, position=False, region=False):
        self.nid: str = nid
        self.unit1: bool = unit1
        self.unit2: bool = unit2
        self.position: bool = position
        self.region: bool = region

all_triggers = Data([
    Trigger('level_start'),
    Trigger('level_end'),
    Trigger('turn_change'),
    Trigger('enemy_turn_change'),
    Trigger('unit_death', True, False, True),
    Trigger('unit_wait', True, False, True),
    Trigger('unit_level_up', True, False, True),
    Trigger('combat_start', True, True, True),
    Trigger('combat_end', True, True, True),
    Trigger('on_talk', True, True, True),
    Trigger('before_base'),
    Trigger('on_title_screen'),
])

class EventPrefab(Prefab):
    def __init__(self, name):
        self.name = name
        self.trigger = None
        self.level_nid = None
        self.condition: str = "True"
        self.commands = []
        self.only_once = False

    @property
    def nid(self):
        if not self.name:
            return None
        if self.level_nid:
            return self.level_nid + " " + self.name
        else:
            return "Global " + self.name

    def save_attr(self, name, value):
        if name == 'commands':
            value = [c.save() for c in value if c]
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'commands':
            value = [event_commands.restore_command(c) for c in value]
            value = [v for v in value if v]
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
