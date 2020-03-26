from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QDir
from PyQt5.QtGui import QPixmap

import os

from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.resources import RESOURCES

from app.editor.base_database_gui import DatabaseTab
from app.extensions.custom_gui import ResourceTreeView
from app.editor.icon_display import IconTreeModel, IconView

class MapDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.maps
        title = "Maps"
        right_frame = MapProperties
        collection_model = MapTreeModel

        def deletion_func(view, idx):
            return view.window._data[idx].nid != "default"
        
        deletion_criteria = (deletion_func, "Cannot delete default map")
        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceTreeView)
        return dialog

class MapTreeModel(IconTreeModel):
    def create_new(self):
        starting_path = QDir.currentPath()
        fn, ok = QFileDialog.getOpenFileName(self.window, "Choose %s", starting_path, "PNG Files (*.png);;All Files(*)")
        if ok:
            if fn.endswith('.png'):
                local_name = os.path.split(fn)[-1]
                pix = QPixmap(fn)
                if pix.width() % TILEWIDTH != 0:
                    QMessageBox.critical(self, 'Error', "Image width must be exactly divisible by %d pixels!" % TILEWIDTH)
                    return
                elif pix.height() % TILEHEIGHT != 0:
                    QMessageBox.critical(self, 'Error', "Image height must be exactly divisible by %d pixels!" % TILEHEIGHT)
                    return
                RESOURCES.create_new_map(local_name, fn, pix)

class MapProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window

        # Populate resources
        for resource in self._data:
            resource.pixmap = QPixmap(resource.full_path)

        self.current = current

        self.view = IconView(self)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.view)

    def set_current(self, current):
        self.current = current
        self.view.set_image(self.current.pixmap)
        self.view.show_image()
