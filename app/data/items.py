try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import data
import app.data.weapons as weapons
import app.data.item_components as IC

from app import utilities

class Item(object):
    next_uid = 100

    def __init__(self, nid, name, desc, min_range, max_range, value, icon_fn=None, icon_index=(0, 0), components=None):
        self.uid = Item.next_uid
        Item.next_uid += 1

        self.nid = nid
        self.name = name

        self.owner_nid = None
        self.desc = desc
        self.min_range = min_range
        self.max_range = max_range
        self.value = int(value)

        self.icon_fn = icon_fn
        self.icon_index = icon_index

        self.components = components or {}
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
        return "Item: %s" % self.nid

class ItemCatalog(data):
    @staticmethod
    def parse_component(item, c):
        if isinstance(c.attr, bool):
            c.value = True
        elif isinstance(c.attr, int):
            c.value = int(item.find(c.nid).text)
        elif isinstance(c.attr, weapons.WeaponRank):
            c.value = weapons.RankData.get(item.find(c.nid).text)
        elif isinstance(c.attr, weapons.WeaponType):
            c.value = weapons.WeaponData.get(item.find(c.nid).text)
        return c

    def import_xml(self, xml_fn):
        item_data = ET.parse(xml_fn)
        for item in item_data.getroot().findall('item'):
            name = item.get('name')
            nid = item.find('id').text
            desc = item.find('desc').text
            range_ = item.find('range').text
            value = int(item.find('value').text)

            icon_fn = item.find('icon_fn').text
            icon_index = item.find('icon_index').text

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
            my_components = {}
            for component in components:
                c = IC.get_component(component)  # Needs to get copy
                if isinstance(c.attr, tuple):
                    pass
                else:
                    my_components[c.nid] = ItemCatalog.parse_component(item, c)

            new_item = \
                Item(nid, name, desc, min_range, max_range, value, 
                     'sprites/item_icons/%s.png' % icon_fn, icon_index,
                     my_components)
            self.append(new_item)
