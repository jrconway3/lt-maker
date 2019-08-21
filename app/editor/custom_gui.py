from PyQt5.QtWidgets import QListWidget, QComboBox
from PyQt5.QtCore import Qt

class SignalList(QListWidget):
    def __init__(self, parent=None, del_func=None):
        super().__init__()
        self.parent = parent
        self.del_func = del_func

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if self.del_func and event.key() == Qt.Key_Delete:
            self.del_func()

class ComboBox(QComboBox):
    def setValue(self, text):
        i = self.findText(text)
        if i >= 0:
            self.setCurrentIndex(i)
