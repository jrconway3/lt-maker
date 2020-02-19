try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from dataclasses import dataclass

from app.data.data import Data, Prefab

@dataclass
class Faction(Prefab):
    nid: str = None
    name: str = None
    desc: str = ""

    icon_nid: str = None
    icon_index: tuple = (0, 0)

class FactionCatalog(Data):
    datatype = Faction

    def import_xml(self, xml_fn):
        faction_data = ET.parse(xml_fn)
        for faction in faction_data.getroot().findall('faction'):
            name = faction.get('name')
            nid = faction.find('id').text
            icon = faction.find('icon').text
            desc = faction.find('desc').text
            new_faction = Faction(nid, name, desc, '%sEmblem' % icon)
            self.append(new_faction)
