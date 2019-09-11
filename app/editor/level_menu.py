from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QDialog, QLabel, \
    QFormLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtCore import Qt, QAbstractListModel

from app.data.database import DB
from app.data.level import Level

from app.editor import commands
from app.editor.custom_gui import RightClickListView, SimpleDialog

class LevelDatabase(QWidget):
    def __init__(self, window=None):
        super().__init__(window)
        self.main_editor = window

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.list_view = RightClickListView('Must have at least one level in project!', self)
        self.list_view.setMinimumSize(128, 320)
        self.list_view.currentChanged = self.on_level_changed

        self.model = LevelModel(self)
        self.list_view.setModel(self.model)

        self.button = QPushButton("Create New Level...")
        self.button.clicked.connect(self.create_new_level)

        self.grid.addWidget(self.list_view, 0, 0)
        self.grid.addWidget(self.button, 1, 0)

    def create_new_level(self):
        dialog = NewLevelDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_level_command = dialog.get_command()
            self.main_editor.undo_stack.push(new_level_command)
            self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))
            last_index = self.model.index(self.model.rowCount() - 1)
            self.list_view.setCurrentIndex(last_index)
            self.main_editor.update_view()

    def on_level_changed(self, curr, prev):
        if DB.levels:
            new_level = DB.levels.values()[curr.row()]
            self.main_editor.set_current_level(new_level)

    def create_initial_level(self):
        DB.levels.append(Level('0', 'Prologue'))
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
            level = self._data.values()[index.row()]
            text = level.nid + " : " + level.title
            return text
        return None 

    def delete(self, idx):
        self._data.pop(idx)
        self.layoutChanged.emit()
        new_level = self._data.values()[max(idx, len(self._data) - 1)]
        self.parent().main_editor.set_current_level(new_level)

class NewLevelDialog(SimpleDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.level_menu = parent
        self.setWindowTitle("Create New Level...")

        self.form = QFormLayout(self)
        self.level_name = QLineEdit(self)
        self.level_id = QLineEdit(self)
        self.level_id.textChanged.connect(self.level_id_changed)
        self.warning_message = QLabel('')
        self.warning_message.setStyleSheet("QLabel { color : red; }")
        self.form.addRow('Full Title: ', self.level_name)
        self.form.addRow('Internal ID: ', self.level_id)
        self.form.addRow(self.warning_message)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.form.addRow(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        # No level id set
        accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
        accept_button.setEnabled(False)
        self.warning_message.setText('No Level ID set.')

    def level_id_changed(self, text):
        if text in [level.nid for level in DB.levels]:
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(False)
            self.warning_message.setText('Level ID is already in use.')
        elif text:
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(True)
            self.warning_message.setText('')
        else:
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(False)
            self.warning_message.setText('No Level ID set.')

    def get_command(self):
        title = self.level_name.text()
        nid = self.level_id.text()
        return commands.CreateNewLevel(title, nid)
