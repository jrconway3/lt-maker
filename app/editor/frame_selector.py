import os

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QListView, QDialog, \
    QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QDir, QSettings
from PyQt5.QtGui import QPixmap, QIcon

from app.data.constants import WINWIDTH, WINHEIGHT

from app import utilities
from app.data import combat_animation

from app.extensions.custom_gui import Dialog
from app.editor.base_database_gui import ResourceCollectionModel
from app.editor.icon_display import IconView

class FrameModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            frame = self._data[index.row()]
            text = frame.nid
            return text
        elif role == Qt.DecorationRole:
            frame = self._data[index.row()]
            if not frame.pixmap:
                frame.pixmap = QPixmap(frame.full_path)
            return QIcon(frame.pixmap)
        return None

class FrameSelector(Dialog):
    def __init__(self, frames, parent=None):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Animation Frames")

        self.frames = frames
        for frame in self.frames:
            frame.pixmap = QPixmap(frame.full_path)
        if self.frames:
            self.current = self.frames[0]
        else:
            self.current = None

        self.display = IconView(self)
        self.display.static_size = WINWIDTH, WINHEIGHT
        self.display.setSceneRect(0, 0, WINWIDTH, WINHEIGHT)

        self.view = QListView(self)
        self.view.currentChanged = self.on_item_changed

        self.model = FrameModel(self.frames, self)
        self.view.setModel(self.model)

        self.add_button = QPushButton("Add Frames...")
        self.add_button.clicked.connect(self.import_frames)

        layout = QVBoxLayout()
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.view)
        left_layout.addWidget(self.add_button)
        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.display)
        layout.addLayout(main_layout)
        layout.addWidget(self.buttonbox)
        self.setLayout(layout)

        self.set_current(self.current)

    def import_frames(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select Frames", starting_path, "PNG Files (*.png);;All Files(*)")
        if ok:
            for fn in fns:
                if fn.endswith('.png'):
                    nid = os.path.split(fn)[-1][:-4]
                    pix = QPixmap(fn)
                    nid = utilities.get_next_name(nid, self.frames.keys())
                    new_frame = combat_animation.Frame(nid, (0, 0), fn, pix)
                    self.frames.append(new_frame)
                    self.model.layoutChanged.emit()
                    self.set_current(new_frame)
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Portrait must be PNG format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

    def on_item_changed(self, curr, prev):
        if self.frames:
            new_data = curr.internalPointer()
            if not new_data:
                new_data = self.frames[curr.row()]
            self.set_current(new_data)

    def set_current(self, frame):
        self.current = frame
        if self.current:
            self.display.set_image(self.current.pixmap)
            self.display.show_image()

    @classmethod
    def get(cls, frames, parent=None):
        dlg = cls(frames, parent)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            return dlg.current, True
        else:
            return None, False
