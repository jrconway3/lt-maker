import copy

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import Qt, QModelIndex

from app.utilities import str_utils
from app.utilities.data import Prefab

from app.data.database import DB

class VirtualListModel(QAbstractItemModel):
    def set_new_data(self, data):
        self._data = data
        self.layoutChanged.emit()

    def index(self, row, column=0, parent_index=QModelIndex()):
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
        self._data.pop(idx)
        self.layoutChanged.emit()

    def append(self):
        new_row = str_utils.get_next_name("New %s" % self.title, self._data)
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
        self._data[index.row()] = value
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren | Qt.ItemIsEditable
        return basic_flags

class MultiAttrListModel(VirtualListModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self._headers = headers

        self.edit_locked = set()
        self.checked_columns = set()
        self.nid_column = -1  # What column the nid is on

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
        self.change_watchers(data, attr, current_value, value)
        setattr(data, attr, value)
        self.dataChanged.emit(index, index)
        return True

    def change_watchers(self, data, attr, old_value, new_value):
        pass

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren
        if not self.edit_locked or getattr(self._data[index.row()], self._headers[0]) not in self.edit_locked or index.column() != 0:
            basic_flags |= Qt.ItemIsEditable
        if index.column() in self.checked_columns:
            basic_flags |= Qt.ItemIsUserCheckable
        return basic_flags

    def delete(self, idx):
        if not self.edit_locked or getattr(self._data[idx], self._headers[0]) not in self.edit_locked:
            self._data.pop(idx)
            self.layoutChanged.emit()
        else:
            QMessageBox.critical(self.window, 'Error', "Cannot delete this row!")

    def create_new(self):
        raise NotImplementedError

    def append(self):
        self.create_new()
        self.layoutChanged.emit()
        last_index = self.index(self.rowCount() - 1, 0)
        self.window.view.setCurrentIndex(last_index)
        self.update_watchers(self.rowCount() - 1)
        return last_index

    def new(self, idx):
        self.create_new()
        self._data.move_index(len(self._data) - 1, idx + 1)
        self.layoutChanged.emit()

        self.update_watchers(idx + 1)

    def duplicate(self, idx):
        obj = self._data[idx]
        if hasattr(obj, 'nid'):
            new_nid = str_utils.get_next_name(obj.nid, self._data.keys())
            if isinstance(obj, Prefab):
                serialized_obj = obj.save()
                print("Duplication!")
                print(serialized_obj, flush=True)
                new_obj = self._data.datatype.restore(serialized_obj)
            else:
                new_obj = copy.copy(obj)
            new_obj.nid = new_nid
        else:
            new_obj = copy.copy(obj)

        self._data.insert(idx + 1, new_obj)
        self.layoutChanged.emit()

        self.update_watchers(idx + 1)

    def update_watchers(self, idx):
        pass

class DragDropMultiAttrListModel(MultiAttrListModel):
    drop_to = None

    def supportedDropActions(self):
        return Qt.MoveAction

    def supportedDragActions(self):
        return Qt.MoveAction

    def insertRows(self, row, count, parent):
        if count < 1 or row < 0 or row > self.rowCount() or parent.isValid():
            return False
        self.drop_to = row
        self.layoutChanged.emit()
        return True

    def do_drag_drop(self, index):
        if self.drop_to is None:
            return False
        if index < self.drop_to:
            self._data.move_index(index, self.drop_to - 1)
            return index, self.drop_to - 1
        else:
            self._data.move_index(index, self.drop_to)
            return index, self.drop_to

    def removeRows(self, row, count, parent):
        if count < 1 or row < 0 or (row + count) > self.rowCount() or parent.isValid():
            return False
        result = self.do_drag_drop(row)
        self.layoutChanged.emit()
        if result:
            self.update_drag_watchers(result[0], result[1])
        return True

    def update_drag_watchers(self, fro, to):
        pass

    def flags(self, index):
        if not index.isValid() or index.row() >= len(self._data) or index.model() is not self:
            return Qt.ItemIsDropEnabled
        else:
            return Qt.ItemIsDragEnabled | super().flags(index)

class DefaultMultiAttrListModel(MultiAttrListModel):
    def change_watchers(self, data, attr, old_value, new_value):
        if attr in self._headers and self._headers.index(attr) == self.nid_column:
            new_value = str_utils.get_next_name(new_value, [d.nid for d in self._data])
            self._data.update_nid(data, new_value)

    def create_new(self):
        self._data.add_new_default(DB)
