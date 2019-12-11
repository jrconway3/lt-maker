from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox, \
    QFileDialog, QWidget, QHBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QDir, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QPixmap, QIcon

import os
from collections import OrderedDict

from app.data.resources import RESOURCES, ImageResource

from app.editor.base_database_gui import DatabaseTab
from app.editor.custom_gui import RightClickTreeView

class ResourceEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resource Editor")
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.tab_bar = QTabWidget(self)

        self.grid.addWidget(self.tab_bar, 0, 0, 1, 2)

        self.create_sub_widgets()
        for name, tab in self.tabs.items():
            self.tab_bar.addTab(tab, name)

        self.tab_bar.currentChanged.connect(self.on_tab_changed)

    def create_sub_widgets(self):
        self.tabs = OrderedDict()
        self.tabs['Icons'] = IconDisplay.create()
        # self.tabs['Portraits'] = PortraitDisplay.create()
        # self.tabs['Panoramas'] = PanoramaDisplay.create()
        # self.tabs['Map Sprites'] = MapSpriteDisplay.create()
        # self.tabs['Combat Animations'] = AnimationDisplay.create()
        # self.tabs['Combat Effects'] = CombatEffectDisplay.create()
        # self.tabs['Map Effects'] = MapEffectDisplay.create()
        # self.tabs['Music'] = MusicDisplay.create()
        # self.tabs['SFX'] = SFXDisplay.create()

    def on_tab_changed(self, index):
        new_tab = self.tab_bar.currentWiedget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def accept(self):
        super().accept()

    def reject(self):
        super().reject()

class IconDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons
        title = "Icon"
        right_frame = IconProperties
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
            nid = os.path.split(fn)[-1]
            pix = QPixmap(fn)
            RESOURCES.create_new_icon(nid, pix)
            # self._data.append(icon)
            self.after_new()

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

class IconProperties(QWidget):
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
            if '16x16' in resource.full_path:
                if width == 16 and height == 16:
                    continue
                for x in range(width//16):
                    for y in range(height//16):
                        region = sheet.copy(x*16, y*16, 16, 16)
                        new_nid = resource.nid + str(x) + '_' + str(y)
                        new_image = ImageResource(new_nid, resource.full_path, region)
                        resource.sub_images.append(new_image)
                        new_image.parent_image = resource
                        # self._data.append(new_image)
            if '32x32' in resource.full_path:
                if width == 32 and height == 32:
                    continue
                for x in range(width//32):
                    for y in range(height//32):
                        region = sheet.copy(x*32, y*32, 32, 32)
                        region = sheet
                        new_nid = resource.nid + str(x) + '_' + str(y)
                        new_image = ImageResource(new_nid, resource.full_path, region)
                        resource.sub_images.append(new_image)
                        new_image.parent_image = resource
                        # self._data.append(new_image)

        self.current = current

        self.view = IconView(self)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.view)

    def set_current(self, current):
        self.current = current
        self.view.set_image(self.current.pixmap)
        self.view.show_image()

# Testing
# Run "python -m app.editor.resource_editor" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ResourceEditor()
    window.show()
    app.exec_()
