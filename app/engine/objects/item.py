from app.utilities.data import Data

from app.data.database import DB

class ItemObject():
    next_uid = 100

    def __init__(self, nid, name, desc, icon_nid=None, icon_index=(0, 0), components=None):
        self.uid = ItemObject.next_uid
        ItemObject.next_uid += 1

        self.nid = nid
        self.name = name

        self.owner_nid = None
        self.desc = desc

        self.icon_nid = icon_nid
        self.icon_index = icon_index

        self.droppable = False

        self.components = components or Data()
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value

        self.data = {}

    @classmethod
    def from_prefab(cls, prefab):
        return cls(prefab.nid, prefab.name, prefab.desc, prefab.icon_nid, prefab.icon_index, prefab.components)

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        return None

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Item: %s %s" % (self.nid, self.uid)

    def save(self):
        serial_dict = {}
        serial_dict['uid'] = self.uid
        serial_dict['nid'] = self.nid
        serial_dict['owner_nid'] = self.owner_nid
        serial_dict['droppable'] = self.droppable
        serial_dict['data'] = self.data
        return serial_dict

    @classmethod
    def restore(cls, dat):
        self = cls.from_prefab(DB.items.get(dat['nid']))
        self.uid = dat['uid']
        self.owner_nid = dat['owner_nid']
        self.droppable = dat['droppable']
        self.data = dat['data']
        return self
