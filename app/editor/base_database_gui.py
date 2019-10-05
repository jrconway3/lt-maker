from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QDialog, QFormLayout, \
    QLineEdit, QDialogButtonBox, QLabel, QListView, QAction, QMenu, QMessageBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtCore import QAbstractListModel

from app.editor.custom_gui import EditDialog

class DatabaseDialog(EditDialog):
    def __init__(self, data, title, right_frame, deletion_msg, creation_func, collection_model, parent):
        super().__init__(data, parent)
        self.window = parent
        self.title = title

        self.setWindowTitle('%s Editor' % self.title)

        self.left_frame = Collection(deletion_msg, creation_func, collection_model, self)
        self.right_frame = right_frame(self)
        self.left_frame.set_display(self.right_frame)

        self.grid.addWidget(self.left_frame, 0, 0)
        self.grid.addWidget(self.right_frame, 0, 1)

    def update_list(self):
        self.left_frame.update_list()

    @classmethod
    def edit(cls, parent=None):
        dialog = cls.create(parent)
        dialog.exec_()

class Collection(QWidget):
    def __init__(self, deletion_msg, creation_func, collection_model, parent):
        super().__init__(parent)
        self.window = parent
        self.database_editor = self.window.window

        self._data = self.window._data
        self.title = self.window.title
        self.creation_func = creation_func
        
        self.display = None

        grid = QGridLayout()
        self.setLayout(grid)

        self.view = RightClickListView(deletion_msg, self)
        self.view.currentChanged = self.on_item_changed

        self.model = collection_model(self._data, self)
        self.view.setModel(self.model)

        self.view.setIconSize(QSize(32, 32))

        self.button = QPushButton("Create %s" % self.title)
        self.button.clicked.connect(self.create_new)

        grid.addWidget(self.view, 0, 0)
        grid.addWidget(self.button, 1, 0)

    def create_new(self):
        dialog = CreateNewDialog(self.title, self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            nid, name = dialog.get_results()
            self.creation_func(nid, name)
            self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))
            last_index = self.model.index(self.model.rowCount() - 1)
            self.view.setCurrentIndex(last_index)

    def on_item_changed(self, curr, prev):
        if self._data:
            new_data = self._data[curr.row()]
            if self.display:
                self.display.set_current(new_data)

    def set_display(self, disp):
        self.display = disp
        first_index = self.model.index(0)
        self.view.setCurrentIndex(first_index)

    def update_list(self):
        self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))                

class CollectionModel(QAbstractListModel):
    def __init__(self, data, window):
        super().__init__(window)
        self._data = data
        self.window = window

    def rowCount(self, parent=None):
        return len(self._data)

    def data(self, index, role):
        raise NotImplementedError

    def delete(self, idx):
        self._data.pop(idx)
        self.layoutChanged.emit()
        new_weapon = self._data[min(idx, len(self._data) - 1)]
        if self.window.display:
            self.window.display.set_current(new_weapon)

class RightClickListView(QListView):
    def __init__(self, msg, parent):
        super().__init__(parent)
        self.window = parent
        self.last_to_delete_msg = msg

        self.uniformItemSizes = True

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customMenuRequested)

    def customMenuRequested(self, pos):
        idx = self.indexAt(pos).row()

        delete_action = QAction("Delete", self, triggered=lambda: self.delete(idx))
        menu = QMenu(self)
        menu.addAction(delete_action)

        menu.popup(self.viewport().mapToGlobal(pos))

    def delete(self, idx):
        if self.window.model.rowCount() > 1 and self.window._data[idx].nid != 'Default':
            self.window.model.delete(idx)
        else:
            QMessageBox.critical(self.window, 'Error', self.last_to_delete_msg)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.delete(self.currentIndex().row())

class CreateNewDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.title = title
        self.menu = parent
        self.setWindowTitle("Create New %s..." % self.title)

        self.form = QFormLayout(self)
        self.name = QLineEdit(self)
        self.nid = QLineEdit(self)
        self.nid.textChanged.connect(self.nid_changed)
        self.warning_message = QLabel('')
        self.warning_message.setStyleSheet("QLabel { color : red; }")
        self.form.addRow('Display Name: ', self.name)
        self.form.addRow('Internal ID: ', self.nid)
        self.form.addRow(self.warning_message)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.form.addRow(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        # No level id set
        accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
        accept_button.setEnabled(False)
        self.warning_message.setText('No %s ID set.' % self.title)

    def nid_changed(self, text):
        if text in self.menu._data.keys():
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(False)
            self.warning_message.setText('%s ID is already in use.' % self.title)
        elif text:
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(True)
            self.warning_message.setText('')
        else:
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(False)
            self.warning_message.setText('No %s ID set.' % self.title)

    def get_results(self):
        name = self.name.text()
        nid = self.nid.text()
        return nid, name
