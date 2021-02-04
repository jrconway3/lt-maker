import sys

from app.engine.game_state import game

class Record():
    def __init__(self):
        self.turn = game.turncount
        self.level_nid = game.level.nid if game.level else None

    def save(self):
        ser_dict = {}
        for attr in self.__dict__.items():
            name, value = attr
            ser_dict[name] = value
        return (self.__class.__name__, ser_dict)

    @classmethod
    def restore(cls, ser_dict):
        self = cls.__new__(cls)
        for name, value in ser_dict.items():
            setattr(self, name, value)
        return self

class KillRecord(Record):
    def __init__(self, killer: str, killee: str):
        super().__init__()
        self.killer = killer
        self.killee = killee

class DamageRecord(Record):
    def __init__(self, dealer: str, receiver: str, item_nid: str, over_damage: int, damage: int, kind: str):
        super().__init__()
        self.dealer = dealer
        self.receiver = receiver
        self.item_nid = item_nid
        self.over_damage = over_damage
        self.damage = damage
        self.kind = kind  # hit, crit, miss

class ItemRecord(Record):
    def __init__(self, user: str, item_nid: str):
        super().__init__()
        self.user = user
        self.item_nid = item_nid

class StealRecord(Record):
    def __init__(self, stealer: str, stealee: str, item_nid: str):
        super().__init__()
        self.stealer = stealer
        self.stealee = stealee
        self.item_nid = item_nid

class CombatRecord(Record):
    def __init__(self, attacker: str, defender: str, result: str):
        super().__init__()
        self.attacker = attacker
        self.defender = defender
        self.result = result

class LevelRecord(Record):
    def __init__(self, unit_nid: str, num: int, klass: str):
        super().__init__()
        self.unit_nid = unit_nid
        self.num = num
        self.klass = klass

class Recordkeeper():
    """
    Needs to keep track of:
    Kills
    Damage Dealt
    Overkill Damage
    Damage Received
    Damage Prevented/Blocked
    Healing (Self and Other)
    Hits/Crits/Misses
    Levels Gained/Exp Gained
    Turnwheel Uses
    Deaths
    Using an Item
    Stealing an Item
    Recruiting a Unit
    Turns Taken

    And for all these, needs to know what Chapter and Turn
    """

    def __init__(self):
        self.kills = []
        self.damage = []
        self.healing = []
        self.death = []
        self.item_use = []
        self.steal = []
        self.combat_results = []
        self.turn_taken = []
        self.levels = []
        self.exp = []

    def save(self):
        ser_dict = {}
        ser_dict['kills'] = [record.save() for record in self.kills]
        ser_dict['damage'] = [record.save() for record in self.damage]
        ser_dict['healing'] = [record.save() for record in self.healing]
        ser_dict['death'] = [record.save() for record in self.death]
        ser_dict['item_use'] = [record.save() for record in self.item_use]
        ser_dict['steal'] = [record.save() for record in self.steal]
        ser_dict['combat_results'] = [record.save() for record in self.combat_results]
        ser_dict['turns_taken'] = [record.save() for record in self.turns_taken]
        ser_dict['levels'] = [record.save() for record in self.levels]
        ser_dict['exp'] = [record.save() for record in self.exp]
        return ser_dict

    @classmethod
    def restore(cls, ser_dict):
        self = cls()
        for name, data in ser_dict.items():
            cur_list = getattr(self, name)
            for obj in data:
                obj_name, value = obj
                record_type = getattr(sys.modules[__name__], obj_name)
                record = record_type.restore(value)
                cur_list.append(record)

    def append(self, record_type: str, data: tuple):
        if record_type == 'kill':
            self.kills.append(KillRecord(*data))
        elif record_type == 'damage':
            self.damage.append(DamageRecord(*data))
        elif record_type == 'heal':
            self.healing.append(DamageRecord(*data))
        elif record_type == 'death':
            self.death.append(KillRecord(*data))
        elif record_type == 'item_use':
            self.item_use.append(ItemRecord(*data))
        elif record_type == 'steal':
            self.steal.append(StealRecord(*data))
        elif record_type == 'hit':
            self.combat_results.append(CombatRecord(*data, 'hit'))
        elif record_type == 'miss':
            self.combat_results.append(CombatRecord(*data, 'miss'))
        elif record_type == 'crit':
            self.combat_results.append(CombatRecord(*data, 'crit'))
        elif record_type == 'turn':
            self.turn_taken.append(Record())
        elif record_type == 'level_gain':
            self.levels.append(LevelRecord(*data))
        elif record_type == 'exp_gain':
            self.exp.append(LevelRecord(*data))

    def pop(self, record_type: str) -> Record:
        if record_type == 'kill':
            return self.kills.pop()
        elif record_type == 'damage':
            return self.damage.pop()
        elif record_type == 'heal':
            return self.healing.pop()
        elif record_type == 'death':
            return self.player_death.pop()
        elif record_type == 'item_use':
            return self.item_use.pop()
        elif record_type == 'steal':
            return self.steal.pop()
        elif record_type in ('hit', 'miss', 'crit'):
            return self.combat_results.pop()
        elif record_type == 'turn':
            return self.turn_taken.pop()
        elif record_type == 'level_gain':
            return self.levels.pop()
        elif record_type == 'exp_gain':
            return self.exp.pop()

    # Interogation functions
    def get_number_of_kills(self, unit_nid: str) -> int: 
        return len([record for record in self.kills if record.killer == unit_nid])
