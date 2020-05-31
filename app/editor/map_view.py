from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor

from app.sprites import SPRITES
from app.data.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT
from app.data.resources import RESOURCES
from app.data.database import DB

from app.editor.timer import TIMER
from app.editor import class_database

class MapView(QGraphicsView):
    min_scale = 1
    max_scale = 4
    
    def __init__(self, window=None):
        super().__init__()
        self.main_editor = window
        self.settings = QSettings("rainlash", "Lex Talionis")
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMouseTracking(True)

        self.setMinimumSize(WINWIDTH, WINHEIGHT)
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

    def get_map_image(self):
        image = QImage(self.current_map.width * TILEWIDTH,
                       self.current_map.height * TILEHEIGHT,
                       QImage.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))

        painter = QPainter()
        painter.begin(image)
        for layer in self.current_map.layers:
            if layer.visible:
                for coord, tile_sprite in layer.sprite_grid.items():
                    tileset = RESOURCES.tilesets.get(tile_sprite.tileset_nid)
                    pix = tileset.get_pixmap(tile_sprite.tileset_position)
                    if pix:
                        painter.drawImage(coord[0] * TILEWIDTH,
                                          coord[1] * TILEHEIGHT,
                                          pix.toImage())
        painter.end()
        return image

    def update_view(self):
        if self.current_map:
            pixmap = QPixmap.fromImage(self.get_map_image())
            self.working_image = pixmap
        else:
            return
        if self.main_editor.dock_visibility['Properties']:
            self.paint_units()
        elif self.main_editor.dock_visibility['Units']:
            self.paint_units()
        else:
            self.paint_units()
        self.show_map()

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
                pixmap = class_database.get_map_sprite_icon(klass, num, False, unit.team, unit.gender)
                coord = unit.starting_position
                if pixmap:
                    painter.drawImage(coord[0] * TILEWIDTH - 9, coord[1] * TILEHEIGHT - 8, pixmap.toImage())
                else:
                    pass  # TODO: for now  # Need a fallback option... CITIZEN??
            # Highlight current unit with cursor
            current_unit = self.main_editor.unit_painter_menu.get_current()
            if current_unit and current_unit.starting_position:
                coord = current_unit.starting_position
                cursor_sprite = SPRITES['cursor']
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

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        scene_pos = self.mapToScene(event.pos())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and self.current_map.check_bounds(pos):
            # Units
            if self.main_editor.dock_visibility['Units']:
                if event.button() == self.settings.value('place_button', Qt.RightButton):
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
                elif event.button() == self.settings.value('select_button', Qt.LeftButton):
                    under_unit = self.main_editor.current_level.check_position(pos)
                    if under_unit:
                        idx = self.main_editor.current_level.units.index(under_unit.nid)
                        self.main_editor.unit_painter_menu.select(idx)
                    else:
                        self.main_editor.unit_painter_menu.deselect()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and self.current_map.check_bounds(pos):
            self.main_editor.set_position_bar(pos)
            self.main_editor.set_terrain(self.current_map.get_terrain(pos))
        else:
            self.main_editor.set_position_bar(None)
            self.main_editor.set_terrain(None)

    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

    def zoom_in(self):
        if self.screen_scale < self.max_scale:
            self.screen_scale += 1
            self.scale(2, 2)

    def zoom_out(self):
        if self.screen_scale > self.min_scale:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        elif event.angleDelta().y() < 0:
            self.zoom_out()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if self.main_editor.dock_visibility['Units']:
            if event.key() == Qt.Key_Delete:
                unit_painter_menu = self.main_editor.unit_painter_menu
                indices = unit_painter_menu.view.selectionModel().selectedIndexes()
                for index in indices:
                    unit_painter_menu.model.delete(index.row())
