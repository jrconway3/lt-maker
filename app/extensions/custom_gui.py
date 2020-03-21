from PyQt5.QtWidgets import QSpinBox, QComboBox, QDialog, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton, QAction, QMenu, QMessageBox, QSizePolicy, QFrame, \
    QDialogButtonBox, QGridLayout, QListView, QTreeView, QItemDelegate, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QSize

class SimpleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
    @classmethod
    def edit(cls, parent):
        dialog = cls(parent)
        dialog.exec_()

class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

class DeletionDialog(Dialog):
    def __init__(self, affected_items, model, msg, box, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Deletion Warning")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.model = model(affected_items, parent)
        self.view = QListView(self)
        self.view.setModel(self.model)
        self.view.setSelectionMode(0)  # No selection
        self.view.setIconSize(QSize(32, 32))

        self.text1 = QLabel(msg)
        self.text2 = QLabel("Swap these references to:")
        self.box = box

        self.layout.addWidget(self.text1)
        self.layout.addWidget(self.view)
        self.layout.addWidget(self.text2)
        self.layout.addWidget(self.box)
        self.layout.addWidget(self.buttonbox)

    @staticmethod
    def get_swap(affected_items, model, msg, box, parent=None):
        dialog = DeletionDialog(affected_items, model, msg, box, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            idx = dialog.box.edit.currentIndex()
            return dialog.box.model._data[idx], True
        else:
            return None, False

    @staticmethod
    def get_simple_swap(affected_items, model, msg, box, parent=None):
        dialog = DeletionDialog(affected_items, model, msg, box, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            idx = dialog.box.edit.currentIndex()
            return idx, True
        else:
            return None, False

class EditDialog(SimpleDialog):
    def __init__(self, data, parent):
        super().__init__(parent)
        if self.parent():
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

class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(1)

class QVLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(1)

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

class PropertyBox(QWidget):
    def __init__(self, label, widget, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label, self)
        self.label.setAlignment(Qt.AlignBottom)
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.edit = widget(self)
        self.edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.bottom_section = QHBoxLayout()
        self.bottom_section.addWidget(self.edit)

        layout.addWidget(self.label)
        layout.addLayout(self.bottom_section)

    def add_button(self, button):
        self.button = button
        self.bottom_section.addWidget(self.button)

class PropertyCheckBox(QWidget):
    def __init__(self, label, widget, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(label, self)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.edit = widget(self)
        self.edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout.addWidget(self.edit)
        layout.addWidget(self.label)
        layout.setAlignment(self.label, Qt.AlignLeft)

class RightClickView(object):
    def __init__(self, deletion_criteria=None, parent=None):
        super().__init__(parent)
        self.window = parent

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(4)  # QAbstractItemView.InternalMove

        if deletion_criteria:
            self.deletion_func, self.deletion_msg = deletion_criteria
        else:
            self.deletion_func, self.deletion_msg = None, "This shouldn't happen"
        print(self.deletion_func, flush=True)
        print(self.deletion_msg, flush=True)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customMenuRequested)

    def customMenuRequested(self, pos):
        index = self.indexAt(pos)

        new_action = QAction("New", self, triggered=lambda: self.new(index.row()))
        duplicate_action = QAction("Duplicate", self, triggered=lambda: self.duplicate(index.row()))
        delete_action = QAction("Delete", self, triggered=lambda: self.delete(index.row()))
        menu = QMenu(self)
        menu.addAction(new_action)
        menu.addAction(duplicate_action)
        menu.addAction(delete_action)

        menu.popup(self.viewport().mapToGlobal(pos))

    def new(self, idx):
        self.window.model.new(idx)
        self.window.view.setCurrentIndex(self.window.model.index(idx, 0))

    def duplicate(self, idx):
        self.window.model.duplicate(idx)
        view = self.window.view
        view.setCurrentIndex(self.window.model.index(idx + 1, 0))

    def delete(self, idx):
        if not self.deletion_func or self.deletion_func(self, idx):
            self.window.model.delete(idx)
        else:
            QMessageBox.critical(self.window, 'Error', self.deletion_msg)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.delete(self.currentIndex().row())

class RightClickTreeView(RightClickView, QTreeView):
    pass

class RightClickListView(RightClickView, QListView):
    pass

class IntDelegate(QItemDelegate):
    def __init__(self, parent, int_columns):
        super().__init__(parent)
        self.int_columns = int_columns

    def createEditor(self, parent, option, index):
        if index.column() in self.int_columns:
            editor = QSpinBox(parent)
            editor.setAlignment(Qt.AlignRight)
            editor.setRange(-1023, 1023)
            return editor
        else:
            return super().createEditor(parent, option, index)
