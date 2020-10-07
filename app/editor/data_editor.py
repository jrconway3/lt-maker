from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox
from PyQt5.QtCore import Qt

from app.data.database import DB

class SingleDatabaseEditor(QDialog):
    def __init__(self, tab, parent=None):
        super().__init__(parent)
        self.window = parent
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.save()

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

        self.tab = tab.create(self)
        self.grid.addWidget(self.tab, 0, 0, 1, 2)

        self.setWindowTitle(self.tab.windowTitle())

    def accept(self):
        if self.window and self.window.current_proj:
            DB.serialize(self.window.current_proj)
        QDialog.accept(self)

    def reject(self):
        self.restore()
        if self.window and self.window.current_proj:
            DB.serialize(self.window.current_proj)
        QDialog.reject(self)

    def save(self):
        self.saved_data = DB.save()
        return self.saved_data

    def restore(self):
        DB.restore(self.saved_data)
        
    def apply(self):
        self.save()
