from app.data.data import Data
import app.data.item_component as IC

class Item(object):
    next_uid = 100

    def __init__(self, nid, name, desc, icon_nid=None, icon_index=(0, 0), components=None):
        self.uid = Item.next_uid
        Item.next_uid += 1

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

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        return None

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __getitem__(self, key):
        return self.__dict__.get(key)

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Item: %s %s" % (self.nid, self.uid)

    def serialize(self):
        serial_dict = {}
        serial_dict['uid'] = self.uid
        serial_dict['nid'] = self.nid
        serial_dict['owner_nid'] = self.owner_nid
        serial_dict['droppable'] = self.droppable
        serial_dict['data'] = self.data
        return serial_dict

    @classmethod
    def deserialize(cls, s_dict, base_item):
        item = base_item
        item.uid = s_dict['uid']
        item.owner_nid = s_dict['owner_nid']
        item.droppable = s_dict['droppable']
        item.data = s_dict['data']
        return item

    def serialize_prefab(self):
        serial_dict = {'nid': self.nid,
                       'name': self.name,
                       'desc': self.desc,
                       'icon_nid': self.icon_nid,
                       'icon_index': self.icon_index,
                       'components': [c.serialize() for c in self.components]
                       }
        return serial_dict

    @classmethod
    def deserialize_prefab(cls, dat):
        item_components = Data()
        components = [IC.deserialize_component(val) for val in dat['components']]
        for component in components:
            item_components.append(component)
        i = cls(dat['nid'], dat['name'], dat['desc'],
                dat['icon_nid'], dat['icon_index'],
                item_components)
        return i

class ItemCatalog(Data):
    def get_instance(self, nid):
        item = self._dict.get(nid)
        if not item:
            return None
        new_item = Item(item.nid, item.name, item.desc,
                        item.icon_nid, item.icon_index, item.components)
        return new_item

    def save(self):
        return [i.serialize_prefab() for i in self._list]

    def restore(self, vals):
        self.clear()
        for val in vals:
            item = Item.deserialize_prefab(val)
            self.append(item)
