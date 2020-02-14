from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QPushButton, \
    QSizePolicy, QSplitter
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QAbstractListModel

import copy

from app.data.data import Prefab
from app.editor.custom_gui import RightClickListView

from app import utilities

class DatabaseTab(QWidget):
    def __init__(self, data, title, right_frame, deletion_criteria, collection_model, parent, 
                 button_text="Create %s", view_type=RightClickListView):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = data
        self.saved_data = self.save()
        self.title = title

        self.setWindowTitle('%s Editor' % self.title)
        self.setStyleSheet("font: 10pt;")

        self.left_frame = Collection(deletion_criteria, collection_model, self, button_text=button_text, view_type=view_type)
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

    def tick(self):
        pass

    def reset(self):
        """
        Whenever the tab is changed, make sure to update the tab display
        Makes sure that current is what is being displayed
        """
        if self.right_frame.current:
            self.right_frame.set_current(self.right_frame.current)

    def create_new(self):
        raise NotImplementedError

    def after_new(self):
        model = self.left_frame.model
        view = self.left_frame.view
        model.dataChanged.emit(model.index(0), model.index(model.rowCount()))
        last_index = model.index(model.rowCount() - 1)
        view.setCurrentIndex(last_index)

    @classmethod
    def edit(cls, parent=None):
        dialog = cls.create(parent)
        dialog.exec_()

    def save(self):
        return self._data.save()

    def restore(self, data):
        self._data.restore(data)

    def apply(self):
        self.saved_data = self.save()

class Collection(QWidget):
    def __init__(self, deletion_criteria, collection_model, parent,
                 button_text="Create %s", view_type=RightClickListView):
        super().__init__(parent)
        self.window = parent
        self.database_editor = self.window.window

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

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.button = QPushButton(button_text % self.title)
        self.button.clicked.connect(self.window.create_new)

        grid.addWidget(self.view, 0, 0)
        grid.addWidget(self.button, 1, 0)

    def on_item_changed(self, curr, prev):
        if self._data:
            new_data = curr.internalPointer()  # Internal pointer is way too powerful
            if not new_data:
                new_data = self._data[curr.row()]
            if self.display:
                self.display.set_current(new_data)

    def set_display(self, disp):
        self.display = disp
        first_index = self.model.index(0)
        self.view.setCurrentIndex(first_index)

    def update_list(self):
        self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))                

    def create_new(self):
        self.window.create_new()

    def after_new(self):
        self.window.after_new()

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
        new_item = self._data[min(idx, len(self._data) - 1)]
        if self.window.display:
            self.window.display.set_current(new_item)

    def update(self):
        self.dataChanged.emit(self.index(0), self.index(self.rowCount()))

    def new(self, idx):
        collection = self.window
        collection.create_new()
        self._data.move_index(len(self._data) - 1, idx + 1)
        # model.dataChanged.emit(model.index(0), model.index(model.rowCount()))
        self.layoutChanged.emit()

    def duplicate(self, idx):
        obj = self._data[idx]
        new_nid = utilities.get_next_name(obj.nid, self._data.keys())
        if isinstance(obj, Prefab):
            serialized_obj = obj.serialize()
            print("Duplication!")
            print(serialized_obj, flush=True)
            new_obj = self._data.datatype.deserialize(serialized_obj)
        else:
            new_obj = copy.copy(obj)
        new_obj.nid = new_nid
        self._data.insert(idx + 1, new_obj)
        # new_obj = model._data.duplicate(obj.nid, new_nid)
        # model.dataChanged.emit(model.index(0), model.index(model.rowCount()))
        self.layoutChanged.emit()
