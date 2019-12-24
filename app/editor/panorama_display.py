from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon

import os, glob

from app.data.resources import RESOURCES

from app.editor.custom_gui import give_timer
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.icon_display import IconView

class PanoramaDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.panoramas
        title = "Background"
        right_frame = PanoramaProperties
        collection_model = PanoramaModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...")
        return dialog

    def create_new(self):
        fn, ok = QFileDialog.getOpenFileName(self, "Add Background")
        if ok:
            if fn.endswith('.png'):
                local_name = os.path.split(fn)[-1]
                if local_name[-4].endswith('0'):
                    movie_prefix = local_name[-5]
                    # Get all images in directory
                    ims = glob.glob(movie_prefix + '*' + '.png')
                else:
                    movie_prefix = local_name[-4]
                    ims = [local_name]
                pixs = [QPixmap(i) for i in ims]
                RESOURCES.create_new_panorama(movie_prefix, pixs, ims)
                self.after_new()

class PanoramaModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            panorama = self._data[index.row()]
            text = panorama.nid
            return text
        elif role == Qt.DecorationRole:
            panorama = self._data[index.row()]
            pixmap = panorama.get_frame()
            if pixmap:
                pixmap = pixmap.scaled(32, 32)
                return QIcon(pixmap)
        return None

class PanoramaProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window

        # Populate resources
        for resource in self._data:
            for path in resource.paths:
                resource.pixmaps.append(QPixmap(path))

        self.current = current

        give_timer(self)

        self.view = IconView(self)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.view)

    def tick(self):
        if self.current:
            self.current.increment_frame()
            self.draw()

    def set_current(self, current):
        self.current = current
        self.draw()

    def draw(self):
        self.view.set_image(self.current.get_frame())
        self.view.show_image()
