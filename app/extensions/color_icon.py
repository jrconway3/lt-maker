from PyQt5.QtWidgets import QPushButton, QColorDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal

class ColorIcon(QPushButton):
    colorChanged = pyqtSignal(QColor)

    def __init__(self, color, parent):
        super().__init__(parent)
        self._color = None
        self.change_color(color)

        self.setMinimumHeight(64)
        self.setMaximumHeight(64)
        self.setMinimumWidth(64)
        self.setMaximumWidth(64)
        self.resize(64, 64)
        self.pressed.connect(self.onColorPicker)

    def change_color(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit(QColor(color))

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        dlg = QColorDialog()
        if self._color:
            dlg.setCurrentColor(QColor(self._color))
        if dlg.exec_():
            self.change_color(dlg.currentColor().name())
