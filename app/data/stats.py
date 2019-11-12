
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

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

class Stat(object):
    def __init__(self, nid, val):
        self.nid = nid
        self.value = val

    def __str__(self):
        return str(self.value)

class StatList(data):
    def __init__(self, data, stat_types):
        vals = []
        for i in range(len(stat_types)):
            if i < len(data):
                vals.append(Stat(stat_types[i].nid, data[i]))
            else:
                vals.append(Stat(stat_types[i].nid, 0))
        super().__init__(vals)

    def new_key(self, key):
        self[key] = 0
