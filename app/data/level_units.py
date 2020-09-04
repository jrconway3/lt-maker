from dataclasses import dataclass

from app.utilities.data import Prefab

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
