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
    ms = QDateTime.currentMSecsSinceEpoch()

    # Only process the ones that need to be updated
    for pos in tilemap.terrain_grid_to_update:
        terrain_nid = tilemap.get_terrain(pos)
        if not terrain_nid:
            continue
        terrain = DB_terrain.get(terrain_nid)
        determine_sprite(pos, terrain, tilemap)
    # Make sure we don't need to update it anymore
    tilemap.terrain_grid_to_update.clear()

    # Draw the tile grid
    for pos, tile_coord in tilemap.tile_grid.items():
        terrain_nid = tilemap.get_terrain((pos[0]//2, pos[1]//2))
        if not terrain_nid:
            continue
        terrain = DB_terrain.get(terrain_nid)
        pix = terrain.tileset_pixmap.copy(
            tile_coord[0] * TILEWIDTH//2,
            tile_coord[1] * TILEHEIGHT//2,
            TILEWIDTH//2, TILEHEIGHT//2)
        assert pix.width() == TILEWIDTH//2, pix.width()
        assert pix.height() == TILEHEIGHT//2, pix.height()
        painter.drawPixmap(pos[0] * TILEWIDTH//2,
                           pos[1] * TILEHEIGHT//2,
                           pix)

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
        new_coord = random.choice(new_coords)
        tilemap.tile_grid[pos] = new_coord

    # Calculate correct tile sprite
    if terrain.forest:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_pos = pos[0], pos[1] - 1
        east_pos = pos[0] + 1, pos[1]
        south_pos = pos[0], pos[1] + 1
        west_pos = pos[0] - 1, pos[1]
        total_index = \
            bool(north and (north != terrain.nid or north_pos in terrain.subforests)) + \
            2 * bool(east and (east != terrain.nid or east_pos in terrain.subforests)) + \
            4 * bool(south and (south != terrain.nid or south_pos in terrain.subforests)) + \
            8 * bool(west and (west != terrain.nid or west_pos in terrain.subforests))
        index1 = \
            bool(north and (north != terrain.nid or north_pos in terrain.subforests)) + \
            8 * bool(west and (west != terrain.nid or west_pos in terrain.subforests))
        index2 = \
            bool(north and (north != terrain.nid or north_pos in terrain.subforests)) + \
            2 * bool(east and (east != terrain.nid or east_pos in terrain.subforests))
        index3 = \
            4 * bool(south and (south != terrain.nid or south_pos in terrain.subforests)) + \
            2 * bool(east and (east != terrain.nid or east_pos in terrain.subforests))
        index4 = \
            4 * bool(south and (south != terrain.nid or south_pos in terrain.subforests)) + \
            8 * bool(west and (west != terrain.nid or west_pos in terrain.subforests))
        if total_index == 15 and random.choice([1, 2, 3]) != 3:
            new_coords1 = [(14, 0)]
            new_coords2 = [(15, 0)]
            new_coords3 = [(15, 1)]
            new_coords4 = [(14, 1)]
            terrain.subforests.add(pos)  # Mark that this forest does not count for adjacency
        elif total_index in (7, 11, 13, 14) and random.choice([1, 2]) == 2:
            new_coords1 = [(14, 0)]
            new_coords2 = [(15, 0)]
            new_coords3 = [(15, 1)]
            new_coords4 = [(14, 1)]
            terrain.subforests.add(pos)
        else:
            new_coords1 = [(index1, {0: 0, 1: 0, 8: 0, 9: 0}[index1])]
            new_coords2 = [(index2, {0: 1, 1: 1, 2: 0, 3: 0}[index2])]
            new_coords3 = [(index3, {0: 3, 2: 1, 4: 1, 6: 0}[index3])]
            new_coords4 = [(index4, {0: 2, 4: 0, 8: 1, 12: 0}[index4])]
            terrain.subforests.discard(pos)
    elif terrain.wang_edge2:
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
