from PyQt5.QtWidgets import QGridLayout, QPushButton, QSlider, QLabel, QListView, \
    QWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap


from app.data.database import DB

from app.editor.resource_editor import ResourceEditor
from app.editor.database_editor import DatabaseEditor
from app.editor.terrain_database import TerrainModel
from app.editor import commands

class TerrainPainterMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_editor = parent

        grid = QGridLayout()
        self.setLayout(grid)

        self.import_button = QPushButton('Select New Map...')
        self.import_button.clicked.connect(self.import_new_map)
        grid.addWidget(self.import_button, 0, 0, 1, 2)

        self.alpha_slider = QSlider(Qt.Horizontal, self)
        self.alpha_slider.setRange(0, 255)
        self.alpha_slider.setValue(192)
        grid.addWidget(QLabel("Transparency"), 1, 0)
        grid.addWidget(self.alpha_slider, 1, 1)
        self.alpha_slider.valueChanged.connect(self.main_editor.update_view)

        self.list_view = QListView(self)
        self.list_view.currentChanged = self.on_item_changed

        self.model = TerrainModel(DB.terrain, self)
        self.list_view.setModel(self.model)
        self.list_view.setIconSize(QSize(32, 32))

        grid.addWidget(self.list_view, 3, 0, 1, 2)

        self.reset_button = QPushButton('Reset Terrain')
        self.reset_button.clicked.connect(self.reset_terrain)
        self.edit_button = QPushButton('Edit Terrain...')
        self.edit_button.clicked.connect(self.edit_terrain)
        grid.addWidget(self.reset_button, 4, 0)
        grid.addWidget(self.edit_button, 4, 1)

    def on_visibility_changed(self, state):
        pass

    def tilemap(self):
        return self.main_editor.current_level.tilemap

    def get_alpha(self):
        return int(self.alpha_slider.value())

    def import_new_map(self):
        res, ok = ResourceEditor.get(self.main_editor, "Maps")
        if ok:
            nid = res.nid
            if not res.pixmap:
                res.pixmap = QPixmap(res.full_path)
            self.main_editor.current_level.tilemap.change_image(nid, res.pixmap.width(), res.pixmap.height())
            self.main_editor.update_view()

    def on_item_changed(self, curr, prev):
        pass

    def reset_terrain(self):
        command = commands.ResetTerrain(self.main_editor.current_level)
        self.main_editor.undo_stack.push(command)
        self.main_editor.update_view()

    def edit_terrain(self):
        dialog = DatabaseEditor(self.main_editor, "Terrain")
        dialog.exec_()
        self.main_editor.update_view()

    def paint_tile(self, pos):
        current_terrain = DB.terrain[self.list_view.currentIndex().row()]
        command = commands.ChangeTileTerrain(self.main_editor.current_level, pos, current_terrain.nid)
        if command.makes_change():
            self.main_editor.undo_stack.push(command)
            self.main_editor.update_view()

    def set_current_nid(self, nid):
        idx = self.model.index(DB.terrain.index(nid))
        self.list_view.setCurrentIndex(idx)
