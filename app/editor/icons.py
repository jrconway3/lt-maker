from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFormLayout, QPushButton, \
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
        self.setStyleSheet("QPushButton {qproperty-iconSize: 64px;}")
        self.change_icon_source(fn)
        self.pressed.connect(self.onIconSourcePicker)

    def render(self):
        if self._fn:
            big_pic = QPixmap(self._fn)
            if big_pic.width() > 0 and big_pic.height() > 0:
                pic = big_pic.copy(self.x*self.width, self.y*self.height, self.width, self.height)
                pic = pic.scaled(64, 64)
                pic = QIcon(pic)
                self.setIcon(pic)
        else:
            self.setIcon(QIcon())

    def get_size(self):
        im = QPixmap(self._fn)
        return im.width() // self.width, im.height() // self.height

    def change_icon_source(self, fn):
        if fn != self._fn:
            self._fn = fn
            # Check bounds
            max_width, max_height = self.get_size()
            if max_width <= self.x:
                self.x = max(0, max_width - 1)  # Maximize
                self.coordsChanged.emit(self.x, self.y)
            if max_height <= self.y:
                self.y = max(0, max_height - 1)  # Maximize
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

class PushableIcon80(PushableIcon16):
    width, height = 80, 72

class ItemIcon16(QWidget):
    width, height = 16, 16
    child_icon = PushableIcon16

    def __init__(self, source, parent):
        super().__init__(parent)
        self.window = parent

        hbox = QHBoxLayout()
        self.setLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)

        self._fn = source
        self._x = 0
        self._y = 0

        self.icon = self.child_icon(self._fn, self._x, self._y, self)
        hbox.addWidget(self.icon, Qt.AlignCenter)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setFormAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        self.x_spinbox = QSpinBox()
        self.y_spinbox = QSpinBox()
        self.x_spinbox.setMinimumWidth(40)
        self.y_spinbox.setMinimumWidth(40)
        form_layout.addRow("X", self.x_spinbox)
        form_layout.addRow("Y", self.y_spinbox)
        hbox.addLayout(form_layout)

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

class ItemIcon80(ItemIcon16):
    width, height = 80, 72
    child_icon = PushableIcon80
