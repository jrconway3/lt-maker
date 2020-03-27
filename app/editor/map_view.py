from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor

from app.sprites import SPRITES
from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.resources import RESOURCES
from app.data.database import DB

from app.editor.timer import TIMER
from app.editor import commands
from app.editor import class_database

class MapView(QGraphicsView):
    min_scale = 1
    max_scale = 4
    
    def __init__(self, window=None):
        super().__init__()
        self.main_editor = window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMouseTracking(True)

        self.setMinimumSize(15*TILEWIDTH, 10*TILEHEIGHT)
        self.setStyleSheet("background-color:rgb(128, 128, 128);")

        self.current_map = None
        self.pixmap = None
        self.screen_scale = 1

        self.working_image = None

    def center_on_pos(self, pos):
        self.centerOn(pos[0]*TILEWIDTH, pos[1]*TILEHEIGHT)
        self.update_view()

    def set_current_map(self, tilemap):
        self.current_map = tilemap
        self.update_view()

    def clear_scene(self):
        self.scene.clear()

    def update_view(self):
        if self.current_map:
            default_map_image = RESOURCES.maps.get('default')
            res = RESOURCES.maps.get(self.current_map.base_image_nid, default_map_image)
            if not res.pixmap:
                res.pixmap = QPixmap(res.full_path)
            pixmap = res.pixmap
            self.working_image = pixmap.copy()
        else:
            return
        if self.main_editor.dock_visibility['Terrain']:
            self.paint_terrain()
        if self.main_editor.dock_visibility['Units']:
            self.paint_units()
        self.show_map()

    def paint_terrain(self):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            alpha = self.main_editor.terrain_painter_menu.get_alpha()
            for coord, tile in self.current_map.tiles.items():
                color = DB.terrain.get(tile.terrain_nid).color
                write_color = QColor(color[0], color[1], color[2])
                write_color.setAlpha(alpha)
                painter.fillRect(coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT, write_color)
            painter.end()

    def paint_units(self):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for unit in self.main_editor.current_level.units:
                if not unit.starting_position:
                    continue
                # Draw unit map sprite
                klass_nid = unit.klass
                num = TIMER.passive_counter.count
                klass = DB.classes.get(klass_nid)
                pixmap = class_database.get_map_sprite_icon(klass, num, False, unit.team)
                coord = unit.starting_position
                if pixmap:
                    painter.drawImage(coord[0] * TILEWIDTH - 9, coord[1] * TILEHEIGHT - 8, pixmap.toImage())
                else:
                    pass  # TODO: for now  # Need a fallback option... CITIZEN??
            # Highlight current unit with cursor
            current_unit = self.main_editor.unit_painter_menu.get_current()
            if current_unit and current_unit.starting_position:
                coord = current_unit.starting_position
                cursor_sprite = SPRITES.get('cursor')
                if cursor_sprite:
                    if not cursor_sprite.pixmap:
                        cursor_sprite.pixmap = QPixmap(cursor_sprite.full_path)
                    cursor_image = cursor_sprite.pixmap.toImage().copy(0, 64, 32, 32)
                    painter.drawImage(coord[0] * TILEWIDTH - 8, coord[1] * TILEHEIGHT - 5, cursor_image)
            painter.end()

    def show_map(self):
        if self.working_image:
            self.clear_scene()
            self.scene.addPixmap(self.working_image)

    def show_map_from_individual_sprites(self):
        if self.current_map:
            image = QImage(self.current_map.width * TILEWIDTH, 
                           self.current_map.height * TILEHEIGHT, 
                           QImage.Format_RGB32)

            painter = QPainter()
            painter.begin(image)
            for coord, tile_image in self.current_map.get_tile_sprites():
                painter.drawImage(coord[0] * TILEWIDTH, 
                                  coord[1] * TILEHEIGHT, tile_image)
            painter.end()

            self.clear_scene()
            self.pixmap = QPixmap.fromImage(image)
            self.scene.addPixmap(self.pixmap)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        scene_pos = self.mapToScene(event.pos())
        # pixmap = self.scene.itemAt(scene_pos, self.transform())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and pos in self.current_map.tiles:
            if self.main_editor.dock_visibility['Terrain']:
                if event.button() == Qt.LeftButton:
                    self.main_editor.terrain_painter_menu.paint_tile(pos)
            elif self.main_editor.dock_visibility['Units']:
                if event.button() == Qt.LeftButton:
                    current_unit = self.main_editor.unit_painter_menu.get_current()
                    if current_unit:
                        under_unit = self.main_editor.current_level.check_position(pos)
                        if under_unit:
                            print("Removing Unit")
                            under_unit.starting_position = None
                        if current_unit.starting_position:
                            print("Move Unit")
                            current_unit.starting_position = pos
                            message = "Moved unit %s to (%d, %d)" % (current_unit.nid, pos[0], pos[1]) 
                            self.main_editor.status_bar.showMessage(message)
                        else:
                            print("Place Unit")
                            current_unit.starting_position = pos
                            message = "Placed unit %s at (%d, %d)" % (current_unit.nid, pos[0], pos[1]) 
                            self.main_editor.status_bar.showMessage(message)
                        self.update_view()
                elif event.button() == Qt.RightButton:
                    under_unit = self.main_editor.current_level.check_position(pos)
                    if under_unit:
                        idx = self.main_editor.current_level.units.index(under_unit)
                        self.main_editor.unit_painter_menu.select(idx)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        # pixmap = self.scene.itemAt(scene_pos, self.transform())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and pos in self.current_map.tiles:
            self.main_editor.set_position_bar(pos)
            if self.main_editor.dock_visibility['Terrain']:
                if (event.buttons() & Qt.LeftButton):
                    self.main_editor.terrain_painter_menu.paint_tile(pos)
        else:
            self.main_editor.set_position_bar(None)

    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and pos in self.current_map.tiles:
            if self.main_editor.dock_visibility['Terrain']:
                if event.button() == Qt.LeftButton:
                    # Force no merge when you've lifted up your pen...
                    last_index = self.main_editor.undo_stack.count() - 1
                    last_command = self.main_editor.undo_stack.command(last_index)
                    if isinstance(last_command, commands.ChangeTileTerrain):
                        last_command.can_merge = False
                elif event.button() == Qt.RightButton:
                    current_nid = self.current_map.tiles[pos].terrain_nid
                    self.main_editor.terrain_painter_menu.set_current_nid(current_nid)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0 and self.screen_scale < self.max_scale:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.angleDelta().y() < 0 and self.screen_scale > self.min_scale:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)
