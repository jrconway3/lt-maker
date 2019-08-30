from PyQt5.QtWidgets import QWidget, QDialog, QToolButton, QGridLayout, QAction

from collections import OrderedDict

from app.editor.custom_gui import EditDialog
from app.editor.terrain_menu import TerrainMenu

class DatabaseEditor(QDialog):
    buttons_per_row = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Editor")

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)
        # self.setMinimumSize(640, 480)

        self.create_tabs()
        self.create_buttons()

    def create_tabs(self):
        self.actions = OrderedDict()
        self.actions['unit'] = QAction("Edit &Units", self, shortcut="U", triggered=lambda: UnitMenu.edit(self))
        self.actions['class'] = QAction("Edit &Classes", self, shortcut="C", triggered=lambda: ClassMenu.edit(self))
        self.actions['faction'] = QAction("Edit &Factions", self, shortcut="F", triggered=lambda: FactionMenu.edit(self))
        self.actions['weapon'] = QAction("Edit &Weapon Types", self, shortcut="W", triggered=lambda: WeaponMenu.edit(self))
        self.actions['item'] = QAction("Edit &Items", self, shortcut="I", triggered=lambda: ItemMenu.edit(self))
        self.actions['status'] = QAction("Edit &Skills", self, shortcut="S", triggered=lambda: StatusMenu.edit(self))
        self.actions['terrain'] = QAction("Edit &Terrain", self, shortcut="T", triggered=lambda: TerrainMenu.edit(self))
        self.actions['ai'] = QAction("Edit &AI", self, shortcut="A", triggered=lambda: AIMenu.edit(self))
        self.actions['support'] = QAction("Edit Su&pports", self, shortcut="P", triggered=lambda: SupportMenu.edit(self))
        self.actions['overworld'] = QAction("Edit &Overworld", self, shortcut="O", triggered=lambda: OverworldMenu.edit(self))
        self.actions['constants'] = QAction("Edit &Constants", self, shortcut="C", triggered=lambda: ConstantsMenu.edit(self))
        self.actions['config'] = QAction("&Edit Configuration", self, shortcut="E", triggered=lambda: ConfigMenu.edit(self))

    def create_buttons(self):
        self.buttons = OrderedDict()
        for idx, (action_name, action) in enumerate(self.actions.items()):
            button = QToolButton(self)
            self.buttons[action_name] = button
            button.setDefaultAction(action)
            button.setAutoRaise(True)
            self.grid.addWidget(button, idx//self.buttons_per_row, idx%self.buttons_per_row)

class UnitMenu(EditDialog):
    pass

class ClassMenu(EditDialog):
    pass

class FactionMenu(EditDialog):
    pass

class WeaponMenu(EditDialog):
    pass

class ItemMenu(EditDialog):
    pass

class StatusMenu(EditDialog):
    pass

class AIMenu(EditDialog):
    pass

class SupportMenu(EditDialog):
    pass

class OverworldMenu(EditDialog):
    pass

class ConstantsMenu(EditDialog):
    pass

class ConfigMenu(EditDialog):
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
