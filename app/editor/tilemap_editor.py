from enum import IntEnum

from PyQt5.QtWidgets import QSplitter, QFrame, QVBoxLayout, QDialogButtonBox, \
    QToolBar, QTabBar, QWidget, QDialog
from PyQt5.QtCore import Qt, QAction
from PyQt5.QtGui import QImage, QPainter, QPixmap, QIcon

from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.resources import RESOURCES

from app.editor.map_view import MapView
from app.editor.icon_display import IconView
from app.editor.resource_editor import ResourceEditor
from app.editor.base_database_gui import ResourceCollectionModel
from app.extensions.custom_gui import ResourceListView

class PaintTool(IntEnum):
    NoTool = 0
    Brush = 1
    Fill = 2
    Eraser = 3

class MapEditorView(MapView):
    min_scale = 0.5
    max_scale = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.resource_editor = self.window

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

    def set_current(self, current):  # Current is a TileMapPrefab
        self.current = current
        self.view.set_current(current)
        self.layer_menu.set_current(current)
        self.tileset_menu.set_current(current)
        self.view.update_view()

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
        self.new_action = QAction(QIcon("icons/new.png"), "New", triggered=lambda: self.view.new(last_index))
        self.duplicate_action = QAction(QIcon("icons/duplicate.png", "Duplicate", triggered=self.duplicate))
        self.delete_action = QAction(QIcon("icons/delete.png", "Delete", triggered=self.delete))

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

    def create_action(self):
        self.new_action = QAction(QIcon("icons/new.png"), "New", triggered=self.new)
        self.delete_action = QAction(QIcon("icons/delete.png"), "Delete", triggered=self.delete)

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.delete_action)

    def new(self):
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
