from PyQt5.QtWidgets import QTabWidget, QWidget, QDialogButtonBox, QDialog
from PyQt5.QtWidgets import QGridLayout, QUndoStack
from PyQt5.QtCore import Qt

from collections import OrderedDict

class DatabaseEditor(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Database Editor")

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)
        self.setMinimumSize(640, 480)

        self.undo_stack = QUndoStack(self)

        self.tab_widget = QTabWidget()
        self.create_tabs()
        self.grid.addWidget(self.tab_widget, 0, 0)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 0)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

    def create_tabs(self):
        self.tabs = OrderedDict()
        self.tabs['unit'] = UnitMenu(self)
        self.tabs['class'] = ClassMenu(self)
        self.tabs['faction'] = FactionMenu(self)
        self.tabs['weapon'] = WeaponMenu(self)
        self.tabs['item'] = ItemMenu(self)
        self.tabs['status'] = StatusMenu(self)
        self.tabs['terrain'] = TerrainMenu(self)
        self.tabs['ai'] = AIMenu(self)
        self.tabs['support'] = SupportMenu(self)
        self.tabs['overworld'] = OverworldMenu(self)
        self.tabs['constants'] = ConstantsMenu(self)
        self.tabs['config'] = ConfigMenu(self)

        for name, tab in self.tabs.items():
            self.tab_widget.addTab(tab, name.capitalize())

    def apply(self):
        print("Apply")

    def accept(self):
        print("Ok")
        super().accept()

    def undo(self):
        self.undo_stack.undo()

    def redo(self):
        self.undo_stack.redo()

class UnitMenu(QWidget):
    pass

class ClassMenu(QWidget):
    pass

class FactionMenu(QWidget):
    pass

class WeaponMenu(QWidget):
    pass

class ItemMenu(QWidget):
    pass

class StatusMenu(QWidget):
    pass

class TerrainMenu(QWidget):
    pass

class AIMenu(QWidget):
    pass

class SupportMenu(QWidget):
    pass

class OverworldMenu(QWidget):
    pass

class ConstantsMenu(QWidget):
    pass

class ConfigMenu(QWidget):
    pass
