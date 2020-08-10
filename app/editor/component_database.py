from functools import partial

from PyQt5.QtWidgets import QWidget, QLabel, QToolButton, QDoubleSpinBox, \
    QSpinBox, QHBoxLayout, QListWidgetItem, \
    QDialog, QTreeView, QDialogButtonBox, QVBoxLayout, QItemDelegate, QComboBox
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex

from app.data.database import DB
from app.data.item_component import Type

from app.extensions.color_icon import ColorIcon, AlphaColorIcon
from app.extensions.custom_gui import ComboBox
from app.extensions.widget_list import WidgetList
from app.extensions.list_widgets import AppendMultiListWidget

from app.engine import item_component

class ComponentList(WidgetList):
    def add_component(self, component):
        item = QListWidgetItem()
        item.setSizeHint(component.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, component)
        self.index_list.append(component.data.nid)
        return item

    def remove_component(self, component):
        if component.data.nid in self.index_list:
            idx = self.index_list.index(component.data.nid)
            self.index_list.remove(component.data.nid)
            return self.takeItem(idx)
        return None

class BoolItemComponent(QWidget):
    delegate = None

    def __init__(self, data, parent, delegate=None):
        super().__init__(parent)
        self._data = data
        self.window = parent
        self.delegate = delegate

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

        name_label = QLabel(self._data.name)
        hbox.addWidget(name_label)

        self.create_editor(hbox)

        x_button = QToolButton(self)
        x_button.setIcon(QIcon("icons/x.png"))
        x_button.setStyleSheet("QToolButton { border: 0px solid #575757; background-color: palette(base); }")
        x_button.clicked.connect(partial(self.window.remove_component, self))
        hbox.addWidget(x_button, Qt.AlignRight)

    def create_editor(self, hbox):
        pass

    def on_value_changed(self, val):
        self._data.value = val

    @property
    def data(self):
        return self._data
        
class IntItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = QSpinBox(self)
        self.editor.setMaximumWidth(40)
        self.editor.setRange(-255, 255)
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = int(val)

class HitItemComponent(IntItemComponent):
    def create_editor(self, hbox):
        super().create_editor(hbox)
        self.editor.setSingleStep(5)

class FloatItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = QDoubleSpinBox(self)
        self.editor.setMaximumWidth(40)
        self.editor.setRange(0, 1)
        self.editor.setSingleStep(.05)
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = float(val)

class WeaponTypeItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_type in DB.weapons.values():
            self.editor.addItem(weapon_type.nid)
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class WeaponRankItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_rank in DB.weapon_ranks.values():
            self.editor.addItem(weapon_rank.nid)
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class EquationItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        self.editor.setInsertPolicy(QComboBox.NoInsert)
        self.editor.addItems(DB.equations.keys())
        self.editor.lineEdit().editingFinished.connect(self.on_value_changed)

    def on_value_changed(self):
        val = self.editor.currentText()
        self._data.value = val

class Color3ItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        color = self._data.value
        self.color = ColorIcon(QColor(*color).name(), self)
        self.color.colorChanged.connect(self.on_value_changed)
        hbox.addWidget(self.color)

    def on_value_changed(self, val):
        color = self.color.color().getRgb()
        self._data.value = color

class Color4ItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        color = self._data.value
        self.color = AlphaColorIcon(QColor(*color).name(), self)
        self.color.colorChanged.connect(self.on_value_changed)
        hbox.addWidget(self.color)

    def on_value_changed(self, val):
        color = self.color.color().getRgba()
        self._data.value = color

# Delegates
class UnitDelegate(QItemDelegate):
    data = DB.units
    name = "Unit"

    def createEditor(self, parent, option, index):
        if index.column() == 0:
            editor = ComboBox(parent)
            for obj in self.data:
                editor.addItem(obj.nid)
            return editor
        elif index.column() == 1:  # Integer value column
            editor = QSpinBox(parent)
            editor.setRange(-255, 255)
            return editor
        else:
            return super().createEditor(parent, option, index)

class ClassDelegate(UnitDelegate):
    data = DB.classes
    name = "Class"

class TagDelegate(UnitDelegate):
    data = DB.tags
    name = "Tag"

class ItemDelegate(UnitDelegate):
    data = DB.items
    name = "Item"

class StatDelegate(UnitDelegate):
    data = DB.stats
    name = "Stat"

