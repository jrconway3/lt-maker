from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, \
    QGraphicsView, QGraphicsScene, QMessageBox
from PyQt5.QtCore import Qt, QDir, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QPixmap, QIcon

import os

from app.data.resources import RESOURCES, ImageResource

from app.editor.base_database_gui import DatabaseTab
from app.editor.custom_gui import RightClickTreeView

class Icon16Display(DatabaseTab):
    creation_func = RESOURCES.create_new_16x16_icon
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons16
        title = "16x16 Icon"
        right_frame = Icon16Properties
        collection_model = IconTreeModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=RightClickTreeView)
        return dialog

    def create_new(self):
        starting_path = QDir.currentPath()
        fn, ok = QFileDialog.getOpenFileName(self, "Choose %s", starting_path, "PNG Files (*.png);;All Files(*)")
        if ok:
            if fn.endswith('.png'):
                local_name = os.path.split(fn)[-1]
                pix = QPixmap(fn)
                self.creation_func(local_name, pix)
                self.after_new()

    def save(self):
        # No need to save icons -- resource editor does the job of serializing
        # them to the filesystem
        return None

class Icon32Display(Icon16Display):
    creation_func = RESOURCES.create_new_32x32_icon
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons32
        title = "32x32 Icon"
        right_frame = Icon32Properties
        collection_model = IconTreeModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=RightClickTreeView)
        return dialog

class Icon80Display(Icon16Display):
    creation_func = RESOURCES.create_new_80x72_icon
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons80
        title = "80x72 Icon"
        right_frame = Icon80Properties
        collection_model = IconTreeModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=RightClickTreeView)
        return dialog

class IconTreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        return None

    def index(self, row, column=0, parent_index=QModelIndex()):
        if not self.hasIndex(row, column, parent_index):
            return QModelIndex()
        if parent_index.isValid():
            parent_item = parent_index.internalPointer()
            child_item = parent_item.sub_images[row]
        else:
            child_item = self._data[row]
        
        return self.createIndex(row, column, child_item)

    def parent(self, child_index):
        if not child_index.isValid():
            return QModelIndex()
        child_item = child_index.internalPointer()
        parent_item = child_item.parent_image
        if parent_item:
            row_in_parent = parent_item.sub_images.index(child_item)
            return self.createIndex(row_in_parent, 0, parent_item)
        else:
            return QModelIndex()

    def rowCount(self, parent_index=None):
        if parent_index and parent_index.isValid():
            parent_item = parent_index.internalPointer()
            return len(parent_item.sub_images)
        else:
            return len(self._data)

    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            item = index.internalPointer()
            text = item.nid
            return text
        elif role == Qt.DecorationRole:
            item = index.internalPointer()
            if item.pixmap:
                pixmap = item.pixmap.scaled(32, 32)
                return QIcon(pixmap)
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        return True

    def flags(self, index):
        if index.isValid():
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.NoItemFlags

    def delete(self, index):
        item = index.internalPointer()
        if item.parent_image:
            QMessageBox.critical(self.window, 'Error', "Can't delete child item!")
        else:
            self._data.delete(item)
            self.layoutChanged.emit()
        # new_item = self._data[min(idx, len(self._data) - 1)]
        # if self.window.display:
        #     self.window.display.set_current(new_item)

class IconView(QGraphicsView):
    min_scale = 1
    max_scale = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setMouseTracking(True)

        self.image = None
        self.screen_scale = 1

    def set_image(self, pixmap):
        self.image = pixmap
        self.setSceneRect(0, 0, self.image.width(), self.image.height())

    def clear_scene(self):
        self.scene.clear()

    def show_image(self):
        if self.image:
            self.clear_scene()
            self.scene.addPixmap(self.image)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0 and self.screen_scale < self.max_scale:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.angleDelta().y() < 0 and self.screen_scale > self.min_scale:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)

class Icon16Properties(QWidget):
    width, height = 16, 16

    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window

        # Populate resources
        for resource in self._data:
            resource.pixmap = QPixmap(resource.full_path)

        for resource in list(self._data.values()):
            sheet = resource.pixmap
            width, height = sheet.width(), sheet.height()
            if width == self.width and height == self.height:
                continue
            for x in range(width//self.width):
                for y in range(height//self.height):
                    region = sheet.copy(x*self.width, y*self.height, self.width, self.height)
                    new_nid = resource.nid + " " + str(x) + ',' + str(y)
                    new_image = ImageResource(new_nid, resource.full_path, region)
                    new_image.icon_index = (x, y)
                    resource.sub_images.append(new_image)
                    new_image.parent_image = resource

        self.current = current

        self.view = IconView(self)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.view)

    def set_current(self, current):
        self.current = current
        self.view.set_image(self.current.pixmap)
        self.view.show_image()

class Icon32Properties(Icon16Properties):
    width, height = 32, 32

class Icon80Properties(Icon16Properties):
    width, height = 80, 72
