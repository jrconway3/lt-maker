from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor

from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.database import DB

from app.editor import commands

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
        self.clear_scene()
        if self.current_map:
            self.working_image = QPixmap(self.current_map.base_image)
        else:
            return
        if self.main_editor.dock_visibility['Terrain']:
            self.paint_terrain()
        self.show_map()

    def paint_terrain(self):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            for coord, tile in self.current_map.tiles.items():
                color = DB.terrain.get(tile.terrain_nid).color
                write_color = QColor(color[0], color[1], color[2])
                write_color.setAlpha(self.main_editor.terrain_painter_menu.get_alpha())
                painter.fillRect(coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT, write_color)
            painter.end()

    def show_map(self):
        if self.working_image:
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
                    current_unit = self.window.units_menu.get_current()
                    if current_unit:
                        under_unit = self.main_editor.current_level.check_position(pos)
                        if under_unit:
                            print("Removing Unit")
                            under_unit.position = None
                        if current_unit.position:
                            print("Move Unit")
                            current_unit.position = pos
                        else:
                            print("Place Unit")
                            current_unit.position = pos
                        self.update_view()
                elif event.button() == Qt.RightButton:
                    under_unit = self.main_editor.current_level.check_position(pos)
                    if under_unit:
                        idx = self.main_editor.current_level.units.index(under_unit)
                        self.window.units_menu.select(idx)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        # pixmap = self.scene.itemAt(scene_pos, self.transform())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and pos in self.current_map.tiles:
            self.main_editor.set_position_bar(pos)
            if (event.buttons() & Qt.LeftButton):
                self.main_editor.terrain_painter_menu.paint_tile(pos)
        else:
            self.main_editor.set_position_bar(None)

    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        pos = int(scene_pos.x() / TILEWIDTH), int(scene_pos.y() / TILEHEIGHT)

        if self.current_map and pos in self.current_map.tiles:
            if event.button() == Qt.LeftButton:
                # Force no merge when you've lifted up your pen...
                last_index = self.main_editor.undo_stack.count() - 1
                last_command = self.main_editor.undo_stack.command(last_index)
                if isinstance(last_command, commands.ChangeTileTerrain):
                    last_command.can_merge = False
            elif event.button() == Qt.RightButton:
                current_nid = self.current_map.tiles[pos].terrain.nid
                self.main_editor.terrain_painter_menu.set_current_nid(current_nid)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0 and self.screen_scale < self.max_scale:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.angleDelta().y() < 0 and self.screen_scale > self.min_scale:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)
