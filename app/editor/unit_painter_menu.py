from PyQt5.QtWidgets import QPushButton, QLineEdit, \
    QWidget, QStyledItemDelegate, QDialog, QSpinBox, \
    QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QBrush, QColor

from app import utilities
from app.data.level_units import GenericUnit
from app.data.database import DB

from app.editor import timer

from app.extensions.custom_gui import PropertyBox, ComboBox, Dialog, RightClickListView
from app.editor.base_database_gui import DragDropCollectionModel
from app.editor.custom_widgets import UnitBox, ClassBox, FactionBox, AIBox
from app.editor.class_editor import class_model
from app.editor.item_editor import item_model
from app.editor.unit_editor import unit_tab
from app.editor.stat_widget import StatAverageDialog, GenericStatAveragesModel
from app.editor.item_list_widget import ItemListWidget

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

        def duplicate_func(model, index):
            return isinstance(model._data[index.row()], GenericUnit)

        self.view = RightClickListView((None, duplicate_func, None), parent=self)
        self.view.currentChanged = self.on_item_changed
        self.view.doubleClicked.connect(self.on_double_click)

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

        timer.get_timer().tick_elapsed.connect(self.tick)

    def on_visibility_changed(self, state):
        pass

    def tick(self):
        # self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))
        self.model.layoutChanged.emit()

    def set_current_level(self, level):
        self.current_level = level
        self._data = self.current_level.units
        self.model._data = self._data
        self.model.update()
        self.inventory_delegate._data = self._data

    def select(self, idx):
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)

    def deselect(self):
        self.view.clearSelection()

    def on_item_changed(self, curr, prev):
        # idx = int(idx)
        if self._data:
            unit = self._data[curr.row()]
            if unit.starting_position:
                self.map_view.center_on_pos(unit.starting_position)

    def get_current(self):
        for index in self.view.selectionModel().selectedIndexes():
            idx = index.row()
            if len(self._data) > 0 and idx < len(self._data):
                return self._data[idx]
        return None

    def create_generic(self, example=None):
        if not example:
            example = self.last_touched_generic
        created_unit, ok = GenericUnitDialog.get_unit(self, example)
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
            return created_unit
        return None

    def load_unit(self):
        unit, ok = LoadUnitDialog.get_unit(self)
        if ok:
            if unit.nid in self._data.keys():
                QMessageBox.critical(self, "Error!", "%s already present in level!" % unit.nid)
            else:
                self._data.append(unit)
                self.model.update()
                # Select the unit
                idx = self._data.index(unit.nid)
                index = self.model.index(idx)
                self.view.setCurrentIndex(index)
                self.window.update_view()
                return unit
        return None

    def on_double_click(self, index):
        idx = index.row()
        unit = self._data[idx]
        if unit.generic:
            serialized_unit = unit.serialize()
            unit, ok = GenericUnitDialog.get_unit(self, unit=unit)
            if ok:
                pass
            else:
                # Restore the old unit
                unit = GenericUnit.restore(serialized_unit)
                self._data.pop(idx)
                self._data.insert(idx, unit)
        else:  # Unique unit
            old_unit_nid = unit.nid
            old_unit_team = unit.team
            old_unit_ai = unit.ai
            edited_unit, ok = LoadUnitDialog.get_unit(self, unit)
            if ok:
                pass
            else:
                unit.nid = old_unit_nid
                unit.prefab = DB.units.get(unit.nid)
                unit.team = old_unit_team
                unit.ai = old_unit_ai

class AllUnitModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            unit = self._data[index.row()]
            text = str(unit.nid)
            if isinstance(unit, GenericUnit):
                text += ' (' + str(unit.ai) + ' Lv ' + str(unit.level) + ')'
            return text
        elif role == Qt.DecorationRole:
            unit = self._data[index.row()]
            klass_nid = unit.klass
            num = timer.get_timer().passive_counter.count
            klass = DB.classes.get(klass_nid)
            active = self.window.view.selectionModel().isSelected(index)
            pixmap = class_model.get_map_sprite_icon(klass, num, active, unit.team, unit.variant)
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

    def new(self, idx):
        unit = self._data[idx]
        if unit.generic:
            ok = self.window.create_generic(unit)
        else:
            ok = self.window.load_unit()
        if ok:
            self._data.move_index(len(self._data) - 1, idx + 1)
            self.layoutChanged.emit()

            self.update_watchers(idx + 1)

    def duplicate(self, idx):
        obj = self._data[idx]
        if obj.generic:
            new_nid = utilities.get_next_generic_nid(obj.nid, self._data.keys())
            serialized_obj = obj.serialize()
            new_obj = GenericUnit.restore(serialized_obj)
            new_obj.nid = new_nid
            new_obj.starting_position = None
            self._data.insert(idx + 1, new_obj)
            self.layoutChanged.emit()

            self.update_watchers(idx + 1)
        else:
            QMessageBox.critical(self.window, "Error!", "Cannot duplicate unique unit!")

class InventoryDelegate(QStyledItemDelegate):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        unit = self._data[index.row()]
        items = unit.starting_items
        for idx, item in enumerate(items):
            item_nid, droppable = item
            item = DB.items.get(item_nid)
            if item:
                pixmap = item_model.get_pixmap(item)
                rect = option.rect
                left = rect.right() - ((idx + 1) * 16)
                top = rect.center().y() - 8
                if droppable:
                    green = QColor("Green")
                    green.setAlpha(80)
                    painter.setBrush(QBrush(green))
                    painter.drawRect(left, top, pixmap.width(), pixmap.height())
                painter.drawImage(left, top, pixmap.toImage())

