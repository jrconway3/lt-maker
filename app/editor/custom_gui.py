from PyQt5.QtWidgets import QSpinBox, QComboBox, QDialog, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton, QAction, QMenu, QMessageBox, QSizePolicy, QFrame, \
    QDialogButtonBox, QGridLayout, QListView, QTreeView, QItemDelegate, QLabel, QVBoxLayout
from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import Qt, QModelIndex, QTimer

from app.data.database import DB

from app import utilities

def give_timer(obj, fps=30):
    obj.main_timer = QTimer()
    obj.main_timer.timeout.connect(obj.tick)
    timer_speed = int(1000/float(fps))
    obj.main_timer.setInterval(timer_speed)
    obj.main_timer.start()

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
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.model = model(affected_items, self)
        self.view = QListView(self)
        self.view.setModel(self.model)
        self.view.setSelectionMode(0)  # No selection

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
        dialog.setWindowTitle("Deletion Warning")
        result = dialog.exec_()
        if result == QDialog.Accepted:
            idx = dialog.box.edit.currentIndex()
            return dialog.model._data[idx], True
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

class RightClickTreeView(QTreeView):
    def __init__(self, deletion_criteria=None, parent=None):
        super().__init__(parent)
        self.window = parent

        if deletion_criteria:
            self.deletion_func, self.deletion_msg = deletion_criteria
        else:
            self.deletion_func, self.deletion_msg = None, "This shouldn't happen"
        print(self.deletion_func, flush=True)
        print(self.deletion_msg, flush=True)
        self.uniformItemSizes = True

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customMenuRequested)

    def customMenuRequested(self, pos):
        index = self.indexAt(pos)

        delete_action = QAction("Delete", self, triggered=lambda: self.delete(index))
        menu = QMenu(self)
        menu.addAction(delete_action)

        menu.popup(self.viewport().mapToGlobal(pos))

    def delete(self, index):
        if not self.deletion_func or self.deletion_func(self, index):
            self.window.model.delete(index)
        else:
            QMessageBox.critical(self.window, 'Error', self.deletion_msg)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.delete(self.currentIndex().row())

class RightClickListView(QListView):
    def __init__(self, deletion_criteria=None, parent=None):
        super().__init__(parent)
        self.window = parent

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
        self.window.view.setCurrentIndex(self.window.model.index(idx))

    def duplicate(self, idx):
        self.window.model.duplicate(idx)
        view = self.window.view
        view.setCurrentIndex(self.window.model.index(idx + 1))

    def delete(self, idx):
        if not self.deletion_func or self.deletion_func(self, idx):
            self.window.model.delete(idx)
        else:
            QMessageBox.critical(self.window, 'Error', self.deletion_msg)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.delete(self.currentIndex().row())

class IntDelegate(QItemDelegate):
    def __init__(self, parent, int_columns):
        super().__init__(parent)
        self.int_columns = int_columns

    def createEditor(self, parent, option, index):
        if index.column() in self.int_columns:
            editor = QSpinBox(parent)
            editor.setAlignment(Qt.AlignRight)
            editor.setRange(-255, 255)
            return editor
        else:
            return super().createEditor(parent, option, index)

# === LIST DIALOGS ===========================================================
class SingleListDialog(QDialog):
    def __init__(self, data, title, parent=None):
        super().__init__(parent)
        self.initiate(data, title, parent)

        self.model = SingleListModel(self._data, title, self)
        self.view = RightClickListView(parent=self)
        self.view.setModel(self.model)

        self.placement(title)

    def initiate(self, data, title, parent):
        self.window = parent
        self._data = data

        self.setWindowTitle("%s Editor" % title)
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.saved_data = self.save()
        self._actions = []

    def placement(self, title):
        layout = QGridLayout(self)
        layout.addWidget(self.view, 0, 0, 1, 2)
        self.setLayout(layout)

        self.add_button = QPushButton("Add %s" % title)
        self.add_button.clicked.connect(self.model.add_new_row)
        layout.addWidget(self.add_button, 1, 0, alignment=Qt.AlignLeft)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        layout.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

    def save(self):
        return self._data

    def restore(self, data):
        self._data = data

    def accept(self):
        super().accept()

    def reject(self):
        self.restore(self.saved_data)
        super().reject()

