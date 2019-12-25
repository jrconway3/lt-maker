from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon

import glob

from app.data.resources import RESOURCES

from app.editor.custom_gui import give_timer
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.icon_display import IconView

import app.utilities as utilities

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
                nid = fn[:-4]
                last_number = utilities.find_last_number(nid)
                if last_number == 0:
                    movie_prefix = fn[:-5]
                    ims = glob.glob(movie_prefix + '*' + '.png')
                    ims = sorted(ims, key=lambda x: utilities.find_last_number(x[:-4]))
                    full_path = movie_prefix + '.png'
                elif last_number is None:
                    movie_prefix = nid
                    ims = [fn]
                    full_path = fn
                pixs = [QPixmap(i) for i in ims]
                RESOURCES.create_new_panorama(movie_prefix, pixs, full_path)
                self.after_new()

    def save(self):
        return None

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
            for path in resource.get_all_paths():
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
