import random

from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QImage, QPainter, QPixmap, QColor

from app.constants import TILEWIDTH, TILEHEIGHT

from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain_database import DB_terrain

import logging

def get_tilemap_pixmap(tilemap) -> QPixmap:
    return QPixmap.fromImage(draw_tilemap(tilemap))

def draw_tilemap(tilemap: MapPrefab, autotile_fps=29) -> QImage:
    image = QImage(tilemap.width * TILEWIDTH,
                   tilemap.height * TILEHEIGHT,
                   QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter()
    painter.begin(image)
    painter.setOpacity(1.0)
    ms = QDateTime.currentMSecsSinceEpoch()
    for coord, terrain_nid in tilemap.terrain_grid.items():
        terrain = DB_terrain.get(terrain_nid)
        terrain_coord = determine_sprite(coord, terrain, tilemap.terrain_grid, tilemap.tile_grid)
        pix = terrain.tileset_pixmap.copy(
            terrain_coord[0] * TILEWIDTH, 
            terrain_coord[1] * TILEHEIGHT,
            TILEWIDTH, TILEHEIGHT)

        if pix:
            painter.drawImage(coord[0] * TILEWIDTH,
                              coord[1] * TILEHEIGHT,
                              pix.toImage())
    painter.end()
    return image

def determine_sprite(pos, terrain, terrain_grid, tile_grid):
    if terrain.regular:
        new_coords = terrain.regular
    else:
        new_coords = [terrain.display_tile_coord]
    if tile_grid.get(pos) in new_coords:
        pass
    else:
        new_coord = random.choice(new_coords)
        tile_grid[pos] = new_coord
    return tile_grid[pos]
