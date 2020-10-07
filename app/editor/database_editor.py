from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox
from PyQt5.QtCore import Qt, QSettings

from collections import OrderedDict

from app.data.database import DB

from app.editor.timer import TIMER

from app.editor.class_database import ClassDatabase
from app.editor.faction_database import FactionDatabase
from app.editor.party_database import PartyDatabase
from app.editor.weapon_database import WeaponDatabase
from app.editor.terrain_database import TerrainDatabase
from app.editor.ai_database import AIDatabase
from app.editor.constant_database import ConstantDatabase
from app.editor.stat_database import StatTypeDatabase

class DatabaseEditor(QDialog):
    def __init__(self, parent=None, starting_tab=None, one_tab_only=None):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Database Editor")
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

        self.tab_bar = QTabWidget(self)
        self.grid.addWidget(self.tab_bar, 0, 0, 1, 2)

        self.create_sub_widgets()
        for name, tab in self.tabs.items():
            self.tab_bar.addTab(tab, name)

        # Handle if only one tab is allowed
        if one_tab_only:
            for idx, name in enumerate(self.tabs.keys()):
                if name != one_tab_only:
                    self.tab_bar.setTabEnabled(idx, False)

        self.current_tab = self.tab_bar.currentWidget()
        self.tab_bar.currentChanged.connect(self.on_tab_changed)

        if not starting_tab and not one_tab_only:
            settings = QSettings("rainlash", "Lex Talionis")
            starting_tab = settings.value("database_tab")
        if starting_tab and starting_tab in self.tabs:
            self.tab_bar.setCurrentWidget(self.tabs[starting_tab])

        TIMER.tick_elapsed.connect(self.tick)

    def tick(self):
        if self.current_tab:
            self.current_tab.tick()

    def create_sub_widgets(self):
        self.tabs = OrderedDict()
        self.tabs['Units'] = UnitDatabase.create(self)
        self.tabs['Classes'] = ClassDatabase.create(self)
        self.tabs['Factions'] = FactionDatabase.create(self)
        self.tabs['Parties'] = PartyDatabase.create(self)
        self.tabs['Weapons'] = WeaponDatabase.create(self)
        self.tabs['Items'] = ItemDatabase.create(self)
        self.tabs['Terrain'] = TerrainDatabase.create(self)
        self.tabs['AI'] = AIDatabase.create(self)
        self.tabs['Constants'] = ConstantDatabase.create(self)
        self.tabs['Stat Types'] = StatTypeDatabase.create(self)

    def on_tab_changed(self, index):
        new_tab = self.tab_bar.currentWidget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def save(self):
        self.saved_data = {}
        self.saved_data['tags'] = DB.tags.save()
        self.saved_data['units'] = DB.units.save()
        self.saved_data['classes'] = DB.classes.save()
        self.saved_data['factions'] = DB.factions.save()
        self.saved_data['parties'] = DB.parties.save()
        self.saved_data['weapons'] = DB.weapons.save()
        self.saved_data['weapon_ranks'] = DB.weapon_ranks.save()
        self.saved_data['items'] = DB.items.save()
        self.saved_data['terrain'] = DB.terrain.save()
        self.saved_data['ai'] = DB.ai.save()
        self.saved_data['equations'] = DB.equations.save()
        self.saved_data['constants'] = DB.constants.save()
        self.saved_data['stats'] = DB.stats.save()
        self.saved_data['mcost'] = DB.mcost.save()
        return self.saved_data

    def restore(self):
        DB.tags.restore(self.saved_data['tags'])
        DB.units.restore(self.saved_data['units'])
        DB.classes.restore(self.saved_data['classes'])
        DB.factions.restore(self.saved_data['factions'])
        DB.parties.restore(self.saved_data['parties'])
        DB.weapons.restore(self.saved_data['weapons'])
        DB.weapon_ranks.restore(self.saved_data['weapon_ranks'])
        DB.items.restore(self.saved_data['items'])
        DB.terrain.restore(self.saved_data['terrain'])
        DB.ai.restore(self.saved_data['ai'])
        DB.equations.restore(self.saved_data['equations'])
        DB.constants.restore(self.saved_data['constants'])
        DB.stats.restore(self.saved_data['stats'])
        DB.mcost.restore(self.saved_data['mcost'])

    def apply(self):
        self.save()

    def accept(self):
        self.store_last_tab()
        if not self.window.current_proj:
            self.window.save_as()
        DB.serialize(self.window.current_proj)
        DB.levels.restore_all_prefabs(DB)
        super().accept()

    def reject(self):
        self.restore()
        self.store_last_tab()
        if self.window.current_proj:
            DB.serialize(self.window.current_proj)
        DB.levels.restore_all_prefabs(DB)
        super().reject()

    def store_last_tab(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_tab_name = self.tab_bar.tabText(self.tab_bar.currentIndex())
        settings.setValue("database_tab", current_tab_name)

    @staticmethod
    def get(parent, tab_name):
        dialog = DatabaseEditor(parent, one_tab_only=tab_name)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            current_tab = dialog.current_tab
            selected_res = current_tab.right_frame.current
            return selected_res, True
        else:
            return None, False

# Testing
# Run "python -m app.editor.database_editor" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DatabaseEditor()
    window.show()
    app.exec_()
