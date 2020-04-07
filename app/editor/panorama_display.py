from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QDir, QSettings
from PyQt5.QtGui import QPixmap, QIcon

import os, glob

from app.data.constants import WINWIDTH, WINHEIGHT
from app.data.resources import RESOURCES

from app.extensions.custom_gui import ResourceListView
from app.editor.timer import TIMER
from app.editor.base_database_gui import DatabaseTab, ResourceCollectionModel
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
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceListView)
        return dialog

class PanoramaModel(ResourceCollectionModel):
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

    def create_new(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Add Background", starting_path, "PNG Files (*.png);;All Files(*)")
        if ok:
            for fn in fns:
                if fn.endswith('.png'):
                    nid = os.path.split(fn)[-1][:-4]
                    last_number = utilities.find_last_number(nid)
                    if last_number == 0:
                        movie_prefix = utilities.get_prefix(fn)
                        ims = glob.glob(movie_prefix + '*' + '.png')
                        ims = sorted(ims, key=lambda x: utilities.find_last_number(x[:-4]))
                        full_path = movie_prefix + '.png'
                    elif last_number is None:
                        movie_prefix = nid
                        ims = [fn]
                        full_path = fn
                    else:  # Should be nommed on by some other import
                        continue
                    pixs = [QPixmap(i) for i in ims]
                    movie_prefix = utilities.get_next_name(movie_prefix, [d.nid for d in RESOURCES.panoramas])
                    if all(pix.width() >= WINWIDTH and pix.height() >= WINHEIGHT for pix in pixs):
                        RESOURCES.create_new_panorama(movie_prefix, full_path, pixs)
                    else:
                        QMessageBox.critical(self.window, "Error", "Image must be at least %dx%d pixels in size" % (WINWIDTH, WINHEIGHT))
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Background must be PNG format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

    def delete(self, idx):
        # Check to see what is using me?
        # Nothing for now -- later Dialogue
        res = self._data[idx]
        nid = res.nid
        super().delete(idx)

    def nid_change_watchers(self, portrait, old_nid, new_nid):
        # What uses panoramas
        # Nothing for now -- later Dialogue
        pass

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

        self.view = IconView(self)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.view)

        TIMER.tick_elapsed.connect(self.tick)

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
