from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QListView, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon

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

        self.frames = frames
        for frame in self.frames:
            frame.pixmap = QPixmap(frame.full_path)
        self.current = self.frames[0]

        self.display = IconView(self)

        self.view = QListView(self)
        self.view.currentChanged = self.on_item_changed

        self.model = FrameModel(self.frames, self)
        self.view.setModel(self.model)

        layout = QVBoxLayout()
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.display)
        layout.addLAyout(main_layout)
        layout.addWidget(self.buttonbox)

        self.set_current(self.current)

    def on_item_changed(self, curr, prev):
        if self._data:
            new_data = curr.internalPointer()
            if not new_data:
                new_data = self._data[curr.row()]
            self.set_current(new_data)

    def set_current(self, frame):
        self.current = frame
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
