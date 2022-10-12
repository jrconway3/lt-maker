from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QImage, QPainter, QPixmap, QColor

from app.constants import TILEWIDTH, TILEHEIGHT

from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain_database import DB_terrain
from app.map_maker.utilities import random_choice

def get_tilemap_pixmap(tilemap) -> QPixmap:
    return QPixmap.fromImage(draw_tilemap(tilemap))

def draw_tilemap(tilemap: MapPrefab, autotile_fps=29) -> QImage:
    image = QImage(tilemap.width * TILEWIDTH,
                   tilemap.height * TILEHEIGHT,
                   QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter()
    painter.begin(image)
    ms = QDateTime.currentMSecsSinceEpoch()

    # Process terrain
    processed_nids = set()
    for pos in sorted(tilemap.terrain_grid):
        # Determine what terrain is in this position
        terrain_nid = tilemap.get_terrain(pos)
        if not terrain_nid:
            continue
        terrain = DB_terrain.get(terrain_nid)
        
        # Only process the ones that need to be updated
        if pos in tilemap.terrain_grid_to_update or terrain.has_autotiles:
            if terrain_nid not in processed_nids:
                terrain.single_process(tilemap)
                processed_nids.add(terrain_nid)
            sprite = terrain.determine_sprite(tilemap, pos, ms, autotile_fps)
            terrain.tile_grid[pos] = sprite

    # Draw the tile grid
    for pos, pix in tilemap.tile_grid.items():
        assert pix.width() == TILEWIDTH, pix.width()
        assert pix.height() == TILEHEIGHT, pix.height()
        painter.drawPixmap(pos[0] * TILEWIDTH,
                           pos[1] * TILEHEIGHT,
                           pix)
    painter.end()

    # Make sure we don't need to update it anymore
    tilemap.terrain_grid_to_update.clear()

    return image
