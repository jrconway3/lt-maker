from functools import partial

from PyQt5.QtWidgets import QWidget, QLabel, QToolButton, QDoubleSpinBox, \
    QSpinBox, QHBoxLayout, QListWidgetItem, QItemDelegate, QComboBox
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt

from app.data.database import DB
from app.data.item_components import Type

from app.extensions.color_icon import ColorIcon, AlphaColorIcon
from app.extensions.custom_gui import ComboBox
from app.extensions.widget_list import WidgetList
from app.extensions.list_widgets import AppendMultiListWidget, AppendSingleListWidget

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
        self.set_format()
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = int(val)

    def set_format(self):
        self.editor.setMaximumWidth(40)
        self.editor.setRange(-255, 255)

class HitItemComponent(IntItemComponent):
    def set_format(self):
        self.editor.setMaximumWidth(40)
        self.editor.setRange(-255, 255)
        self.editor.setSingleStep(5)

class ValueItemComponent(IntItemComponent):
    def set_format(self):
        self.editor.setMaximumWidth(60)
        self.editor.setRange(0, 99999)

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
        if not self._data.value and DB.weapons:
            self._data.value = DB.weapons[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class WeaponRankItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_rank in DB.weapon_ranks.values():
            self.editor.addItem(weapon_rank.nid)
        if not self._data.value and DB.weapon_ranks:
            self._data.value = DB.weapon_ranks[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class EquationItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        self.editor.setInsertPolicy(QComboBox.NoInsert)
        self.editor.addItems(DB.equations.keys())
        if not self._data.value and DB.equations:
            self._data.value = DB.equations[0].nid
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
        self.editor = AppendSingleListWidget(self._data.value, self._data.name, self.delegate, self)
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
        if component.nid == 'hit':
            c = HitItemComponent(component, parent)
        elif component.nid == 'value':
            c = ValueItemComponent(component, parent)
        else:
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
            component.value = []
            c = ListItemComponent(component, parent, delegate)
        elif component.expose[0] == Type.Dict:
            component.value = {}
            c = DictItemComponent(component, parent, delegate)

    else:  # TODO
        c = BoolItemComponent(component, parent)
    return c
