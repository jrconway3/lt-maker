import sys

from app.data import units, items
from app.engine.game_state import game

class Action():
    def __init__(self):
        pass

    # When used normally
    def do(self):
        pass

    # When put in forward motion by the turnwheel
    def execute(self):
        self.do()

    # When put in reverse motion by the turnwheel
    def reverse(self):
        pass

    def serialize_obj(self, value):
        if isinstance(value, units.UniqueUnit) or isinstance(value, unit.GenericUnit):
            value = ('unit', value.nid)
        elif isinstance(value, items.Item):
            value = ('item', value.uid)
        elif isinstance(value, list):
            value = ('list', [self.serialize_obj(v) for v in value])
        elif isinstance(value, Action):
            value = ('action', value.serialize())
        else:
            value = ('generic', value)
        return value

    def serialize(self):
        ser_dict = {}
        for attr in self.__dict__.items():
            name, value = attr
            value = self.serialize_obj(value)
            ser_dict[name] = value
        return (self.__class__.__name__, ser_dict)

    def deserialize_obj(self, value):
        if value[0] == 'unit':
            return game.level.units.get(value[1])
        elif value[0] == 'item':
            return game.allitems.get(value[1])
        elif value[0] == 'list':
            return [self.deserialize_obj(v) for v in value[1]]
        elif value[0] == 'action':
            name, value = value[1][0], value[1][1]
            action = getattr(sys.modules[__name__], name)
            return action.deserialize(value)
        else:
            return value[1]

    @classmethod
    def deserialize(cls, ser_dict):
        self = cls.__new__(cls)
        for name, value in ser_dict.items():
            setattr(self, name, self.deserialize_obj(value))
        return self

class IncrementTurn(Action):
    def __init__(self):
        pass

    def do(self):
        game.turncount += 1

    def reverse(self):
        game.turncount -= 1
