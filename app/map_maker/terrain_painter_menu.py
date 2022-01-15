from PyQt5.QtWidgets import QGridLayout, QListView, \
    QWidget
from PyQt5.QtCore import QSize

from app.map_maker.terrain_database import DB_terrain

from app.editor.terrain_editor.map_terrain_model import MapTerrainModel

class TerrainPainterMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.map_editor = parent

        grid = QGridLayout()
        self.setLayout(grid)

        self.list_view = QListView(self)

        self.model = MapTerrainModel(DB_terrain, self)
        self.list_view.setModel(self.model)
        self.list_view.setIconSize(QSize(32, 32))

        grid.addWidget(self.list_view, 3, 0, 1, 2)

    def on_visibility_changed(self, state):
        pass

    def set_current_nid(self, nid):
        idx = self.model.index(DB_terrain.index(nid))
        self.list_view.setCurrentIndex(idx)

    def get_current_nid(self):
        index = self.list_view.currentIndex()
        terrain = DB_terrain[index.row()]
        return terrain.nid
