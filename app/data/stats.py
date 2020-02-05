
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from dataclasses import dataclass

from app.data.data import data, Prefab
from app import utilities

@dataclass
class StatTypePrefab(Prefab):
    nid: str = None
    name: str = None
    maximum: int = 30
    desc: str = ""

    def __repr__(self):
        return "%s: %s" % (self.nid, self.name)

class StatCatalog(data):
    datatype = StatTypePrefab

    def import_xml(self, xml_fn):
        stat_data = ET.parse(xml_fn)
        for stat in stat_data.getroot().findall('stat'):
            name = stat.get('name')
            nid = stat.find('id').text
            maximum = int(stat.find('maximum').text)
            desc = stat.find('desc').text
            new_stat = StatTypePrefab(nid, name, maximum, desc)
            self.append(new_stat)

    def add_new_default(self, db):
        new_row_nid = utilities.get_next_name('STAT', self.keys())
        new_stat = StatTypePrefab(new_row_nid, "New Stat", 30, "")
        self.append(new_stat)
        return new_stat

@dataclass
class Stat(Prefab):
    nid: str = None
    value: int = 10

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
