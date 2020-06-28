import os

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QListView, QDialog, \
    QPushButton, QFileDialog, QMessageBox, QGroupBox, QFormLayout, QSpinBox
from PyQt5.QtCore import Qt, QDir, QSettings
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter

from app.data.constants import WINWIDTH, WINHEIGHT

from app import utilities
from app.resources import combat_anims

from app.extensions.custom_gui import Dialog
from app.editor.base_database_gui import ResourceCollectionModel
from app.editor.icon_display import IconView
import app.editor.utilities as editor_utilities

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

        offset_section = QGroupBox(self)
        offset_section.setTitle("Offset")
        offset_layout = QFormLayout()
        self.x_box = QSpinBox()
        self.x_box.setValue(0)
        self.x_box.setRange(0, WINWIDTH)
        self.x_box.valueChanged.connect(self.on_x_changed)
        offset_layout.addRow("X:", self.x_box)
        self.y_box = QSpinBox()
        self.y_box.setValue(0)
        self.y_box.setRange(0, WINHEIGHT)
        self.y_box.valueChanged.connect(self.on_y_changed)
        offset_layout.addRow("Y:", self.y_box)
        offset_section.setLayout(offset_layout)

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
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.display)
        right_layout.addWidget(offset_section)
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
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
                    new_frame = combat_anims.Frame(nid, (0, 0), fn, pix)
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

    def on_x_changed(self, val):
        self.current.offset = (val, self.current.offset[1])
        self.draw()

    def on_y_changed(self, val):
        self.current.offset = (self.current.offset[0], val)
        self.draw()

    def set_current(self, frame):
        self.current = frame
        if self.current:
            self.x_box.setValue(self.current.offset[0])
            self.y_box.setValue(self.current.offset[1])
            self.draw()

    def draw(self):
        base_image = QImage(WINWIDTH, WINHEIGHT, QImage.Format_ARGB32)
        base_image.fill(editor_utilities.qCOLORKEY)
        painter = QPainter()
        painter.begin(base_image)
        painter.drawImage(self.current.offset[0], self.current.offset[1], self.current.pixmap.toImage())
        painter.end()
        self.display.set_image(QPixmap.fromImage(base_image))
        self.display.show_image()

    @classmethod
    def get(cls, frames, parent=None):
        dlg = cls(frames, parent)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            return dlg.current, True
        else:
            return None, False
