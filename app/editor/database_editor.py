from PyQt5.QtWidgets import QDialog, QToolButton, QGridLayout, QAction
from PyQt5.QtCore import Qt

from collections import OrderedDict

from app.editor.custom_gui import EditDialog
from app.editor.terrain_database import TerrainDatabase

class DatabaseEditor(QDialog):
    buttons_per_row = 4

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Database Editor")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)
        # self.setMinimumSize(640, 480)

        self.create_tabs()
        self.create_buttons()

    def create_tabs(self):
        self.actions = OrderedDict()
        self.actions['unit'] = QAction("Edit &Units", self, shortcut="U", triggered=lambda: UnitDatabase.edit(self))
        self.actions['class'] = QAction("Edit &Classes", self, shortcut="C", triggered=lambda: ClassDatabase.edit(self))
        self.actions['faction'] = QAction("Edit &Factions", self, shortcut="F", triggered=lambda: FactionDatabase.edit(self))
        self.actions['weapon'] = QAction("Edit &Weapon Types", self, shortcut="W", triggered=lambda: WeaponDatabase.edit(self))
        self.actions['item'] = QAction("Edit &Items", self, shortcut="I", triggered=lambda: ItemDatabase.edit(self))
        self.actions['status'] = QAction("Edit &Skills", self, shortcut="S", triggered=lambda: StatusDatabase.edit(self))
        self.actions['terrain'] = QAction("Edit &Terrain", self, shortcut="T", triggered=lambda: TerrainDatabase.edit(self))
        self.actions['ai'] = QAction("Edit &AI", self, shortcut="A", triggered=lambda: AIDatabase.edit(self))
        self.actions['support'] = QAction("Edit Su&pports", self, shortcut="P", triggered=lambda: SupportDatabase.edit(self))
        self.actions['overworld'] = QAction("Edit &Overworld", self, shortcut="O", triggered=lambda: OverworldDatabase.edit(self))
        self.actions['constants'] = QAction("Edit &Constants", self, shortcut="C", triggered=lambda: ConstantsDatabase.edit(self))
        self.actions['config'] = QAction("&Edit Configuration", self, shortcut="E", triggered=lambda: ConfigDatabase.edit(self))

    def create_buttons(self):
        self.buttons = OrderedDict()
        for idx, (action_name, action) in enumerate(self.actions.items()):
            button = QToolButton(self)
            self.buttons[action_name] = button
            button.setDefaultAction(action)
            button.setAutoRaise(True)
            self.grid.addWidget(button, idx//self.buttons_per_row, idx%self.buttons_per_row)

class UnitDatabase(EditDialog):
    pass

class ClassDatabase(EditDialog):
    pass

class FactionDatabase(EditDialog):
    pass

class WeaponDatabase(EditDialog):
    pass

class ItemDatabase(EditDialog):
    pass

class StatusDatabase(EditDialog):
    pass

class AIDatabase(EditDialog):
    pass

class SupportDatabase(EditDialog):
    pass

class OverworldDatabase(EditDialog):
    pass

class ConstantsDatabase(EditDialog):
    pass

class ConfigDatabase(EditDialog):
    pass

# Testing
# Run "python -m app.editor.database_editor" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DatabaseEditor()
    window.show()
    app.exec_()
