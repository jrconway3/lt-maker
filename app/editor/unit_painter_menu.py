from PyQt5.QtWidgets import QPushButton, \
    QWidget, QStyledItemDelegate, QDialog, QSpinBox, \
    QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QBrush, QColor

from app import utilities
from app.data.database import DB

from app.editor.timer import TIMER

from app.extensions.custom_gui import PropertyBox, ComboBox, Dialog, RightClickListView
from app.editor.base_database_gui import DragDropCollectionModel
from app.editor.custom_widgets import UnitBox, ClassBox, FactionBox, AIBox
from app.editor import class_database, item_database
from app.editor.database_editor import DatabaseEditor
from app.editor.unit_database import GenderGroup
from app.editor.item_database import ItemListWidget

class UnitPainterMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.main_editor = self.window
        self.map_view = self.main_editor.map_view
        self.current_level = self.main_editor.current_level
        if self.current_level:
            self._data = self.current_level.units
        else:
            self._data = []

        grid = QVBoxLayout()
        self.setLayout(grid)

        self.view = RightClickListView(parent=self)
        self.view.currentChanged = self.on_item_changed

        self.model = AllUnitModel(self._data, self)
        self.view.setModel(self.model)
        self.view.setIconSize(QSize(32, 32))
        self.inventory_delegate = InventoryDelegate(self._data)
        self.view.setItemDelegate(self.inventory_delegate)

        grid.addWidget(self.view)

        self.create_button = QPushButton("Create Generic Unit...")
        self.create_button.clicked.connect(self.create_generic)
        grid.addWidget(self.create_button)
        self.load_button = QPushButton("Load Unit...")
        self.load_button.clicked.connect(self.load_unit)
        grid.addWidget(self.load_button)

        self.last_touched_generic = None

        # self.display = self
        self.display = None

        TIMER.tick_elapsed.connect(self.tick)

    def on_visibility_changed(self, state):
        pass

    def tick(self):
        self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))

    def set_current_level(self, level):
        self.current_level = level
        self._data = self.current_level.units
        self.model._data = self._data
        self.model.update()
        self.inventory_delegate._data = self._data

    def select(self, idx):
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)

    def on_item_changed(self, curr, prev):
        # idx = int(idx)
        if self._data:
            unit = self._data[curr.row()]
            if unit.starting_position:
                self.map_view.center_on_pos(unit.starting_position)

    def get_current(self):
        idx = self.view.currentIndex().row()
        if idx < len(self._data):
            return self._data[idx]
        return None

        #     def get_current(self):
        # idx = self.view.currentIndex().row()
        # data_length = len(self._data)
        # if idx < data_length:
        #     return self._data[idx]
        # else:
        #     self.select(data_length - 1)
        #     return self._data[-1]

    def create_generic(self):
        created_unit, ok = GenericUnitDialog.get_unit(self, self.last_touched_generic)
        if ok:
            self.last_touched_generic = created_unit
            self._data.append(created_unit)
            self.model.update()
            # Select the unit
            idx = self._data.index(created_unit.nid)
            index = self.model.index(idx)
            self.view.setCurrentIndex(index)
            self.last_touched_generic = created_unit
            self.window.update_view()

    def load_unit(self):
        unit, ok = LoadUnitDialog.get_unit(self)
        if ok:
            self._data.append(unit)
            self.model.update()
            # Select the unit
            idx = self._data.index(unit.nid)
            index = self.model.index(idx)
            self.view.setCurrentIndex(index)
            self.window.update_view()

class AllUnitModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            unit = self._data[index.row()]
            text = unit.nid
            return text
        elif role == Qt.DecorationRole:
            unit = self._data[index.row()]
            klass_nid = unit.klass
            num = TIMER.passive_counter.count
            num = 0
            klass = DB.classes.get(klass_nid)
            active = index == self.window.view.currentIndex()
            pixmap = class_database.get_map_sprite_icon(klass, num, active, unit.team)
            if pixmap:
                return QIcon(pixmap)
            else:
                return None
        elif role == Qt.ForegroundRole:
            unit = self._data[index.row()]
            if unit.starting_position:
                return QBrush()
            else:
                return QBrush(QColor("red"))
        return None

class InventoryDelegate(QStyledItemDelegate):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        unit = self._data[index.row()]
        items = unit.starting_items
        for idx, item_nid in enumerate(items):
            item = DB.items.get(item_nid)
            if item:
                pixmap = item_database.get_pixmap(item)
                rect = option.rect
                painter.drawImage(rect.right() - ((idx + 1) * 16), rect.center().y() - 8, pixmap.toImage())

