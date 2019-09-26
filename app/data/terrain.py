try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import data

class Terrain(object):
    def __init__(self, nid, name, color, minimap, platform, mtype):
        self.nid = nid
        self.name = name

        self.color = color
        self.minimap = minimap
        self.platform = platform

        self.mtype = mtype

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
