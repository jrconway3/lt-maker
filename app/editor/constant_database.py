from PyQt5.QtWidgets import QGridLayout, QLineEdit, QSpinBox, QHBoxLayout, \
    QVBoxLayout, QGroupBox, QTreeView, QWidget
from PyQt5.QtCore import Qt, QAbstractItemModel

from app.data.data import Data
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, ComboBox

from app.editor.base_database_gui import DatabaseTab
from app.editor.component_database import ComponentModel

class BoolConstantsModel(ComponentModel):
    def __init__(self, data, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.window = parent
        self._data = data

    def data(self, index, role):
        if not index.isValid():
            return None
        data = self._data[index.row()]
        if role == Qt.DisplayRole:
            return data.name
        elif role == Qt.CheckStateRole:
            value = Qt.Checked if data.value else Qt.Unchecked
            return value
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            data = self._data[index.row()]
            if value == Qt.Checked:
                data.value = True
            else:
                data.value = False
            self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemNeverHasChildren | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        return basic_flags

class ConstantDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.constants
        title = "Constants"

        dialog = cls(data, title, parent)
        return dialog

    def update_list(self):
        pass

    def reset(self):
        pass

    # Now we get to the new stuff
    def __init__(self, data, title, parent=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = data
        self.saved_data = self.save()
        self.title = title

        self.setWindowTitle('%s Editor' % self.title)
        self.setStyleSheet("font: 10pt")

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        bool_section = QGroupBox(self)
        bool_constants = Data([d for d in self._data if d.attr == bool])
        bool_model = BoolConstantsModel(bool_constants, self)
        bool_view = QTreeView()
        bool_view.setModel(bool_model)
        bool_view.header().hide()

        bool_layout = QHBoxLayout()
        bool_section.setLayout(bool_layout)
        bool_layout.addWidget(bool_view)

        battle_constants = ('num_items', 'num_accessories', 'min_damage', 'unarmed_disadvantage', 'enemy_leveling', 'rng')
        battle_section = self.create_section(battle_constants)
        battle_section.setTitle("Battle Constants")
        misc_constants = ('title', 'steal')
        misc_section = self.create_section(misc_constants)
        misc_section.setTitle("Miscellaneous Constants")

        self.layout.addWidget(battle_section, 0, 0)
        self.layout.addWidget(misc_section, 1, 0)
        self.layout.addWidget(bool_section, 0, 1, 2, 1)

    def create_section(self, constants):
        section = QGroupBox(self)
        layout = QVBoxLayout()
        section.setLayout(layout)
        
        for constant_nid in constants:
            constant = self._data.get(constant_nid)
            if not constant:
                print("Couldn't find constant %s" % constant_nid)
                continue
            if constant.attr == int:
                box = PropertyBox(constant.name, QSpinBox, self)
                box.edit.setRange(0, 10)
                box.edit.setValue(constant.value)
                box.edit.valueChanged.connect(constant.set_value)
            elif constant.attr == str:
                box = PropertyBox(constant.name, QLineEdit, self)
                box.edit.setText(constant.value)
                box.edit.textChanged.connect(constant.set_value)
            else: # Choice tuple
                box = PropertyBox(constant.name, ComboBox, self)
                box.edit.addItems(constant.attr)
                box.edit.setValue(constant.value)
                box.edit.currentTextChanged.connect(constant.set_value)
            layout.addWidget(box)
        return section

        # self.layout.addWidget()
