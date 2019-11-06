
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from collections import OrderedDict

from app.data.data import data
from app import utilities

class StatType(object):
    def __init__(self, nid, name, maximum, desc):
        self.nid = nid
        self.name = name
        self.maximum = maximum
        self.desc = desc

    def __repr__(self):
        return "%s: %s" % (self.nid, self.name)

class StatList(OrderedDict):
    def __init__(self, data, stat_types):
        for i in range(len(stat_types)):
            key = stat_types[i].nid
            if i < len(data):
                self[key] = data[i]
            else:
                self[key] = 0

    def fix(self, stat_types):
        """
        Given a new set of stat types, change current stat types to match
        Delete old keys and add new keys
        """
        current_stat_types = set(self.keys())
        st = set(stat_types)
        to_remove = current_stat_types - st
        to_add = st - current_stat_types
        # Actually make the change
        for remove_me in to_remove:
            del self[remove_me]
        for add_me in to_add:
            self[add_me] = 0

    def remove_key(self, key):
        del self[key]

    def change_key(self, old_key, new_key):
        old_value = self[old_key]
        del self[old_key]
        self[new_key] = old_value

class StatCatalog(data):
    def import_xml(self, xml_fn):
        stat_data = ET.parse(xml_fn)
        for stat in stat_data.getroot().findall('stat'):
            name = stat.get('name')
            nid = stat.find('id').text
            maximum = int(stat.find('maximum').text)
            desc = stat.find('desc').text
            new_stat = StatType(nid, name, maximum, desc)
            self.append(new_stat)

    def add_new_default(self, db):
        new_row_nid = utilities.get_next_name('STAT', self.keys())
        new_stat = StatType(new_row_nid, "New Stat", 30, "")
        self.append(new_stat)
        return new_stat
