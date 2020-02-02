try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from dataclasses import dataclass

from app.data.data import data, Prefab

@dataclass
class Terrain(Prefab):
    nid: str = None
    name: str = None

    color: tuple = (0, 0, 0)
    minimap: str = None
    platform: str = None

    mtype: str = None

class TerrainCatalog(data):
    def import_xml(self, xml_fn):
        terrain_data = ET.parse(xml_fn)
        for terrain in terrain_data.getroot().findall('terrain'):
            name = terrain.get('name')
            nid = terrain.find('id').text
            color = tuple([int(_) for _ in terrain.find('color').text.split(',')])
            minimap = terrain.find('minimap').text
            platform = terrain.find('platform').text
            mtype = terrain.find('mtype').text
            new_terrain = Terrain(nid, name, color, minimap, platform, mtype)
            self.append(new_terrain)
