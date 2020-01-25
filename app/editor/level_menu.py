from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import Qt, QAbstractListModel

from app.data.database import DB
from app.data.levels import Level

from app.editor import commands
from app.editor.custom_gui import RightClickListView
import app.utilities as utilities

class LevelDatabase(QWidget):
    def __init__(self, window=None):
        super().__init__(window)
        self.main_editor = window

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        def deletion_func(view, idx):
            return len(DB.levels) > 1

        deletion_criteria = (deletion_func, 'Must have at least one level in project!')
        self.list_view = RightClickListView(deletion_criteria, self)
        self.list_view.setMinimumSize(128, 320)
        self.list_view.currentChanged = self.on_level_changed

        self.model = LevelModel(self)
        self.list_view.setModel(self.model)

        self.button = QPushButton("Create New Level...")
        self.button.clicked.connect(self.create_new)

        self.grid.addWidget(self.list_view, 0, 0)
        self.grid.addWidget(self.button, 1, 0)

    def create_new(self):
        nids = [l.nid for l in DB.levels]
        nid = str(utilities.get_next_int("0", nids))
        name = "Chapter %s" % nid

        new_level_command = commands.CreateNewLevel(nid, name)
        self.main_editor.undo_stack.push(new_level_command)

        self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))
        last_index = self.model.index(self.model.rowCount() - 1)
        self.list_view.setCurrentIndex(last_index)
        self.main_editor.update_view()

    def on_level_changed(self, curr, prev):
        if DB.levels:
            new_level = DB.levels[curr.row()]
            self.main_editor.set_current_level(new_level)

    def create_initial_level(self):
        nids = [l.nid for l in DB.levels]
        new_nid = str(utilities.get_next_int("0", nids))
        DB.levels.append(Level(new_nid, 'Prologue'))
        self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))
        first_index = self.model.index(0)
        self.list_view.setCurrentIndex(first_index)

    def update_view(self):
        self.model.layoutChanged.emit()
        # self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))

class LevelModel(QAbstractListModel):
    def __init__(self, window=None):
        super().__init__(window)
        self._data = DB.levels

    def rowCount(self, parent=None):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            level = self._data[index.row()]
            text = level.nid + " : " + level.title
            return text
        return None 

    def delete(self, idx):
        self._data.pop(idx)
        self.layoutChanged.emit()
        new_level = self._data[min(idx, len(self._data) - 1)]
        self.parent().main_editor.set_current_level(new_level)
