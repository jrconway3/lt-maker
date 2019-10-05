from functools import partial

from PyQt5.QtWidgets import QWidget, QLabel, QToolButton, \
    QSpinBox, QHBoxLayout, QListWidget, QListWidgetItem, \
    QDialog, QTreeView, QDialogButtonBox, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex

from app.data.database import DB
from app.data.weapons import WeaponType, WeaponRank

from app.editor.custom_gui import ComboBox

class ComponentList(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.index_list = []

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
        self._data.value = val

class WeaponTypeItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_type in DB.weapons.values():
            self.editor.addItem(weapon_type.nid)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = DB.weapons.get(val)

class WeaponRankItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_rank in DB.weapon_ranks.values():
            self.editor.addItem(weapon_rank.nid)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = DB.weapon_ranks.get(val)

def get_display_widget(component, parent):
    if component.attr == bool:
        c = BoolItemComponent(component, parent)
    elif component.attr == int:
        c = IntItemComponent(component, parent)
    elif component.attr == WeaponType:
        c = WeaponTypeItemComponent(component, parent)
    elif component.attr == WeaponRank:
        c = WeaponRankItemComponent(component, parent)
    elif type(component.attr) == tuple:  # TODO
        c = BoolItemComponent(component, parent)
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
        return self.model.checked

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
        if data.nid in self.already_present:
            pass
        elif data.requires(set(self.already_present.keys()) | self.checked):
            basic_flags |= Qt.ItemIsEnabled | Qt.ItemIsSelectable
            basic_flags |= Qt.ItemIsUserCheckable
        return basic_flags
