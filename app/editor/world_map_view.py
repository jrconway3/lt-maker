from enum import Enum
import logging
from typing import List
from app.utilities.enums import Direction
from app.utilities.utils import dot_product, tmult, tuple_add, tuple_sub
import app.editor.utilities as editor_utilities
from app.constants import TILEHEIGHT, TILEWIDTH
from app.data.database import DB
from app.data.overworld import OverworldPrefab
from app.editor.map_view import SimpleMapView
from app.editor.tile_editor import tile_model
from app.resources.resources import RESOURCES
from app.sprites import SPRITES
from app.utilities.typing import Point
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QImage, QTransform

class RoadSpriteWrapper():
    """Not a real class, just factoring out some sprite-specific logic.
    If you don't have `overworld_routes.png` open as you're reading this code,
    it will make 0 sense.
    """
    SPRITE_DIMENSIONS = (8, 8)
    # the real spritesheet (see overworld_routes.png) includes sea routes
    # for a total of 120x8 pixels, but i'm not doing the dotted-line sea routes
    # since those seem like a pain, so I'm leaving them as a future todo
    SPRITESHEET_DIMENSIONS = (64, 8)

    def __init__(self):
        road_sprite = SPRITES['overworld_routes']
        self.sprite_dict = {}
        if road_sprite:
            if not road_sprite.pixmap:
                road_sprite.pixmap = QPixmap(road_sprite.full_path)
        self.road_sprite = road_sprite
        if self.road_sprite:
            self.subsprites: List[QImage] = []
            for x in range(0, self.SPRITESHEET_DIMENSIONS[0], self.SPRITE_DIMENSIONS[0]):
                self.subsprites.append(road_sprite.pixmap.toImage().copy(x, 0, 8, 8))
            self.htop = self.subsprites[1]
            self.hbot = self.subsprites[2]
            self.vleft = self.subsprites[3]
            self.vright = self.subsprites[4]
            self.right_angle = self.subsprites[5]
            self.diag_main = self.subsprites[6]
            self.diag_corner = self.subsprites[7]

    def has_image(self) -> bool:
        return self.road_sprite is not None

    @classmethod
    def road_to_full_points_list(cls, road: List[Point]) -> List[Point]:
        """'unpacks' a road into constituent points (e.g. [(0, 0), (3, 3)] => [(0, 0), (1, 1), (2, 2), (3, 3)]).
        This requires that the road is a "locked" road, i.e. it only contains 45 and 90 degree angles.

        Args:
            road (List[Point]): initial road

        Returns:
            List[Point]: unpacked points
        """
        unpacked: List[Point] = []
        prev_point = road[0]
        for point in road:
            if point == prev_point:
                continue
            diff = tuple_sub(point, prev_point)
            length = max(abs(diff[0]), abs(diff[1]))
            inc = tmult(diff, 1 / length)
            inc = (int(inc[0]), int(inc[1]))
            start = prev_point
            while start != tuple(point):
                unpacked.append(start)
                start = tuple_add(start, inc)
            prev_point = point
        unpacked.append(road[-1])
        return unpacked

    def _draw_straight(self, painter: QPainter, tile_pos: Point, direction: Direction):
        left, top = tile_pos[0] * TILEWIDTH, tile_pos[1] * TILEHEIGHT
        off_x, off_y = TILEWIDTH / 2, TILEHEIGHT / 2
        # quadrants oriented like cartesian plane
        q1 = (left + off_x, top)
        q2 = (left, top)
        q3 = (left, top + off_y)
        q4 = (left + off_x, top + off_y)

        if direction == Direction.UP:
            painter.drawImage(*q2, self.vleft)
            painter.drawImage(*q1, self.vright)
        elif direction == Direction.DOWN:
            painter.drawImage(*q3, self.vleft)
            painter.drawImage(*q4, self.vright)
        elif direction == Direction.LEFT:
            painter.drawImage(*q2, self.htop)
            painter.drawImage(*q3, self.hbot)
        elif direction == Direction.RIGHT:
            painter.drawImage(*q1, self.htop)
            painter.drawImage(*q4, self.hbot)

    def _draw_diagonal(self, painter: QPainter, tile_pos: Point, direction: Direction, is_vertical_right_angle: bool=False):
        # shorthand
        left, top = tile_pos[0] * TILEWIDTH, tile_pos[1] * TILEHEIGHT
        off_x, off_y = TILEWIDTH / 2, TILEHEIGHT / 2
        # quadrants oriented like cartesian plane
        q1 = (left + off_x, top)
        q2 = (left, top)
        q3 = (left, top + off_y)
        q4 = (left + off_x, top + off_y)

        quadrant = q1
        if direction == Direction.UP_LEFT:
            quadrant = q2
            sprite = self.diag_main
        elif direction == Direction.UP_RIGHT:
            quadrant = q1
            sprite = self.diag_main.transformed(QTransform().rotate(90))
        elif direction == Direction.DOWN_LEFT:
            quadrant = q3
            sprite = self.diag_main.transformed(QTransform().rotate(90))
        elif direction == Direction.DOWN_RIGHT:
            quadrant = q4
            sprite = self.diag_main

        painter.drawImage(*quadrant, sprite)
        x, y = quadrant
        if is_vertical_right_angle:
            if quadrant == q1:
                painter.drawImage(x, y - off_y, self.diag_corner.transformed(QTransform().rotate(270)))
                painter.drawImage(x - off_x, y, self.diag_corner.transformed(QTransform().rotate(270)))
            elif quadrant == q2:
                painter.drawImage(x, y - off_y, self.diag_corner.transformed(QTransform().rotate(0)))
                painter.drawImage(x + off_x, y, self.diag_corner.transformed(QTransform().rotate(0)))
            elif quadrant == q3:
                painter.drawImage(x, y + off_y, self.diag_corner.transformed(QTransform().rotate(90)))
                painter.drawImage(x + off_x, y, self.diag_corner.transformed(QTransform().rotate(90)))
            elif quadrant == q4:
                painter.drawImage(x, y + off_y, self.diag_corner.transformed(QTransform().rotate(180)))
                painter.drawImage(x - off_x, y, self.diag_corner.transformed(QTransform().rotate(180)))
        else:
            if quadrant in [q1, q3]:
                painter.drawImage(x, y - off_y, self.diag_corner.transformed(QTransform().rotate(270)))
                painter.drawImage(x, y + off_y, self.diag_corner.transformed(QTransform().rotate(90)))
            else:
                painter.drawImage(x, y - off_y, self.diag_corner.transformed(QTransform().rotate(0)))
                painter.drawImage(x, y + off_y, self.diag_corner.transformed(QTransform().rotate(180)))

    def _draw_turn(self, painter: QPainter, tile_pos: Point, directions: List[Direction]):
        # shorthand
        left, top = tile_pos[0] * TILEWIDTH, tile_pos[1] * TILEHEIGHT
        off_x, off_y = TILEWIDTH / 2, TILEHEIGHT / 2
        # quadrants oriented like cartesian plane
        q1 = (left + off_x, top)
        q2 = (left, top)
        q3 = (left, top + off_y)
        q4 = (left + off_x, top + off_y)

        if Direction.UP in directions:
            if Direction.LEFT in directions: # up left
                painter.drawImage(*q2, self.right_angle.transformed(QTransform().rotate(90)))
                painter.drawImage(*q3, self.hbot)
                painter.drawImage(*q1, self.vright)
            else: # up right
                painter.drawImage(*q1, self.right_angle.transformed(QTransform().rotate(180)))
                painter.drawImage(*q2, self.vleft)
                painter.drawImage(*q4, self.hbot)
        else:
            if Direction.LEFT in directions: # down left
                painter.drawImage(*q3, self.right_angle)
                painter.drawImage(*q2, self.htop)
                painter.drawImage(*q4, self.vright)
            else: # down right
                painter.drawImage(*q4, self.right_angle.transformed(QTransform().rotate(270)))
                painter.drawImage(*q1, self.htop)
                painter.drawImage(*q3, self.vleft)

    def draw_tile(self, painter: QPainter, tile_pos: Point, neighbor_points: List[Point]):
        """I apologize to anyone who has to read this code."""
        """Note: `neighbor_points` can be very far away, they are just used to establish angle"""
        if not self.has_image():
            logging.error("Road Sprite not found!")
            return
        # quadrants oriented like cartesian plane
        is_diagonal_vertical_right_angle = False

        # first, if we're at right angles, use special logic
        if len(neighbor_points) == 2:
            vec_a = tuple_sub(neighbor_points[0], tile_pos)
            vec_b = tuple_sub(neighbor_points[1], tile_pos)
            is_perpendicular = dot_product(vec_a, vec_b) == 0
            if is_perpendicular and (0 in vec_a or 0 in vec_b): # right angle, draw corner
                direcs = [Direction.parse_map_direction(v[0], v[1]) for v in [vec_a, vec_b]]
                print(direcs)
                self._draw_turn(painter, tile_pos, direcs)
                return
            elif is_perpendicular and not (0 in vec_a or 0 in vec_b): # right angle but diagonal
                if Direction.which_vertical_dir(Direction.parse_map_direction(*vec_a)) != Direction.which_vertical_dir(Direction.parse_map_direction(*vec_b)):
                    is_diagonal_vertical_right_angle = True

        for point in neighbor_points:
            direc = Direction.parse_map_direction(*tuple_sub(point, tile_pos))
            if direc in [Direction.UP, Direction.DOWN, Direction.RIGHT, Direction.LEFT]:
                self._draw_straight(painter, tile_pos, direc)
            else: # diagonal
                self._draw_diagonal(painter, tile_pos, direc, is_diagonal_vertical_right_angle)

