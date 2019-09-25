try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import data

class Item(object):
    next_uid = 100

    def __init__(self, nid, name, desc, range_, value, icon_fn=None, icon_index=(0, 0), components=None):
        self.uid = Item.next_uid
        Item.next_uid += 1

        self.nid = nid
        self.name = name

        self.owner_nid = None
        self.desc = desc
        self.range = self.parse_range_str(range_)
        self.value = int(value)

        self.icon_fn = icon_fn
        self.icon_index = icon_index

        self.components = components or {}
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value

        if self.droppable == self.locked == True:
            print("%s can't be both droppable and locked to a unit!" % self.nid)
            self.droppable = False

    # TODO
    def parse_range_str(self, range_):
        return range_

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

class ItemData(data):
    def import_xml(self, xml_fn):
        item_data = ET.parse(xml_fn)