from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QDir, QSettings
from PyQt5.QtGui import QPixmap

import os

from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.resources import RESOURCES
from app.data.database import DB

from app.editor.base_database_gui import DatabaseTab
from app.extensions.custom_gui import ResourceTreeView
from app.editor.icon_display import IconTreeModel, IconView

from app import utilities

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
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Choose %s", starting_path, "PNG Files (*.png);;All Files(*)")
        if ok:
            for fn in fns:
                if fn.endswith('.png'):
                    nid = os.path.split(fn)[-1][:-4]
                    pix = QPixmap(fn)
                    nid = utilities.get_next_name(nid, [d.nid for d in RESOURCES.maps])
                    if pix.width() % TILEWIDTH != 0:
                        QMessageBox.critical(self, 'Error', "Image width must be exactly divisible by %d pixels!" % TILEWIDTH)
                        continue
                    elif pix.height() % TILEHEIGHT != 0:
                        QMessageBox.critical(self, 'Error', "Image height must be exactly divisible by %d pixels!" % TILEHEIGHT)
                        continue
                    RESOURCES.create_new_map(nid, fn, pix)
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Icon must be PNG format!") 
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

    def nid_change_watchers(self, icon, old_nid, new_nid):
        # What uses maps
        for level in DB.levels:
            if level.tilemap.base_image_nid == old_nid:
                level.tilemap.base_image_nid = new_nid

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
