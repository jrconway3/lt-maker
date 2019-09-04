from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QDialog, QLabel, \
    QFormLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt

from app.data.database import DB
from app.data.level import Level

from app.editor import commands
from app.editor.custom_gui import RightClickListView

class LevelListModel(QStandardItemModel):
    def __init__(self, window=None):
        super().__init__(window)
        self.level_list = DB.level_list
        for level in self.level_list:
            item = QStandardItem(level.nid + ' : ' + level.title)
            self.appendRow(item)

    def insert(self, idx, level):
        self.level_list.insert(idx, level)
        item = QStandardItem(level.nid + ' : ' + level.title)
        self.insertRow(idx, item)
        return self.indexFromItem(item)

    def remove(self, idx, level):
        self.level_list.remove(level)
        self.takeRow(idx)

    def delete(self, idx):
        del self.level_list[idx]
        self.takeRow(idx)

    def get_index_from_item(self, level):
        return self.level_list.index(level)

    def get_item_from_qindex(self, model_index):
        row = model_index.row()
        if row >= 0:
            return self.level_list[row]
        else:
            return None

class LevelMenu(QWidget):
    def __init__(self, window=None):
        super().__init__(window)
        self.main_editor = window

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.listview = RightClickListView('Must have at least one level in project!', self)
        self.listview.setMinimumSize(128, 320)
        self.listview.currentChanged = self.on_level_changed

        self.model = LevelListModel(self)
        self.listview.setModel(self.model)

        self.button = QPushButton("Create New Level...")
        self.button.clicked.connect(self.create_new_level_dialog)

        self.grid.addWidget(self.listview, 0, 0)
        self.grid.addWidget(self.button, 1, 0)

    def on_level_changed(self, curr, prev):
        level = self.model.get_item_from_qindex(curr)
        if level:
            self.main_editor.set_current_level(level)

    def create_new_level_dialog(self):
        dialog = NewLevelDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_level_command = dialog.get_command()
            self.main_editor.undo_stack.push(new_level_command)
            self.main_editor.update_view()

    def create_initial_level(self):
        model_index = self.model.insert(0, Level('0', 'Prologue'))
        self.listview.setCurrentIndex(model_index)

class NewLevelDialog(QDialog):
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
        if text in [level.nid for level in DB.level_list]:
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
        return commands.CreateNewLevel(title, nid, self.level_menu)
