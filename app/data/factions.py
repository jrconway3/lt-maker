try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import data

class Faction(object):
    def __init__(self, nid, name, desc, icon_fn=None, icon_index=(0, 0)):
        self.nid = nid
        self.name = name
        self.desc = desc
        self.icon_fn = icon_fn
        self.icon_index = icon_index

class FactionData(data):
    def import_xml(self, xml_fn):
        faction_data = ET.parse(xml_fn)
        for faction in faction_data.getroot().findall('faction'):
            name = faction.get('name')
            nid = faction.find('id').text
            icon = faction.find('icon').text
            desc = faction.find('desc').text
            new_faction = Faction(nid, name, desc, 'sprites/faction_icons/%sEmblem.png' % icon)
            self.append(new_faction)
