try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import data

class StatType(object):
    def __init__(self, nid, name, maximum, desc):
        self.nid = nid
        self.name = name
        self.maximum = maximum
        self.desc = desc

class StatData(data):
    def import_xml(self, xml_fn):
        stat_data = ET.parse(xml_fn)
        for stat in stat_data.getroot().findall('stat'):
            name = stat.get('name')
            nid = stat.find('id').text
            maximum = int(stat.find('maximum').text)
            desc = stat.find('desc').text
            new_stat = StatType(nid, name, maximum, desc)
            self.append(new_stat)
