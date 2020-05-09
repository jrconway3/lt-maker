import sys

from app import utilities
from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data import unit_object, items
from app.data.database import DB

from app.engine import banner, static_random, unit_funcs
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
        if isinstance(value, unit_object.UnitObject):
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
            return game.get_unit(value[1])
        elif value[0] == 'item':
            return game.get_item(value[1])
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

class SimpleMove(Move):
    """
    A script directed move, no animation
    """
    def __init__(self, unit, new_pos):
        self.unit = unit
        self.old_pos = self.unit.position
        self.new_pos = new_pos

    def do(self):
        game.leave(self.unit)
        self.unit.position = self.new_pos
        game.arrive(self.unit)

    def reverse(self):
        game.leave(self.unit)
        self.unit.position = self.old_pos
        game.arrive(self.unit)

class Teleport(SimpleMove):
    pass

class ForcedMovement(SimpleMove):
    pass

class Warp(SimpleMove):
    def do(self):
        self.unit.sprite.set_transition('warp_move')
        self.unit.sprite.set_next_position(self.new_pos)
        # Initiate warp flowers

    def execute(self):
        game.leave(self.unit)
        self.unit.position = self.new_pos
        game.arrive(self.unit)

class ArriveOnMap(Action):
    def __init__(self, unit, pos):
        self.unit = unit
        self.place_on_map = PlaceOnMap(unit, pos)

    def do(self):
        self.place_on_map.do()
        game.arrive(self.unit)

    def reverse(self):
        game.leave(self.unit)
        self.place_on_map.reverse()

class PlaceOnMap(Action):
    def __init__(self, unit, pos):
        self.unit = unit
        self.pos = pos

    def do(self):
        self.unit.position = self.pos
        if self.unit.position:
            self.unit.previous_position = self.unit.position

    def reverse(self):
        self.unit.position = None

class LeaveMap(Action):
    def __init__(self, unit):
        self.unit = unit
        self.remove_from_map = RemoveFromMap(self.unit)

    def do(self):
        game.leave(self.unit)
        self.remove_from_map.do()

    def reverse(self):
        self.remove_from_map.reverse()
        game.arrive(self.unit)

class RemoveFromMap(Action):
    def __init__(self, unit):
        self.unit = unit
        self.old_pos = self.unit.position

    def do(self):
        self.unit.position = None

    def reverse(self):
        self.unit.position = self.old_pos
        if self.unit.position:
            self.unit.previous_position = self.unit.position

class IncrementTurn(Action):
    def do(self):
        game.turncount += 1

    def reverse(self):
        game.turncount -= 1

class MarkPhase(Action):
    def __init__(self, phase_name):
        self.phase_name = phase_name

class LockTurnwheel(Action):
    def __init__(self, lock):
        self.lock = lock

class Message(Action):
    def __init__(self, message):
        self.message = message

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

class HasAttacked(Reset):
    def do(self):
        self.unit.has_attacked = True

class HasTraded(Reset):
    def do(self):
        self.unit.has_traded = True

# === RESCUE ACTIONS ========================================================
class Rescue(Action):
    def __init__(self, unit, rescuee):
        self.unit = unit
        self.rescuee = rescuee
        self.old_pos = self.rescuee.position

    def do(self):
        self.unit.traveler = self.rescuee.nid
        self.unit.has_attacked = True

        # TODO Add transition

        game.leave(self.rescuee)
        self.rescuee.position = None

    def execute(self):
        self.unit.traveler = self.rescuee.nid
        self.unit.has_attacked = True

        game.leave(self.rescuee)
        self.rescuee.position = None

    def reverse(self):
        self.rescuee.position = self.old_pos
        game.arrive(self.rescuee)
        self.unit.has_attacked = False
        self.unit.traveler = None

class Drop(Action):
    def __init__(self, unit, droppee, pos):
        self.unit = unit
        self.droppee = droppee
        self.pos = pos
        self.droppee_wait_action = Wait(self.droppee)
        self.action_state = unit.get_action_state()

    def do(self):
        self.droppee.position = self.pos
        game.arrive(self.droppee)
        self.droppee.sprite.change_state('normal')
        self.droppee_wait_action.do()

        self.unit.has_attacked = True
        self.unit.has_traded = True
        self.unit.traveler = None

        if utilities.calculate_distance(self.unit.position, self.pos) == 1:
            self.droppee.sprite.set_transition('fake_in')
            self.droppee.sprite.offset = [(self.unit.position[0] - self.pos[0]) * TILEWIDTH, 
                                          (self.unit.position[1] - self.pos[1]) * TILEHEIGHT]

    def execute(self):
        self.droppee.position = self.pos
        game.arrive(self.droppee)
        self.droppee.sprite.change_state('normal')
        self.droppee_wait_action.execute()

        self.unit.has_attacked = True
        self.unit.has_traded = True
        self.unit.traveler = None

    def reverse(self):
        self.unit.traveler = self.droppee.nid
        self.unit.set_action_state(self.action_state)

        self.droppee.droppee_wait_action.reverse()
        game.leave(self.droppee)
        self.droppee.position = None