class LoadUnitDialog(Dialog):
    def __init__(self, parent=None, current=None):
        super().__init__(parent)
        self.setWindowTitle("Load Unit")
        self.window = parent

        layout = QVBoxLayout()
        self.setLayout(layout)

        if current:
            self.current = current
        else:
            assert len(DB.units) > 0 and len(DB.ai) > 0
            self.current = DB.create_unit_unique(DB.units[0].nid, 'player', DB.ai[0].nid)

        self.unit_box = UnitBox(self, button=True)
        self.unit_box.edit.setValue(self.current.nid)
        self.unit_box.edit.currentIndexChanged.connect(self.unit_changed)
        self.unit_box.button.clicked.connect(self.access_units)
        layout.addWidget(self.unit_box)

        self.team_box = PropertyBox("Team", ComboBox, self)
        self.team_box.edit.addItems(DB.teams)
        self.team_box.edit.setValue(self.current.team)
        self.team_box.edit.activated.connect(self.team_changed)
        layout.addWidget(self.team_box)      

        self.ai_box = AIBox(self)
        self.ai_box.edit.setValue(self.current.ai)
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
        unit, ok = unit_tab.get()
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
    def get_unit(cls, parent, unit=None):
        dialog = cls(parent, unit)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            unit = dialog.current
            return unit, True
        else:
            return None, False

class GenericUnitDialog(Dialog):
    def __init__(self, parent=None, example=None, unit=None):
        super().__init__(parent)
        self.setWindowTitle("Create Generic Unit")
        self.window = parent

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.averages_dialog = None

        units = self.window._data
        if unit:
            self.current = unit
        elif example:
            new_nid = utilities.get_next_generic_nid(example.nid, units.keys())
            self.current = GenericUnit(
                new_nid, example.variant, example.level, example.klass, example.faction,
                example.starting_items, example.team, example.ai)
        else:
            new_nid = utilities.get_next_generic_nid(101, units.keys())
            assert len(DB.classes) > 0 and len(DB.factions) > 0 and len(DB.items) > 0 and len(DB.ai) > 0
            self.current = GenericUnit(
                new_nid, None, 1, DB.classes[0].nid, DB.factions[0].nid,
                [(DB.items[0].nid, False)], 'player', DB.ai[0].nid)

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
        self.level_box.add_button(QPushButton("..."))
        self.level_box.button.clicked.connect(self.display_averages)
        self.level_box.button.setMaximumWidth(40)

        self.variant_box = PropertyBox("Animation Variant", QLineEdit, self)
        self.variant_box.edit.setPlaceholderText("No Variant")
        self.variant_box.edit.textChanged.connect(self.variant_changed)

        mini_layout = QHBoxLayout()
        mini_layout.addWidget(self.variant_box)
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
        self.check_color()
        if self.averages_dialog:
            self.averages_dialog.update()

    def level_changed(self, val):
        self.current.level = val
        if self.averages_dialog:
            self.averages_dialog.set_current(self.current)
            self.averages_dialog.update()

    def variant_changed(self, text):
        self.current.variant = text

    def faction_changed(self, index):
        faction_nid = self.faction_box.edit.currentText()
        faction = DB.factions.get(faction_nid)
        self.current.faction = faction
        self.current.name = faction.name
        self.current.desc = faction.desc

    def ai_changed(self, val):
        self.current.ai = self.ai_box.edit.currentText()

    def check_color(self):
        # See which ones can actually be wielded
        color_list = []
        for item_nid, droppable in self.current.starting_items:
            item = DB.items.get(item_nid)
            if droppable:
                color_list.append(Qt.darkGreen)
            elif not can_wield(self.current, item, prefab=False):
                color_list.append(Qt.red)
            else:
                color_list.append(Qt.black)
        self.item_widget.set_color(color_list)

    def items_changed(self):
        self.current.starting_items = self.item_widget.get_items()
        self.check_color()

    def display_averages(self):
        # Modeless dialog
        if not self.averages_dialog:
            self.averages_dialog = StatAverageDialog(self.current, "Generic", GenericStatAveragesModel, self)
        self.averages_dialog.show()
        self.averages_dialog.raise_()
        self.averages_dialog.activateWindow()

    def close_averages(self):
        if self.averages_dialog:
            self.averages_dialog.done(0)
            self.averages_dialog = None

    def set_current(self, current):
        self.current = current
        self.team_box.edit.setValue(current.team)
        self.level_box.edit.setValue(current.level)
        self.class_box.edit.setValue(current.klass)
        if current.variant:
            self.variant_box.edit.setText(current.variant)
        else:
            self.variant_box.edit.clear()
        self.faction_box.edit.setValue(current.faction)
        self.ai_box.edit.setValue(current.ai)
        self.item_widget.set_current(current.starting_items)
        if self.averages_dialog:
            self.averages_dialog.set_current(current)

    @classmethod
    def get_unit(cls, parent, last_touched_generic=None, unit=None):
        dialog = cls(parent, last_touched_generic, unit)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            unit = dialog.current
            return unit, True
        else:
            return None, False

    def hideEvent(self, event):
        self.close_averages()
