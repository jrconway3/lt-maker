import os

from PyQt5.QtWidgets import QSplitter, QFrame, QVBoxLayout, \
    QToolBar, QDialog, QSpinBox, QAction, \
    QActionGroup, \
    QDesktopWidget, QFileDialog, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from app.extensions.custom_gui import PropertyBox
from app.editor.settings import MainSettingsController

from app.map_maker.resize_dialog import ResizeDialog
from app.map_maker.terrain_painter_menu import TerrainPainterMenu
from app.map_maker.map_editor_view import PaintTool, MapEditorView
from app.map_maker.draw_tilemap import draw_tilemap
from app.map_maker.map_prefab import MapPrefab
import app.map_maker.utilities as map_utils

class MapEditor(QDialog):
    def __init__(self, parent=None, current=None):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Map Maker")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.settings = MainSettingsController()

        desktop = QDesktopWidget()
        main_screen_size = desktop.availableGeometry(desktop.primaryScreen())
        default_size = main_screen_size.width()*0.7, main_screen_size.height()*0.7
        self.resize(*default_size)

        self.current = current
        self.save()
        self.current_tool = PaintTool.NoTool

        self.terrain_painter_menu = TerrainPainterMenu(self)

        self.view = MapEditorView(self)
        self.view.set_current(current)

        self.create_actions()
        self.create_toolbar()

        self.main_splitter = QSplitter(self)
        self.main_splitter.setChildrenCollapsible(False)

        self.autotile_fps_box = PropertyBox("Autotile Speed", QSpinBox, self)
        self.autotile_fps_box.edit.setValue(self.current.autotile_fps)
        self.autotile_fps_box.setMaximumWidth(100)
        self.autotile_fps_box.edit.setAlignment(Qt.AlignRight)
        self.autotile_fps_box.edit.valueChanged.connect(self.autotile_fps_changed)

        self.random_seed_box = PropertyBox("RNG Seed", QSpinBox, self)
        self.random_seed_box.edit.setRange(0, 1023)
        self.random_seed_box.edit.setValue(map_utils.RANDOM_SEED)
        self.random_seed_box.setMaximumWidth(100)
        self.random_seed_box.edit.setAlignment(Qt.AlignRight)
        self.random_seed_box.edit.valueChanged.connect(self.random_seed_changed)

        view_frame = QFrame()
        view_layout = QVBoxLayout()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(self.toolbar)
        toolbar_layout.addWidget(self.autotile_fps_box)
        toolbar_layout.addWidget(self.random_seed_box)
        view_layout.addLayout(toolbar_layout)
        view_layout.addWidget(self.view)
        view_frame.setLayout(view_layout)

        self.main_splitter.addWidget(view_frame)
        self.main_splitter.addWidget(self.terrain_painter_menu)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.main_splitter)

        self.check_brush()

        # Restore Geometry
        geometry = self.settings.component_controller.get_geometry(self._type())
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.component_controller.get_state(self._type())
        if state:
            self.main_splitter.restoreState(state)

        self.view.update_view()

    def create_actions(self):
        theme = self.settings.get_theme()
        if theme == 0:
            icon_folder = 'icons/icons'
        else:
            icon_folder = 'icons/dark_icons'

        paint_group = QActionGroup(self)
        self.brush_action = QAction(QIcon(f"{icon_folder}/brush.png"), "&Brush", self, shortcut="B", triggered=self.set_brush)
        self.brush_action.setCheckable(True)
        paint_group.addAction(self.brush_action)
        self.paint_action = QAction(QIcon(f"{icon_folder}/fill.png"), "&Fill", self, shortcut="F", triggered=self.set_fill)
        self.paint_action.setCheckable(True)
        paint_group.addAction(self.paint_action)
        self.erase_action = QAction(QIcon(f"{icon_folder}/eraser.png"), "&Erase", self, shortcut="E", triggered=self.set_erase)
        self.erase_action.setCheckable(True)
        paint_group.addAction(self.erase_action)
        self.resize_action = QAction(QIcon(f"{icon_folder}/resize.png"), "&Resize", self, shortcut="R", triggered=self.resize_map)

        self.export_as_png_action = QAction(QIcon(f"{icon_folder}/export_as_png.png"), "E&xport Current Image as PNG", self, shortcut="X", triggered=self.export_as_png)

        self.show_gridlines_action = QAction(QIcon(f"{icon_folder}/gridlines.png"), "Show GridLines", self, triggered=self.gridline_toggle)
        self.show_gridlines_action.setCheckable(True)
        self.show_gridlines_action.setChecked(True)

    def void_right_selection(self):
        self.view.right_selection.clear()

    def check_brush(self):
        self.brush_action.setChecked(True)
        self.set_brush(True)

    def set_brush(self, val):
        self.current_tool = PaintTool.Brush

    def set_fill(self, val):
        self.current_tool = PaintTool.Fill

    def set_erase(self, val):
        self.current_tool = PaintTool.Erase

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.brush_action)
        self.toolbar.addAction(self.paint_action)
        self.toolbar.addAction(self.erase_action)
        self.toolbar.addAction(self.resize_action)
        self.toolbar.addAction(self.export_as_png_action)
        self.toolbar.addAction(self.show_gridlines_action)

    def set_current(self, current: MapPrefab):
        self.current = current
        self.view.set_current(current)
        self.autotile_fps_box.edit.setValue(current.autotile_fps)
        self.view.update_view()

    def resize_map(self):
        ResizeDialog.get_new_size(self.current, self)

    def gridline_toggle(self, val):
        self.view.draw_gridlines = val

    def autotile_fps_changed(self, val):
        self.current.autotile_fps = val

    def random_seed_changed(self, val):
        map_utils.RANDOM_SEED = val
        self.current.reset_all()

    def export_as_png(self):
        if self.current:
            image = draw_tilemap(self.current, autotile_fps=0)
            starting_path = self.settings.get_last_open_path()
            fn, ok = QFileDialog.getSaveFileName(
                self, "Export Current Image", starting_path,
                "PNG Files (*.png)")
            if fn and ok:
                image.save(fn)
                parent_dir = os.path.split(fn)[0]
                self.settings.set_last_open_path(parent_dir)

    def update_view(self):
        self.view.update_view()

    def accept(self):
        self.save_geometry()
        super().accept()

    def reject(self):
        self.restore()
        self.save_geometry()
        super().reject()

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)

    def save(self):
        self.saved_data = self.current.save()

    def restore(self):
        self.current.restore_edits(self.saved_data)

    def _type(self):
        return 'map_maker'

    def save_geometry(self):
        self.settings.component_controller.set_geometry(self._type(), self.saveGeometry())
        self.settings.component_controller.set_state(self._type(), self.main_splitter.saveState())

# Testing
# Run "python -m app.map_maker.map_editor" from main directory
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from app import dark_theme
    ap = QApplication(sys.argv)
    ap.setWindowIcon(QIcon('favicon.ico'))
    settings = MainSettingsController()
    theme = settings.get_theme(0)
    dark_theme.set(ap, theme)
    sample_tilemap = MapPrefab('sample')
    map_editor = MapEditor(current=sample_tilemap)
    map_editor.show()
    ap.exec_()
