from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QPushButton, \
    QListView, QAction, QMenu, QMessageBox, QSizePolicy, QSplitter
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtCore import QAbstractListModel

from app import utilities

class DatabaseTab(QWidget):
    def __init__(self, data, title, right_frame, deletion_msg, creation_func, collection_model, parent):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.saved_data = self.save()
        self.title = title

        self.setWindowTitle('%s Editor' % self.title)
        self.setStyleSheet("font: 10pt;")

        self.left_frame = Collection(deletion_msg, creation_func, collection_model, self)
        self.right_frame = right_frame(self)
        self.left_frame.set_display(self.right_frame)

        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.left_frame)
        self.splitter.addWidget(self.right_frame)
        self.splitter.setStyleSheet("QSplitter::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: 2px; margin-bottom: 2px; border-radius: 4px;}")

        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)

        self.layout.addWidget(self.splitter)

    def update_list(self):
        self.left_frame.update_list()

    def reset(self):
        """
        Whenever the tab is changed, make sure to update the tab display
        Makes sure that current is what is being displayed
        """
        if self.right_frame.current:
            self.right_frame.set_current(self.right_frame.current)

    @classmethod
    def edit(cls, parent=None):
        dialog = cls.create(parent)
        dialog.exec_()

    def save(self):
        return self._data.serialize()

    def restore(self, data):
        self._data.restore(data)

    def apply(self):
        self.saved_data = self.save()

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

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.button = QPushButton("Create %s" % self.title)
        self.button.clicked.connect(self.create_new)

        grid.addWidget(self.view, 0, 0)
        grid.addWidget(self.button, 1, 0)

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = utilities.get_next_name("New " + self.title, nids)
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
