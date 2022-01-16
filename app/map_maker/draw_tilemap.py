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
    for pos, terrain_nid in tilemap.terrain_grid.items():
        terrain = DB_terrain.get(terrain_nid)
        tile_coord1, tile_coord2, tile_coord3, tile_coord4 = determine_sprite(pos, terrain, tilemap)
        pix1 = terrain.tileset_pixmap.copy(
            tile_coord1[0] * TILEWIDTH//2, 
            tile_coord1[1] * TILEHEIGHT//2,
            TILEWIDTH//2, TILEHEIGHT//2)
        pix2 = terrain.tileset_pixmap.copy(
            tile_coord2[0] * TILEWIDTH//2, 
            tile_coord2[1] * TILEHEIGHT//2,
            TILEWIDTH//2, TILEHEIGHT//2)
        pix3 = terrain.tileset_pixmap.copy(
            tile_coord3[0] * TILEWIDTH//2, 
            tile_coord3[1] * TILEHEIGHT//2,
            TILEWIDTH//2, TILEHEIGHT//2)
        pix4 = terrain.tileset_pixmap.copy(
            tile_coord4[0] * TILEWIDTH//2, 
            tile_coord4[1] * TILEHEIGHT//2,
            TILEWIDTH//2, TILEHEIGHT//2)

        if pix1:
            painter.drawImage(pos[0] * TILEWIDTH,
                              pos[1] * TILEHEIGHT,
                              pix1.toImage())
        if pix2:
            painter.drawImage(pos[0] * TILEWIDTH + TILEWIDTH//2,
                              pos[1] * TILEHEIGHT,
                              pix2.toImage())
        if pix3:
            painter.drawImage(pos[0] * TILEWIDTH + TILEWIDTH//2,
                              pos[1] * TILEHEIGHT + TILEHEIGHT//2,
                              pix3.toImage())
        if pix4:
            painter.drawImage(pos[0] * TILEWIDTH,
                              pos[1] * TILEHEIGHT + TILEHEIGHT//2,
                              pix4.toImage())
    painter.end()
    return image

def determine_sprite(pos: tuple, terrain, tilemap) -> tuple:
    """
    pos is in terrain space (16x16)
    """
    def _push_to_tilemap(pos: tuple, new_coords: tuple):
        """
        pos is in tile space (8x8)
        """
        if tilemap.tile_grid.get(pos) in new_coords:
            pass
        else:
            new_coord = random.choice(new_coords)
            tilemap.tile_grid[pos] = new_coord

    # Calculate correct tile sprite
    if terrain.wang_edge2:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        index1 = \
            bool(north and north != terrain.nid) + \
            8 * bool(west and west != terrain.nid)
        index2 = \
            bool(north and north != terrain.nid) + \
            2 * bool(east and east != terrain.nid)
        index3 = \
            4 * bool(south and south != terrain.nid) + \
            2 * bool(east and east != terrain.nid)
        index4 = \
            4 * bool(south and south != terrain.nid) + \
            8 * bool(west and west != terrain.nid)
        new_coords1 = [(index1, k) for k in range(terrain.wang_edge2_limits[index1])]
        new_coords2 = [(index2, k) for k in range(terrain.wang_edge2_limits[index2])]
        new_coords3 = [(index3, k) for k in range(terrain.wang_edge2_limits[index3])]
        new_coords4 = [(index4, k) for k in range(terrain.wang_edge2_limits[index4])]
    elif terrain.regular:
        new_coords1 = [(p[0]*2, p[1]*2) for p in terrain.regular]
        new_coords2 = [(p[0]*2 + 1, p[1]*2) for p in terrain.regular]
        new_coords3 = [(p[0]*2 + 1, p[1]*2 + 1) for p in terrain.regular]
        new_coords4 = [(p[0]*2, p[1]*2 + 1) for p in terrain.regular]
    else:
        new_coords1 = [(terrain.display_tile_coord[0]*2, terrain.display_tile_coord[1]*2)]
        new_coords2 = [(terrain.display_tile_coord[0]*2 + 1, terrain.display_tile_coord[1]*2)]
        new_coords3 = [(terrain.display_tile_coord[0]*2 + 1, terrain.display_tile_coord[1]*2 + 1)]
        new_coords4 = [(terrain.display_tile_coord[0]*2, terrain.display_tile_coord[1]*2 + 1)]

    _push_to_tilemap((pos[0] * 2, pos[1] * 2), new_coords1)
    _push_to_tilemap((pos[0] * 2 + 1, pos[1] * 2), new_coords2)
    _push_to_tilemap((pos[0] * 2 + 1, pos[1] * 2 + 1), new_coords3)
    _push_to_tilemap((pos[0] * 2, pos[1] * 2 + 1), new_coords4)

    return (
        tilemap.tile_grid[(pos[0] * 2, pos[1] * 2)], 
        tilemap.tile_grid[(pos[0] * 2 + 1, pos[1] * 2)],
        tilemap.tile_grid[(pos[0] * 2 + 1, pos[1] * 2 + 1)],
        tilemap.tile_grid[(pos[0] * 2, pos[1] * 2 + 1)]
    )
