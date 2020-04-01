from functools import partial

from PyQt5.QtWidgets import QWidget, QLabel, QToolButton, QPushButton, \
    QSpinBox, QHBoxLayout, QListWidget, QListWidgetItem, \
    QDialog, QTreeView, QDialogButtonBox, QVBoxLayout, QItemDelegate
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, pyqtSignal

from app.data.data import Data
from app.data.database import DB
from app.data import item_components

from app.extensions.custom_gui import ComboBox
from app.extensions.list_widgets import AppendMultiListWidget

class ComponentList(QListWidget):
    order_swapped = pyqtSignal(int, int)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.index_list = []

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(4)  # Internal Move

        self.model().rowsMoved.connect(self.row_moved)

    def clear(self):
        super().clear()
        self.index_list.clear()

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

    def row_moved(self, parent, start, end, destination, row):
        # print(start, end, row, flush=True)
        elem = self.index_list.pop(start)
        self.index_list.insert(row, elem)
        self.order_swapped.emit(start, row)

class BoolItemComponent(QWidget):
    def __init__(self, data, parent):
        super().__init__(parent)
        self._data = data
        self.window = parent

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
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = int(val)

class HitItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = QSpinBox(self)
        self.editor.setMaximumWidth(40)
        self.editor.setValue(self._data.value)
        self.editor.setSingleStep(5)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class UsesItemComponent(IntItemComponent):
    def on_value_changed(self, val):
        self._data.value = int(val)
        self.window.update_value_boxes()

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

class SpellItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor1 = ComboBox(self)
        self.editor1.setMaximumWidth(120)
        for weapon_rank in DB.weapon_ranks.value():
            self.editor1.addItem(weapon_rank.nid)
        self.editor1.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor1)

        self.editor2 = ComboBox(self)
        for spell_affect in item_components.SpellAffect:
            self.editor2.addItem(spell_affect.name)
        self.editor2.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor2)

        self.editor3 = ComboBox(self)
        for spell_target in item_components.SpellTarget:
            self.editor3.addItem(spell_target.name)
        self.editor3.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor3)

    def on_value_changed(self, val):
        v1 = self.editor1.currentText()
        v2 = item_components.SpellAffect[self.editor2.currentText()].value
        v3 = item_components.SpellTarget[self.editor3.currentText()].value
        self._data.value = (v1, v2, v3)

class EffectiveDelegate(QItemDelegate):
    int_column = 1
    tag_column = 0

    def createEditor(self, parent, option, index):
        if index.column() == self.int_column:
            editor = QSpinBox(parent)
            editor.setRange(-255, 255)
            return editor
        elif index.column() == self.tag_column:
            editor = ComboBox(parent)
            for tag in DB.tags:
                editor.addItem(tag.nid)
            return editor
        else:
            return super().createEditor(parent, option, index)

class EffectiveItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        attrs = ("tag", "damage")
        self.editor = AppendMultiListWidget(self._data.value, self._data.name, attrs, EffectiveDelegate, self)
        self.editor.view.setColumnWidth(0, 100)
        self.editor.view.setMaximumHeight(75)

        hbox.addWidget(self.editor)

def get_display_widget(component, parent):
    if component.attr == bool:
        c = BoolItemComponent(component, parent)
    elif component.attr == item_components.EffectiveSubComponent:
        c = EffectiveItemComponent(component, parent)
    elif component.nid == 'uses':
        c = UsesItemComponent(component, parent)
    elif component.nid in ('hit', 'crit'):
        c = HitItemComponent(component, parent)
    elif component.attr == int:
        c = IntItemComponent(component, parent)
    elif component.attr == 'WeaponType':
        c = WeaponTypeItemComponent(component, parent)
    elif component.attr == 'WeaponRank':
        c = WeaponRankItemComponent(component, parent)
    elif component.nid == 'spell':  # TODO
        c = SpellItemComponent(component, parent)
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

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        layout.addWidget(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

    def get_checked(self):
        components = item_components.item_components
        # sort based off position in item_components
        sorted_components = sorted(self.model.checked, key=lambda x: [c.nid for c in components].index(x))
        return sorted_components

class ComponentModel(QAbstractItemModel):
    def __init__(self, data, already_present, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.already_present = already_present
        self.checked = set()
    
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
            return data.name
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
        if data.nid in self.already_present.keys():
            pass
        elif data.requires(set(self.already_present.keys()) | self.checked):
            basic_flags |= Qt.ItemIsEnabled | Qt.ItemIsSelectable
            basic_flags |= Qt.ItemIsUserCheckable
        return basic_flags
