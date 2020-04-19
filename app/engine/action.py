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

class Move(Action):
    """
    A basic, user-directed move
    """
    def __init__(self, unit, new_pos, path=None):
        self.unit = unit
        self.old_pos = self.unit.position
        self.new_pos = new_pos

        self.prev_movement_left = self.unit.movement_left
        self.new_movement_left = None

        self.path = path
        self.has_moved = self.unit.has_moved

    def do(self):
        if self.path is None:
            self.path = game.cursor.path
        game.moving_units.begin_move(self.unit, self.path)

    def execute(self):
        game.leave(self.unit)
        if self.new_movement_left is not None:
            self.unit.movement_left = self.new_movement_left
        self.unit.has_moved = True
        self.unit.position = self.new_pos
        game.arrive(self.unit)

    def reverse(self):
        game.leave(self.unit)
        self.new_movement_left = self.unit.movement_left
        self.unit.movement_left = self.prev_movement_left
        self.unit.has_moved = self.has_moved
        self.unit.position = self.old_pos
        game.arrive(self.unit)

# Just another name for move
class CantoMove(Move):
    pass

class IncrementTurn(Action):
    def do(self):
        game.turncount += 1

    def reverse(self):
        game.turncount -= 1

class LockTurnwheel(Action):
    def __init__(self, lock):
        self.lock = lock

class Wait(Action):
    def __init__(self, unit):
        self.unit = unit
        self.action_state = self.unit.get_action_state()

    def do(self):
        self.unit.has_moved = True
        self.unit.has_traded = True
        self.unit.has_attacked = True
        self.unit.finished = True
        self.unit.current_move = None
        self.unit.sprite.change_state('normal')

    def reverse(self):
        self.unit.set_action_state(self.action_state)

class Reset(Action):
    def __init__(self, unit):
        self.unit = unit
        self.action_state = self.unit.get_action_state()

    def do(self):
        self.unit.reset()

    def reverse(self):
        self.unit.set_action_state(self.action_state)

class ResetAll(Action):
    def __init__(self, units):
        self.actions = [Reset(unit) for unit in units]

    def do(self):
        for action in self.actions:
            action.do()

    def reverse(self):
        for action in self.actions:
            action.reverse()

# === Master Functions for adding to the action log ===
def do(action):
    game.action_log.action_depth += 1
    action.do()
    game.action_log.action_depth -= 1
    if game.action_log.record and game.action_log.action_depth <= 0:
        game.action_log.append(action)

def execute(action):
    game.action_log.action_depth += 1
    action.execute()
    game.action_log.action_depth -= 1
    if game.action_log.record and game.action_log.action_depth <= 0:
        game.action_log.append(action)

def reverse(action):
    game.action_log.action_depth += 1
    action.reverse()
    game.action_log.action_depth -= 1
    if game.action_log.record and game.action_log.action_depth <= 0:
        game.action_log.remove(action)
