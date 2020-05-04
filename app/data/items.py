try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import Data
import app.data.weapons as weapons
import app.data.item_components as IC

from app import utilities

class Item(object):
    next_uid = 100

    def __init__(self, nid, name, desc, min_range, max_range, value, icon_nid=None, icon_index=(0, 0), components=None):
        self.uid = Item.next_uid
        Item.next_uid += 1

        self.nid = nid
        self.name = name

        self.owner_nid = None
        self.desc = desc
        self.min_range = min_range
        self.max_range = max_range
        self.value = int(value)

        self.icon_nid = icon_nid
        self.icon_index = icon_index

        self.components = components or Data()
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value

        if self.droppable == self.locked == True:
            print("%s can't be both droppable and locked to a unit!" % self.nid)
            self.droppable = False

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
        serial_dict['volatiles'] = []
        for component in self.components.values():
            if component.volatile:
                serial_dict['volatiles'].append(component.serialize())
        return serial_dict

    @classmethod
    def deserialize(cls, s_dict, base_item):
        item = base_item
        item.uid = s_dict['uid']
        item.owner_nid = s_dict['owner_nid']
        item.droppable = s_dict['droppable']
        for serialized_component in s_dict['volatiles']:
            component = IC.deserialize(serialized_component)
            setattr(item, component.nid, component)
        return item

    def serialize_prefab(self):
        serial_dict = {'nid': self.nid,
                       'name': self.name,
                       'desc': self.desc,
                       'value': self.value,
                       'min_range': self.min_range,
                       'max_range': self.max_range,
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
                dat['min_range'], dat['max_range'],
                dat['value'], dat['icon_nid'], dat['icon_index'],
                item_components)
        return i

class ItemCatalog(Data):
    @staticmethod
    def parse_component(item, c):
        if c.attr == bool:
            c.value = True
        elif c.attr == int:
            c.value = int(item.find(c.nid).text)
        elif c.attr == weapons.WeaponRank:
            c.value = item.find(c.nid).text
        elif c.attr == weapons.WeaponType:
            c.value = item.find(c.nid).text
        return c

    def import_xml(self, xml_fn):
        item_data = ET.parse(xml_fn)
        for item in item_data.getroot().findall('item'):
            name = item.get('name')
            nid = item.find('id').text
            desc = item.find('desc').text
            range_ = item.find('range').text
            value = int(item.find('value').text)

            icon_nid = item.find('icon_fn').text
            icon_index = item.find('icon_id').text

            if '-' in range_:
                min_range, max_range = range_.split('-')
            else:
                min_range = max_range = range_

            if ',' in icon_index:
                icon_index = tuple(utilities.intify(icon_index))
            else:
                icon_index = (0, int(icon_index))

            components = item.find('components').text or ''
            components = components.split(',')
            my_components = Data()
            for c_nid in components:
                c = IC.get_component(c_nid)  # Needs to get copy
                if isinstance(c.attr, tuple):
                    pass
                else:
                    my_components.append(ItemCatalog.parse_component(item, c))

            new_item = \
                Item(nid, name, desc, min_range, max_range, value, 
                     icon_nid, icon_index, my_components)
            self.append(new_item)

    def get_instance(self, nid):
        item = self._dict.get(nid)
        if not item:
            return None
        new_item = Item(item.nid, item.name, item.desc, item.min_range, item.max_range,
                        item.value, item.icon_nid, item.icon_index, item.components)
        return new_item

    def save(self):
        return [i.serialize_prefab() for i in self._list]

    def restore(self, vals):
        self.clear()
        for val in vals:
            item = Item.deserialize_prefab(val)
            self.append(item)