class MultiAttrListDialog(SingleListDialog):
    def __init__(self, data, title, attrs, locked=None, parent=None):
        QDialog.__init__(self, parent)
        self.initiate(data, title, parent)

        self.model = MultiAttrListModel(self._data, attrs, locked, self)
        self.view = RightClickTreeView(parent=self)
        self.view.setModel(self.model)
        int_columns = [i for i, attr in enumerate(attrs) if type(getattr(self._data[0], attr)) == int]
        delegate = IntDelegate(self.view, int_columns)
        self.view.setItemDelegate(delegate)
        for col in range(len(attrs)):
            self.view.resizeColumnToContents(col)

        self.placement(title)

    def save(self):
        return self._data.save()

    def restore(self, data):
        self._data.restore(data)

    def accept(self):
        for action in self._actions:
            kind = action[0]
            if kind == 'Delete':
                self.on_delete(action[1])
            elif kind == 'Change':
                self.on_change(*action[1])
            elif kind == 'Append':
                self.on_append(action[1])
        super().accept()

# === LIST MODELS ============================================================
class VirtualListModel(QAbstractItemModel):
    def set_new_data(self, data):
        self._data = data
        self.layoutChanged.emit()

    def index(self, row, column, parent_index=QModelIndex()):
        if self.hasIndex(row, column, parent_index):
            return self.createIndex(row, column)
        return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        pass

    def data(self, index, role):
        pass

    def setData(self, index, value, role):
        pass

    def flags(self, index):
        pass

class SingleListModel(VirtualListModel):
    def __init__(self, data, title, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.title = title
        self._headers = [title]

    def delete(self, idx):
        self.window._actions.append(('Delete', self._data[idx]))
        self._data.pop(idx)
        self.layoutChanged.emit()

    def add_new_row(self):
        new_row = utilities.get_next_name("New %s" % self.title, self._data)
        self.window._actions.append(('Append', new_row))
        self._data.append(new_row)
        self.layoutChanged.emit()
        last_index = self.index(self.rowCount() - 1, 0)
        self.window.view.setCurrentIndex(last_index)

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return None
        elif orientation == Qt.Horizontal:
            return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._data[index.row()]
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        self.window._actions.append(('Change', self._data[index.row()], value))
        self._data[index.row()] = value
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren | Qt.ItemIsEditable
        return basic_flags

class MultiAttrListModel(VirtualListModel):
    def __init__(self, data, headers, locked=None, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self._headers = headers
        assert (isinstance(self._headers, list) or isinstance(self._headers, tuple))
        self.locked = locked
        if not locked:
            self.locked = set()
        self.checked_columns = set()

    def delete(self, idx):
        if getattr(self._data[idx], self._headers[0]) not in self.locked:
            self.window._actions.append(('Delete', self._data[idx]))
            self._data.pop(idx)
            self.layoutChanged.emit()
        else:
            QMessageBox.critical(self.window, 'Error', "Cannot delete this row!")

    def add_new_row(self):
        new = self._data.add_new_default(DB)
        self.window._actions.append(('Append', new))
        self.layoutChanged.emit()
        last_index = self.index(self.rowCount() - 1, 0)
        self.window.view.setCurrentIndex(last_index)

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return None
        elif orientation == Qt.Horizontal:
            return self._headers[idx].replace('_', ' ').capitalize()

    def data(self, index, role):
        if not index.isValid():
            return None
        if index.column() in self.checked_columns:
            if role == Qt.CheckStateRole:
                data = self._data[index.row()]
                attr = self._headers[index.column()]
                val = getattr(data, attr)
                return Qt.Checked if bool(val) else Qt.Unchecked
            else:
                return None
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            data = self._data[index.row()]
            attr = self._headers[index.column()]
            return getattr(data, attr)
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        data = self._data[index.row()]
        attr = self._headers[index.column()]
        current_value = getattr(data, attr)
        setattr(data, attr, value)
        self.window._actions.append(('Change', data, attr, current_value, value))
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren
        if getattr(self._data[index.row()], self._headers[0]) not in self.locked or index.column() != 0:
            basic_flags |= Qt.ItemIsEditable
        if index.column() in self.checked_columns:
            basic_flags |= Qt.ItemIsUserCheckable
        return basic_flags