class WorldMapView(SimpleMapView):
    def __init__(self):
        super().__init__()
        self.selected = None
        self.possible_road_endpoint: Point = None
        self.road_sprite = RoadSpriteWrapper()

    def set_current_level(self, overworld_nid):
        overworld = DB.overworlds.get(overworld_nid)
        if isinstance(overworld, OverworldPrefab):
            self.current_level = overworld
            self.current_map = RESOURCES.tilemaps.get(overworld.tilemap)
            self.update_view()

    def set_selected(self, sel):
        self.selected = sel
        self.update_view()

    def set_ghost_road_endpoint(self, ghost):
        self.possible_road_endpoint = ghost
        self.update_view()

    def update_view(self, _=None):
        if(self.current_level and not self.current_map):
            self.current_map = RESOURCES.tilemaps.get(
                self.current_level.tilemap)
        if self.current_map:
            pixmap = tile_model.create_tilemap_pixmap(self.current_map)
            self.working_image = pixmap
        else:
            self.clear_scene()
            return
        self.paint_roads(self.current_level)
        self.paint_nodes(self.current_level)
        self.paint_selected()
        self.paint_border(self.current_level)
        self.show_map()

    def paint_border(self, current_level: OverworldPrefab):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            pixel_border_width = TILEWIDTH * current_level.border_tile_width
            # draw top and left borders
            painter.fillRect(0, 0, self.working_image.width(), pixel_border_width, QColor(160, 0, 0, 128))
            painter.fillRect(0, 0, pixel_border_width, self.working_image.height(), QColor(160, 0, 0, 128))
            # draw bottom and right borders
            painter.fillRect(0, self.working_image.height() - pixel_border_width, self.working_image.width(), pixel_border_width, QColor(160, 0, 0, 128))
            painter.fillRect(self.working_image.width() - pixel_border_width, 0, pixel_border_width, self.working_image.height(), QColor(160, 0, 0, 128))
            painter.end()

    def draw_node(self, painter, node, position, opacity=False):
        icon_nid = node.icon
        icon = RESOURCES.map_icons.get(icon_nid)
        coord = position
        pixmap = icon.get_pixmap()
        pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
        # to support 16x16, 32x32, and 48x48 map icons, we offset them differently
        offset_x = (pixmap.width() / 16 - 1) * 8
        offset_y = (pixmap.height() - 16)
        if pixmap:
            if opacity:
                painter.setOpacity(0.33)
            painter.drawImage(coord[0] * TILEWIDTH - offset_x,
                              coord[1] * TILEHEIGHT - offset_y, pixmap.toImage())
            painter.setOpacity(1.0)
        else:
            pass

    def draw_road_segment(self, painter, start_position, end_position, selected=False, transparent=False):
        start_x = start_position[0] * TILEWIDTH + TILEWIDTH / 2
        start_y = start_position[1] * TILEHEIGHT + TILEHEIGHT / 2
        end_x = end_position[0] * TILEWIDTH + TILEWIDTH / 2
        end_y = end_position[1] * TILEHEIGHT + TILEHEIGHT / 2

        # if this is our current working line, draw an accent to let the user know
        if selected:
            pen = QPen(Qt.yellow, 3, style=Qt.SolidLine)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(pen)
            painter.drawLine(start_x, start_y, end_x, end_y)

        # draw the road segment
        if transparent:
            pen = QPen(QColor(256, 0, 256, 80), 3, style=Qt.SolidLine)
        else:
            pen = QPen(QColor(232, 216, 136, 160), 3, style=Qt.SolidLine)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        painter.drawLine(start_x, start_y, end_x, end_y)
        pen = QPen(QColor(248, 248, 200), 2, style=Qt.DotLine)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        painter.drawLine(start_x, start_y, end_x, end_y)

    def paint_nodes(self, current_level):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for node in current_level.overworld_nodes:
                if not node.pos:
                    continue
                self.draw_node(painter, node, node.pos)
            painter.end()

    def paint_roads(self, current_level):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for path in current_level.map_paths.values():
                unpacked_path = RoadSpriteWrapper.road_to_full_points_list(path)
                for i in range(len(unpacked_path)):
                    neighbors = []
                    if i != 0:
                        neighbors.append(unpacked_path[i - 1])
                    if i < len(unpacked_path) - 1:
                        neighbors.append(unpacked_path[i + 1])
                    self.road_sprite.draw_tile(painter, unpacked_path[i], neighbors)
            painter.end()

    def paint_ghost_road(self, selected):
        if isinstance(selected, list):
            last_road_point = selected[-1]
        elif isinstance(selected, tuple):
            last_road_point = selected
        else:
            return

        painter = QPainter()
        painter.begin(self.working_image)
        if last_road_point and self.possible_road_endpoint:
            self.draw_road_segment(painter, last_road_point, self.possible_road_endpoint, transparent=True)
        painter.end()

    def paint_selected(self):
        """Draws some sort of accent around the selected object (road, node).
           For the road, draws highlights.
           For the node, draws a cursor around it.
        """
        if self.working_image:
            if isinstance(self.selected, list):
                # this is a road
                self.paint_selected_road(self.selected)
                self.paint_ghost_road(self.selected)
            elif isinstance(self.selected, tuple):
                # this is a selected coord of a node
                self.paint_cursor(self.selected)
                self.paint_ghost_road(self.selected)
            else:
                # ??? None type, or something went wrong. Don't draw
                return

    def paint_selected_road(self, path):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for i in range(len(path) - 1):
                self.draw_road_segment(painter, path[i], path[i+1], True)
            painter.end()

    def paint_cursor(self, coord):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            coord = coord
            cursor_sprite = SPRITES['cursor']
            if cursor_sprite:
                if not cursor_sprite.pixmap:
                    cursor_sprite.pixmap = QPixmap(cursor_sprite.full_path)
                cursor_image = cursor_sprite.pixmap.toImage().copy(0, 64, 32, 32)
                painter.drawImage(
                    coord[0] * TILEWIDTH - 8, coord[1] * TILEHEIGHT - 5, cursor_image)
            painter.end()

    def show_map(self):
        if self.working_image:
            self.clear_scene()
            self.scene.addPixmap(self.working_image)

    # these two are in the superclass but are useless in this context, override just in case
    def paint_units(self, current_level):
        pass
    def draw_unit(self, painter, unit, position, opacity=False):
        pass