class Give(Action):
    def __init__(self, unit, other):
        self.unit = unit
        self.other = other
        self.action_state = self.unit.get_action_state()

    def do(self):
        self.other.traveler = self.unit.traveler
        self.unit.traveler = None

        self.unit.has_traded = True
        
    def reverse(self):
        self.unit.traveler = self.other.traveler
        self.other.traveler = None

        self.unit.set_action_state(self.action_state)

class Take(Action):
    def __init__(self, unit, other):
        self.unit = unit
        self.other = other
        self.action_state = self.unit.get_action_state()

    def do(self):
        self.unit.traveler = self.other.traveler
        self.other.traveler = None

        self.unit.has_traded = True
        
    def reverse(self):
        self.other.traveler = self.unit.traveler
        self.unit.traveler = None

        self.unit.set_action_state(self.action_state)

# === ITEM ACTIONS ==========================================================
class PutItemInConvoy(Action):
    def __init__(self, item):
        self.item = item

    def do(self):
        game.convoy.append(self.item)
        game.alerts.append(banner.SentToConvoy(self.item))
        game.state.change('alert')

    def execute(self):
        game.convoy.append(self.item)

    def reverse(self, gameStateObj):
        game.convoy.remove(self.item)

class GiveItem(Action):
    def __init__(self, unit, item, choice=True):
        self.unit = unit
        self.item = item
        self.choice = choice

    # with banner
    def do(self):
        if self.unit.team == 'player' or len(self.unit.items) < DB.constants.get('max_items').value:
            self.unit.add_item(self.item)
            if self.choice:
                game.alerts.append(banner.AcquiredItem(self.unit, self.item))
            else:
                game.alerts.append(banner.NoChoiceAcquiredItem(self.unit, self.item))
            game.state.change('alert')

    # there shouldn't be any time this is called where the player has not already checked 
    # that there are less than cf.CONSTANTS['max_items'] items in their inventory
    def execute(self):
        if self.unit.team == 'player' or len(self.unit.items) < DB.constants.get('max_items').value:
            self.unit.add_item(self.item)

    def reverse(self):
        if self.item in self.unit.items:
            self.unit.remove_item(self.item)

class DropItem(Action):
    def __init__(self, unit, item):
        self.unit = unit
        self.item = item

    def do(self):
        self.item.droppable = False
        self.unit.add_item(self.item)
        game.alerts.append(banner.AcquiredItem(self.unit, self.item))
        game.state.change('alert')

    def execute(self):
        self.item.droppable = False
        self.unit.add_item(self.item)

    def reverse(self):
        self.item.droppable = True
        self.unit.remove_item(self.item)

class DiscardItem(Action):
    def __init__(self, unit, item):
        self.unit = unit
        self.item = item
        self.item_index = self.unit.items.index(self.item)

    def do(self):
        self.unit.remove_item(self.item)
        game.convoy.append(self.item)

    def reverse(self):
        game.convoy.remove(self.item)
        self.unit.insert_item(self.item_index, self.item)

class RemoveItem(DiscardItem):
    def do(self):
        self.unit.remove_item(self.item)

    def reverse(self):
        self.unit.insert_item(self.item_index, self.item)

class EquipItem(Action):
    """
    Assumes item is already in inventory
    """
    def __init__(self, unit, item):
        self.unit = unit
        self.item = item
        self.old_idx = self.unit.items.index(self.item)

    def do(self):
        self.unit.equip(self.item)

    def reverse(self):
        self.unit.insert_item(self.old_idx, self.item)

class TradeItem(Action):
    def __init__(self, unit1, unit2, item1, item2):
        self.unit1 = unit1
        self.unit2 = unit2
        self.item1 = item1
        self.item2 = item2
        self.item_index1 = unit1.items.index(item1) if item1 else 4
        self.item_index2 = unit2.items.index(item2) if item2 else 4

    def swap(self, unit1, unit2, item1, item2, item_index1, item_index2):
        # Do the swap
        if item1:
            unit1.remove_item(item1)
            unit2.insert_item(item_index2, item1)
        if item2:
            unit2.remove_item(item2)
            unit1.insert_item(item_index1, item2)

    def do(self):
        self.swap(self.unit1, self.unit2, self.item1, self.item2, self.item_index1, self.item_index2)

    def reverse(self):
        self.swap(self.unit1, self.unit2, self.item2, self.item1, self.item_index2, self.item_index1)

