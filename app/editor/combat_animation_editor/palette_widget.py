import functools

from PyQt5.QtWidgets import QWidget, QButtonGroup, QInputDialog, QMenu, \
    QListWidgetItem, QRadioButton, QHBoxLayout, QLabel, QListWidget, QAction, \
    QColorDialog, QVBoxLayout
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor

from app.editor.icon_editor.icon_view import IconView
from app.utilities.data import Data
from app.resources import combat_anims
from app.editor.combat_animation_editor.palette_model import PaletteModel

from app.extensions.color_icon import ColorIcon
from app.extensions.custom_gui import RightClickListView

class PaletteWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self._data = Data()
        self.view = RightClickListView((None, None, None), parent=self)
        self.model = PaletteModel(self._data, self)
        self.view.setModel(self.model)
        self.view.setIconSize(QSize(16 * 16, 16))
        self.view.doubleClicked.connect(self.on_double_click)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        self.setLayout(main_layout)

    def set_current(self, current):
        palettes = self.current.palettes
        self._data = palettes
        self.model._data = self._data
        self.model.layoutChanged.emit()

    def get_current(self):
        for index in self.view.selectionModel().selectedIndexes():
            idx = index.row()
            if len(self._data) > 0 and idx < len(self._data):
                return self._data[idx]
        return None

    def on_double_click(self, index):
        idx = index.row()
        palette = self._data[idx]
        dlg = PaletteDisplay.create(palette)
        result = dlg.exec_()
