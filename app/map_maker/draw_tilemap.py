from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QImage, QPainter, QPixmap, QColor

from app.constants import TILEWIDTH, TILEHEIGHT

from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain_database import DB_terrain

import logging

def get_tilemap_pixmap(tilemap) -> QPixmap:
    return QPixmap.fromImage(draw_tilemap(tilemap))

def draw_tilemap(tilemap: MapPrefab) -> QImage:
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
        if not terrain.tileset_pixmap:
            terrain.tileset_pixmap = QPixmap(terrain.tileset_path)
        tileset = terrain.tileset_pixmap
        sprite_coord = terrain.display_tile_coord
        pix = tileset.copy(*sprite_coord, 16, 16)

        if pix:
            painter.drawImage(coord[0] * TILEWIDTH,
                              coord[1] * TILEHEIGHT,
                              pix.toImage())
    painter.end()
    return image
