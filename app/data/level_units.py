from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass 
class GenericUnit(Prefab):
    nid: str = None
    variant: str = None

    level: int = None
    klass: str = None

    faction: str = None

    starting_items: list = None

    team: str = None
    ai: str = None

    starting_position: list = None  # 2-tuple

    name: str = None
    desc: str = None
    generic: bool = True

    def replace_item_nid(self, old_nid, new_nid):
        for item in self.starting_items:
            if item[0] == old_nid:
                item[0] = new_nid

    def restore_attr(self, name, value):
        if name == 'starting_items':
            # Need to convert to item nid + droppable
            value = [i if isinstance(i, list) else [i, False] for i in value]
        else:
            value = super().restore_attr(name, value)
        return value

    def get_items(self):
        return [i[0] for i in self.starting_items]

    @property
    def learned_skills(self):
        return []  # Generic units don't have personal skills

@dataclass
class UniqueUnit(Prefab):
    nid: str = None
    team: str = None
    ai: str = None

    starting_position: list = None  # 2-tuple

    generic: bool = False

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        elif self.nid:
            from app.data.database import DB
            prefab = DB.units.get(self.nid)
            return getattr(prefab, attr)
        return None

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['team'] = self.team
        s_dict['ai'] = self.ai
        s_dict['starting_position'] = self.starting_position
        s_dict['generic'] = self.generic
        return s_dict

@dataclass
class UnitGroup(Prefab):
    nid: str = None
    units: Data = None  # Actually unit, not unit nid
    positions: dict = None

    def save_attr(self, name, value):
        if name == 'units':
            value = [unit.nid for unit in value]
        else:
            value = super().save_attr(name, value)
        return value

    @classmethod
    def restore(cls, value, units):
        self = cls(value['nid'], [], value['positions'])
        units = [units.get(unit_nid) for unit_nid in value['units']]
        # Only include units that actually exist
        units = [u for u in units if u]
        self.units = Data(units)
        return self

    @classmethod
    def from_prefab(cls, prefab, units):
        self = cls(prefab.nid, [], prefab.positions)
        units = [units.get(unit.nid) for unit in prefab.units]
        # Only include units that actually exist
        units = [u for u in units if u]
        self.units = Data(units)
        return self
