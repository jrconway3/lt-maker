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
