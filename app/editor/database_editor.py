from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox
from PyQt5.QtCore import Qt

import time

from collections import OrderedDict

import app.data.constants as constants
import app.counters as counters

from app.data.database import DB

from app.editor.custom_gui import give_timer
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

        # Timing Section
        give_timer(self, constants.FPS)
        framerate = constants.FRAMERATE
        self.passive_counter = counters.generic3counter(int(32*framerate), int(4*framerate))
        self.active_counter = counters.generic3counter(int(13*framerate), int(6*framerate))

        self.tab_bar = QTabWidget(self)
        self.grid.addWidget(self.tab_bar, 0, 0, 1, 2)
        self.current_tab = None

        self.create_sub_widgets()
        for name, tab in self.tabs.items():
            self.tab_bar.addTab(tab, name)

        self.tab_bar.currentChanged.connect(self.on_tab_changed)

    def tick(self):
        current_time = int(round(time.time() * 1000))
        self.passive_counter.update(current_time)
        self.active_counter.update(current_time)
        if self.current_tab:
            self.current_tab.tick()

    def create_sub_widgets(self):
        self.tabs = OrderedDict()
        self.tabs['Units'] = UnitDatabase.create(self)
        self.tabs['Classes'] = ClassDatabase.create(self)
        self.tabs['Factions'] = FactionDatabase.create(self)
        self.tabs['Weapons'] = WeaponDatabase.create(self)
        self.tabs['Items'] = ItemDatabase.create(self)
        self.tabs['Terrain'] = TerrainDatabase.create(self)
        self.tabs['AI'] = AIDatabase.create(self)

    def on_tab_changed(self, index):
        new_tab = self.tab_bar.currentWidget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def mass_restore(self):
        for tab in self.tabs.values():
            tab.restore(tab.saved_data)

    def mass_apply(self):
        for tab in self.tabs.values():
            tab.apply()

    def accept(self):
        DB.serialize()
        super().accept()

    def reject(self):
        self.mass_restore()
        DB.serialize()
        super().reject()

# Testing
# Run "python -m app.editor.database_editor" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DatabaseEditor()
    window.show()
    app.exec_()
