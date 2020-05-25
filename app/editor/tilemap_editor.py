from enum import IntEnum

from PyQt5.QtWidgets import QSplitter, QFrame, QVBoxLayout, QDialogButtonBox, \
    QToolBar, QTabBar, QWidget, QDialog, QGroupBox, QFormLayout, QSpinBox, QAction, \
    QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QPixmap, QIcon, QColor, QPen

from app.data.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT
from app.data.resources import RESOURCES

from app.editor.icon_display import IconView
from app.editor.base_database_gui import ResourceCollectionModel
from app.extensions.custom_gui import ResourceListView, Dialog

class PaintTool(IntEnum):
    NoTool = 0
    Brush = 1
    Fill = 2
    Eraser = 3

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
        self.tile_pixmap = None

        self.left_selecting = False
        self.right_selecting = False

    def set_current(self, current):
        self.tilemap = current
        self.update_view()

    def set_current_tile_pixmap(self, tile_pixmap):
        self.tile_pixmap = tile_pixmap

    def clear_scene(self):
        self.scene.clear()

    def update_view(self):
        self.show_map()

    def show_map(self):
        image = QImage(self.tilemap.width * TILEWIDTH,
                       self.tilemap.height * TILEHEIGHT,
                       QImage.Format_RGB32)

        painter = QPainter()
        painter.begin(image)
        for layer in self.tilemap.layers:
            if layer.visible:
                for coord, tile_image in layer.sprite_grid.items():
                    painter.drawImage(coord[0] * TILEWIDTH,
                                      coord[1] * TILEHEIGHT,
                                      tile_image)
        painter.end()
        self.clear_scene()
        self.pixmap = QPixmap.fromImage(image)
        self.scene.addPixmap(self.pixmap)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // TILEWIDTH), \
            int(scene_pos.y() // TILEHEIGHT)

        if self.tilemap.check_bounds(tile_pos):
            if event.button() == Qt.LeftButton:
                if self.window.current_tool == PaintTool.Brush:
                    tile = self.window.current_tile
                    self.paint_tile(tile, tile_pos)
                    self.left_selecting = True
                elif self.window.current_tool == PaintTool.Eraser:
                    self.erase_tile(tile_pos)
                elif self.window.current_tool == PaintTool.Fill:
                    tile = self.window.current_tile
                    all_positions = self.flood_fill(tile_pos)
                    for pos in all_positions:
                        self.paint_tile(tile, pos)
            elif event.button() == Qt.RightButton:
                if self.window.current_tool == PaintTool.Brush:
                    self.right_selecting = tile_pos

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // TILEWIDTH), \
            int(scene_pos.y() // TILEHEIGHT)

        if self.left_selecting and self.tilemap.check_bounds(tile_pos):
            tile = self.window.current_tile
            self.paint_tile(tile, tile_pos)

    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // TILEWIDTH), \
            int(scene_pos.y() // TILEHEIGHT)

        if self.window.current_tool == PaintTool.Brush:
            if event.button() == Qt.LeftButton:
                self.left_selecting = False
            elif event.button() == Qt.RightButton:
                if self.right_selecting:
                    tile_pixmap = self.tilemap.get_tile_pixmap(tile_pos)
                    self.set_current_tile_pixmap(tile_pixmap)

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

        self.view = MapEditorView(self)

        self.current = current
        self.current_tool = PaintTool.NoTool

        self.create_actions()
        self.create_toolbar()

        self.tileset_menu = TileSetMenu(self)
        self.layer_menu = LayerMenu(self)

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

        main_splitter.addWidget(view_frame)
        main_splitter.addWidget(right_splitter)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(main_splitter)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        self.layout.addWidget(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)

        self.view.update_view()

    def create_actions(self):
        self.brush_action = QAction(QIcon("icons/brush.png"), "&Brush", self, shortcut="B", triggered=self.set_brush)
        self.brush_action.setCheckable(True)
        self.paint_action = QAction(QIcon("icons/paint.png"), "&Fill", self, shortcut="F", triggered=self.set_fill)
        self.paint_action.setCheckable(True)
        self.eraser_action = QAction(QIcon("icons/eraser.png"), "&Eraser", self, shortcut="E", triggered=self.set_eraser)
        self.eraser_action.setCheckable(True)
        self.resize_action = QAction(QIcon("icons/resize.png"), "&Resize", self, shortcut="R", triggered=self.resize)

    def set_brush(self, val):
        if val:
            self.current_tool = PaintTool.Brush
        else:
            self.current_tool = PaintTool.NoTool

    def set_fill(self, val):
        if val:
            self.current_tool = PaintTool.Fill
        else:
            self.current_tool = PaintTool.NoTool

    def set_eraser(self, val):
        if val:
            self.current_tool = PaintTool.Eraser
        else:
            self.current_tool = PaintTool.NoTool

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.brush_action)
        self.toolbar.addAction(self.paint_action)
        self.toolbar.addAction(self.eraser_action)
        self.toolbar.addAction(self.resize_action)

    def set_current(self, current):  # Current is a TileMapPrefab
        self.current = current
        self.view.set_current(current)
        self.layer_menu.set_current(current)
        self.tileset_menu.set_current(current)
        self.view.update_view()

    def resize(self):
        ResizeDialog.get_new_size(self.current, self)

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
        # self.x_box.valueChanged.connect(self.on_x_changed)
        offset_layout.addRow("X:", self.x_box)
        self.y_box = QSpinBox()
        self.y_box.setValue(0)
        self.y_box.setRange(0, 0)
        # self.y_box.valueChanged.connect(self.on_y_changed)
        offset_layout.addRow("Y:", self.y_box)
        offset_section.setLayout(size_layout)

        self.layout.addWidget(size_section)
        self.layout.addWidget(offset_section)

        self.icon_view = IconView(self)

        self.layout.addWidget(self.size_section)
        self.layout.addWidget(self.offset_section)
        self.layout.addWidget(self.icon_view)
        self.layout.addWidget(self.buttonbox)

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
        base_image = QImage(200, 200, QImage.Format_ARGB32)
        base_image.fill(QColor(200, 200, 200, 255))
        painter = QPainter()
        painter.begin(base_image)
        painter.setPen(QPen(Qt.black, 1, Qt.Line))
        # Draw regular square around
        highest_dim = max([self.width_box.value(), self.height_box.value(), 
                           self.current.width, self.current.height])
        new_offset_x = int(self.x_box.value() / highest_dim * 200)
        new_offset_y = int(self.y_box.value() / highest_dim * 200)
        new_width = int(self.width_box.value() / highest_dim * 200)
        new_height = int(self.height_box.value() / highest_dim * 200)
        painter.drawRect(new_offset_x, new_offset_y, new_width, new_height)
        painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
        new_width = int(self.current.width / highest_dim * 200)
        new_height = int(self.current.height / highest_dim * 200)
        painter.drawRect(0, 0, new_width, new_height)

        painter.end()

        self.icon_view.set_image(QPixmap.fromImage(base_image))
        self.icon_view.show_image()

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
        if role == Qt.DisplayRole:
            layer = self._data[index.row()]
            text = layer.nid
            return text
        elif role == Qt.CheckStateRole:
            layer = self._data[index.row()]
            value = Qt.Checked if layer.visible else Qt.Unchecked
            return value
        return None

    # def setData(self, index, value, role):
    #     if not index.isValid():
    #         return False
    #     if role == Qt.CheckStateRole:
    #         layer = self._data[index.row()]
    #         if value == Qt.Checked:
    #             layer.visible = True
    #         else:
    #             layer.visible = False
    #         self.dataChanged.emit(index, index)
    #         # self.window.update_view()
    #     return super().setData(index, value, role)

class LayerMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.title = "Layers"
        self._data = None
        self.current = None

        deletion_criteria = (self.deletion_func, self.deletion_func, None)

        self.model = LayerModel(self._data, self)

        self.view = ResourceListView(deletion_criteria, self)
        self.view.setModel(self.model)
        self.view.clicked.connect(self.on_click)

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
        last_index = self.model.index(len(self._data) - 1)
        self.new_action = QAction(QIcon("icons/file-plus.png"), "New", triggered=lambda: self.view.new(last_index))
        self.duplicate_action = QAction(QIcon("icons/duplicate.png", "Duplicate", triggered=self.duplicate))
        self.delete_action = QAction(QIcon("icons/x-circle.png", "Delete", triggered=self.delete))

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.duplicate_action)
        self.toolbar.addAction(self.eraser_action)

    def duplicate(self):
        current_index = self.view.currentIndex()
        self.view.duplicate(current_index)

    def delete(self):
        current_index = self.view.currentIndex()
        if self.deletion_func(self.model, current_index):
            self.view.delete(current_index)

class TileSetMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.current = None

        self.tab_bar = QTabBar(self)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)

        self.view = IconView(self)

        self.create_actions()
        self.create_toolbar()

        layout = QVBoxLayout()
        layout.addWidget(self.tab_bar)
        layout.addWidget(self.view)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

    def on_tab_changed(self, idx):
        tileset_nid = self.current.tilesets[idx]
        self.load_tileset(tileset_nid)

    def tab_clear(self):
        for idx in range(self.tab_bar.count()):
            i = self.tab_bar.count() - idx - 1
            self.tab_bar.removeTab(i)

    def set_current(self, current):
        self.current = current

        self.tab_clear()
        for nid in self.current.tilesets:
            self.tab_bar.addTab(nid)

        if self.current.tilesets:
            self.load_tileset(self.current.tilesets[0])

    def load_tileset(self, tileset_nid):
        tileset = RESOURCES.tilesets.get(tileset_nid)
        if not tileset.pixmap:
            tileset.set_pixmap(QPixmap(tileset.full_path))
        self.view.set_image(tileset.pixmap)
        self.view.show_image()

    def create_actions(self):
        self.new_action = QAction(QIcon("icons/file-plus.png"), "New", triggered=self.new)
        self.delete_action = QAction(QIcon("icons/x-circle.png"), "Delete", triggered=self.delete)

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.delete_action)

    def new(self):
        from app.editor.resource_editor import ResourceEditor
        res, ok = ResourceEditor.get(self, "Tilesets")
        if ok:
            nid = res.nid
            self.current.tilesets.append(nid)
            self.tab_bar.addTab(nid)
            self.load_tileset(nid)

    def delete(self):
        idx = self.tab_bar.currentIndex()
        if idx < len(self.current.tilesets):
            self.current.tilesets.pop(idx)
            self.tab_bar.removeTab(idx)

        new_idx = self.tab_bar.currentIndex()
        self.load_tileset(self.current.tilesets[new_idx])
