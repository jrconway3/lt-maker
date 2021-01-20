import copy

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QPushButton, \
    QSizePolicy, QSplitter, QMessageBox
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtCore import QAbstractListModel

from app.utilities.data import Prefab
from app.data import items
from app.extensions.custom_gui import RightClickListView
from app.editor.data_editor import SingleDatabaseEditor

from app.utilities import str_utils


class Collection(QWidget):
    def __init__(self, deletion_criteria, collection_model, parent,
                 button_text="Create %s", view_type=RightClickListView):
        super().__init__(parent)
        self.window = parent

        self._data = self.window._data
        self.title = self.window.title

        self.display = None

        grid = QGridLayout()
        self.setLayout(grid)

        self.view = view_type(deletion_criteria, self)
        self.view.currentChanged = self.on_item_changed

        self.model = collection_model(self._data, self)
        self.view.setModel(self.model)

        self.view.setIconSize(QSize(32, 32))

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.button = QPushButton(button_text % self.title)
        self.button.clicked.connect(self.model.append)

        grid.addWidget(self.view, 0, 0)
        grid.addWidget(self.button, 1, 0)

        if self.window.allow_import_from_lt:
            self.import_button = QPushButton("Import Legacy data file...")
            self.import_button.clicked.connect(self.window.import_data)
            grid.addWidget(self.import_button, 2, 0)

    def on_item_changed(self, curr, prev):
        if self._data:
            new_data = curr.internalPointer()  # Internal pointer is way too powerful
            if not new_data:
                if self._data:
                    new_data = self._data[curr.row()]
                elif self.display:
                    self.display.setEnabled(False)
            if self.display:
                self.display.set_current(new_data)
                self.display.setEnabled(True)

    def set_display(self, disp):
        self.display = disp
        first_index = self.model.index(0)
        self.view.setCurrentIndex(first_index)

    def set_current_row(self, idx):
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)

    def update_list(self):
        self.model.dataChanged.emit(self.model.index(
            0), self.model.index(self.model.rowCount()))


class DatabaseTab(QWidget):
    allow_import_from_lt = False

    def __init__(self, data, title, right_frame, deletion_criteria, collection_model, parent,
                 button_text="Create %s", view_type=RightClickListView, collection_type=Collection):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = data
        self.title = title

        self.setWindowTitle('%s Editor' % self.title)
        self.setStyleSheet("font: 10pt;")

        self.left_frame = collection_type(
            deletion_criteria, collection_model, self, button_text=button_text, view_type=view_type)
        self.right_frame = right_frame(self)
        self.left_frame.set_display(self.right_frame)

        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.left_frame)
        self.splitter.addWidget(self.right_frame)
        self.splitter.setStyleSheet(
            "QSplitter::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: 2px; margin-bottom: 2px; border-radius: 4px;}")

        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)

        self.layout.addWidget(self.splitter)

        # Check this on startup
        self.reset()

    def update_list(self):
        self.left_frame.update_list()

    def tick(self):
        pass

    def reset(self):
        """
        Whenever the tab is changed, make sure to update the tab display
        Makes sure that current is what is being displayed
        """
        if self.right_frame.current:
            self.right_frame.setEnabled(True)
            self.right_frame.set_current(self.right_frame.current)
        else:
            self.right_frame.setEnabled(False)

    def on_tab_close(self):
        pass

    @classmethod
    def edit(cls, parent=None):
        window = SingleDatabaseEditor(cls, parent)
        window.exec_()


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
        # special case for 1-length data
        if len(self._data) == 1:
            QMessageBox.critical(None, "Deletion Error", "Can not delete last object of a kind!")
            return
            
        new_index = 0
        # If deleting the element at the bottom of the list
        if idx == len(self._data) - 1:
            new_index = self.index(idx - 1)
        else:
            new_index = self.index(idx + 1)
        self.window.view.setCurrentIndex(new_index)
        self._data.pop(idx)
        new_index = self.index(min(idx, len(self._data) - 1))
        self.window.view.setCurrentIndex(new_index)
        self.layoutChanged.emit()

    def update(self):
        # self.dataChanged.emit(self.index(0), self.index(self.rowCount()))
        self.layoutChanged.emit()

    def create_new(self):
        raise NotImplementedError

    def append(self):
        new_item = self.create_new()
        if not new_item:
            return
        view = self.window.view
        self.dataChanged.emit(self.index(0), self.index(self.rowCount()))
        self.layoutChanged.emit()
        last_index = self.index(self.rowCount() - 1)
        view.setCurrentIndex(last_index)
        return last_index

    def new(self, idx):
        new_item = self.create_new()
        if not new_item:
            return
        view = self.window.view
        self._data.move_index(len(self._data) - 1, idx + 1)
        self.layoutChanged.emit()
        new_index = self.index(idx + 1)
        view.setCurrentIndex(new_index)
        return new_index

    def duplicate(self, idx):
        view = self.window.view
        obj = self._data[idx]
        new_nid = str_utils.get_next_name(obj.nid, self._data.keys())
        if isinstance(obj, Prefab):
            serialized_obj = obj.save()
            print("Duplication!")
            print(serialized_obj, flush=True)
            new_obj = self._data.datatype.restore(serialized_obj)
        elif isinstance(obj, items.Item):
            serialized_obj = obj.serialize_prefab()
            print("Duplication of Item!")
            new_obj = self._data.datatype.deserialize_prefab(serialized_obj)
        else:
            new_obj = copy.copy(obj)
        new_obj.nid = new_nid
        self._data.insert(idx + 1, new_obj)
        self.layoutChanged.emit()
        new_index = self.index(idx + 1)
        view.setCurrentIndex(new_index)
        return new_index

class DragDropCollectionModel(CollectionModel):
    drop_to = None
    most_recent_dragdrop = None
    drag_drop_finished = pyqtSignal()

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
        self.most_recent_dragdrop = self.do_drag_drop(row)
        self.layoutChanged.emit()
        self.drop_to = None

        old, new = self.most_recent_dragdrop
        view = self.window.view
        new_index = self.index(new)
        view.setCurrentIndex(new_index)
        self.drag_drop_finished.emit()
        return True

    def flags(self, index):
        if not index.isValid() or index.row() >= len(self._data) or index.model() is not self:
            return Qt.ItemIsDropEnabled
        else:
            return Qt.ItemIsDragEnabled | super().flags(index)


class ResourceCollectionModel(DragDropCollectionModel):
    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.EditRole and not self.drop_to:
            print("ResourceCollectionModel setData", value)
            if value:
                item = self._data[index.row()]
                old_nid = item.nid
                nids = [d.nid for d in self._data if d is not item]
                nid = str_utils.get_next_name(value, nids)
                self._data.update_nid(item, nid)
                self.on_nid_changed(old_nid, nid)
        return True

    def flags(self, index):
        flags = super().flags(index)
        if not index.isValid():
            return flags
        return flags | Qt.ItemIsEditable

    def on_nid_changed(self, old_nid, new_nid):
        pass
