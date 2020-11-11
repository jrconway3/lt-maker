from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor

from app.utilities import utils
from app.sprites import SPRITES
from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT
from app.data.database import DB

from app.editor import timer
from app.editor.class_editor import class_model
import app.editor.tilemap_editor as tilemap_editor

class SimpleMapView(QGraphicsView):
    min_scale = 1
    max_scale = 4
    position_clicked = pyqtSignal(int, int)
    position_moved = pyqtSignal(int, int)
    
    def __init__(self, window=None):
        super().__init__()
        self.main_editor = window
        self.settings = QSettings("rainlash", "Lex Talionis")
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMouseTracking(True)

        self.setMinimumSize(WINWIDTH, WINHEIGHT)
        self.setStyleSheet("background-color:rgb(128, 128, 128);")

        self.current_level = None
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

    def set_current_level(self, level):
        self.current_level = level

    def clear_scene(self):
        self.scene.clear()

    def update_view(self):
        if self.current_map:
            image = tilemap_editor.draw_tilemap(self.current_map)
            pixmap = QPixmap.fromImage(image)
            self.working_image = pixmap
        else:
            return
        self.paint_units(self.current_level)
        self.show_map()

    def draw_unit(self, painter, unit, position, opacity=False):
        # Draw unit map sprite
        klass_nid = unit.klass
        num = timer.get_timer().passive_counter.count
        klass = DB.classes.get(klass_nid)
        pixmap = class_model.get_map_sprite_icon(klass, num, False, unit.team, unit.variant)
        coord = position
        if pixmap:
            if opacity:
                painter.setOpacity(0.33)
            painter.drawImage(coord[0] * TILEWIDTH - 9, coord[1] * TILEHEIGHT - 8, pixmap.toImage())
            painter.setOpacity(1.0)
        else:
            pass  # TODO: for now  # Need a fallback option... CITIZEN??

    def paint_units(self, current_level):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for unit in current_level.units:
                if not unit.starting_position:
                    continue
                self.draw_unit(painter, unit, unit.starting_position)
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
            self.position_clicked.emit(*pos)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and self.current_map.check_bounds(pos):
            self.position_moved.emit(*pos)
        else:
            self.position_moved.emit(-1, -1)

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

class MapView(SimpleMapView):
    def check_position(self, level_prefab, pos):
        for unit in level_prefab.units:
            if unit.starting_position and \
                    unit.starting_position[0] == pos[0] and \
                    unit.starting_position[1] == pos[1]:
                return unit
        return None

    def update_view(self):
        if self.current_map:
            image = tilemap_editor.draw_tilemap(self.current_map)
            pixmap = QPixmap.fromImage(image)
            self.working_image = pixmap
        else:
            return
        if self.main_editor.dock_visibility['Properties']:
            self.paint_units()
        elif self.main_editor.dock_visibility['Units']:
            self.paint_units()
        elif self.main_editor.dock_visibility['Regions']:
            self.paint_regions()
        elif self.main_editor.dock_visibility['Groups']:
            self.paint_groups()
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
                self.draw_unit(painter, unit, unit.starting_position)
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

    def paint_groups(self):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for group in self.main_editor.current_level.unit_groups:
                for unit in group.units:
                    position = group.positions.get(unit.nid)
                    if not position:
                        continue
                    self.draw_unit(painter, unit, position, opacity=True)
            # Draw current group
            current_group = self.main_editor.group_painter_menu.get_current()
            if current_group:
                for unit in current_group.units:
                    position = current_group.positions.get(unit.nid)
                    if not position:
                        continue
                    # With full opacity
                    self.draw_unit(painter, unit, position)
            painter.end()

    def paint_regions(self):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for region in self.main_editor.current_level.regions:
                if not region.position:
                    continue
                x, y = region.position
                width, height = region.size
                color = utils.hash_to_color(hash(region.nid))
                pixmap = QPixmap(width * TILEWIDTH, height * TILEHEIGHT)
                pixmap.fill(QColor(color))
                painter.drawImage(x * TILEWIDTH, y * TILEHEIGHT, pixmap.toImage())
            current_region = self.main_editor.region_painter_menu.get_current()
            if current_region and current_region.position:
                x, y = current_region.position
                width, height = current_region.size
                painter.setBrush(Qt.NoBrush)
                painter.setPen(Qt.yellow)
                painter.drawRect(x * TILEWIDTH, y * TILEHEIGHT, width * TILEWIDTH, height * TILEHEIGHT)
            painter.end()

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
                        under_unit = self.check_position(self.main_editor.current_level, pos)
                        if under_unit:
                            print("Removing Unit")
                            under_unit.starting_position = None
                        if under_unit is current_unit:
                            message = "Removed unit %s from map" % (current_unit.nid)
                            self.main_editor.status_bar.showMessage(message)
                        elif current_unit.starting_position:
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
                    under_unit = self.check_position(self.main_editor.current_level, pos)
                    if under_unit:
                        idx = self.main_editor.current_level.units.index(under_unit.nid)
                        self.main_editor.unit_painter_menu.select(idx)
                    else:
                        self.main_editor.unit_painter_menu.deselect()
            # Groups
            elif self.main_editor.dock_visibility['Groups']:
                if event.button() == self.settings.value('place_button', Qt.RightButton):
                    current_group = self.main_editor.group_painter_menu.get_current()
                    current_unit = self.main_editor.group_painter_menu.get_current_unit()
                    if current_unit:
                        if current_group.positions.get(current_unit.nid) == pos:
                            del current_group.positions[current_unit.nid]
                            message = "Removing unit %s from map" % (current_unit.nid)
                        else:
                            current_group.positions[current_unit.nid] = pos
                            message = "Group %s unit %s's position to (%d, %d)" % (current_group.nid, current_unit.nid, pos[0], pos[1])
                        self.main_editor.status_bar.showMessage(message)
                        self.update_view()
                elif event.button() == self.settings.value('select_button', Qt.LeftButton):
                    current_group = self.main_editor.group_painter_menu.get_current()
                    under_unit = None
                    for unit_nid, position in current_group.positions.items():
                        if pos == position:
                            under_unit = current_group.units.get(unit_nid)
                            break
                    for group in self.main_editor.current_level.unit_groups:
                        if under_unit:
                            break
                        for unit_nid, position in group.positions.items():
                            if pos == position:
                                current_group = group
                                under_unit = group.units.get(unit_nid)
                                break
                    if under_unit:
                        self.main_editor.group_painter_menu.select(current_group, under_unit.nid)
                    else:
                        self.main_editor.group_painter_menu.deselect()

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

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if self.main_editor.dock_visibility['Units']:
            if event.key() == Qt.Key_Delete:
                unit_painter_menu = self.main_editor.unit_painter_menu
                indices = unit_painter_menu.view.selectionModel().selectedIndexes()
                for index in indices:
                    unit_painter_menu.model.delete(index.row())
