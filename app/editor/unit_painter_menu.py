from PyQt5.QtWidgets import QGridLayout, QPushButton, QListView, \
    QWidget, QStyledItemDelegate
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon

from app.editor.base_database_gui import CollectionModel
from app.editor import class_database, item_database
from app.editor.database_editor import DatabaseEditor

class UnitPainterMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.main_editor = self.window
        self.map_view = self.main_editor.map_view
        self.current_level = self.main_editor.current_level
        self._data = self.current_level.units

        grid = QGridLayout()
        self.setLayout(grid)

        self.list_view = QListView(self)
        self.list_view.currentChanged = self.on_item_changed

        self.model = AllUnitModel(self._data, self)
        self.list_view.setModel(self.model)
        self.list_view.setIconSize(QSize(32, 32))
        inventory_delegate = InventoryDelegate(self._data)
        self.list_view.setItemDelegate(inventory_delegate)

        grid.addWidget(self.list_view, 0, 0)

        self.create_button = QPushButton("Create Generic Unit...")
        self.create_button.clicked.connect(self.create_generic)
        grid.addWidget(self.create_button, 1, 0)
        self.load_button = QPushButton("Load Unit...")
        self.load_button.clicked.connect(self.load_unit)
        grid.addWidget(self.load_button, 2, 0)

        self.last_touched_generic = None

    def select(self, idx):
        index = self.model.index(idx)
        self.list_view.setCurrentIndex(index)

    def on_item_changed(self, idx):
        # idx = int(idx)
        unit = self._data[idx]
        if unit.position:
            self.map_view.center_on_pos(unit.position)

    def create_generic(self):
        created_unit, ok = GenericUnitDialog.get_unit()
        if ok:
            self.last_touched_generic = created_unit
            self._data.append(created_unit)
            # Select the unit
            idx = self.model.index(self._data.index(created_unit))
            self.list_view.setCurrentIndex(idx)
            self.last_touched_generic = created_unit
            self.window.update_view()

    def load_unit(self):
        unit, ok = DatabaseEditor.get(self, "Units")
        if ok:
            self._data.append(unit)
            # Select the unit
            idx = self.model.index(self._data.index(unit))
            self.list_view.setCurrentIndex(idx)
            self.last_touched_generic = unit
            self.window.update_view()

class AllUnitModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            unit = self._data[index.row()]
            text = unit.nid
            return text
        elif role == Qt.DecorationRole:
            unit = self._data[index.row()]
            klass = unit.klass
            num = self.window.main_editor.passive_counter.count
            pixmap = class_database.get_map_sprite_icon(klass, num, index == self.window.view.currentIndex())
            if pixmap:
                return QIcon(pixmap)
            else:
                return None
        return None

class InventoryDelegate(QStyledItemDelegate):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        unit = self._data[index.row()]
        items = unit.items
        for idx, item in items:
            pixmap = item_database.get_pixmap(item)
            rect = option.rect
            painter.drawImage(rect.right() - ((idx + 1) * 16), rect.center().y() - 8, pixmap)

class GenericUnitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.current = DB.create_new_unit()

        self.team_box = PropertyBox("Team", QComboBox, self)
        self.team_box.edit.addItems(DB.teams)
        self.team_box.edit.activated.connect(self.team_changed)

        self.class_box = PropertyBox("Class", QComboBox, self)
        self.class_box.edit.addItems(DB.classes.keys())
        self.class_box.edit.currentIndexChanged.connect(self.class_changed)

        self.level_box = PropertyBox("Level", QSpinBox, self)
        self.level_box.edit.setRange(1, 255)
        self.level_box.edit.setAlignment(Qt.AlignRight)
        self.level_box.edit.valueChanged.connect(self.level_changed)

        self.gender_box = PropertyBox("Gender", GenderGroup, self)
        self.gender_box.edit.toggled.connect(self.gender_changed)

        self.faction_box = PropertyBox("Faction", QComboBox, self)
        self.faction_box.edit.addItems(DB.factions.keys())
        self.faction_box.edit.currentIndexChanged.connect(self.faction_changeD)

        self.ai_box = PropertyBox("AI", QComboBox, self)
        self.ai_box.edit.addItems(DB.ai.keys())
        self.ai_box.edit.currentIndexChanged.connect()

    def team_changed(self, val):
        self.current.team = val

    def class_changed(self, index):
        self.current.klass = self.class_box.edit.currentText()
        self.level_box.edit.setMaximum(DB.classes.get(self.current.klass).max_level)

    def level_changed(self, val):
        self.current.level = val

    def gender_changed(self, male):
        if male:
            self.current.gender = 0
        else:
            self.current.gender = 5

    def faction_changed(self, index):
        faction_nid = self.faction_box.edit.currentText()
        faction = DB.factions.get(faction_nid)
        self.current.faction = faction
        self.current.name = faction.name
        self.current.desc = faction.desc

    @classmethod
    def getUnit(cls, parent):
        dialog = cls(parent)
        dialog.setWindowTitle("Create Generic Unit")
        result = dialog.exec_()
        if result == QDialog.Accepted:
            unit = dialog.current
            return unit, True
        else:
            return None, False

