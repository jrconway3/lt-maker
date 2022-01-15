from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass
class Terrain(Prefab):
    nid: str = None
    name: str = None
    tileset_path: str = None

    display_tile_coord: tuple = (0, 0)

    display_pixmap = None
    tileset_pixmap = None

    def restore_attr(self, name, value):
        if name in ('color', 'tile_coord', 'display_tile_coord'):
            value = tuple(value)
        else:
            value = super().restore_attr(name, value)
        return value

class TerrainCatalog(Data[Terrain]):
    datatype = Terrain

tileset = 'app/map_maker/rainlash_fields1.png'

d = [
    Terrain('Plains', 'Plains', tileset, (2, 2)),
    Terrain('Road', 'Road', tileset, (20, 22)),
    Terrain('Forest', 'Forest', tileset, (16, 22)),
    Terrain('Thicket', 'Thicket', tileset, (17, 22)),
]

DB_terrain = TerrainCatalog(d)
