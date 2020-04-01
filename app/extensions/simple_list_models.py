from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import Qt, QModelIndex

from app.data.database import DB

from app import utilities

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
        if not self.locked or getattr(self._data[index.row()], self._headers[0]) not in self.locked or index.column() != 0:
            basic_flags |= Qt.ItemIsEditable
        if index.column() in self.checked_columns:
            basic_flags |= Qt.ItemIsUserCheckable
        return basic_flags
