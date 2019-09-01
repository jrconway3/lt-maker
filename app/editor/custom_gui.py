from PyQt5.QtWidgets import QListWidget, QComboBox, QDialog, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton
from PyQt5.QtCore import Qt

class EditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
    @classmethod
    def edit(cls, parent):
        dialog = cls(parent)
        dialog.exec_()

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

class LineSearch(QWidget):
    def __init__(self, parent, func=None):
        layout = QHBoxLayout()
        self.line_edit = QLineEdit(self)
        self.search_button = QPushButton(self)
        layout.setHorizontalSpacing(0)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.search_button)
        self.setLayout(layout)
        if func:
            self.search_button.clicked.connect(func)

    def set_func(self, func):
        self.search_button.clicked.connect(func)
