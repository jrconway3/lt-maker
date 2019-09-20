from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, \
    QFileDialog, QSpinBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QDir, pyqtSignal

class PushableIcon16(QPushButton):
    sourceChanged = pyqtSignal(str)
    coordsChanged = pyqtSignal(int, int)
    width, height = 16, 16

    def __init__(self, fn, x, y, parent):
        super().__init__(parent)
        self.window = parent
        self._fn = fn
        self.x, self.y = x, y

        self.setMinimumHeight(64)
        self.setMaximumHeight(64)
        self.setMinimumWidth(64)
        self.setMaximumWidth(64)
        self.resize(64, 64)
        self.setStyleSheet("qproperty-iconSize: 64px;")
        self.change_icon_source(fn)
        self.pressed.connect(self.onIconSourcePicker)

    def render(self):
        if self._fn:
            big_pic = QPixmap(self._fn)
            pic = big_pic.copy(self.x*self.width, self.y*self.height, self.width, self.height)
            pic = pic.scaled(64, 64)
            pic = QIcon(pic)
            self.setIcon(pic)

    def get_size(self):
        im = QPixmap(self._fn)
        return im.width() // self.width, im.height() // self.height

    def change_icon_source(self, fn):
        if fn != self._fn:
            self._fn = fn
            # Check bounds
            max_width, max_height = self.get_size()
            if max_width >= self.x:
                self.x = max_width - 1  # Maximize
                self.coordsChanged.emit(self.x, self.y)
            if max_height >= self.y:
                self.y = max_height - 1  # Maximize
                self.coordsChanged.emit(self.x, self.y)
            self.sourceChanged.emit(fn)
        self.render()

    def change_icon_x(self, x):
        if x != self.x:
            self.x = x
            self.coordsChanged.emit(self.x, self.y)
        self.render()

    def change_icon_y(self, y):
        if y != self.y:
            self.y = y
            self.coordsChanged.emit(self.x, self.y)
        self.render()

    def onIconSourcePicker(self):
        starting_path = QDir.currentPath()
        fn, ok = QFileDialog.getOpenFileName(self, "Choose Sprite Sheet", starting_path,
                                             "PNG Files (*.png);;All Files(*)")
        if ok:
            self.change_icon_source(fn)

class PushableIcon32(PushableIcon16):
    width, height = 32, 32

class ItemIcon16(QWidget):
    width, height = 16, 16
    child_icon = PushableIcon16

    def __init__(self, source, parent):
        super().__init__(parent)
        self.window = parent

        grid = QGridLayout()
        self.setLayout(grid)

        self._fn = source
        self._x = 0
        self._y = 0

        self.icon = self.child_icon(self._fn, self._x, self._y, self)
        grid.addWidget(self.icon, 0, 0, 1, 4, Qt.AlignCenter)

        x_label = QLabel("X:")
        y_label = QLabel("Y:")
        grid.addWidget(x_label, 1, 0)
        grid.addWidget(y_label, 1, 2)

        self.x_spinbox = QSpinBox()
        self.y_spinbox = QSpinBox()
        grid.addWidget(self.x_spinbox, 1, 1)
        grid.addWidget(self.y_spinbox, 1, 3)

        self.set_spinbox_range()
        self.icon.sourceChanged.connect(self.on_source_changed)
        self.x_spinbox.valueChanged.connect(self.change_x)
        self.y_spinbox.valueChanged.connect(self.change_y)
        self.change_x(self._x)
        self.change_y(self._y)

    def set_current(self, fn, sprite_index):
        self._fn = fn
        self.icon.change_icon_source(self._fn)
        x, y = sprite_index
        self.change_x(x)
        self.change_y(y)
        self.set_spinbox_range()

    def change_x(self, value):
        self._x = value
        self.x_spinbox.setValue(self._x)
        self.icon.change_icon_x(value)
        if self.window.current:
            self.window.current.icon_index = (self._x, self._y)
            self.window.window.update_list()

    def change_y(self, value):
        self._y = value
        self.y_spinbox.setValue(self._y)
        self.icon.change_icon_y(value)
        if self.window.current:
            self.window.current.icon_index = (self._x, self._y)
            self.window.window.update_list()

    def on_source_changed(self, fn):
        self._fn = fn
        if self.window.current:
            self.window.current.icon_fn = self._fn
            self.window.window.update_list()
        self.set_spinbox_range()

    def set_spinbox_range(self):
        max_width, max_height = self.icon.get_size()
        self.x_spinbox.setRange(0, max_width - 1)
        self.y_spinbox.setRange(0, max_height - 1)

class ItemIcon32(ItemIcon16):
    width, height = 32, 32
    child_icon = PushableIcon32