class UseItem(Action):
    def __init__(self, item):
        self.item = item

    def do(self):
        if self.item.uses:
            self.item.uses.value -= 1
        if self.item.c_uses:
            self.item.c_uses.value -= 1

    def reverse(self):
        if self.item.uses:
            self.item.uses.value += 1
        if self.item.c_cuses:
            self.item.c_uses.value += 1

class GainExp(Action):
    def __init__(self, unit, exp_gain):
        self.unit = unit
        self.old_exp = self.unit.exp
        self.exp_gain = exp_gain

    def do(self):
        self.unit.set_exp((self.old_exp + self.exp_gain) % 100)

    def reverse(self):
        self.unit.set_exp(self.old_exp)

class SetExp(GainExp):
    def do(self):
        self.unit.set_exp(self.exp_gain)

class IncLevel(Action):
    """
    Assumes unit did not promote
    """
    def __init__(self, unit):
        self.unit = unit

    def do(self):
        self.unit.level += 1

    def reverse(self):
        self.unit.level -= 1

class ApplyLevelUp(Action):
    def __init__(self, unit, stat_changes):
        self.unit = unit
        self.stat_changes = stat_changes

    def do(self):
        unit_funcs.apply_stat_changes(self.unit, self.stat_changes)

    def reverse(self):
        negative_changes = {(k, -v) for k, v in self.stat_changes.items()}
        unit_funcs.apply_stat_changes(self.unit, negative_changes)

class GainWexp(Action):
    def __init__(self, unit, item):
        self.unit = unit
        self.item = item

    def increase_wexp(self):
        if self.item.weapon:
            weapon_type = self.item.weapon.value
        elif self.item.spell:
            weapon_type = self.item.spell.weapon_type
        else:
            return 0, 0
        increase = self.item.wexp.value if self.item.wexp is not None else 1
        self.unit.wexp[weapon_type] += increase
        return self.unit.wexp[weapon_type] - increase, self.unit.wexp[weapon_type]

    def do(self):
        self.old_value, self.current_value = self.increase_wexp()
        for weapon_rank in DB.weapon_ranks:
            if self.old_value < weapon_rank.requirement and self.current_value >= weapon_rank.requirement:
                game.alerts.append(banner.GainWexp(weapon_rank, self.item))
                game.state.change('alert')
                break

    def execute(self):
        self.old_value, self.current_value = self.increase_wexp()

    def reverse(self):
        if self.item.weapon:
            weapon_type = self.item.weapon.value
        elif self.item.spell:
            weapon_type = self.item.spell.weapon_type
        else:
            return
        self.unit.wexp[weapon_type] = self.old_value

class ChangeHP(Action):
    def __init__(self, unit, num):
        self.unit = unit
        self.num = num
        self.old_hp = self.unit.get_hp()

    def do(self):
        self.unit.set_hp(self.old_hp + self.num)

    def reverse(self):
        self.unit.set_hp(self.old_hp)

class ChangeTileHP(Action):
    def __init__(self, pos, num):
        self.position = pos
        self.num = num
        self.old_hp = 1

class Die(Action):
    def __init__(self, unit):
        self.unit = unit
        self.old_pos = unit.position
        self.leave_map = LeaveMap(self.unit)
        self.drop = None

    def do(self):
        if self.unit.traveler:
            drop_me = game.level.units.get(self.unit.traveler)
            self.drop = Drop(self.unit, drop_me, self.unit.position)
            self.drop.do()
            # TODO Drop Sound

        self.leave_map.do()
        self.unit.dead = True
        self.unit.is_dying = False

    def reverse(self):
        self.unit.dead = False
        self.unit.sprite.set_transition('normal')
        self.unit.sprite.change_state('normal')

        self.leave_map.reverse()
        if self.drop:
            self.drop.reverse()

class Resurrect(Action):
    def __init__(self, unit):
        self.unit = unit

    def do(self):
        self.unit.dead = False

    def reverse(self):
        self.unit.dead = True

class UpdateUnitRecords(Action):
    def __init__(self, unit, record):
        self.unit = unit
        self.record = record

    # TODO Implement rest of this

class RecordRandomState(Action):
    run_on_load = True  # TODO is this necessary?

    def __init__(self, old, new):
        self.old = old
        self.new = new

    def do(self):
        pass

    def execute(self):
        static_random.set_combat_random_state(self.new)

    def reverse(self):
        static_random.set_combat_random_state(self.old)

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
