from enum import IntEnum

from PyQt5.QtWidgets import QSplitter, QFrame, QVBoxLayout, QDialogButtonBox, \
    QToolBar, QTabBar, QWidget, QDialog, QGroupBox, QFormLayout, QSpinBox, QAction, \
    QGraphicsView, QGraphicsScene, QAbstractItemView, QActionGroup
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QImage, QPainter, QPixmap, QIcon, QColor, QPen

from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT
from app.resources.resources import RESOURCES
from app.resources.tiles import LayerGrid
from app.data.database import DB

from app.editor import timer
from app.editor.icon_editor.icon_view import IconView
from app.editor.terrain_painter_menu import TerrainPainterMenu
from app.editor.base_database_gui import ResourceCollectionModel
from app.extensions.custom_gui import ResourceListView, Dialog

from app.utilities import str_utils

def draw_tilemap(tilemap):
    image = QImage(tilemap.width * TILEWIDTH,
                   tilemap.height * TILEHEIGHT,
                   QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter()
    painter.begin(image)
    for layer in tilemap.layers:
        if layer.visible:
            for coord, tile_sprite in layer.sprite_grid.items():
                tileset = RESOURCES.tilesets.get(tile_sprite.tileset_nid)
                if not tileset.pixmap:
                    tileset.set_pixmap(QPixmap(tileset.full_path))
                pix = tileset.get_pixmap(tile_sprite.tileset_position)
                if pix:
                    painter.drawImage(coord[0] * TILEWIDTH,
                                      coord[1] * TILEHEIGHT,
                                      pix.toImage())
    painter.end()
    return image

class PaintTool(IntEnum):
    NoTool = 0
    Brush = 1
    Fill = 2
    Erase = 3

class MapEditorView(QGraphicsView):
    min_scale = 0.5
    max_scale = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.resource_editor = self.window

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMouseTracking(True)

        self.setMinimumSize(WINWIDTH, WINHEIGHT)
        self.setStyleSheet("background-color:rgb(128, 128, 128);")

        self.screen_scale = 1

        self.tilemap = None

        self.current_mouse_position = (0, 0)

        self.left_selecting = False
        self.right_selecting = False
        self.right_selection = {}  # Dictionary of tile_sprites

        timer.get_timer().tick_elapsed.connect(self.tick)

    def tick(self):
        if self.tilemap:
            self.update_view()

    def set_current(self, current):
        self.tilemap = current
        self.update_view()

    def clear_scene(self):
        self.scene.clear()

    def update_view(self):
        if self.tilemap:
            pixmap = QPixmap.fromImage(self.get_map_image())
            self.working_image = pixmap
        else:
            return
        if self.window.terrain_mode:
            self.draw_terrain()
        self.show_map()

    def get_map_image(self):
        image = draw_tilemap(self.tilemap)
        painter = QPainter()
        painter.begin(image)
        # Draw grid lines
        painter.setPen(QPen(QColor(0, 0, 0, 128), 1, Qt.DotLine))
        for x in range(self.tilemap.width):
            painter.drawLine(x * TILEWIDTH, 0, x * TILEWIDTH, self.tilemap.height * TILEHEIGHT)
        for y in range(self.tilemap.height):
            painter.drawLine(0, y * TILEHEIGHT, self.tilemap.width * TILEWIDTH, y * TILEHEIGHT)

        # Draw cursor...
        if not self.window.terrain_mode:
            if self.right_selecting:  
                # Currently holding down right click and selecting area
                self.draw_selection(painter)
            elif self.right_selection:
                # Currently drawing with a right click held down area
                self.draw_right_cursor(painter)
            else:
                # Currently drawing with a tileset area
                self.draw_normal_cursor(painter)

        painter.end()
        return image

    def draw_terrain(self):
        if self.working_image:
            painter = QPainter()
            painter.begin(self.working_image)
            alpha = self.window.terrain_painter_menu.get_alpha()
            explored_coords = set()
            for layer in reversed(self.tilemap.layers):
                if layer.visible:
                    for coord, terrain_nid in layer.terrain_grid.items():
                        # Don't draw the one's below...
                        if coord in explored_coords:
                            continue
                        explored_coords.add(coord)
                        color = DB.terrain.get(terrain_nid).color
                        write_color = QColor(color[0], color[1], color[2])
                        write_color.setAlpha(alpha)
                        painter.fillRect(coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT, write_color)
            painter.end()

    def show_map(self):
        self.clear_scene()
        self.scene.addPixmap(self.working_image)

    def draw_normal_cursor(self, painter):
        tileset, coords = self.window.get_tileset_coords()
        if tileset and coords:
            mouse_pos = self.current_mouse_position
            topleft = min(coords)
            for coord in coords:
                im = tileset.subpixmaps[coord].toImage()
                rel_coord = coord[0] - topleft[0], coord[1] - topleft[1]
                true_pos = mouse_pos[0] + rel_coord[0], mouse_pos[1] + rel_coord[1]                
                painter.drawImage(true_pos[0] * TILEWIDTH,
                                  true_pos[1] * TILEHEIGHT,
                                  im)
                # Fill with blue
                rect = QRect(true_pos[0] * TILEWIDTH, true_pos[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                painter.fillRect(rect, QColor(0, 255, 255, 96))

    def draw_right_cursor(self, painter):
        mouse_pos = self.current_mouse_position
        for coord, tile_sprite in self.right_selection.items():
            # print(coord, tile_sprite)
            if not tile_sprite:
                continue
            tileset = RESOURCES.tilesets.get(tile_sprite.tileset_nid)
            pix = tileset.get_pixmap(tile_sprite.tileset_position)
            if pix:
                true_coord = mouse_pos[0] + coord[0], mouse_pos[1] + coord[1]
                painter.drawImage(true_coord[0] * TILEWIDTH,
                                  true_coord[1] * TILEHEIGHT,
                                  pix.toImage())
                # Fill with blue
                rect = QRect(true_coord[0] * TILEWIDTH, true_coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                painter.fillRect(rect, QColor(0, 255, 255, 96))

    def draw_selection(self, painter):
        starting_pos = self.right_selecting
        if not starting_pos:
            return
        for coord, tile_sprite in self.right_selection.items():
            true_coord = starting_pos[0] + coord[0], starting_pos[1] + coord[1]
            color = QColor(0, 255, 255, 128)
            rect = QRect(true_coord[0] * TILEWIDTH, true_coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
            painter.fillRect(rect, color)

    def get_current_layer(self):
        current_layer_index = self.window.layer_menu.view.currentIndex()
        idx = current_layer_index.row()
        return self.tilemap.layers[idx]

    def get_tile_sprite(self, pos):
        for layer in reversed(self.tilemap.layers):
            if layer.visible:
                if pos in layer.sprite_grid:
                    tile_sprite = layer.sprite_grid[pos]
                    return tile_sprite
                else:
                    return None
        return None

    def find_coords(self):
        self.right_selection.clear()
        left = min(self.right_selecting[0], self.current_mouse_position[0])
        width = max(self.right_selecting[0], self.current_mouse_position[0]) - left + 1
        top = min(self.right_selecting[1], self.current_mouse_position[1])
        height = max(self.right_selecting[1], self.current_mouse_position[1]) - top + 1
        print(left, top, width, height)
        for x in range(width):
            for y in range(height):
                self.right_selection[(x, y)] = self.get_tile_sprite((x + left, y + top))

    def paint_terrain(self, tile_pos):
        current_layer = self.get_current_layer()
        if self.tilemap.check_bounds(tile_pos):
            current_nid = self.window.terrain_painter_menu.get_current_nid()
            current_layer.terrain_grid[tile_pos] = current_nid

    def paint_tile(self, tile_pos):
        current_layer = self.get_current_layer()

        if self.right_selection:
            for coord, tile_sprite in self.right_selection.items():
                true_pos = tile_pos[0] + coord[0], tile_pos[1] + coord[1]
                if self.tilemap.check_bounds(true_pos):
                    if tile_sprite:
                        tileset_nid = tile_sprite.tileset_nid
                        pos = tile_sprite.tileset_position
                        current_layer.set_sprite(true_pos, tileset_nid, pos)
                    else:
                        current_layer.erase_sprite(true_pos)
        else:
            tileset, coords = self.window.get_tileset_coords()
            if tileset and coords:
                topleft = min(coords)
                for coord in coords:
                    rel_coord = coord[0] - topleft[0], coord[1] - topleft[1]
                    true_pos = tile_pos[0] + rel_coord[0], tile_pos[1] + rel_coord[1]
                    if self.tilemap.check_bounds(true_pos):
                        current_layer.set_sprite(true_pos, tileset.nid, coord)

    def erase_terrain(self, tile_pos):
        current_layer = self.get_current_layer()

        if self.tilemap.check_bounds(tile_pos):
            current_layer.erase_terrain(tile_pos)

    def erase_tile(self, tile_pos):
        current_layer = self.get_current_layer()

        if self.tilemap.check_bounds(tile_pos):
            current_layer.erase_sprite(tile_pos)

    def flood_fill_terrain(self, tile_pos):
        if not self.tilemap.check_bounds(tile_pos):
            return 

        coords_to_replace = set()

        def find_similar(x, y, terrain_nid):
            if not self.tilemap.check_bounds((x, y)):
                return
            if (x, y) in coords_to_replace:
                return
            other_nid = current_layer.get_terrain((x, y))
            if terrain_nid != other_nid:
                return

            coords_to_replace.add((x, y))

            # Now recur for all directions
            find_similar(x + 1, y, terrain_nid)
            find_similar(x - 1, y, terrain_nid)
            find_similar(x, y + 1, terrain_nid)
            find_similar(x, y - 1, terrain_nid)

        current_layer = self.get_current_layer()

        # Get coords like current coord in current_layer
        terrain_nid = current_layer.get_terrain(tile_pos)
        # Determine which coords should be flood-filled
        find_similar(tile_pos[0], tile_pos[1], terrain_nid)

        # Do the deed
        for coord in coords_to_replace:
            current_nid = self.window.terrain_painter_menu.get_current_nid()
            current_layer.terrain_grid[coord] = current_nid

    def flood_fill_tile(self, tile_pos):
        if not self.tilemap.check_bounds(tile_pos):
            return 

        coords_to_replace = set()

        def find_similar(x, y, sprite):
            if not self.tilemap.check_bounds((x, y)):
                return
            if (x, y) in coords_to_replace:
                return
            tile = current_layer.get_sprite((x, y))
            if tile:
                nid = tile.tileset_nid
                coord = tile.tileset_position
            else:
                nid, coord = None, None
            if sprite:
                if nid != sprite.tileset_nid or coord != sprite.tileset_position:
                    return
            elif tile:
                return

            coords_to_replace.add((x, y))

            # Now recur for all directions
            find_similar(x + 1, y, sprite)
            find_similar(x - 1, y, sprite)
            find_similar(x, y + 1, sprite)
            find_similar(x, y - 1, sprite)

        current_layer = self.get_current_layer()
        tileset, coords = self.window.get_tileset_coords()

        # Get coords like current coord in current_layer
        current_tile = current_layer.get_sprite(tile_pos)
        # Determine which coords should be flood-filled
        find_similar(tile_pos[0], tile_pos[1], current_tile)

        topleft = min(coords)
        w = max(coord[0] for coord in coords) - topleft[0] + 1
        h = max(coord[1] for coord in coords) - topleft[1] + 1

        # Do the deed
        for x in range(self.tilemap.width):
            for y in range(self.tilemap.height):
                if (x, y) in coords_to_replace:
                    new_coord_x = x%w + topleft[0]
                    new_coord_y = y%h + topleft[1]
                    if (new_coord_x, new_coord_y) in coords:
                        current_layer.set_sprite(
                            (x, y), tileset, (new_coord_x, new_coord_y))

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // TILEWIDTH), \
            int(scene_pos.y() // TILEHEIGHT)

        if event.button() == Qt.LeftButton:
            if self.window.current_tool == PaintTool.Brush:
                if self.window.terrain_mode:
                    self.paint_terrain(tile_pos)
                else:
                    self.paint_tile(tile_pos)
                self.left_selecting = True
            elif self.window.current_tool == PaintTool.Erase:
                if self.window.terrain_mode:
                    self.erase_terrain(tile_pos)
                else:
                    self.erase_tile(tile_pos)
                self.left_selecting = True
            elif self.window.current_tool == PaintTool.Fill:
                if self.window.terrain_mode:
                    self.flood_fill_terrain(tile_pos)
                else:
                    self.flood_fill_tile(tile_pos)
        elif event.button() == Qt.RightButton and self.tilemap.check_bounds(tile_pos):
            if self.window.terrain_mode:
                current_nid = self.tilemap.get_terrain(tile_pos)
                if current_nid:
                    self.window.terrain_painter_menu.set_current_nid(current_nid)
            elif self.window.current_tool == PaintTool.Brush:
                self.right_selecting = tile_pos
                self.right_selection.clear()
                self.window.void_tileset_selection()

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // TILEWIDTH), \
            int(scene_pos.y() // TILEHEIGHT)

        self.current_mouse_position = tile_pos

        if self.left_selecting and self.tilemap.check_bounds(tile_pos):
            if self.window.current_tool == PaintTool.Brush:
                if self.window.terrain_mode:
                    self.paint_terrain(tile_pos)
                else:
                    self.paint_tile(tile_pos)
            elif self.window.current_tool == PaintTool.Erase:
                if self.window.terrain_mode:
                    self.erase_terrain(tile_pos)
                else:
                    self.erase_tile(tile_pos)
        elif self.right_selecting:
            self.find_coords()

    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // TILEWIDTH), \
            int(scene_pos.y() // TILEHEIGHT)

        if self.window.terrain_mode:
            if event.button() == Qt.LeftButton:
                self.left_selecting = False
        elif self.window.current_tool == PaintTool.Brush:
            if event.button() == Qt.LeftButton:
                self.left_selecting = False
            elif event.button() == Qt.RightButton:
                print("Right Selecting", self.right_selecting)
                if self.right_selecting:
                    self.find_coords()
                    self.right_selecting = False
        elif self.window.current_tool == PaintTool.Erase:
            if event.button() == Qt.LeftButton:
                self.left_selecting = False

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

class MapEditor(QDialog):
    def __init__(self, parent=None, current=None):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Tilemap Editor")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.current = current
        self.current_tool = PaintTool.NoTool
        self.terrain_mode: bool = False

        self.tileset_menu = TileSetMenu(self, self.current)
        self.layer_menu = LayerMenu(self, self.current)
        self.view = MapEditorView(self)
        self.view.set_current(current)

        self.create_actions()
        self.create_toolbar()

        right_splitter = QSplitter(self)
        right_splitter.setOrientation(Qt.Vertical)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.addWidget(self.layer_menu)
        right_splitter.addWidget(self.tileset_menu)

        main_splitter = QSplitter(self)
        main_splitter.setChildrenCollapsible(False)

        view_frame = QFrame()
        view_layout = QVBoxLayout()
        view_layout.addWidget(self.toolbar)
        view_layout.addWidget(self.view)
        view_frame.setLayout(view_layout)

        self.terrain_painter_menu = TerrainPainterMenu(self)

        main_splitter.addWidget(self.terrain_painter_menu)
        main_splitter.addWidget(view_frame)
        main_splitter.addWidget(right_splitter)

        self.terrain_painter_menu.hide()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(main_splitter)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        self.layout.addWidget(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)

        self.view.update_view()

    def create_actions(self):
        paint_group = QActionGroup(self)
        self.brush_action = QAction(QIcon("icons/brush.png"), "&Brush", self, shortcut="B", triggered=self.set_brush)
        self.brush_action.setCheckable(True)
        paint_group.addAction(self.brush_action)
        self.paint_action = QAction(QIcon("icons/fill.png"), "&Fill", self, shortcut="F", triggered=self.set_fill)
        self.paint_action.setCheckable(True)
        paint_group.addAction(self.paint_action)
        self.erase_action = QAction(QIcon("icons/eraser.png"), "&Erase", self, shortcut="E", triggered=self.set_erase)
        self.erase_action.setCheckable(True)
        paint_group.addAction(self.erase_action)
        self.resize_action = QAction(QIcon("icons/resize.png"), "&Resize", self, shortcut="R", triggered=self.resize)

        self.terrain_action = QAction(QIcon("icons/terrain.png"), "&Terrain Mode", self, shortcut="T", triggered=self.terrain_mode_toggle)
        self.terrain_action.setCheckable(True)

    def void_right_selection(self):
        self.view.right_selection.clear()

    def void_tileset_selection(self):
        self.tileset_menu.reset_selection()

    def check_brush(self):
        self.brush_action.setChecked(True)
        self.set_brush(True)

    def set_brush(self, val):
        self.current_tool = PaintTool.Brush

    def set_fill(self, val):
        self.current_tool = PaintTool.Fill

    def set_erase(self, val):
        self.tileset_menu.reset_selection()
        self.current_tool = PaintTool.Erase

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.brush_action)
        self.toolbar.addAction(self.paint_action)
        self.toolbar.addAction(self.erase_action)
        self.toolbar.addAction(self.resize_action)
        self.toolbar.addAction(self.terrain_action)

    def set_current(self, current):  # Current is a TileMapPrefab
        self.current = current
        self.view.set_current(current)
        self.layer_menu.set_current(current)
        self.tileset_menu.set_current(current)
        self.view.update_view()

    def resize(self):
        ResizeDialog.get_new_size(self.current, self)

    def terrain_mode_toggle(self, val):
        self.terrain_mode = val
        if self.terrain_mode:
            self.terrain_painter_menu.show()
        else:
            self.terrain_painter_menu.hide()

    def update_view(self):
        self.view.update_view()

    def reset_terrain(self):
        current_layer_index = self.layer_menu.view.currentIndex()
        idx = current_layer_index.row()
        current_layer = self.current.layers[idx]
        current_layer.terrain_grid.clear()

    def get_tileset_coords(self):
        return self.tileset_menu.current_tileset, self.tileset_menu.get_selection_coords()

class ResizeDialog(Dialog):
    def __init__(self, current, parent=None):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Tilemap Resize")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.current = current  # TilemapPrefab

        size_section = QGroupBox(self)
        size_section.setTitle("Size")
        size_layout = QFormLayout()
        self.width_box = QSpinBox()
        self.width_box.setValue(self.current.width)
        self.width_box.setRange(15, 59)
        self.width_box.valueChanged.connect(self.on_width_changed)
        size_layout.addRow("Width:", self.width_box)
        self.height_box = QSpinBox()
        self.height_box.setValue(self.current.height)
        self.height_box.setRange(10, 39)
        self.height_box.valueChanged.connect(self.on_height_changed)
        size_layout.addRow("Height:", self.height_box)
        size_section.setLayout(size_layout)

        offset_section = QGroupBox(self)
        offset_section.setTitle("Offset")
        offset_layout = QFormLayout()
        self.x_box = QSpinBox()
        self.x_box.setValue(0)
        self.x_box.setRange(0, 0)
        self.x_box.valueChanged.connect(self.on_offset_changed)
        # self.x_box.valueChanged.connect(self.on_x_changed)
        offset_layout.addRow("X:", self.x_box)
        self.y_box = QSpinBox()
        self.y_box.setValue(0)
        self.y_box.setRange(0, 0)
        self.y_box.valueChanged.connect(self.on_offset_changed)
        # self.y_box.valueChanged.connect(self.on_y_changed)
        offset_layout.addRow("Y:", self.y_box)
        offset_section.setLayout(offset_layout)

        self.icon_view = IconView(self)
        self.icon_view.scene.setBackgroundBrush(QColor(200, 200, 200, 255))

        self.layout.addWidget(size_section)
        self.layout.addWidget(offset_section)
        self.layout.addWidget(self.icon_view)
        self.layout.addWidget(self.buttonbox)

        self.draw_image()

    def on_width_changed(self, val):
        if val > self.current.width:
            self.x_box.setMaximum(val - self.current.width)
        elif val < self.current.width:
            self.x_box.setMinimum(val - self.current.width)
        self.draw_image()

    def on_height_changed(self, val):
        if val > self.current.height:
            self.y_box.setMaximum(val - self.current.height)
        elif val < self.current.height:
            self.y_box.setMinimum(val - self.current.height)
        self.draw_image()

    def on_offset_changed(self, val):
        self.draw_image()

    def draw_image(self):
        base_image = QImage(202, 202, QImage.Format_ARGB32)
        base_image.fill(QColor(200, 200, 200, 255))
        painter = QPainter()
        painter.begin(base_image)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        # Draw regular square around
        highest_dim = max([self.width_box.value(), self.height_box.value(), 
                           self.current.width, self.current.height])
        new_offset_x = int(self.x_box.value() / highest_dim * 200)
        new_offset_y = int(self.y_box.value() / highest_dim * 200)
        new_width = int(self.width_box.value() / highest_dim * 200)
        new_height = int(self.height_box.value() / highest_dim * 200)
        painter.drawRect(1, 1, new_width, new_height)
        painter.setPen(QPen(Qt.black, 2, Qt.DashLine))
        new_width = int(self.current.width / highest_dim * 200)
        new_height = int(self.current.height / highest_dim * 200)
        painter.drawRect(1 + new_offset_x, 1 + new_offset_y, new_width, new_height)

        painter.end()

        self.icon_view.set_image(QPixmap.fromImage(base_image))
        self.icon_view.show_image()

    @classmethod
    def get_new_size(cls, tilemap_prefab, parent=None):
        dialog = cls(tilemap_prefab, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_width = int(dialog.width_box.value())
            new_height = int(dialog.height_box.value())
            x_offset = int(dialog.x_box.value())
            y_offset = int(dialog.y_box.value())
            tilemap_prefab.resize(new_width, new_height, x_offset, y_offset)
            return True
        else:
            return False

class LayerModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        layer = self._data[index.row()]
        if role == Qt.DisplayRole:
            text = layer.nid
            return text
        elif role == Qt.CheckStateRole:
            value = Qt.Checked if layer.visible else Qt.Unchecked
            return value
        return None

    def create_new(self):
        new_nid = str_utils.get_next_name('New Layer', self._data.keys())
        parent = self.window.current
        new_layer = LayerGrid(new_nid, parent)
        self._data.append(new_layer)
        return new_layer

    def delete(self, idx):
        self._data.pop(idx)
        self.layoutChanged.emit()

    def duplicate(self, idx):
        layer = self._data[idx]
        parent = layer.parent
        new_nid = str_utils.get_next_name(layer.nid, self._data.keys())
        # Duplicate by serializing and then deserializing
        ser_layer = layer.serialize()
        new_layer = LayerGrid.deserialize(ser_layer, parent)
        new_layer.nid = new_nid
        self._data.insert(idx + 1, new_layer)
        self.layoutChanged.emit()

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            layer = self._data[index.row()]
            if value == Qt.Checked:
                layer.visible = True
            else:
                layer.visible = False
            self.dataChanged.emit(index, index)
            self.window.update_view()
        return super().setData(index, value, role)

    def flags(self, index):
        flags = super().flags(index)
        if not index.isValid():
            return flags
        return flags | Qt.ItemIsUserCheckable

class LayerMenu(QWidget):
    def __init__(self, parent=None, current=None):
        super().__init__(parent)
        self.window = parent
        self.title = "Layers"
        self.current = current
        self._data = current.layers

        deletion_criteria = (self.deletion_func, None, self.deletion_func)

        self.model = LayerModel(self._data, self)

        self.view = ResourceListView(deletion_criteria, self)
        self.view.setModel(self.model)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Remove edit on double click
        # self.view.clicked.connect(self.on_click)
        self.view.selectionModel().currentChanged.connect(self.on_item_changed)

        self.create_actions()
        self.create_toolbar()

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

    def deletion_func(self, model, index):
        return model._data[index.row()].nid != "base"

    def update_view(self):
        self.window.update_view()

    def set_current(self, current):
        self.current = current
        self._data = current.layers
        self.collection.update_list()

    def on_item_changed(self, curr, prev):
        # Turn off delete action if layer should not be deletable
        if self.deletion_func(self.model, curr):
            self.delete_action.setEnabled(True)
        else:
            self.delete_action.setEnabled(False)

    def on_click(self, index):
        if bool(self.model.flags(index) & Qt.ItemIsEnabled):
            layer = self.model._data[index.row()]
            layer.visible = not layer.visible
            self.model.dataChanged.emit(index, index)
            self.window.update_view()

    def create_actions(self):
        self.new_action = QAction(QIcon("icons/file-plus.png"), "New Layer", triggered=self.new)
        self.duplicate_action = QAction(QIcon("icons/duplicate.png"), "Duplicate Layer", triggered=self.duplicate)
        self.delete_action = QAction(QIcon("icons/x-circle.png"), "Delete Layer", triggered=self.delete)
        self.delete_action.setEnabled(False)

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.duplicate_action)
        self.toolbar.addAction(self.delete_action)

    def new(self):
        last_index = self.model.index(len(self._data) - 1)
        self.view.new(last_index)

    def duplicate(self):
        current_index = self.view.currentIndex()
        self.view.duplicate(current_index)

    def delete(self):
        current_index = self.view.currentIndex()
        if self.deletion_func(self.model, current_index):
            self.view.delete(current_index)

class TileSetMenu(QWidget):
    def __init__(self, parent=None, current=None):
        super().__init__(parent)
        self.window = parent

        self.current = current

        self.tab_bar = QTabBar(self)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)

        self.view = TileSetView(self)

        self.create_actions()
        self.create_toolbar()

        layout = QVBoxLayout()
        layout.addWidget(self.tab_bar)
        layout.addWidget(self.view)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

        self.current_tileset = None
        self.set_current(self.current)

    def on_tab_changed(self, idx):
        if self.current.tilesets:
            tileset_nid = self.current.tilesets[idx]
            self.load_tileset(tileset_nid)

    def tab_clear(self):
        for idx in range(self.tab_bar.count()):
            i = self.tab_bar.count() - idx - 1
            self.tab_bar.removeTab(i)

    def get_selection_coords(self):
        return self.view.get_selection_coords()

    def reset_selection(self):
        self.view.reset_selection()

    def set_current(self, current):
        self.current = current

        self.tab_clear()
        for nid in self.current.tilesets:
            self.tab_bar.addTab(nid)

        if self.current.tilesets:
            self.load_tileset(self.current.tilesets[0])
        else:
            self.empty_tileset()

    def load_tileset(self, tileset_nid):
        tileset = RESOURCES.tilesets.get(tileset_nid)
        if not tileset.pixmap:
            tileset.set_pixmap(QPixmap(tileset.full_path))
        self.current_tileset = tileset
        self.delete_action.setEnabled(True)
        self.view.set_current(tileset)
        self.view.update_view()

    def empty_tileset(self):
        self.delete_action.setEnabled(False)
        self.view.set_current(None)
        self.view.update_view()

    def create_actions(self):
        self.new_action = QAction(QIcon("icons/file-plus.png"), "Load Tileset", triggered=self.new)
        self.delete_action = QAction(QIcon("icons/x-circle.png"), "Unload Tileset", triggered=self.delete)
        self.delete_action.setEnabled(False)

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.delete_action)

    def new(self):
        from app.editor.tile_editor import tile_tab
        res, ok = tile_tab.get_tilesets()
        if ok:
            nid = res.nid
            self.current.tilesets.append(nid)
            self.tab_bar.addTab(nid)
            self.tab_bar.setCurrentIndex(len(self.current.tilesets) - 1)
            # self.load_tileset(nid)

    def delete(self):
        idx = self.tab_bar.currentIndex()
        if 0 <= idx < len(self.current.tilesets):
            self.current.tilesets.pop(idx)
            self.tab_bar.removeTab(idx)

        new_idx = self.tab_bar.currentIndex()
        if self.current.tilesets:
            self.load_tileset(self.current.tilesets[new_idx])
        else:
            self.empty_tileset()

class TileSetView(MapEditorView):
    tilewidth = TILEWIDTH + 1
    tileheight = TILEHEIGHT + 1

    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.window = parent

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMouseTracking(True)

        self.setStyleSheet("background-color:rgb(248, 248, 248);")

        self.screen_scale = 1

        self.tileset = None
        self.current_mouse_position = (0, 0)
        self.left_selecting = None
        self.current_coords = set()

    def get_selection_coords(self):
        return self.current_coords

    def reset_selection(self):
        self.left_selecting = None
        self.current_coords.clear()
        self.update_view()

    def update_view(self):
        if self.tileset:
            self.show_map()
        else:
            self.clear_scene()

    def set_current(self, current):
        self.tileset = current
        self.left_selecting = None
        self.current_coords.clear()
        self.update_view()

    def show_map(self):
        image = QImage(self.tileset.width * self.tilewidth,
                       self.tileset.height * self.tileheight,
                       QImage.Format_ARGB32)
        image.fill(QColor(255, 255, 255, 0))

        painter = QPainter()
        painter.begin(image)
        for coord, pixmap in self.tileset.subpixmaps.items():
            im = pixmap.toImage()
            painter.drawImage(coord[0] * self.tilewidth, coord[1] * self.tileheight, im)
            if coord in self.current_coords:
                color = QColor(0, 255, 255, 128)
                rect = QRect(coord[0] * self.tilewidth, coord[1] * self.tileheight, TILEWIDTH, TILEHEIGHT)
                painter.fillRect(rect, color)
            
        # Draw grid lines
        painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))
        for x in range(self.tileset.width):
            painter.drawLine(x * self.tilewidth, 0, x * self.tilewidth, self.tileset.height * self.tileheight)
        for y in range(self.tileset.height):
            painter.drawLine(0, y * self.tileheight, self.tileset.width * self.tilewidth, y * self.tileheight)

        painter.end()
        self.clear_scene()
        self.pixmap = QPixmap.fromImage(image)
        self.scene.addPixmap(self.pixmap)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // self.tilewidth), \
            int(scene_pos.y() // self.tileheight)

        if self.tileset and self.tileset.check_bounds(tile_pos):
            if event.button() == Qt.LeftButton:
                self.left_selecting = tile_pos
                self.window.window.void_right_selection()
                self.current_coords.clear()

    def find_coords(self):
        self.current_coords.clear()
        left = min(self.left_selecting[0], self.current_mouse_position[0])
        width = max(self.left_selecting[0], self.current_mouse_position[0]) - left + 1
        top = min(self.left_selecting[1], self.current_mouse_position[1])
        height = max(self.left_selecting[1], self.current_mouse_position[1]) - top + 1
        for x in range(width):
            for y in range(height):
                new_coord = (x + left, y + top)
                if self.tileset.check_bounds(new_coord):
                    self.current_coords.add(new_coord)
            
    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // self.tilewidth), \
            int(scene_pos.y() // self.tileheight)

        if self.left_selecting and self.tileset and self.tileset.check_bounds(tile_pos):
            self.current_mouse_position = tile_pos
            self.find_coords()
            self.update_view()
            
    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // self.tilewidth), \
            int(scene_pos.y() // self.tileheight)
        self.current_mouse_position = tile_pos

        if self.left_selecting:
            if event.button() == Qt.LeftButton:
                self.find_coords()
                self.left_selecting = False
                if self.window.window.current_tool not in (PaintTool.Brush, PaintTool.Fill):
                    self.window.window.check_brush()
                self.update_view()
