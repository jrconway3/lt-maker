from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox, \
    QFileDialog, QWidget, QHBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QPixmap, QIcon

import os
from collections import OrderedDict

from app.data.resources import RESOURCES

from app.editor.base_database_gui import DatabaseTab, CollectionModel

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
        collection_model = IconModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...")
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

class IconModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            icon = self._data[index.row()]
            text = icon.nid
            return text
        elif role == Qt.DecorationRole:
            icon = self._data[index.row()]
            if icon.pixmap:
                pixmap = icon.pixmap.scaled(32, 32)
                return QIcon(pixmap)
        return None

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
        if event.delta() > 0 and self.screen_scale < self.max_scale:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.delta() < 0 and self.screen_scale > self.min_scale:
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