class WeaponTypeDelegate(UnitDelegate):
    data = DB.weapons
    name = "Weapon Type"

class ListItemComponent(BoolItemComponent):
    delegate = None

    def create_editor(self, hbox):    
        self.editor = AppendMultiListWidget(self._data.value, self._data.name, (self.delegate.name), self.delegate, self)
        self.editor.view.setColumnWidth(0, 100)
        self.editor.view.setMaximumHeight(75)
        self.editor.model.nid_column = 0

        hbox.addWidget(self.editor)

class DictItemComponent(BoolItemComponent):
    delegate = None

    def create_editor(self, hbox):    
        self.editor = AppendMultiListWidget(self._data.value, self._data.name, (self.delegate.name, "Value"), self.delegate, self)
        self.editor.view.setColumnWidth(0, 100)
        self.editor.view.setMaximumHeight(75)
        self.editor.model.nid_column = 0

        hbox.addWidget(self.editor)

def get_display_widget(component, parent):
    if not component.expose:
        c = BoolItemComponent(component, parent)
    elif component.expose == Type.Int:
        c = IntItemComponent(component, parent)
    elif component.expose == Type.Float:
        c = FloatItemComponent(component, parent)
    elif component.expose == Type.WeaponType:
        c = WeaponTypeItemComponent(component, parent)
    elif component.expose == Type.WeaponRank:
        c = WeaponRankItemComponent(component, parent)
    elif isinstance(component.expose, tuple):
        delegate = None
        if component.expose[1] == Type.Unit:
            delegate = UnitDelegate
        elif component.expose[1] == Type.Class:
            delegate = ClassDelegate
        elif component.expose[1] == Type.Tag:
            delegate = TagDelegate
        elif component.expose[1] == Type.Item:
            delegate = ItemDelegate
        elif component.expose[1] == Type.Stat:
            delegate = StatDelegate
        elif component.expose[1] == Type.WeaponType:
            delegate = WeaponTypeDelegate

        if component.expose[0] == Type.List:
            c = ListItemComponent(component, parent, delegate)
        elif component.expose[0] == Type.Dict:
            c = DictItemComponent(component, parent, delegate)

    else:  # TODO
        c = BoolItemComponent(component, parent)
    return c

class ComponentDialog(QDialog):
    def __init__(self, data, title, parent=None):
        super().__init__(parent)

        self.window = parent
        self._data = data
        self.current_components = self.window.current.components

        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.model = ComponentModel(data, self.current_components, self)

        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.header().hide()
        self.view.clicked.connect(self.on_click)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        layout.addWidget(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

    def get_checked(self):
        components = item_component.get_item_components()
        # remove components that were already present
        checked = self.model.checked - set(self.model.already_present.keys())
        # sort based off position in item_components
        sorted_components = sorted(checked, key=lambda x: [c.nid for c in components].index(x))
        return sorted_components

    def on_click(self, index):
        # Only if clickable
        if bool(self.model.flags(index) & Qt.ItemIsEnabled):
            nid_clicked = self.model._data[index.row()].nid
            if nid_clicked in self.model.checked:
                self.model.checked.discard(nid_clicked)
            else:
                self.model.checked.add(nid_clicked)
            self.model.dataChanged.emit(index, index)

class ComponentModel(QAbstractItemModel):
    def __init__(self, data, already_present, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.already_present = already_present
        self.checked = set(self.already_present.keys())
    
    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        return None

    def index(self, row, column, parent_index=QModelIndex()):
        if self.hasIndex(row, column, parent_index):
            return self.createIndex(row, column)
        return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        data = self._data[index.row()]
        if role == Qt.DisplayRole:
            return data.class_name()
        elif role == Qt.CheckStateRole:
            value = Qt.Checked if data.nid in self.checked else Qt.Unchecked
            return value
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            data = self._data[index.row()]
            if value == Qt.Checked:
                self.checked.add(data.nid)
            else:
                self.checked.discard(data.nid)
            self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemNeverHasChildren
        data = self._data[index.row()]
        true_components = set(self.already_present.keys()) | self.checked
        if data.nid in self.already_present.keys():
            pass
        elif not data.requires or all(r in true_components for r in data.requires):
            basic_flags |= Qt.ItemIsEnabled | Qt.ItemIsSelectable
            # basic_flags |= Qt.ItemIsUserCheckable
        return basic_flags
