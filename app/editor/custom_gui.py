from PyQt5.QtWidgets import QListWidget, QComboBox, QDialog, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton, QListView, QAction, QMenu, QMessageBox, \
    QDialogButtonBox, QGridLayout
from PyQt5.QtCore import Qt

class SimpleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
    @classmethod
    def edit(cls, parent):
        dialog = cls(parent)
        dialog.exec_()

class EditDialog(SimpleDialog):
    def __init__(self, data, parent):
        super().__init__(parent)
        self.main_editor = self.parent().parent()
        self.main_editor.undo_stack.clear()
        self._data = data
        self.saved_data = self.save()

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

    def save(self):
        return self._data.serialize()

    def restore(self, data):
        self._data.restore(data)

    def apply(self):
        self.saved_data = self.save()

    def accept(self):
        super().accept()

    def reject(self):
        self.restore(self.saved_data)
        super().reject()

class SignalList(QListWidget):
    def __init__(self, parent=None, del_func=None):
        super().__init__()
        self.parent = parent
        self.del_func = del_func

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if self.del_func and event.key() == Qt.Key_Delete:
            self.del_func()

class ComboBox(QComboBox):
    def setValue(self, text):
        i = self.findText(text)
        if i >= 0:
            self.setCurrentIndex(i)

class LineSearch(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.line_edit = QLineEdit(self)
        self.line_edit.setReadOnly(True)
        self.search_button = QPushButton('...', self)
        self.search_button.setMaximumWidth(40)
        layout.setSpacing(0)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.search_button)
        self.setLayout(layout)

class RightClickListView(QListView):
    def __init__(self, msg='', parent=None):
        super().__init__(parent)
        self.parent = parent
        self.last_to_delete_msg = msg

        self.uniformItemSizes = True

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customMenuRequested)

    def customMenuRequested(self, pos):
        idx = self.indexAt(pos).row()
        # self.parent().model.selectRow(idx)

        delete_action = QAction("Delete", self, triggered=lambda: self.delete(idx))
        menu = QMenu(self)
        menu.addAction(delete_action)

        menu.popup(self.viewport().mapToGlobal(pos))

    def delete(self, idx):
        if self.parent.model.rowCount() > 1:
            self.parent.model.remove(idx)
        else:
            QMessageBox.critical(self.parent(), 'Error', self.last_to_delete_msg)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.delete(self.currentIndex().row())
