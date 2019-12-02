from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox
from PyQt5.QtCore import Qt

from collections import OrderedDict

from app.editor.unit_database import UnitDatabase
from app.editor.class_database import ClassDatabase
from app.editor.faction_database import FactionDatabase
from app.editor.weapon_database import WeaponDatabase
from app.editor.item_database import ItemDatabase
from app.editor.terrain_database import TerrainDatabase
from app.editor.ai_database import AIDatabase

class DatabaseEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Editor")
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.button(QDialogButtonBox.Apply).clicked.connect(self.mass_apply)

        self.tab_bar = QTabWidget(self)
        self.grid.addWidget(self.tab_bar, 0, 0, 2, 1)

        self.create_sub_widgets()
        for name, tab in self.tabs.items():
            self.tab_bar.addTab(tab, name)

    def create_sub_widgets(self):
        self.tabs = OrderedDict()
        self.tabs['Units'] = UnitDatabase.create()
        self.tabs['Classes'] = ClassDatabase.create()
        self.tabs['Factions'] = FactionDatabase.create()
        self.tabs['Weapons'] = WeaponDatabase.create()
        self.tabs['Items'] = ItemDatabase.create()
        self.tabs['Terrain'] = TerrainDatabase.create()
        self.tabs['AI'] = AIDatabase.create()

    def on_tab_changed(self, index):
        new_tab = self.tab_bar.currentWidget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def mass_restore(self):
        for tab in self.tabs.values():
            tab.restore(tab.saved_data)

    def mass_apply(self):
        # Maybe?
        for tab in self.tabs.values():
            tab.apply()

    def accept(self):
        super().accept()

    def reject(self):
        self.mass_restore()
        super().reject()

# Testing
# Run "python -m app.editor.database_editor_2" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DatabaseEditor()
    window.show()
    app.exec_()