class LoadUnitDialog(Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.current = DB.create_unit_unique(DB.units[0].nid, 'player', DB.ai[0].nid)

        self.unit_box = UnitBox(self, button=True)
        self.unit_box.edit.currentIndexChanged.connect(self.unit_changed)
        self.unit_box.button.clicked.connect(self.access_units)
        layout.addWidget(self.unit_box)

        self.team_box = PropertyBox("Team", ComboBox, self)
        self.team_box.edit.addItems(DB.teams)
        self.team_box.edit.activated.connect(self.team_changed)
        layout.addWidget(self.team_box)      

        self.ai_box = AIBox(self)
        self.ai_box.edit.activated.connect(self.ai_changed)
        layout.addWidget(self.ai_box)  

        layout.addWidget(self.buttonbox)

    def team_changed(self, val):
        self.current.team = self.team_box.edit.currentText()

    def unit_changed(self, index):
        self.nid_changed(DB.units[index].nid)

    def ai_changed(self, val):
        self.current.ai = self.ai_box.edit.currentText()

    def access_units(self):
        unit, ok = DatabaseEditor.get(self, "Units")
        if ok:
            self.nid_changed(unit.nid)

    def nid_changed(self, nid):
        self.current.nid = nid
        self.current.prefab = DB.units.get(nid)

    # def set_current(self, current):
    #     self.current = current
    #     self.current.nid = self.
    #     self.current.team = self.team_box.edit.currentText()
    #     self.current.ai = self.ai_box.edit.currentText()

    @classmethod
    def get_unit(cls, parent):
        dialog = cls(parent)
        dialog.setWindowTitle("Load Unit")
        result = dialog.exec_()
        if result == QDialog.Accepted:
            unit = dialog.current
            return unit, True
        else:
            return None, False

class GenericUnitDialog(Dialog):
    def __init__(self, parent=None, example=None):
        super().__init__(parent)
        self.window = parent

        layout = QVBoxLayout()
        self.setLayout(layout)

        units = self.window._data
        if example:
            new_nid = utilities.get_next_generic_nid(example.nid, [unit.nid for unit in units])
            self.current = DB.create_unit_generic(new_nid, example.gender, example.level, example.klass, example.faction,
                                                  example.starting_items, example.team, example.ai)
        else:
            new_nid = utilities.get_next_generic_nid(101, [unit.nid for unit in units])
            self.current = DB.create_unit_generic(new_nid, 0, 1, DB.classes[0].nid, DB.factions[0].nid, [DB.items[0].nid], 'player', DB.ai[0].nid)

        self.team_box = PropertyBox("Team", ComboBox, self)
        self.team_box.edit.addItems(DB.teams)
        self.team_box.edit.activated.connect(self.team_changed)
        layout.addWidget(self.team_box)

        self.class_box = ClassBox(self)
        self.class_box.edit.currentIndexChanged.connect(self.class_changed)
        self.class_box.model.display_team = self.current.team
        layout.addWidget(self.class_box)

        self.level_box = PropertyBox("Level", QSpinBox, self)
        self.level_box.edit.setRange(1, 255)
        self.level_box.edit.setAlignment(Qt.AlignRight)
        self.level_box.edit.valueChanged.connect(self.level_changed)

        self.gender_box = PropertyBox("Gender", GenderGroup, self)
        self.gender_box.edit.toggled.connect(self.gender_changed)

        mini_layout = QHBoxLayout()
        mini_layout.addWidget(self.gender_box)
        mini_layout.addWidget(self.level_box)
        layout.addLayout(mini_layout)

        self.faction_box = FactionBox(self)
        self.faction_box.edit.currentIndexChanged.connect(self.faction_changed)
        layout.addWidget(self.faction_box)

        self.ai_box = AIBox(self)
        self.ai_box.edit.activated.connect(self.ai_changed)
        layout.addWidget(self.ai_box)

        self.item_widget = ItemListWidget("Items", self)
        self.item_widget.items_updated.connect(self.items_changed)
        layout.addWidget(self.item_widget)

        layout.addWidget(self.buttonbox)

        self.set_current(self.current)

    def team_changed(self, val):
        self.current.team = self.team_box.edit.currentText()
        self.class_box.model.display_team = self.current.team
        self.class_box.model.layoutChanged.emit()  # Force color change

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

    def ai_changed(self, val):
        self.current.ai = self.ai_box.edit.currentText()

    def items_changed(self):
        self.current.starting_items = self.item_widget.get_items()

    def set_current(self, current):
        self.current = current
        self.team_box.edit.setValue(current.team)
        self.level_box.edit.setValue(current.level)
        self.class_box.edit.setValue(current.klass)
        self.gender_box.edit.setValue(current.gender)
        self.faction_box.edit.setValue(current.faction)
        self.ai_box.edit.setValue(current.ai)
        self.item_widget.set_current(current.starting_items)

    @classmethod
    def get_unit(cls, parent, last_touched_generic):
        dialog = cls(parent, last_touched_generic)
        dialog.setWindowTitle("Create Generic Unit")
        result = dialog.exec_()
        if result == QDialog.Accepted:
            unit = dialog.current
            return unit, True
        else:
            return None, False
